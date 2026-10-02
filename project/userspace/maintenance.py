#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Host-only maintenance bundle; no production RAM-root integration."""
import argparse,hashlib,json,subprocess,tarfile,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent

def main():
 a=argparse.ArgumentParser();a.add_argument('--source',required=True,type=Path);a.add_argument('--out',required=True,type=Path);v=a.parse_args()
 lock=json.loads((HERE/'maintenance-sources.lock.json').read_text())['mmc-utils-1.0.tar.gz']
 assert hashlib.sha256(v.source.read_bytes()).hexdigest()==lock['sha256']
 assert v.out.resolve().is_relative_to(HERE.parents[1]/'out'), 'output must stay in this worktree/out'
 v.out.mkdir(parents=True,exist_ok=False);dest=v.out/'source';dest.mkdir()
 with tarfile.open(v.source) as archive:archive.extractall(dest,filter='data')
 src=dest/'mmc-utils-1.0';bundle=v.out/'maintenance';bundle.mkdir()
 compiler=subprocess.check_output(['arm-linux-gnueabihf-gcc','--version'],text=True).splitlines()[0]
 with (v.out/'build.log').open('w') as log:
  subprocess.run(['make','-j8','C=0','CC=arm-linux-gnueabihf-gcc','GIT_VERSION="v1.0"','CFLAGS=-O2 -mno-unaligned-access','LDFLAGS=-static'],cwd=src,stdout=log,stderr=subprocess.STDOUT,check=True)
  shutil.copyfile(src/'mmc',bundle/'mmc')
  subprocess.run(['arm-linux-gnueabihf-strip','--strip-unneeded',str(bundle/'mmc')],check=True)
  subprocess.run(['arm-linux-gnueabihf-gcc','-O2','-Wall','-Wextra','-Werror','-mno-unaligned-access','-static',str(HERE/'extcsd-read-only.c'),'-o',str(bundle/'extcsd-read')],stdout=log,stderr=subprocess.STDOUT,check=True)
  subprocess.run(['arm-linux-gnueabihf-strip','--strip-unneeded',str(bundle/'extcsd-read')],check=True)
 report={'source':lock,'toolchain':compiler,'artifacts':{}}
 for item in bundle.iterdir():
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
  shutil.copyfile(HERE.parents[1]/'barebox/boot1'/name,bundle/name)
  (bundle/name).chmod(0o755)
 shutil.copyfile(v.source,bundle/'mmc-utils-1.0.tar.gz')
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
