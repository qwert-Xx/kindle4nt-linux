#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Host-only source reconstruction. No device commands or runtime installation."""
import argparse,hashlib,json,os,pathlib,shutil,subprocess,tarfile,re
from build_support import output, toolchain
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]/"sources"))
from fetch import checked
HERE=pathlib.Path(__file__).resolve().parent

def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def run(cmd,cwd,env=None):
    with (OUT/'build.log').open('ab') as log:
        subprocess.run(cmd,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
def extract(name,target):
    target.mkdir(exist_ok=True)
    if not any(target.iterdir()):
        with tarfile.open(CACHE/name) as t:
            t.extractall(target,filter='data')
    return next(p for p in target.iterdir() if p.is_dir())
def busybox(name,cross,stamp):
    src=extract('busybox-1.31.1.tar.bz2',OUT/name)
    shutil.copyfile(HERE/(name+'.config'),src/'.config')
    cmd=['make','ARCH=arm','CROSS_COMPILE='+cross]
    run(cmd+['oldconfig'],src)
    run(cmd+['prepare'],src)
    h=src/'include/autoconf.h'
    text=h.read_text(); text,n=re.subn(r'#define AUTOCONF_TIMESTAMP .*','#define AUTOCONF_TIMESTAMP "'+stamp+'"',text)
    if n!=1: raise ValueError('BusyBox timestamp macro absent')
    h.write_text(text)
    run(cmd+['-j8'],src)
    shutil.copyfile(src/'busybox',BIN/('busybox' if name=='busybox' else 'busybox-modutils'))
    if name == 'busybox':
        run(cmd+['busybox.links'],src)
        shutil.copyfile(src/'busybox.links', OUT/'busybox.links')

def main():
    global OUT,CACHE,BIN
    a=argparse.ArgumentParser();a.add_argument('--cache',type=pathlib.Path,default=pathlib.Path.home()/'.cache/k4/sources');a.add_argument('--offline',action='store_true');a.add_argument('--out',default=os.environ.get('OUT',str(HERE.parents[1]/'out/userspace')))
    a.add_argument('--clean',action='store_true');a.add_argument('--verify-release',action='store_true')
    a.add_argument('--busybox-cross-compile', help='override the compiler prefix for legacy BusyBox')
    a.add_argument('--components',default='busybox,modutils,dropbear,wifi,regdb');a.add_argument('--reference',help='read-only accepted inner/bin')
    v=a.parse_args();OUT=pathlib.Path(v.out).resolve()
    CACHE=v.cache.resolve()
    OUT=output(OUT,[HERE,CACHE]+([v.reference] if v.reference else []),v.clean)
    CACHE.mkdir(parents=True,exist_ok=True);BIN=OUT/'bin';BIN.mkdir(exist_ok=True)
    lock=json.loads((HERE/'sources.lock.json').read_text())
    components=v.components.split(',')
    needed={'busybox':['busybox-1.31.1.tar.bz2'],'modutils':['busybox-1.31.1.tar.bz2'],'dropbear':['dropbear-2024.86.tar.bz2'],'wifi':['wpa_supplicant-2.11.tar.gz','libnl-3.12.0.tar.gz','iw-6.17.tar.xz'],'regdb':['wireless-regdb-2026.09.03.tar.xz']}
    names={name for c in components for name in needed[c]}
    if 'busybox' in components and not v.busybox_cross_compile:names.add('gcc-linaro-4.9.4-2017.01-x86_64_arm-linux-gnueabi.tar.xz')
    for name in sorted(names):
        checked(CACHE,dict(lock[name],file=name),v.offline)
    expected=json.loads((HERE/'toolchain.lock.json').read_text()) if v.verify_release else None
    compiler=toolchain(expected=expected)
    for c in components:
        if c=='busybox':
            # BusyBox 1.31.1 needs the legacy libc/kernel headers in this
            # source recipe (modern headers removed the CBQ interface).
            cross=v.busybox_cross_compile
            if cross is None:
                tc=extract('gcc-linaro-4.9.4-2017.01-x86_64_arm-linux-gnueabi.tar.xz',OUT/'linaro')
                cross=str(tc/'bin/arm-linux-gnueabi-')
            if v.verify_release:
                version=subprocess.check_output([cross+'gcc','--version'],text=True).splitlines()[0]
                if version!=expected['busybox_compiler']:raise ValueError('release BusyBox toolchain mismatch: '+version)
            busybox(c,cross,'2026-09-24 23:41:16 CST')
        elif c=='modutils':busybox(c,'arm-linux-gnueabihf-','2026-09-27 21:26:22 CST')
        elif c=='dropbear':
            src=extract('dropbear-2024.86.tar.bz2',OUT/'dropbear');env=dict(os.environ,CFLAGS='-O2 -mno-unaligned-access',LDFLAGS='-static')
            run(['./configure','--host=arm-linux-gnueabihf','--disable-zlib','--disable-syslog'],src,env)
            (src/'localoptions.h').write_text('#define DROPBEAR_SVR_PASSWORD_AUTH 0\n')
            run(['make','-j8','PROGRAMS=dropbear dropbearkey'],src)
            for f in ('dropbear','dropbearkey'):
                shutil.copyfile(src/f,BIN/f);run(['arm-linux-gnueabihf-strip','--strip-unneeded',str(BIN/f)],src)
        elif c=='wifi':
            run(['bash',str(HERE/'wifi.sh'),str(CACHE),str(OUT/'wifi')],OUT)
            for f in ('wpa_supplicant','wpa_cli','iw'):shutil.copyfile(OUT/'wifi/bin'/f,BIN/f)
        elif c=='regdb':
            src=extract('wireless-regdb-2026.09.03.tar.xz',OUT/'regdb')
            run(['python3','db2fw.py',str(BIN/'regulatory.db'),'db.txt'],src)
            if sha(BIN/'regulatory.db')!=sha(src/'regulatory.db'):raise ValueError('regdb differs from release')
            shutil.copyfile(src/'regulatory.db.p7s',BIN/'regulatory.db.p7s')
            run(['openssl','cms','-verify','-binary','-inform','DER','-in',str(BIN/'regulatory.db.p7s'),'-content',str(BIN/'regulatory.db'),'-certfile',str(src/'wens.x509.pem'),'-noverify','-out',str(OUT/'verified.db')],src)
        else:raise ValueError('unknown component '+c)
    results={}
    for f in sorted(BIN.iterdir()):
        item={'rebuilt_sha256':sha(f)}
        if v.reference:
            ref=pathlib.Path(v.reference)/f.name
            if ref.is_file():item.update(reference_sha256=sha(ref),byte_identical=sha(f)==sha(ref))
        results[f.name]=item
    if v.verify_release and any(not item.get('byte_identical',False) for item in results.values()):
        raise ValueError('release verification needs matching --reference binaries')
    report={'toolchain':compiler,'results':results}
    if (OUT/'busybox.links').is_file(): report['busybox_links']={'sha256':sha(OUT/'busybox.links')}
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(results,indent=2))
if __name__=='__main__':main()
