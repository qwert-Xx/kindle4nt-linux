#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Host-only maintenance bundle; no production RAM-root integration."""
from build_support import output as prepare_output, toolchain
import argparse,os,hashlib,json,subprocess,tarfile,shutil,gzip
from pathlib import Path
HERE=Path(__file__).resolve().parent

def main():
 a=argparse.ArgumentParser();a.add_argument('--cache',type=Path,default=Path.home()/'.cache/k4/sources');a.add_argument('--offline',action='store_true');a.add_argument('--out',type=Path,default=os.environ.get('OUT',str(HERE.parents[1]/'out/maintenance')));a.add_argument('--clean',action='store_true');v=a.parse_args()
 lock=json.loads((HERE/'maintenance-sources.lock.json').read_text())['mmc-utils']
 cache=v.cache.resolve();repository=cache/'mmc-utils.git'
 v.out=prepare_output(v.out,[cache,HERE],v.clean)
 cache.mkdir(parents=True,exist_ok=True)
 if not repository.exists():
  if v.offline:raise FileNotFoundError(repository)
  subprocess.run(['git','clone','--bare',lock['upstream'],str(repository)],check=True)
 try:
  commit=subprocess.check_output(['git','-C',str(repository),'rev-parse','--verify',lock['commit']+'^{commit}'],text=True).strip()
 except subprocess.CalledProcessError:
  if v.offline:raise
  subprocess.run(['git','-C',str(repository),'fetch','origin',lock['commit']],check=True)
  commit=subprocess.check_output(['git','-C',str(repository),'rev-parse',lock['commit']+'^{commit}'],text=True).strip()
 if commit!=lock['commit']:raise ValueError('mmc-utils commit mismatch: '+commit)
 src=v.out/'source'
 if not src.exists():subprocess.run(['git','clone','--no-checkout',str(repository),str(src)],check=True)
 subprocess.run(['git','-C',str(src),'checkout','--detach',commit],check=True)
 if subprocess.check_output(['git','-C',str(src),'rev-parse','HEAD'],text=True).strip()!=commit:raise ValueError('mmc-utils checkout mismatch')
 if subprocess.check_output(['git','-C',str(src),'status','--porcelain','--untracked-files=no'],text=True).strip():raise ValueError('mmc-utils tracked source modified; use --clean')
 bundle=v.out/'maintenance';bundle.mkdir(exist_ok=True)
 compiler=toolchain()
 with (v.out/'build.log').open('w') as log:
  subprocess.run(['make','-j8','C=0','CC=arm-linux-gnueabihf-gcc','GIT_VERSION="v1.0"','CFLAGS=-O2 -mno-unaligned-access','LDFLAGS=-static'],cwd=src,stdout=log,stderr=subprocess.STDOUT,check=True)
  shutil.copyfile(src/'mmc',bundle/'mmc')
  subprocess.run(['arm-linux-gnueabihf-strip','--strip-unneeded',str(bundle/'mmc')],check=True)
  subprocess.run(['arm-linux-gnueabihf-gcc','-O2','-Wall','-Wextra','-Werror','-mno-unaligned-access','-static',str(HERE/'extcsd-read-only.c'),'-o',str(bundle/'extcsd-read')],stdout=log,stderr=subprocess.STDOUT,check=True)
  subprocess.run(['arm-linux-gnueabihf-strip','--strip-unneeded',str(bundle/'extcsd-read')],check=True)
 report={'source':lock,'toolchain':compiler,'artifacts':{}}
 for name in ('mmc','extcsd-read'):
  item=bundle/name
  item.chmod(0o755)
  headers=subprocess.check_output(['arm-linux-gnueabihf-readelf','-h',str(item)],text=True)
  segments=subprocess.check_output(['arm-linux-gnueabihf-readelf','-l',str(item)],text=True)
  assert 'ARM' in headers and 'hard-float ABI' in headers and 'INTERP' not in segments
  report['artifacts'][item.name]={'sha256':hashlib.sha256(item.read_bytes()).hexdigest(),'size':item.stat().st_size,'static_armhf':True}
 (v.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 (bundle/'SHA256SUMS').write_text(''.join(x['sha256']+'  '+name+'\n' for name,x in report['artifacts'].items()))
 shutil.copyfile('/usr/share/common-licenses/GPL-2',bundle/'COPYING.GPL-2')
 notices=[]
 for name in ('mmc_cmds.c','lsmmc.c','3rdparty/hmac_sha/hmac_sha2.c','3rdparty/hmac_sha/sha2.c'):
  text=(src/name).read_text();notices.append(name+'\n'+text[:text.index('*/')+2])
 (bundle/'NOTICES').write_text('\n\n'.join(notices)+'\n')
 for name in ('set-partition-config-draft.sh','rollback-boot0-draft.sh'):
  shutil.copyfile(HERE.parents[1]/'porting/barebox-emmc'/name,bundle/name)
  (bundle/name).chmod(0o755)
 with (bundle/'mmc-utils-source.tar.gz').open('wb') as packed:
  with gzip.GzipFile(fileobj=packed,mode='wb',filename='',mtime=0) as compressed:
   with tarfile.open(fileobj=compressed,mode='w') as source_archive:
    for tracked in subprocess.check_output(['git','-C',str(src),'ls-files','-z']).split(b'\0'):
     if tracked:
      name=os.fsdecode(tracked)
      info=source_archive.gettarinfo(src/name,arcname='mmc-utils/'+name)
      info.uid=info.gid=info.mtime=0;info.uname=info.gname=''
      with (src/name).open('rb') as source:source_archive.addfile(info,source)
 (bundle/'SOURCE-COMMIT').write_text(commit+'\n')
 entries=[x for x in sorted(bundle.iterdir()) if x.name!='SHA256SUMS']
 (bundle/'SHA256SUMS').write_text(''.join(hashlib.sha256(x.read_bytes()).hexdigest()+'  '+x.name+'\n' for x in entries))
 archive=v.out/'maintenance.tar.gz'
 with archive.open('wb') as output:
  tar=subprocess.Popen(['tar','--sort=name','--mtime=@0','--owner=0','--group=0','--numeric-owner','-cf','-','-C',str(v.out),'maintenance'],stdout=subprocess.PIPE)
  subprocess.run(['gzip','-n'],stdin=tar.stdout,stdout=output,check=True);tar.stdout.close()
  assert tar.wait()==0
 report['bundle_sha256']=hashlib.sha256(archive.read_bytes()).hexdigest()
 (v.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
