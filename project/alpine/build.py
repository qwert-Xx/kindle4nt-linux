#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""User-mode, offline Alpine/K4 assembly. Never accesses a device."""
import argparse,gzip,hashlib,io,json,os,pathlib,shutil,stat,subprocess,tarfile
HERE=pathlib.Path(__file__).resolve().parent
RELEASE='6.6.157-k4-production'
def sha(p,algorithm='sha256'):return hashlib.new(algorithm,p.read_bytes()).hexdigest()
def run(args,log=None):
    r=subprocess.run([str(x) for x in args],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if log:log.write_text(r.stdout)
    if r.returncode:raise RuntimeError(str(args)+'\n'+r.stdout)
    return r.stdout
def write(root,name,text,mode=0o644):
    p=root/name;p.parent.mkdir(parents=True,exist_ok=True)
    if p.is_symlink():p.unlink()
    p.write_text(text);p.chmod(mode)
def link(root,name,target):
    p=root/name;p.parent.mkdir(parents=True,exist_ok=True)
    if p.is_symlink() or p.exists():p.unlink()
    p.symlink_to(target)
def archive(root,path):
    paths={p.relative_to(root).as_posix():p for p in root.rglob('*')}
    nodes={'dev/console':(5,1,0o600),'dev/null':(1,3,0o666)}
    with path.open('wb') as raw,gzip.GzipFile(fileobj=raw,mode='wb',filename='',mtime=0) as gz,tarfile.open(fileobj=gz,mode='w',format=tarfile.GNU_FORMAT) as t:
        for n in sorted(set(paths)|set(nodes)):
            if n in nodes:
                major,minor,mode=nodes[n];ti=tarfile.TarInfo(n);ti.type=tarfile.CHRTYPE;ti.mode=mode;ti.devmajor=major;ti.devminor=minor;t.addfile(ti);continue
            p=paths[n];ti=t.gettarinfo(str(p),n);ti.uid=ti.gid=ti.mtime=0;ti.uname=ti.gname=''
            with p.open('rb') if p.is_file() and not p.is_symlink() else io.BytesIO() as f:t.addfile(ti,f if ti.isfile() else None)
def installed(root):
    result={}
    for b in (root/'lib/apk/db/installed').read_text().strip().split('\n\n'):
        d=dict(l.split(':',1) for l in b.splitlines() if ':' in l);result[d['P']]=d['V']
    return result
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--cache',type=pathlib.Path,required=True);ap.add_argument('--k4-repo',type=pathlib.Path,required=True);ap.add_argument('--busybox-tar',type=pathlib.Path);ap.add_argument('--busybox-sha');ap.add_argument('--k4-root',type=pathlib.Path);ap.add_argument('--public-key',type=pathlib.Path);ap.add_argument('--out',type=pathlib.Path,required=True);ap.add_argument('--kernel',type=pathlib.Path,required=True);ap.add_argument('--dtb',type=pathlib.Path,required=True);ap.add_argument('--modules',type=pathlib.Path,required=True);a=ap.parse_args()
    a.out.mkdir(mode=0o700);out=a.out.resolve();cache=a.cache.resolve();root=out/'rootfs';root.mkdir()
    lock=json.loads((HERE/'packages.lock.json').read_text())
    def checked(name,d,key='sha256'):p=cache/name;assert sha(p,key)==d[key],name;return p
    mini=checked(lock['minirootfs']['file'],lock['minirootfs']);hostpkg=checked(lock['host_apk']['file'],lock['host_apk']);hostmini=checked(lock['host_mini']['file'],lock['host_mini']);qdeb=checked(lock['qemu']['file'],lock['qemu'],'sha512')
    for d in lock['packages']:checked(d['file'],d)
    assert sha(cache/'APKINDEX-armv7.tar.gz')==lock['index_sha256']
    if a.busybox_tar:assert sha(a.busybox_tar)==a.busybox_sha
    run(['tar','-xf',mini,'-C',root]);host=out/'host';host.mkdir();run(['tar','-xf',hostpkg,'-C',host]);keys=out/'hostkeys';keys.mkdir();run(['tar','-xf',hostmini,'-C',keys,'./etc/apk/keys'])
    apk=host/'sbin/apk.static'
    local=a.k4_repo.resolve();lp=local/'armv7/wpa_supplicant-2.12-r0.apk'
    if a.busybox_tar:
        assert sha(lp)==lock['local_package']['apk_sha256']
        assert sha(local/'armv7/APKINDEX.tar.gz')==lock['local_package']['index_sha256']
    public_key=a.public_key or HERE/'k4-alpine.rsa.pub'
    shutil.copy2(public_key,root/'etc/apk/keys'/public_key.name)
    run([apk,'--keys-dir',keys/'etc/apk/keys','verify',hostpkg],out/'host-apk-signature.log')
    repo=out/'repository/armv7';repo.mkdir(parents=True);shutil.copy2(cache/'APKINDEX-armv7.tar.gz',repo/'APKINDEX.tar.gz')
    for d in lock['packages']:(repo/d['file']).symlink_to(cache/d['file'])
    repositories=out/'repositories';repositories.write_text(str(repo.parent)+'\n@k4 '+str(local)+'\n')
    common=[apk,'--root',root,'--arch','armv7','--keys-dir',root/'etc/apk/keys','--repositories-file',repositories,'--no-network']
    # apk authenticates the index and checks each selected archive against it.
    (out/'fetched').mkdir()
    run(common+['fetch','--recursive','--output',out/'fetched']+[d['name']+'='+d['version'] for d in lock['packages']]+['wpa_supplicant@k4'],out/'index-and-package-check.log')
    run([apk,'--keys-dir',root/'etc/apk/keys','verify']+[repo/d['file'] for d in lock['packages']]+[lp],out/'package-signatures.log')
    run(common+['--no-scripts','add','--usermode','--upgrade']+[d['name']+'='+d['version'] for d in lock['packages']]+['wpa_supplicant@k4'],out/'apk-install.log')
    assert installed(root)==({d['name']:d['version'] for d in lock['packages']}|{'wpa_supplicant':'2.12-r0'})
    shutil.copytree(local/'armv7',root/'var/lib/apk/k4/armv7',symlinks=False)
    qdir=out/'qemu';qdir.mkdir();deb=subprocess.Popen(['dpkg-deb','--fsys-tarfile',str(qdeb)],stdout=subprocess.PIPE)
    r=subprocess.run(['tar','-x','-C',str(qdir),'./usr/bin/qemu-arm-static'],stdin=deb.stdout);deb.stdout.close();assert r.returncode==0 and deb.wait()==0
    qemu=qdir/'usr/bin/qemu-arm-static';qr=[qemu,'-L',root]
    applets=run(qr+[root/'bin/busybox','--list-full']).splitlines()
    # Replay busybox installation without executing ARM shell child processes.
    for n in applets:
        p=root/n
        if not p.exists() and not p.is_symlink():p.parent.mkdir(parents=True,exist_ok=True);p.symlink_to('/bin/busybox')
    with (out/'package-scripts.txt').open('w') as log:
        for d in lock['packages']:
            with tarfile.open(repo/d['file']) as t:
                for member in t.getmembers():
                    if member.name in ('.pre-install','.post-install','.trigger'):
                        log.write(d['file']+' '+member.name+'\n'+t.extractfile(member).read().decode()+'\n')
    # busybox's only additional post-install action is its logging account.
    with (root/'etc/group').open('a') as f:f.write('klogd:x:101:\n')
    with (root/'etc/passwd').open('a') as f:f.write('klogd:x:101:101:klogd:/dev/null:/sbin/nologin\n')
    with (root/'etc/shadow').open('a') as f:f.write('klogd:!:0:0:99999:7:::\n')
    # Certificate trigger equivalent: official bundle plus hashed PEM links.
    certdir=root/'etc/ssl/certs'
    for cert in sorted((root/'usr/share/ca-certificates/mozilla').glob('*.crt')):
        pem=cert.stem+'.pem';link(root,'etc/ssl/certs/'+pem,'/usr/share/ca-certificates/mozilla/'+cert.name)
        h=run(['openssl','x509','-in',cert,'-noout','-hash']).strip();i=0
        while (certdir/(h+'.'+str(i))).is_symlink():i+=1
        link(root,'etc/ssl/certs/'+h+'.'+str(i),pem)
    # OpenRC legacy migration post-install has no rcS.d/rcL.d on minirootfs.
    private=out/'busybox-source'
    if a.busybox_tar:
        private.mkdir();run(['tar','-xf',a.busybox_tar,'-C',private,'--exclude=dev/*'])
    else:
        shutil.copytree(a.k4_root,private,symlinks=True)
    kernel_lock=json.loads((HERE/'kernel.lock.json').read_text())
    assert sha(a.kernel)==kernel_lock['zImage']
    assert sha(a.dtb)==kernel_lock['dtb']
    source_modules=a.modules/RELEASE
    actual={p.relative_to(source_modules).as_posix():sha(p) for p in source_modules.rglob('*.ko')}
    assert actual==kernel_lock['modules']
    assert len(actual)==23
    copied=[]
    for directory in ('lib/firmware','root/.ssh','etc/dropbear'):
        shutil.copytree(private/directory,root/directory,dirs_exist_ok=True,symlinks=True)
    shutil.copytree(a.modules,root/'lib/modules',symlinks=True)
    if not a.busybox_tar:
        for name in ('build','source'):
            (root/'lib/modules'/RELEASE/name).unlink(missing_ok=True)
    (root/'boot').mkdir()
    shutil.copy2(a.kernel,root/'boot/zImage')
    shutil.copy2(a.dtb,root/'boot/imx50-kindle-k4.dtb')
    for p in sorted((private/'bin').iterdir()):
        if (p.name.startswith('k4-') or p.name in ('udhcpc-wifi',)) and 'watchdog-guard' not in p.name and 'watchdog-probe' not in p.name:
            shutil.copy2(p,root/'bin'/p.name);copied.append('bin/'+p.name)
    for p in (root/'bin').glob('k4-*'):
        if p.read_bytes().startswith(b'#!'):
            text=p.read_text().replace('/bin/wpa_supplicant','/sbin/wpa_supplicant').replace('/bin/wpa_cli','/sbin/wpa_cli')
            write(root,'bin/'+p.name,text,0o755)
    for n in ('k4-charge-current-ua','k4-wifi-driver'):shutil.copy2(private/'etc'/n,root/'etc'/n)
    shutil.copy2(private/'etc/wpa_supplicant.conf',root/'etc/wpa_supplicant.conf')
    # Existing SSH public-key authorization and host identity; disable passwords.
    link(root,'bin/dropbear','/usr/sbin/dropbear');link(root,'bin/dropbearkey','/usr/bin/dropbearkey');link(root,'bin/iw','/usr/sbin/iw')
    s=(root/'bin/k4-userspace-service').read_text().replace('-F -r','-F -E -s -r');write(root,'bin/k4-userspace-service',s,0o755)
    shadow=(root/'etc/shadow').read_text();shadow='\n'.join('root::0:0:99999:7:::' if l.startswith('root:') else l for l in shadow.splitlines())+'\n';write(root,'etc/shadow',shadow,0o600)
    assert list((root/'lib/modules').iterdir())[0].name==RELEASE
    run(qr+[root/'sbin/depmod','-b',root,RELEASE],out/'depmod.log')
    write(root,'etc/k4-root-profile','alpine-emmc-root\n')
    fstab='/dev/mmcblk2p1 / ext4 rw,defaults 0 0\nproc /proc proc defaults 0 0\nsysfs /sys sysfs defaults 0 0\ndevtmpfs /dev devtmpfs defaults 0 0\ndevpts /dev/pts devpts defaults 0 0\ntmpfs /tmp tmpfs mode=1777,size=32m 0 0\ntmpfs /run tmpfs mode=0755 0 0\nconfigfs /sys/kernel/config configfs defaults 0 0\n'
    write(root,'etc/fstab',fstab)
    # Keep existing initialization contents; OpenRC now owns mounts/watchdog.
    base=(private/'etc/init.d/rcS.k4-base').read_text();base=base[base.index('$bb mkdir -p /run/wpa_supplicant'):];base='#!/bin/sh\nPATH=/bin:/sbin:/usr/bin:/usr/sbin\nbb=/bin/busybox\n'+base;base=base.replace('/bin/busybox modprobe','/sbin/modprobe')
    write(root,'etc/k4/platform-start',base,0o755)
    services={
    'k4-filesystems': '#!/sbin/openrc-run\ndescription="K4 virtual filesystems and early watchdog"\ndepend() { before k4-platform; }\nstart() {\n grep -q " /proc proc " /proc/mounts 2>/dev/null || mount -t proc proc /proc\n grep -q " /sys sysfs " /proc/mounts || mount -t sysfs sysfs /sys\n grep -q " /dev devtmpfs " /proc/mounts || mount -t devtmpfs devtmpfs /dev\n mkdir -p /dev/pts\n mount -t devpts devpts /dev/pts\n mount -t tmpfs -o mode=1777,size=32m tmpfs /tmp\n mount -t tmpfs tmpfs /run\n mount -t configfs configfs /sys/kernel/config\n /bin/busybox watchdog -T 30 -t 10 /dev/watchdog\n}\n',
    'k4-platform':'#!/sbin/openrc-run\ndescription="K4 USB, SPI and charging initialization"\ndepend() { need k4-filesystems; before k4-coldplug; }\nstart() { /bin/sh /etc/k4/platform-start; }\nstop() { /bin/sh /bin/k4-charge-policy stop; }\n',
    'k4-coldplug':'#!/sbin/openrc-run\ndescription="K4 generic modalias coldplug"\ndepend() { need k4-platform; before k4-usb-ssh k4-wifi; }\nstart() { (umask 077; /bin/busybox timeout 60 /bin/sh /bin/k4-modalias-coldplug > /run/k4-modalias-coldplug.log 2>&1) || :; }\n',
    }
    for name,arg in [('k4-usb-ssh','usb-ssh'),('k4-wifi','wifi')]:
        services[name]='#!/sbin/openrc-run\ndescription="K4 '+arg+'"\nsupervisor="supervise-daemon"\ncommand="/bin/k4-userspace-service"\ncommand_args="'+arg+'"\npidfile="/run/'+name+'.pid"\ndepend() { need k4-coldplug hwclock; }\n'
    mounts=services['k4-filesystems'].split('start() {\n',1)[1].split(' /bin/busybox watchdog',1)[0]
    write(root,'etc/k4/mount-early','#!/bin/sh\nPATH=/bin:/sbin:/usr/bin:/usr/sbin\n'+mounts,0o755)
    services['k4-filesystems']='#!/sbin/openrc-run\ndescription="K4 early watchdog"\ndepend() { before k4-platform; }\nstart() { /bin/busybox watchdog -T 30 -t 10 /dev/watchdog; }\n'
    # Original UTC SRTC source, including halt/reboot systohc.
    write(root,'etc/conf.d/hwclock','clock="UTC"\nclock_hctosys="YES"\nclock_systohc="YES"\nclock_adjfile="NO"\nclock_args="--rtc=/dev/rtc0"\n')
    services['k4-ntpd']='#!/sbin/openrc-run\ndescription="Optional BusyBox network time"\nsupervisor="supervise-daemon"\ncommand="/bin/busybox"\ncommand_args="ntpd -n -p pool.ntp.org"\npidfile="/run/k4-ntpd.pid"\ndepend() { need k4-wifi hwclock; }\n'
    for n,s in services.items():write(root,'etc/init.d/'+n,s,0o755)
    for level,names in {'sysinit':['k4-filesystems'],'boot':['k4-platform','k4-coldplug','hwclock'],'default':['k4-usb-ssh','k4-wifi','k4-ntpd'],'shutdown':['killprocs','mount-ro']}.items():
        for n in names:link(root,'etc/runlevels/'+level+'/'+n,'/etc/init.d/'+n)
    write(root,'etc/rc.conf',(root/'etc/rc.conf').read_text()+'\nrc_parallel="NO"\nrc_sys=""\n')
    write(root,'etc/inittab','::sysinit:/bin/sh /etc/k4/mount-early\n::sysinit:/sbin/openrc sysinit\n::sysinit:/sbin/openrc boot\n::wait:/sbin/openrc default\nttyGS0::respawn:/bin/sh\n::ctrlaltdel:/bin/busybox reboot\n::shutdown:/sbin/openrc shutdown\n')
    write(root,'etc/apk/repositories','https://dl-cdn.alpinelinux.org/alpine/v3.24/main\n@k4 /var/lib/apk/k4\n')
    write(root,'etc/network/interfaces','auto lo\niface lo inet loopback\n# usb0 and wlan0 are configured by the existing K4 services.\n')
    link(root,'etc/resolv.conf','/run/resolv.conf')
    # APK lock inode is host state, not a deployment input.
    (root/'lib/apk/db/lock').unlink(missing_ok=True)
    write(root,'var/log/apk.log','')
    sums=''.join(sha(p)+'  '+p.relative_to(root).as_posix()+'\n' for p in sorted(root.rglob('*')) if p.is_file() and not p.is_symlink())
    write(root,'etc/k4-rootfs.sha256',sums)
    archive(root,out/'rootfs.tar.gz')
    (out/'rootfs.tar.gz').chmod(0o600)
    shutil.copy2(HERE.parent/'tools/deploy-emmc-root',out/'deploy-alpine-root')
    report=dict(kernel_release=RELEASE,packages=installed(root),busybox_tar_sha256=a.busybox_sha,source_built_k4=not bool(a.busybox_tar),kernel_reference=kernel_lock['reference'],kernel_sha256=sha(a.kernel),dtb_sha256=sha(a.dtb),module_count=len(actual),k4_copied=copied,device_operations=False,rootfs_sha256=sha(out/'rootfs.tar.gz'),rootfs_bytes=(out/'rootfs.tar.gz').stat().st_size)
    (out/'build-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('packages','k4_copied')}))
if __name__=='__main__':main()
