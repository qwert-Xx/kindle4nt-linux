#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Offline feasibility experiment; copies sources, never changes config/defaults."""
import argparse,pathlib,shutil,subprocess,json,hashlib
p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--kernel-out',required=True);p.add_argument('--provider-kernel-out',required=True);p.add_argument('--out',required=True);a=p.parse_args()
r=pathlib.Path(a.source).resolve();o=pathlib.Path(a.out).resolve();k=pathlib.Path(a.kernel_out).resolve();pk=pathlib.Path(a.provider_kernel_out).resolve()
if o.exists() or r in o.parents:raise ValueError('fresh external output required')
o.mkdir();symvers={}
for label,build in [('production',k),('providers-disabled',pk)]:
 lines=(build/'Module.symvers').read_text().splitlines();symvers[label]={x.split()[1]:x.split() for x in lines};
items={'cpufreq-dt':('drivers/cpufreq',['cpufreq-dt.c','cpufreq-dt.h'],k),
'charger':('drivers/power/supply',['k4-mc13892-charger.c','k4-charge-policy.h'],k),
'usb-phy':('drivers/usb/phy',['phy-k4.c','phy-generic.h'],k),
'anatop':('drivers/clk/imx',['clk-imx50-anatop.c'],k),
'pxp':('drivers/soc/imx',['imx50-pxp.c'],pk),
'papyrus':('drivers/regulator',['k4-papyrus.c','k4-panel-vcom.h'],pk)}
results={}
for name,(folder,files,build) in items.items():
 dest=o/name;dest.mkdir()
 for f in files:shutil.copyfile(r/folder/f,dest/f)
 # Driver includes its private PMIC constants by a relative path.
 if name=='papyrus':
  (o/'misc').mkdir(exist_ok=True);shutil.copyfile(r/'drivers/misc/k4-papyrus-registers.h',o/'misc/k4-papyrus-registers.h')
 source=pathlib.Path(files[0]).stem
 (dest/'Makefile').write_text('obj-m += '+source+'.o\nccflags-y += -I'+str(r/'include')+'\n')
 with (dest/'build.log').open('w') as log:
  proc=subprocess.run(['make','-C',str(r),'O='+str(build),'ARCH=arm','CROSS_COMPILE=arm-linux-gnueabihf-','M='+str(dest),'-j8','modules'],stdout=log,stderr=subprocess.STDOUT)
 item={'build_exit':proc.returncode,'profile_symvers':'providers-disabled' if build==pk else 'production','source_sha256':hashlib.sha256((dest/files[0]).read_bytes()).hexdigest(),'exports':[],'unresolved':[]}
 ko=dest/(source+'.ko')
 if ko.exists():
  item['modinfo']=subprocess.check_output(['modinfo',str(ko)],text=True)
  undefined=subprocess.check_output(['arm-linux-gnueabihf-nm','-u',str(ko)],text=True).splitlines()
  table=symvers[item['profile_symvers']]
  for line in undefined:
   symbol=line.split()[-1]
   if symbol in table:
    row=table[symbol];item['exports'].append({'symbol':symbol,'crc':row[0],'provider':row[2],'kind':row[3],'namespace':row[4] if len(row)>4 else ''})
   else:item['unresolved'].append(symbol)
 else:item['failure_tail']=(dest/'build.log').read_text().splitlines()[-15:]
 results[name]=item
 (o/'report.json').write_text(json.dumps(results,indent=2)+'\n')
 print(name,proc.returncode,flush=True)
