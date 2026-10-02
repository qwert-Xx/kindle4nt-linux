#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Deterministic host-only RAM archive from a hashed external file recipe."""
import gzip,hashlib,json,pathlib,stat,subprocess,tempfile,os

def name(value):
    p=pathlib.PurePosixPath(value)
    if not value or p.is_absolute() or any(x in ('','.', '..') for x in value.split('/')) or '\x00' in value:
        raise ValueError('unsafe root path')
    return value

def load(path):
    path=pathlib.Path(path).resolve();d=json.loads(path.read_text());seen=set()
    for e in d['entries']:
        n=name(e['name'])
        if n in seen: raise ValueError('duplicate root path')
        seen.add(n)
        if e['kind']=='file':
            src=(path.parent/e['source']).resolve()
            if not src.is_file() or hashlib.sha256(src.read_bytes()).hexdigest()!=e['sha256']:
                raise ValueError('root input hash mismatch: '+n)
            e['resolved']=str(src)
        elif e['kind'] not in ('dir','link','char','block'):raise ValueError('unsupported root entry')
    return d

def archive(d):
    result=bytearray()
    def add(n,mode,data=b'',major=0,minor=0,ino=1):
        fields=(ino,mode,0,0,1,0,len(data),0,0,major,minor,len(n.encode())+1,0)
        result.extend(b'070701'+b''.join(f'{x:08x}'.encode() for x in fields))
        result.extend(n.encode()+b'\0');result.extend(b'\0'*(-len(result)%4))
        result.extend(data);result.extend(b'\0'*(-len(result)%4))
    for ino,e in enumerate(sorted(d['entries'],key=lambda e:e['name']),1):
        k=e['kind'];data=(b'#!/bin/busybox sh\nexit 0\n' if e['name']=='bin/k4-bootmark' and not d.get('automatic_diagnostics',False) else pathlib.Path(e['resolved']).read_bytes()) if k=='file' else e.get('target','').encode() if k=='link' else b''
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
    tools=pathlib.Path(__file__).parent/'tools'
    for n,src in [('etc/init.d/rcS','k4-modalias-startup'),('bin/k4-modalias-coldplug','k4-modalias-coldplug')]:
        entries.append({'name':n,'kind':'file','mode':0o755,'resolved':str(tools/src)})
    return entries

def filesystem(recipe,output,diagnostics=None,modules=None,release=None,modalias_coldplug=False,formal_modules=True):
    """Create a regular host ext3 file; never mount it or open a block device."""
    d=load(recipe); output=pathlib.Path(output).absolute()
    if output.exists() and (output.is_symlink() or not output.is_file()):
        raise ValueError('filesystem output must be a regular host file')
    if any(output.resolve()==pathlib.Path(e['resolved']) for e in d['entries'] if e['kind']=='file'):
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
                if formal_modules and (n.endswith(('/dmatest.ko','/usbtest.ko','/k4-mc13892-monitor.ko','/k4-pm-trace.ko')) or '/k4-debug/' in n):
                    raise ValueError('diagnostic module in production root: '+n)
                e['resolved']=str(p)
            d['entries'].append(e)
    if modalias_coldplug: d['entries']=modalias_startup_entries(d['entries'])
    entries={e['name']:e for e in d['entries']}
    for n,e in entries.items():
        if any(c.isspace() or c in '"\'\\' for c in n):raise ValueError('unsupported filesystem path')
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
            elif k=='file':p.write_bytes(b'#!/bin/busybox sh\nexit 0\n' if e['name']=='bin/k4-bootmark' and not diagnostics else pathlib.Path(e['resolved']).read_bytes())
            elif k=='link':p.symlink_to(e['target'])
            if k in ('dir','file'):p.chmod(e['mode'])
        with output.open('wb') as f:f.truncate(d['image_bytes'])
        extra=['-E','hash_seed='+d['uuid']] if reproducible else []
        subprocess.run(['mke2fs','-q','-F','-t','ext3','-b','4096','-I','256','-m','0',
                        '-U',d['uuid'],'-O','^64bit,^metadata_csum']+extra+['-d',str(stage),str(output)],check=True,env=env)
        commands=[]
        for e in d['entries']:
            n='/'+e['name']
            if e['kind'] in ('char','block'):
                # debugfs mknod creates a filesystem inode, not a host device.
                commands += ['cd /'+str(pathlib.PurePosixPath(e['name']).parent),
                             'mknod '+pathlib.PurePosixPath(n).name+' '+('c' if e['kind']=='char' else 'b')+' '+str(e['major'])+' '+str(e['minor'])]
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
    p=argparse.ArgumentParser();p.add_argument('recipe');p.add_argument('output');a=p.parse_args();print(json.dumps(build(a.recipe,a.output),indent=2))
