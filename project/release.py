#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Build Linux, barebox, source-built userspace and the Alpine root on the host."""
import argparse, json, os, pathlib, shutil, subprocess, sys, tarfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'sources'));import fetch
sys.path.insert(0,str(ROOT/'rootfs'));from stage import stage
def run(cmd,env=None):subprocess.run([str(x) for x in cmd],check=True,env=env)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--cache',type=pathlib.Path,required=True);ap.add_argument('--out',type=pathlib.Path,required=True);ap.add_argument('--private-inputs',type=pathlib.Path,required=True);ap.add_argument('--signing-key',type=pathlib.Path);ap.add_argument('--offline',action='store_true');ap.add_argument('--jobs',default='12');a=ap.parse_args()
 a.cache=a.cache.resolve();a.out=a.out.resolve();a.private_inputs=a.private_inputs.resolve();a.out.mkdir(parents=True)
 run([sys.executable,ROOT/'sources/fetch.py','--cache',a.cache]+(['--offline'] if a.offline else []))
 src=fetch.extract(a.cache,'Linux',a.out/'linux-source',True)
 for n in (ROOT/'kernel/patches/series').read_text().splitlines():
  if n and not n.startswith('#'):subprocess.run(['git','apply',str(ROOT/'kernel/patches'/n)],cwd=src,check=True)
 inputs=a.out/'kernel-inputs.json';inputs.write_text(json.dumps({'kernel_profile':'emmc-root','inputs':{}})+'\n')
 kernel=a.out/'kernel';run([sys.executable,ROOT/'project/build.py','--source',src,'--inputs',inputs,'--out',kernel,'--jobs',a.jobs])
 run(['make','-C',src,'O='+str(kernel),'ARCH=arm','CROSS_COMPILE=arm-linux-gnueabihf-','KERNELRELEASE=6.6.157-k4-production','modules_install','INSTALL_MOD_PATH='+str(a.out/'modules'),'INSTALL_MOD_STRIP=1'])
 wifi=a.out/'wifi';run(['bash',ROOT/'project/userspace/wifi.sh',a.cache,wifi])
 cachemap=a.out/'cache-map.json';lock=json.loads((ROOT/'project/userspace/sources.lock.json').read_text());cachemap.write_text(json.dumps({n:str(a.cache/n) for n in lock})+'\n')
 run([sys.executable,ROOT/'project/userspace/rebuild.py','--cache-map',cachemap,'--out',a.out/'userspace','--components','busybox,modutils,dropbear,regdb'])
 k4=stage(a.out/'k4-root',a.private_inputs,wifi)
 # Keep the compiled maintenance BusyBox available; Alpine owns /bin/busybox.
 shutil.copyfile(a.out/'userspace/bin/busybox-modutils',k4/'bin/k4-busybox-modutils')
 env=dict(os.environ,KBUILD_BUILD_TIMESTAMP='Fri Oct 2 20:48:05 CST 2026',KBUILD_BUILD_VERSION='1',KBUILD_BUILD_USER='k4',KBUILD_BUILD_HOST='builder')
 usb=a.out/'usb-barebox';run(['sh',ROOT/'barebox/overlay/build.sh',a.cache,ROOT/'barebox/boot1/barebox.config',usb],env)
 run(['sh',ROOT/'barebox/boot1/build.sh',a.cache,ROOT/'barebox/boot1/barebox.config',usb/'build/images/barebox-kindle-d01100.img',a.out/'barebox',a.private_inputs/'boot0.bin'],env)
 keys=a.out/'keys';keys.mkdir(mode=0o700);key=a.signing_key or keys/'k4-alpine.rsa'
 if not a.signing_key:run(['openssl','genrsa','-out',key,'2048']);key.chmod(0o600)
 pub=keys/'k4-alpine.rsa.pub'
 with pub.open('wb') as f:subprocess.run(['openssl','pkey','-in',str(key),'-pubout'],stdout=f,check=True)
 host=a.out/'host-apk';host.mkdir()
 with tarfile.open(a.cache/'apk-tools-static-3.0.8-r0.apk') as t:t.extractall(host,filter='data')
 wsrc=wifi/'work/wpa_supplicant-2.12';local=a.out/'k4-repository'
 run([sys.executable,ROOT/'project/alpine/package_wpa.py','--bin-dir',wifi/'bin','--copying',wsrc/'COPYING','--key',key,'--public-key',pub,'--apk',host/'sbin/apk.static','--out',local])
 run([sys.executable,ROOT/'project/alpine/build.py','--cache',a.cache,'--k4-repo',local,'--public-key',pub,'--k4-root',k4,'--kernel',kernel/'arch/arm/boot/zImage','--dtb',kernel/'arch/arm/boot/dts/nxp/imx/imx50-kindle-k4.dtb','--modules',a.out/'modules/lib/modules','--out',a.out/'alpine'])
 run([sys.executable,ROOT/'project/alpine/verify.py','--build',a.out/'alpine'])
 print('Host build complete. No device operations were performed.')
if __name__=='__main__':main()
