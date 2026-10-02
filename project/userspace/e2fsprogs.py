#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Build only a static ARM mke2fs maintenance tool, never run on devices."""
import argparse,gzip,hashlib,json,os,pathlib,shutil,subprocess,tarfile
HERE=pathlib.Path(__file__).parent
def package(bundle,output):
    with output.open('wb') as raw,gzip.GzipFile(fileobj=raw,filename='',mtime=0,mode='wb') as gz,tarfile.open(fileobj=gz,mode='w',format=tarfile.GNU_FORMAT) as t:
        for src in sorted(bundle.iterdir()):
            info=t.gettarinfo(str(src),arcname='maintenance/'+src.name);info.uid=info.gid=info.mtime=0;info.uname=info.gname=''
            with src.open('rb') as f:t.addfile(info,f)
def main():
    a=argparse.ArgumentParser();a.add_argument('--source',required=True,type=pathlib.Path);a.add_argument('--out',required=True,type=pathlib.Path);v=a.parse_args()
    lock=json.loads((HERE/'e2fsprogs.lock.json').read_text())
    assert hashlib.sha256(v.source.read_bytes()).hexdigest()==lock['sha256']
    v.out.mkdir(parents=True,exist_ok=False)
    with tarfile.open(v.source) as t:t.extractall(v.out,filter='data')
    src=v.out/('e2fsprogs-'+lock['version']);build=v.out/'build';build.mkdir();bundle=v.out/'maintenance';bundle.mkdir()
    env=dict(os.environ,CC='arm-linux-gnueabihf-gcc',AR='arm-linux-gnueabihf-ar',RANLIB='arm-linux-gnueabihf-ranlib',CFLAGS='-O2 -mno-unaligned-access',LDFLAGS='-static',SOURCE_DATE_EPOCH='1727740800')
    with (v.out/'build.log').open('w') as log:
        def run(cmd):subprocess.run(cmd,cwd=build,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
        run([str(src/'configure'),'--host=arm-linux-gnueabihf','--disable-nls','--disable-elf-shlibs','--disable-uuidd','--disable-fsck','--disable-e2initrd-helper','--without-crond-dir','--enable-libuuid','--enable-libblkid'])
        run(['make','-j8','libs'])
        run(['make','-C','misc','-j8','mke2fs'])
    shutil.copyfile(build/'misc/mke2fs',bundle/'mke2fs');(bundle/'mke2fs').chmod(0o755)
    subprocess.run(['arm-linux-gnueabihf-strip','--strip-unneeded',str(bundle/'mke2fs')],check=True)
    h=subprocess.check_output(['arm-linux-gnueabihf-readelf','-h',str(bundle/'mke2fs')],text=True);segments=subprocess.check_output(['arm-linux-gnueabihf-readelf','-l',str(bundle/'mke2fs')],text=True)
    assert 'ARM' in h and 'hard-float ABI' in h and 'INTERP' not in segments
    for name in ('mke2fs.conf',):shutil.copyfile(HERE/name,bundle/name)
    shutil.copyfile(src/'NOTICE',bundle/'NOTICE')
    shutil.copyfile(v.source,bundle/v.source.name)
    shutil.copyfile(HERE.parent/'tools/deploy-emmc-root',bundle/'deploy-emmc-root');(bundle/'deploy-emmc-root').chmod(0o755)
    report={'source':lock,'compiler':subprocess.check_output(['arm-linux-gnueabihf-gcc','--version'],text=True).splitlines()[0],'static_armhf':True,'artifacts':{x.name:{'size':x.stat().st_size,'sha256':hashlib.sha256(x.read_bytes()).hexdigest()} for x in sorted(bundle.iterdir())}}
    (bundle/'SHA256SUMS').write_text(''.join(v['sha256']+'  '+n+'\n' for n,v in report['artifacts'].items()))
    package(bundle,v.out/'maintenance.tar.gz')
    report['bundle_sha256']=hashlib.sha256((v.out/'maintenance.tar.gz').read_bytes()).hexdigest()
    (v.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
