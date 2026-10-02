#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Offline persistent root from the hashed RAM userspace recipe."""
import gzip,hashlib,io,json,pathlib,shutil,tarfile
import rootfs
HERE=pathlib.Path(__file__).parent
UUID='bc53465e-1be7-4c38-8965-d5bdc7b4c4f1'
def build(recipe,out,modules,release,kernel,dtb):
    outer=rootfs.load(recipe);nested=pathlib.Path(recipe).parent/outer['filesystem_recipe']
    if hashlib.sha256(nested.read_bytes()).hexdigest()!=outer['filesystem_recipe_sha256']:raise ValueError('nested recipe hash mismatch')
    original={e['name']:e for e in rootfs.load(nested)['entries']}
    entries={n:dict(e) for n,e in original.items() if not n.startswith('lib/modules/') and 'watchdog-guard' not in n and 'watchdog-probe' not in n}
    gen=out/'emmc-generated';gen.mkdir(exist_ok=True)
    def file(n,data,mode=0o644):
        src=gen/n.replace('/','_');src.write_text(data)
        entries[n]={'name':n,'kind':'file','mode':mode,'resolved':str(src)}
    rc=pathlib.Path(original['etc/init.d/rcS']['resolved']).read_text()
    rc=rc[:rc.index('root_device=')]+rc[rc.index('# Resolve SPI module aliases'):]
    rc=rc.replace('/bin/k4-bootmark','$bb true').replace('PATH=/bin','PATH=/bin:/sbin:/usr/bin')
    rc=rc.replace('mount_one tmpfs tmpfs /run','mount_one tmpfs tmpfs /run\n$bb mkdir -p /dev/pts\nmount_one devpts devpts /dev/pts\n$bb watchdog -T 30 -t 10 /dev/watchdog')
    rc=rc.replace('RAM-only RNDIS and ACM probe','Linux RNDIS and ACM')
    file('etc/init.d/rcS.k4-base',rc,0o755)
    for n,src in [('etc/init.d/rcS','k4-modalias-startup'),('bin/k4-modalias-coldplug','k4-modalias-coldplug')]:
        entries[n]={'name':n,'kind':'file','mode':0o755,'resolved':str(HERE/'tools'/src)}
    it=pathlib.Path(original['etc/inittab']['resolved']).read_text()
    file('etc/inittab','\n'.join(l for l in it.splitlines() if 'watchdog' not in l.lower())+'\n')
    file('etc/init.d/rcShutdown','#!/bin/busybox sh\n/bin/sh /bin/k4-charge-policy stop > /run/k4-charge-stop.log 2>&1\n/bin/busybox sync\n/bin/busybox mount -o remount,ro /\n',0o755)
    file('etc/k4-root-profile','emmc-root\n')
    file('etc/fstab','/dev/mmcblk2p1 / ext4 defaults 0 1\nproc /proc proc defaults 0 0\nsysfs /sys sysfs defaults 0 0\ndevtmpfs /dev devtmpfs defaults 0 0\ndevpts /dev/pts devpts defaults 0 0\ntmpfs /tmp tmpfs mode=1777 0 0\ntmpfs /run tmpfs mode=0755 0 0\nconfigfs /sys/kernel/config configfs defaults 0 0\n')
    for n,src in [('boot/zImage',kernel),('boot/imx50-kindle-k4.dtb',dtb)]:entries[n]={'name':n,'kind':'file','mode':0o644,'resolved':str(src)}
    module_modes={tuple(pathlib.PurePosixPath(n).parts[3:]):e['mode'] for n,e in original.items() if n.startswith('lib/modules/')}
    for src in sorted(pathlib.Path(modules).rglob('*')):
        n=src.relative_to(modules).as_posix()
        if not n.startswith('lib/modules/'+release) or src.is_symlink():continue
        entries[n]={'name':n,'kind':'dir' if src.is_dir() else 'file','mode':module_modes.get(tuple(pathlib.PurePosixPath(n).parts[3:]),0o755 if src.is_dir() else 0o644),'resolved':str(src)}
    for n in list(entries):
        par=pathlib.PurePosixPath(n).parent
        while str(par)!='.':
            entries.setdefault(str(par),{'name':str(par),'kind':'dir','mode':0o755});par=par.parent
    sums=''.join(hashlib.sha256(b'#!/bin/busybox sh\nexit 0\n' if n=='bin/k4-bootmark' else pathlib.Path(e['resolved']).read_bytes()).hexdigest()+'  '+n+'\n' for n,e in sorted(entries.items()) if e['kind']=='file')
    file('etc/k4-rootfs.sha256',sums)
    tree=out/'rootfs'
    if tree.exists():shutil.rmtree(tree)
    tree.mkdir();manifest=[]
    with (out/'rootfs.tar.gz').open('wb') as raw,gzip.GzipFile(fileobj=raw,mode='wb',filename='',mtime=0) as gz,tarfile.open(fileobj=gz,mode='w',format=tarfile.GNU_FORMAT) as tar:
        for n,e in sorted(entries.items()):
            t=tarfile.TarInfo(n);t.mode=e['mode'];t.uid=t.gid=t.mtime=0;k=e['kind'];dest=tree/n;data=None
            if k=='dir':t.type=tarfile.DIRTYPE;dest.mkdir(parents=True,exist_ok=True)
            elif k=='link':t.type=tarfile.SYMTYPE;t.linkname=e['target'];dest.parent.mkdir(parents=True,exist_ok=True);dest.symlink_to(e['target'])
            elif k in ('char','block'):t.type=tarfile.CHRTYPE if k=='char' else tarfile.BLKTYPE;t.devmajor=e['major'];t.devminor=e['minor']
            else:
                data=pathlib.Path(e['resolved']).read_bytes()
                if n=='bin/k4-bootmark':data=b'#!/bin/busybox sh\nexit 0\n'
                dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);t.size=len(data)
            tar.addfile(t,io.BytesIO(data) if data is not None else None)
            if k in ('dir','file'):dest.chmod(t.mode)
            item={'name':n,'kind':k,'mode':t.mode,'target':e.get('target')}
            if data is not None:item['sha256']=hashlib.sha256(data).hexdigest()
            manifest.append(item)
    report={'entries':manifest,'removed':sorted(set(original)-set(entries)),'changed':sorted(n for n in original.keys() & entries.keys() if original[n]!=entries[n]),'device_nodes_in_tar_only':True,'uuid':UUID,'private_inputs':True,'device_operations':False}
    (out/'rootfs-manifest.json').write_text(json.dumps(report,indent=2)+'\n');return report
