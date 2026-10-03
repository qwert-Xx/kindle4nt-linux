#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Deterministic host-only RAM archive from a hashed external file recipe."""
import gzip,hashlib,json,pathlib,stat,subprocess,tempfile,os,re
import rootfs_sources

def name(value):
    p=pathlib.PurePosixPath(value)
    if not value or p.is_absolute() or any(x in ('','.', '..') for x in value.split('/')) or '\x00' in value:
        raise ValueError('unsafe root path')
    return value

def load(path):
    path=pathlib.Path(path).resolve();d=json.loads(path.read_text());seen=set()
    sources=rootfs_sources.files('common','busybox/maintenance','busybox/ram')
    if d.get('automatic_diagnostics',False): sources.pop('bin/k4-bootmark')
    d['entries']=[e for e in d['entries'] if not rootfs_sources.diagnostic(e['name'])]
    for e in d['entries']:
        n=name(e['name'])
        if n in seen: raise ValueError('duplicate root path')
        seen.add(n)
        if e['kind']=='file':
            src=sources.get(n)
            if src is None: src=(path.parent/e['source']).resolve()
            if n not in sources and (not src.is_file() or hashlib.sha256(src.read_bytes()).hexdigest()!=e['sha256']):
                raise ValueError('root input hash mismatch: '+n)
            e['resolved']=str(src)
            if n in sources: e['mode']=stat.S_IMODE(src.stat().st_mode)
        elif e['kind'] not in ('dir','link','char','block'):raise ValueError('unsupported root entry')
    if 'busybox_links' in d:
        item = d['busybox_links']
        links = (path.parent / item['path']).resolve()
        if hashlib.sha256(links.read_bytes()).hexdigest() != item['sha256']:
            raise ValueError('BusyBox links hash mismatch')
        d['busybox_links_resolved'] = str(links)
    return d

def input_paths(recipe):
    """List the recipe and hashed file inputs before an output is cleaned."""
    recipe=pathlib.Path(recipe).resolve();d=load(recipe)
    paths=[recipe]+[pathlib.Path(e['resolved']) for e in d['entries'] if e['kind']=='file']
    if 'busybox_links_resolved' in d: paths.append(pathlib.Path(d['busybox_links_resolved']))
    if 'filesystem_recipe' in d:
        nested=recipe.parent/d['filesystem_recipe']
        if hashlib.sha256(nested.read_bytes()).hexdigest()!=d['filesystem_recipe_sha256']:
            raise ValueError('nested recipe hash mismatch')
        paths+=input_paths(nested)
    return paths
def archive(d):
    result=bytearray()
    def add(n,mode,data=b'',major=0,minor=0,ino=1):
        fields=(ino,mode,0,0,1,0,len(data),0,0,major,minor,len(n.encode())+1,0)
        result.extend(b'070701'+b''.join(f'{x:08x}'.encode() for x in fields))
        result.extend(n.encode()+b'\0');result.extend(b'\0'*(-len(result)%4))
        result.extend(data);result.extend(b'\0'*(-len(result)%4))
    for ino,e in enumerate(sorted(d['entries'],key=lambda e:e['name']),1):
        k=e['kind'];data=((rootfs_sources.ROOT/'common/bin/k4-bootmark').read_bytes() if e['name']=='bin/k4-bootmark' and not d.get('automatic_diagnostics',False) else pathlib.Path(e['resolved']).read_bytes()) if k=='file' else e.get('target','').encode() if k=='link' else b''
        types={'file':stat.S_IFREG,'dir':stat.S_IFDIR,'link':stat.S_IFLNK,'char':stat.S_IFCHR,'block':stat.S_IFBLK}
        add(e['name'],types[k]|e['mode'],data,e.get('major',0),e.get('minor',0),ino)
    add('TRAILER!!!',0);result.extend(b'\0'*(-len(result)%512))
    return gzip.compress(result,mtime=0)

def modalias_startup_entries(entries):
    """Wrap the unchanged external startup; input failure stays nonfatal."""
    entries=[dict(e) for e in entries]
    by_name={e['name']:e for e in entries}
    base='etc/init.d/rcS.k4-base'
    if base in by_name or 'bin/k4-modalias-coldplug' in by_name:
        raise ValueError('module coldplug reserved path already present')
    if 'etc/init.d/rcS' not in by_name or by_name['etc/init.d/rcS']['kind']!='file':
        raise ValueError('module coldplug requires structured rcS startup')
    old=by_name['etc/init.d/rcS'];old['name']=base
    entries.extend(rootfs_sources.entries('busybox/coldplug').values())
    entries.append(rootfs_sources.entries('common')['bin/k4-modalias-coldplug'])
    return entries

def busybox_applet_entries(entries, links):
    """Install the supplied BusyBox applets without replacing standalone tools."""
    entries = [dict(e) for e in entries]
    existing = {e['name']: e for e in entries}
    binary = existing.get('bin/busybox')
    if binary is None or binary['kind'] != 'file':
        return entries
    if links is None: raise ValueError('maintenance recipe requires hashed busybox_links from its BusyBox build')
    applets = pathlib.Path(links).read_text().splitlines()
    for applet in applets:
        n = name(applet.removeprefix('/'))
        if n != 'linuxrc' and pathlib.PurePosixPath(n).parent.as_posix() not in ('bin', 'sbin', 'usr/bin', 'usr/sbin'):
            raise ValueError('unexpected BusyBox applet path: ' + n)
        if n in existing:
            continue
        parent = pathlib.PurePosixPath(n).parent
        for directory in reversed(parent.parents):
            if str(directory) != '.' and str(directory) not in existing:
                e = {'name': str(directory), 'kind': 'dir', 'mode': 0o755}
                entries.append(e); existing[e['name']] = e
        if str(parent) != '.' and str(parent) not in existing:
            e = {'name': str(parent), 'kind': 'dir', 'mode': 0o755}
            entries.append(e); existing[e['name']] = e
        e = {'name': n, 'kind': 'link', 'mode': 0o777, 'target': '/bin/busybox'}
        entries.append(e); existing[n] = e
    return entries

def filesystem(recipe,output,diagnostics=None,modules=None,release=None,modalias_coldplug=False,formal_modules=True):
    """Create a regular host ext3 file; never mount it or open a block device."""
    d=load(recipe); output=pathlib.Path(output).absolute()
    d['entries']=[e for e in d['entries'] if 'watchdog-guard' not in e['name'] and 'watchdog-probe' not in e['name']]
    if output.exists() and (output.is_symlink() or not output.is_file()):
        raise ValueError('filesystem output must be a regular host file')
    if output.resolve() in input_paths(recipe):
        raise ValueError('output overlaps input')
    if diagnostics is None: diagnostics=bool(d.get('automatic_diagnostics',False))
    if modules is not None:
        template_modes={tuple(pathlib.PurePosixPath(e['name']).parts[3:]):e['mode'] for e in d['entries'] if e['name'].startswith('lib/modules/')}
        d['entries']=[e for e in d['entries'] if not e['name'].startswith('lib/modules/') ]
        for p in sorted(pathlib.Path(modules).rglob('*')):
            n=p.relative_to(modules).as_posix()
            if not n.startswith('lib/modules/') or p.is_symlink(): continue
            if release is not None and len(pathlib.PurePosixPath(n).parts)>2 and pathlib.PurePosixPath(n).parts[2]!=release:continue
            k='dir' if p.is_dir() else 'file'
            e={'name':n,'kind':k,'mode':template_modes.get(tuple(pathlib.PurePosixPath(n).parts[3:]),0o755 if k=='dir' else 0o644)}
            if k=='file':
                e['resolved']=str(p)
            d['entries'].append(e)
    if modalias_coldplug: d['entries']=modalias_startup_entries(d['entries'])
    d['entries']=busybox_applet_entries(d['entries'], d.get('busybox_links_resolved'))
    entries={e['name']:e for e in d['entries']}
    for n,e in entries.items():
        parent=pathlib.PurePosixPath(n).parent
        while str(parent)!='.':
            if str(parent) not in entries or entries[str(parent)]['kind']!='dir':
                raise ValueError('non-directory parent')
            parent=parent.parent
    reproducible=bool(d.get('reproducible_metadata',False))
    env=dict(os.environ, E2FSPROGS_FAKE_TIME='1727740800') if reproducible else None
    with tempfile.TemporaryDirectory(prefix='rootfs.',dir=output.parent) as td:
        stage=pathlib.Path(td)/'tree';stage.mkdir()
        for e in sorted(d['entries'],key=lambda x:(x['name'].count('/'),x['name'])):
            p=stage/e['name'];k=e['kind']
            if k=='dir':p.mkdir(exist_ok=True)
            elif k=='file':p.write_bytes((rootfs_sources.ROOT/'common/bin/k4-bootmark').read_bytes() if e['name']=='bin/k4-bootmark' and not diagnostics else pathlib.Path(e['resolved']).read_bytes())
            elif k=='link':p.symlink_to(e['target'])
            elif k in ('char','block'):p.touch()
            if k in ('dir','file'):p.chmod(e['mode'])
        with output.open('wb') as f:f.truncate(d['image_bytes'])
        extra=['-E','hash_seed='+d['uuid']] if reproducible else []
        subprocess.run(['mke2fs','-q','-F','-t','ext3','-b','4096','-I','256','-m','0',
                        '-U',d['uuid'],'-O','^64bit,^metadata_csum']+extra+['-d',str(stage),str(output)],check=True,env=env)
        # mke2fs imports path names directly. Address metadata by inode,
        # avoiding debugfs's shell-like path parser (which cannot escape quotes).
        inodes={'.':2}
        directories=['.']+[e['name'] for e in sorted(d['entries'],key=lambda e:e['name'].count('/')) if e['kind']=='dir']
        for directory in directories:
            listing=subprocess.check_output(['debugfs','-R','ls -p <'+str(inodes[directory])+'>',str(output)],stderr=subprocess.DEVNULL)
            for match in re.finditer(rb'/([0-9]+)/[0-7]+/[0-9]+/[0-9]+/([^/]*)/[^/]*/\n',listing):
                child=os.fsdecode(match[2])
                if child not in ('.','..'):
                    n=child if directory=='.' else directory+'/'+child
                    inodes[n]=int(match[1])
        commands=[]
        for e in d['entries']:
            n='<'+str(inodes[e['name']])+'>'
            if e['kind'] in ('char','block'):
                # Empty staged files become device inodes inside the image;
                # Linux's new_encode_dev layout is stored in i_block[1].
                major,minor=e['major'],e['minor']
                device=(minor & 0xff) | (major << 8) | ((minor & ~0xff) << 12)
                commands.append('set_inode_field '+n+' block[1] '+str(device))
            types={'file':stat.S_IFREG,'dir':stat.S_IFDIR,'link':stat.S_IFLNK,'char':stat.S_IFCHR,'block':stat.S_IFBLK}
            commands.append('set_inode_field '+n+' mode '+hex(types[e['kind']]|e['mode']))
            for field,value in [('uid',0),('gid',0),('mtime',0),('atime',0)]+([('ctime',0),('crtime',0)] if reproducible else []):
                commands.append('set_inode_field '+n+' '+field+' '+str(value))
        if reproducible:
            for inode in ('<2>','<8>','<11>'):
                for field in ('mtime','atime','ctime','crtime'):
                    commands.append('set_inode_field '+inode+' '+field+' 0')
        batch=pathlib.Path(td)/'commands';batch.write_text('\n'.join(commands)+'\n')
        subprocess.run(['debugfs','-w','-f',str(batch),str(output)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,env=env)
    output.chmod(0o600)
    return {'filesystem_entries':len(entries),'host_regular_image':True}
def build(recipe,output,modules=None,release=None,modalias_coldplug=False,formal_modules=True):
    d=load(recipe);output=pathlib.Path(output)
    if output.resolve() in input_paths(recipe):
        raise ValueError('output overlaps input')
    output.parent.mkdir(parents=True,exist_ok=True)
    if modalias_coldplug and 'filesystem_recipe' not in d:
        raise ValueError('module coldplug requires structured filesystem recipe')
    if 'filesystem_recipe' in d:
        image=output.with_suffix('.ext3')
        nested=pathlib.Path(recipe).parent/d['filesystem_recipe']
        if hashlib.sha256(nested.read_bytes()).hexdigest()!=d['filesystem_recipe_sha256']:
            raise ValueError('nested recipe hash mismatch')
        filesystem(nested,image,bool(d.get('automatic_diagnostics',False)),modules,release,modalias_coldplug,formal_modules)
        entry=next(e for e in d['entries'] if e['name']=='rootfs.ext3')
        entry['resolved']=str(image)
    output.write_bytes(archive(d));output.chmod(0o600)
    return {'entries':len(d['entries']),'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
            'private_inputs':bool(d.get('private_inputs',False)),'automatic_diagnostics':bool(d.get('automatic_diagnostics',False)), 'modalias_coldplug':modalias_coldplug}
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('recipe');p.add_argument('output',nargs='?',default=os.environ.get('OUT','out/ram.cpio.gz'));a=p.parse_args();print(json.dumps(build(a.recipe,a.output),indent=2))
