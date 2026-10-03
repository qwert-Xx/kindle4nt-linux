#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Offline ABI, dependency, content and deterministic archive checks."""
import argparse,hashlib,json,pathlib,re,subprocess,tarfile
from build import RELEASE,sha,run

def resolve(root,n):
    p=root/n.lstrip('/')
    for _ in range(20):
        if not p.is_symlink():return p
        target=p.readlink();p=root/str(target).lstrip('/') if target.is_absolute() else p.parent/target
    raise ValueError(n)
def verify(out):
    root=out/'rootfs';q=out/'qemu/usr/bin/qemu-arm-static';qr=[q,'-L',root]
    elfs=[];modules=[];dynamic=[]
    for p in sorted(root.rglob('*')):
        if p.is_symlink() or not p.is_file() or p.read_bytes()[:4]!=b'\x7fELF':continue
        header=run(['readelf','-h',p]);assert 'ELF32' in header and 'little endian' in header and re.search(r'Machine:\s+ARM',header) and 'Version5 EABI' in header,p
        attrs=run(['readelf','-A',p]);assert ('Tag_CPU_arch: v7' in attrs or p.suffix=='.ko' and 'Tag_CPU_arch: v6K' in attrs),p
        if p.suffix=='.ko':
            assert RELEASE in run(['readelf','-p','.modinfo',p]);modules.append(str(p.relative_to(root)))
        else:
            assert 'hard-float ABI' in header,p
            segments=run(['readelf','-l',p]);interp=re.findall(r'Requesting program interpreter: ([^\]]+)',segments)
            for n in interp:assert resolve(root,n).is_file(),(p,n)
            if interp:assert interp==['/lib/ld-musl-armhf.so.1'],(p,interp)
            for lib in re.findall(r'Shared library: \[([^\]]+)\]',run(['readelf','-d',p])):
                assert any(resolve(root,d+'/'+lib).is_file() for d in ('lib','usr/lib')), (p,lib)
            if interp:dynamic.append(str(p.relative_to(root)))
        elfs.append(str(p.relative_to(root)))
    assert not (root/'bin/wpa_supplicant').exists() and not (root/'bin/wpa_cli').exists()
    from build import installed
    pkgs=installed(root);assert pkgs['wpa_supplicant']=='2.11-r4' and pkgs['wpa_supplicant-openrc']=='2.11-r4'
    assert 'wpa_supplicant=2.11-r4' in (root/'etc/apk/world').read_text().splitlines()
    assert '@k4' not in (root/'etc/apk/world').read_text()+(root/'etc/apk/repositories').read_text()
    assert not (root/'var/lib/apk/k4').exists()
    assert not (root/'etc/runlevels/default/wpa_supplicant').exists()
    for n in ('bin/k4-wifi-connect','bin/udhcpc-wifi','etc/init.d/k4-wifi','etc/runlevels/default/k4-wifi','etc/wpa_supplicant.conf'):
        assert not (root/n).exists() and not (root/n).is_symlink(),n
    assert (root/'etc/wpa_supplicant/wpa_supplicant.conf').stat().st_mode&0o777==0o600
    for n in ('bin/k4-userspace-service','bin/dropbear','bin/dropbearkey','usr/sbin/dropbear','etc/dropbear','etc/init.d/k4-usb-ssh','etc/conf.d/k4-usb-ssh','etc/runlevels/default/k4-usb-ssh'):
        assert not (root/n).exists() and not (root/n).is_symlink(),n
    assert not any(n.startswith('dropbear') for n in pkgs)
    assert pkgs['openssh']=='10.3_p1-r1'
    assert 'ifconfig usb0' not in (root/'etc/k4/platform-start').read_text()
    for n in ('ifup','ifdown','ifquery'):
        assert (root/'sbin'/n).readlink()==pathlib.Path('ifupdown')
    for p in (pathlib.Path(__file__).parent/'network').rglob('*'):
        if p.is_file() and not p.name.endswith('.license'):
            assert p.read_bytes()==(root/p.relative_to(pathlib.Path(__file__).parent/'network')).read_bytes()
    for level,n in [('boot','wpa_supplicant'),('boot','networking'),('default','wpa_cli')]:
        assert (root/'etc/runlevels'/level/n).readlink()==pathlib.Path('/etc/init.d/'+n)
    reference=out/'busybox-source'
    same=[]
    for base in ('lib/firmware',):
        for p in sorted((reference/base).rglob('*')):
            if p.is_file() and not p.is_symlink():
                n=p.relative_to(reference).as_posix()
                if n.startswith('lib/modules/') and p.suffix!='.ko' and '/modules.' in n:continue
                assert p.read_bytes()==(root/n).read_bytes(),n;same.append(n)
    lock=json.loads((pathlib.Path(__file__).parent/'kernel.lock.json').read_text())
    assert sha(root/'boot/zImage')==lock['zImage']
    assert sha(root/'boot/imx50-kindle-k4.dtb')==lock['dtb']
    actual={p.relative_to(root/'lib/modules'/RELEASE).as_posix():sha(p) for p in (root/'lib/modules'/RELEASE).rglob('*.ko')}
    assert actual==lock['modules']
    assert len(modules)==23,len(modules)
    assert not list(root.rglob('*watchdog-guard*'))
    assert not list(root.rglob('*watchdog-probe*'))
    assert '--rtc=/dev/rtc0' in (root/'etc/conf.d/hwclock').read_text()
    assert 'clock_systohc="YES"' in (root/'etc/conf.d/hwclock').read_text()
    assert (root/'etc/runlevels/boot/hwclock').is_symlink()
    assert (root/'etc/runlevels/default/k4-ntpd').is_symlink()
    assert '/dev/mmcblk2p1 / ext4 rw,defaults 0 0' in (root/'etc/fstab').read_text()
    assert 'watchdog -T 30 -t 10 /dev/watchdog' in (root/'etc/init.d/k4-filesystems').read_text()
    run(['sh','-n',out/'deploy-alpine-root'])
    for p in (root/'bin').glob('k4-*'):
        if p.is_file() and p.read_bytes()[:2]==b'#!':run(['sh','-n',p])
    services=['k4-filesystems','k4-platform','k4-coldplug','sshd','wpa_supplicant','networking','wpa_cli','killprocs','mount-ro','hwclock','k4-ntpd','localmount','hostname','root','fsck','modules'];graph={n:set() for n in services};declarations={}
    # Source declarations only in a host shell, never call service start/stop.
    for n in services:
        p=root/'etc/init.d'/n;run(['sh','-n',p])
        conf=root/'etc/conf.d'/n
        script=('set -a; . \"$2\"; set +a\n' if conf.exists() else '')+'for op in need before after use want provide; do eval "$op() { echo $op \"\\$@\"; }"; done\nkeyword() { :; }\n. "$1"\ndepend\nfor target in $rc_need; do echo need $target; done\nfor target in $rc_after; do echo after $target; done\n'
        text=run(['sh','-c',script,'deps',p,conf]);declarations[n]=text.splitlines()
        for l in text.splitlines():
            op,*targets=l.split()
            for target in targets:
                if op=='need':assert target in services,(n,target)
                if target not in services:continue
                if op in ('need','after'):graph[n].add(target)
                elif op=='before':graph[target].add(n)
    order=[]
    while len(order)<len(graph):
        ready=sorted(n for n,deps in graph.items() if n not in order and deps<=set(order));assert ready,graph;order.extend(ready)
    startup=['k4-filesystems','k4-platform','k4-coldplug','wpa_supplicant','networking','wpa_cli']
    for a,b in zip(startup,startup[1:]):assert order.index(a)<order.index(b)
    assert 'networking' in graph['sshd']
    assert {'networking','wpa_cli','hwclock'}<=graph['k4-ntpd']
    assert {'localmount','hostname','wpa_supplicant','k4-coldplug'}<=graph['networking']
    assert (root/'root/.ssh/authorized_keys').stat().st_mode&0o777==0o600
    hostkey=root/'etc/ssh/ssh_host_ecdsa_key'
    if hostkey.exists():assert hostkey.stat().st_mode&0o777==0o600
    assert 'dropbear' not in (root/'etc/k4/platform-start').read_text()
    assert 'ttyGS0::respawn:/bin/sh' in (root/'etc/inittab').read_text()
    assert (root/'etc/runlevels/default/sshd').is_symlink()
    effective=run(qr+[root/'usr/sbin/sshd','-G','-f',root/'etc/ssh/sshd_config'])
    for setting in ('port 22','listenaddress 0.0.0.0:22','listenaddress [::]:22','hostkey /etc/ssh/ssh_host_ecdsa_key','permitrootlogin prohibit-password','passwordauthentication no','kbdinteractiveauthentication no','pubkeyauthentication yes','subsystem sftp internal-sftp'):
        assert setting in effective.splitlines(),setting
    assert 'sshd:x:22:22:sshd:/dev/null:/sbin/nologin' in (root/'etc/passwd').read_text()
    assert (root/'usr/lib/ssh/sftp-server').is_file()
    interfaces=run(qr+[root/'sbin/ifquery','-i',root/'etc/network/interfaces','--list','-a']).splitlines()
    assert interfaces==['lo','usb0','wlan0']
    checks={}
    for name,args in [('busybox',['bin/busybox','--help']),('kmod',['bin/kmod','--version']),('openrc',['sbin/openrc','--version']),('openssh',['usr/sbin/sshd','-V']),('wpa-official',['sbin/wpa_supplicant','-v']),('wpa-cli-official',['sbin/wpa_cli','-v']),('iw',['usr/sbin/iw','--version']),('e2fsprogs',['sbin/e2fsck','-V']),('mount',['bin/mount','--version']),('hwclock',['sbin/hwclock','--help']),('ntpd',['bin/busybox','ntpd','--help'])]:
        # Some programs print help/version and deliberately return nonzero.
        r=subprocess.run([str(x) for x in qr+[resolve(root,args[0])]+args[1:]],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        assert r.returncode in (0,1) and r.stdout and not re.search('Error loading|not found|Illegal instruction|qemu:',r.stdout),(name,r.stdout)
        checks[name]={'exit':r.returncode,'output':r.stdout[:800]}
    with tarfile.open(out/'rootfs.tar.gz') as t:
        members=t.getmembers();names=[m.name for m in members]
        assert len(names)==len(set(names))
        assert all(m.uid==0 and m.gid==0 and m.mtime==0 for m in members)
        assert names==sorted(names)
        sums=t.extractfile('etc/k4-rootfs.sha256').read().decode().splitlines()
        for l in sums:
            expected,n=l.split('  ',1);assert hashlib.sha256(t.extractfile(n).read()).hexdigest()==expected,n
        assert t.getmember('dev/console').ischr()
    signatures=(out/'package-signatures.log').read_text();assert signatures.count(': OK')==84 and 'UNTRUSTED' not in signatures
    report=dict(elf_count=len(elfs),dynamic_elf_count=len(dynamic),module_count=len(modules),abi='ARMv7 little-endian EABI5, hard-float userspace; musl dynamic or existing static K4 binaries',reference_equal_files=len(same),service_declarations=declarations,topological_order=order,service_validation='shell syntax and evaluated dependency graph; no PID1/OpenRC boot or hardware execution',qemu_smoke=checks,tar_files=len(members),signature_packages=84,package_index_validation=True,device_operations=False)
    (out/'verification.json').write_text(json.dumps(report,indent=2)+'\n');return report
def verify_ram(directory):
    import gzip,stat
    raw=gzip.decompress((directory/'alpine-ram.cpio.gz').read_bytes());offset=0;entries={};names=[]
    while True:
        assert raw[offset:offset+6]==b'070701'
        fields=[int(raw[offset+6+i*8:offset+14+i*8],16) for i in range(13)];offset+=110
        ino,mode,uid,gid,links,mtime,size,dm,dn,rm,rn,ns,checksum=fields
        name=raw[offset:offset+ns-1].decode();offset+=ns;offset=(offset+3)&~3
        data=raw[offset:offset+size];offset+=size;offset=(offset+3)&~3
        if name=='TRAILER!!!':break
        assert uid==gid==mtime==0 and name not in entries
        entries[name]=(mode,data,rm,rn);names.append(name)
    assert names==sorted(names)
    for l in entries['etc/k4-rootfs.sha256'][1].decode().splitlines():
        expected,n=l.split('  ',1);assert hashlib.sha256(entries[n][1]).hexdigest()==expected,n
    for n,(mode,data,_,_) in entries.items():
        if stat.S_ISREG(mode) and data.startswith(b'#!'):
            result=subprocess.run(['sh','-n'],input=data.decode(),text=True,capture_output=True);assert result.returncode==0,(n,result.stderr)
    assert entries['dev/console'][2:]==(5,1) and stat.S_ISCHR(entries['dev/console'][0])
    assert b'/dev/mmc' not in entries['etc/fstab'][1]
    assert b'blockdev --setro' in entries['init'][1] and b'exec /sbin/init' in entries['init'][1]
    assert b'600 30 expire' in entries['etc/init.d/k4-filesystems'][1]
    for n in ('zImage','imx50-kindle-k4.dtb'):assert (directory/n).read_bytes()==entries['boot/'+n][1]
    report=dict(entries=len(entries),checksums=True,sorted_zero_owner_time=True,shell_syntax=True,emmc_fstab_absent=True,read_only_init_present=True,device_executed=False)
    (directory/'ram-verification.json').write_text(json.dumps(report,indent=2)+'\n');return report
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--build',type=pathlib.Path,required=True);ap.add_argument('--compare',type=pathlib.Path);ap.add_argument('--ram',type=pathlib.Path);a=ap.parse_args();r=verify(a.build)
    if a.compare:assert (a.build/'rootfs.tar.gz').read_bytes()==(a.compare/'rootfs.tar.gz').read_bytes();r['reproducible_tar']=True;(a.build/'verification.json').write_text(json.dumps(r,indent=2)+'\n')
    if a.ram:print(json.dumps(verify_ram(a.ram)))
    print(json.dumps({k:v for k,v in r.items() if k not in ('qemu_smoke','service_declarations','topological_order')}))
