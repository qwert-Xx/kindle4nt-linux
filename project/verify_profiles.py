#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Link/config checks for production/debug K4 builds. No device access."""
import argparse,hashlib,json,pathlib,subprocess
p=argparse.ArgumentParser();p.add_argument('baseline');p.add_argument('production');p.add_argument('debug');p.add_argument('--report',required=True);a=p.parse_args()
paths={k:pathlib.Path(getattr(a,k)) for k in ('baseline','production','debug')}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def symbols(x):return subprocess.check_output(['arm-linux-gnueabihf-nm',str(x/'vmlinux')],text=True)
required=('IMX50_PM','IMX50_OCRAM','K4_MC13892_STANDBY','POWER_RESET_K4_MC13892','CHARGER_K4_MC13892','USB_K4_PHY','IMX2_WDT')
reports={}
for name in ('production','debug'):
 x=paths[name];s=symbols(x);c=(x/'.config').read_text()
 for k in required:assert 'CONFIG_'+k+'=y\n' in c,k
 for k in ('imx50_ocram_cache_enter','imx50_ocram_stop_prepare','imx50_ocram_stop_finish'):assert ' T '+k+'\n' in s,k
 assert sha(x/'arch/arm/mach-imx/ocram-imx50-cache.o')==sha(paths['baseline']/'arch/arm/mach-imx/ocram-imx50-cache.o')
 assert sha(x/'arch/arm/boot/dts/nxp/imx/imx50-kindle-k4-stock-pxp.dtb')==sha(paths['baseline']/'arch/arm/boot/dts/nxp/imx/imx50-kindle-k4-stock-pxp.dtb')
 if name=='production':
  for sym in ('k4_ram_trace_mark','k4_trace_early','__param_clock_snapshot','__param_sdio_init_diag','__param_k4_diagnostic_cycle_ms'):
   assert not any(line.split()[-1]==sym for line in s.splitlines()),sym
  for k in ('K4_DIAGNOSTICS','K4_BOOT_TRACE','K4_PM_RAM_TRACE','IMX50_OCRAM_PROBE'):assert 'CONFIG_'+k+'=y\n' not in c and 'CONFIG_'+k+'=m\n' not in c,k
 else:
  assert ' T k4_ram_trace_mark\n' in s
  assert 'CONFIG_K4_DIAGNOSTICS=y\n' in c and 'CONFIG_IMX50_OCRAM_PROBE=y\n' in c
 reports[name]={'zImage_sha256':sha(x/'arch/arm/boot/zImage'),'dtb_exact':True,'ocram_assembly_exact':True,'recovery_builtins':list(required),'modules':len((x/'modules.order').read_text().splitlines()),'link_checks':'passed'}
pathlib.Path(a.report).write_text(json.dumps({'profiles':reports,'physical_regression':'pending supervisor scheduling'},indent=2)+'\n');print('PROFILE_LINK_CHECKS_PASS')
