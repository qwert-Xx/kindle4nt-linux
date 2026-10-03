#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Build K4 programs; stage public files and explicit external private inputs."""
import argparse, json, pathlib, shutil, subprocess, os
HERE=pathlib.Path(__file__).resolve().parent
def stage(out,private,wifi):
 out=pathlib.Path(out);shutil.copytree(HERE/'k4',out,ignore=shutil.ignore_patterns('*.license'))
 env=dict(os.environ,SOURCE_DATE_EPOCH='1790812800')
 programs=json.loads((HERE/'programs.json').read_text())
 for name,(source,flags) in programs.items():
  extra=[str(HERE/'src/vfp-suspend.S')] if '-DK4_VFP_PROBE' in flags else []
  common=['arm-linux-gnueabihf-gcc','-static','-Os','-Wall','-Wextra','-Werror','-Wl,--build-id=sha1','-ffile-prefix-map='+str(HERE)+'=/src/k4','-fdebug-prefix-map='+str(HERE)+'=/src/k4']+flags
  objects=out.parent/(out.name+'-objects');objects.mkdir(exist_ok=True)
  compiled=[]
  for source_file in [str(HERE/'src'/source)]+extra:
   obj=objects/(name+'.'+pathlib.Path(source_file).stem+'.o')
   subprocess.run(common+['-save-temps=obj','-c',source_file,'-o',str(obj)],env=env,check=True);compiled.append(str(obj))
  subprocess.run(common+compiled+['-o',str(out/'bin'/name)],env=env,check=True)
 for name in ('wpa_supplicant','wpa_cli'):shutil.copyfile(pathlib.Path(wifi)/'bin'/name,out/'bin'/name)
 for n in ('lib/firmware','root/.ssh','etc/dropbear'):
  target=out/n;target.mkdir(parents=True,exist_ok=True)
  p=pathlib.Path(private)/n
  if p.exists():shutil.copytree(p,target,dirs_exist_ok=True,symlinks=True)
 p=pathlib.Path(private)/'etc/wpa_supplicant.conf'
 (out/'etc/wpa_supplicant.conf').write_bytes(p.read_bytes() if p.exists() else b'ctrl_interface=/run/wpa_supplicant\n')
 return out
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--private-inputs',required=True);ap.add_argument('--wifi',required=True);a=ap.parse_args();stage(a.out,a.private_inputs,a.wifi)
