#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Host-only source reconstruction. No device commands or runtime installation."""
import argparse,hashlib,json,os,pathlib,shutil,subprocess,tarfile,re
HERE=pathlib.Path(__file__).resolve().parent

def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def run(cmd,cwd,env=None):
    with (OUT/'build.log').open('ab') as log:
        subprocess.run(cmd,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
def extract(name,target):
    target.mkdir()
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

def main():
    global OUT,CACHE,BIN
    a=argparse.ArgumentParser();a.add_argument('--cache-map',required=True);a.add_argument('--out',required=True)
    a.add_argument('--components',default='busybox,modutils,dropbear,wifi,regdb');a.add_argument('--reference',help='read-only accepted inner/bin')
    v=a.parse_args();OUT=pathlib.Path(v.out).resolve()
    if OUT.exists() or HERE.parent.parent in OUT.parents:raise ValueError('require fresh external output directory')
    if v.reference and (OUT==pathlib.Path(v.reference).resolve() or pathlib.Path(v.reference).resolve() in OUT.parents):raise ValueError('output inside reference')
    OUT.mkdir(parents=True);CACHE=OUT/'cache';CACHE.mkdir();BIN=OUT/'bin';BIN.mkdir()
    lock=json.loads((HERE/'sources.lock.json').read_text());sources=json.loads(pathlib.Path(v.cache_map).read_text())
    for name,expected in lock.items():
        source=pathlib.Path(sources[name]).resolve()
        if sha(source)!=expected:raise ValueError('source hash mismatch: '+name)
        (CACHE/name).symlink_to(source)
    compiler=subprocess.check_output(['arm-linux-gnueabihf-gcc','--version'],text=True).splitlines()[0]
    if compiler!='arm-linux-gnueabihf-gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0':raise ValueError('unverified toolchain '+compiler)
    for c in v.components.split(','):
        if c=='busybox':
            tc=extract('gcc-linaro-4.9.4-2017.01-x86_64_arm-linux-gnueabi.tar.xz',OUT/'linaro')
            busybox(c,str(tc/'bin/arm-linux-gnueabi-'),'2026-09-24 23:41:16 CST')
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
    (OUT/'report.json').write_text(json.dumps({'toolchain':compiler,'results':results},indent=2)+'\n')
    print(json.dumps(results,indent=2))
if __name__=='__main__':main()
