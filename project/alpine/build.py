#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""User-mode, offline Alpine/K4 assembly. Never accesses a device."""
import argparse,gzip,hashlib,io,json,os,pathlib,shutil,stat,subprocess,tarfile,bz2,lzma,re,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from userspace.build_support import output
import rootfs_sources
HERE=pathlib.Path(__file__).resolve().parent
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
def kernel_release(kernel):
    data=kernel.read_bytes()
    if int.from_bytes(data[36:40],'little') != 0x016f2818:
        raise ValueError('expected ARM zImage')
    payloads=[data]
    for magic,decompress in ((b'\x1f\x8b\x08',lambda b: __import__('zlib').decompress(b,31)),(b'BZh',bz2.decompress),(b'\xfd7zXZ\x00',lzma.decompress)):
        offset=data.find(magic)
        while offset>=0:
            try:payloads.append(decompress(data[offset:]));break
            except (ValueError,OSError,EOFError,__import__('zlib').error):offset=data.find(magic,offset+1)
    for payload in payloads:
        match=re.search(rb'Linux version ([^\s\x00]+)',payload)
        if match:return match[1].decode()
    raise ValueError('kernel release missing from zImage')

def compatible_modules(kernel,source_modules):
    release=kernel_release(kernel)
    if source_modules.name != release:raise ValueError('kernel/modules release mismatch')
    actual={}
    for p in source_modules.rglob('*.ko'):
        data=p.read_bytes()
        if data[:4]!=b'\x7fELF' or int.from_bytes(data[18:20],'little')!=40:
            raise ValueError('expected ARM module: '+str(p))
        vermagic=re.search(rb'vermagic=([^\s\x00]+)',data)
        if not vermagic or vermagic[1].decode()!=release:raise ValueError('module release mismatch: '+str(p))
        actual[p.relative_to(source_modules).as_posix()]=sha(p)
    return release,actual

def verify_release(kernel,dtb,source_modules):
    lock=json.loads((HERE/'kernel.lock.json').read_text())
    release,actual=compatible_modules(kernel,source_modules)
    if sha(kernel)!=lock['zImage'] or sha(dtb)!=lock['dtb'] or actual!=lock['modules']:
        raise ValueError('release hash mismatch')
    print('VERIFY_RELEASE_OK '+release+' modules='+str(len(actual)))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--cache',type=pathlib.Path,required=True);ap.add_argument('--firmware-dir',type=pathlib.Path,required=True,help='external contents of /lib/firmware (ath6kl firmware, calibration and regulatory.db); private input');ap.add_argument('--wifi-config',type=pathlib.Path,required=True,help='external private wpa_supplicant.conf');ap.add_argument('--tools-dir',type=pathlib.Path,help='bin directory from project/userspace builds or explicitly supplied K4 ELF tools; diagnostics are omitted');ap.add_argument('--ssh-host-key',type=pathlib.Path,help='existing external OpenSSH ECDSA private host key; omit for first-start key generation');ap.add_argument('--authorized-keys',type=pathlib.Path,help='external root SSH public-key authorization file');ap.add_argument('--out',type=pathlib.Path,default=os.environ.get('OUT',str(HERE.parents[1]/'out/alpine')));ap.add_argument('--clean',action='store_true');ap.add_argument('--verify-release',action='store_true');ap.add_argument('--kernel',type=pathlib.Path,required=True);ap.add_argument('--dtb',type=pathlib.Path,required=True);ap.add_argument('--modules',type=pathlib.Path,required=True);a=ap.parse_args()
    out=output(a.out,[HERE,a.cache,a.firmware_dir,a.wifi_config,a.kernel,a.dtb,a.modules]+[p for p in (a.tools_dir,a.ssh_host_key,a.authorized_keys) if p],a.clean);cache=a.cache.resolve()
    # Reassemble staging trees; retain reusable output and logs between invocations.
    for directory in ('rootfs','host','hostkeys','repository','fetched','qemu'):
        if (out/directory).exists():shutil.rmtree(out/directory)
    root=out/'rootfs';root.mkdir()
    release=kernel_release(a.kernel);source_modules=a.modules/release
    release,actual=compatible_modules(a.kernel,source_modules)
    if a.verify_release:verify_release(a.kernel,a.dtb,source_modules)
    lock=json.loads((HERE/'packages.lock.json').read_text())
    def checked(name,d,key='sha256'):p=cache/name;assert sha(p,key)==d[key],name;return p
    mini=checked(lock['minirootfs']['file'],lock['minirootfs']);hostpkg=checked(lock['host_apk']['file'],lock['host_apk']);hostmini=checked(lock['host_mini']['file'],lock['host_mini']);qdeb=checked(lock['qemu']['file'],lock['qemu'],'sha512')
    for d in lock['packages']:checked(d['file'],d)
    assert sha(cache/'APKINDEX-armv7.tar.gz')==lock['index_sha256']
    run(['tar','-xf',mini,'-C',root]);host=out/'host';host.mkdir();run(['tar','-xf',hostpkg,'-C',host]);keys=out/'hostkeys';keys.mkdir();run(['tar','-xf',hostmini,'-C',keys,'./etc/apk/keys'])
    apk=host/'sbin/apk.static'
    run([apk,'--keys-dir',keys/'etc/apk/keys','verify',hostpkg],out/'host-apk-signature.log')
    repo=out/'repository/armv7';repo.mkdir(parents=True);shutil.copy2(cache/'APKINDEX-armv7.tar.gz',repo/'APKINDEX.tar.gz')
    for d in lock['packages']:(repo/d['file']).symlink_to(cache/d['file'])
    repositories=out/'repositories';repositories.write_text(str(repo.parent)+'\n')
    common=[apk,'--root',root,'--arch','armv7','--keys-dir',root/'etc/apk/keys','--repositories-file',repositories,'--no-network']
    # apk authenticates the index and checks each selected archive against it.
    (out/'fetched').mkdir()
    run(common+['fetch','--recursive','--output',out/'fetched']+[d['name']+'='+d['version'] for d in lock['packages']],out/'index-and-package-check.log')
    run([apk,'--keys-dir',root/'etc/apk/keys','verify']+[repo/d['file'] for d in lock['packages']],out/'package-signatures.log')
    run(common+['--no-scripts','add','--usermode','--upgrade']+[d['name']+'='+d['version'] for d in lock['packages']],out/'apk-install.log')
    assert installed(root)==({d['name']:d['version'] for d in lock['packages']})
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
    for n in ('ifup','ifdown','ifquery'):
        link(root,'sbin/'+n,'ifupdown')
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
    copied=[]
    shutil.copytree(a.firmware_dir,root/'lib/firmware',dirs_exist_ok=True,symlinks=True)
    shutil.copytree(a.modules,root/'lib/modules',symlinks=True)
    (root/'boot').mkdir()
    shutil.copy2(a.kernel,root/'boot/zImage')
    shutil.copy2(a.dtb,root/'boot/imx50-kindle-k4.dtb')
    for p in sorted(a.tools_dir.iterdir()) if a.tools_dir else ():
        if p.name.startswith('k4-') and not rootfs_sources.diagnostic('bin/'+p.name) and p.read_bytes().startswith(b'\x7fELF'):
            shutil.copy2(p,root/'bin'/p.name);copied.append('bin/'+p.name)
    copied += [n for n in rootfs_sources.copy(root,'common',exclude=('bin/k4-wifi-connect','bin/k4-userspace-service','bin/udhcpc-wifi','bin/k4-root-select')) if n.startswith('bin/')]
    copied.sort()
    shutil.copy2(a.wifi_config,root/'etc/wpa_supplicant/wpa_supplicant.conf')
    (root/'etc/wpa_supplicant/wpa_supplicant.conf').chmod(0o600)
    (root/'root/.ssh').mkdir(mode=0o700,exist_ok=True)
    if a.authorized_keys:
        shutil.copy2(a.authorized_keys,root/'root/.ssh/authorized_keys')
        (root/'root/.ssh/authorized_keys').chmod(0o600)
    (root/'root/.ssh').chmod(0o700)
    if a.ssh_host_key:
        shutil.copy2(a.ssh_host_key,root/'etc/ssh/ssh_host_ecdsa_key')
        (root/'etc/ssh/ssh_host_ecdsa_key').chmod(0o600)
        public=run(['ssh-keygen','-y','-f',a.ssh_host_key])
        assert public.startswith('ecdsa-sha2-'), 'provide an OpenSSH ECDSA host key'
        write(root,'etc/ssh/ssh_host_ecdsa_key.pub',public)
    shadow=(root/'etc/shadow').read_text();shadow='\n'.join('root::0:0:99999:7:::' if l.startswith('root:') else l for l in shadow.splitlines())+'\n';write(root,'etc/shadow',shadow,0o600)
    run(qr+[root/'sbin/depmod','-b',root,release],out/'depmod.log')
    if not (root/'lib/modules'/release/'modules.dep').is_file():raise ValueError('depmod did not generate modules.dep')
    rootfs_sources.copy(root,'alpine')
    # Match the device's apk world: split packages stay dependencies.
    world=(root/'etc/apk/world').read_text().splitlines()
    world=[n.split('=')[0] if n.split('=')[0] in ('ifupdown-ng','openssh','openssh-server','openssh-sftp-server') else n for n in world
           if n.split('=')[0] not in ('bridge','ifupdown-ng-wifi','wpa_supplicant-openrc','libedit','openssh-keygen','openssh-client-common','openssh-client-default','openssh-server-common','openssh-server-common-openrc')]
    write(root,'etc/apk/world','\n'.join(world)+'\n')
    # APK lock inode is host state, not a deployment input.
    (root/'lib/apk/db/lock').unlink(missing_ok=True)
    write(root,'var/log/apk.log','')
    sums=''.join(sha(p)+'  '+p.relative_to(root).as_posix()+'\n' for p in sorted(root.rglob('*')) if p.is_file() and not p.is_symlink())
    write(root,'etc/k4-rootfs.sha256',sums)
    archive(root,out/'rootfs.tar.gz')
    (out/'rootfs.tar.gz').chmod(0o600)
    shutil.copy2(HERE.parent/'tools/deploy-emmc-root',out/'deploy-alpine-root')
    report=dict(kernel_release=release,packages=installed(root),firmware_sha256={p.relative_to(a.firmware_dir).as_posix():sha(p) for p in sorted(a.firmware_dir.rglob("*")) if p.is_file() and not p.is_symlink()},release_verified=a.verify_release,kernel_sha256=sha(a.kernel),dtb_sha256=sha(a.dtb),module_count=len(actual),k4_copied=copied,device_operations=False,rootfs_sha256=sha(out/'rootfs.tar.gz'),rootfs_bytes=(out/'rootfs.tar.gz').stat().st_size)
    (out/'build-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('packages','k4_copied')}))
if __name__=='__main__':main()
