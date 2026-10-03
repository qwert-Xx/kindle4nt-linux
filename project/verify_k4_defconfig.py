#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Read-only config/recovery/clean-artifact gates for three K4 profiles."""
import argparse,hashlib,json,pathlib,re,subprocess
RECOVERY=('IMX50_PM','IMX50_OCRAM','K4_MC13892_STANDBY',
          'POWER_RESET_K4_MC13892','CHARGER_K4_MC13892','USB_K4_PHY','IMX2_WDT',
          'KEXEC','BLK_DEV_INITRD','BLK_DEV_RAM','BLK_DEV_LOOP','EXT3_FS','MMC_BLOCK',
          'MMC_SDHCI_ESDHC_IMX','USB_CONFIGFS','USB_CONFIGFS_ACM','USB_CONFIGFS_RNDIS',
          'CFG80211','MAC80211','CFG80211_REQUIRE_SIGNED_REGDB')
LIFECYCLE={'CONFIG_FB_IMX50_EPDC','CONFIG_IMX50_EPDC','CONFIG_REGULATOR_K4_PAPYRUS','CONFIG_IMX50_EPDC_IMAGE','CONFIG_IMX50_EPDC_BUFFER',
           'CONFIG_IMX50_EPDC_HW','CONFIG_IMX50_EPDC_WAVEFORM'}
def values(p): return dict(re.findall(r'^(CONFIG_\w+)=(.*)$',p.read_text(),re.M))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(production,debug,lifecycle):
    reports={}
    for name,path in [('production',production),('debug',debug),('lifecycle',lifecycle)]:
        cfg=values(path/'.config')
        for key in RECOVERY: assert cfg.get('CONFIG_'+key)=='y',(name,key)
        for key in ('ATH6KL','ATH6KL_SDIO'): assert cfg.get('CONFIG_'+key)=='m',(name,key)
        assert (cfg.get('CONFIG_ATH6KL_DEBUG')=='y')==(name=='debug'),name
        assert (cfg.get('CONFIG_K4_DIAGNOSTICS')=='y')==(name=='debug'),name
        for key in LIFECYCLE: assert cfg.get(key,'n')==('n' if name=='lifecycle' else 'y'),(name,key)
        dtb=path/'arch/arm/boot/dts/nxp/imx/imx50-kindle-k4.dtb'
        modules=(path/'modules.order').read_text().splitlines()
        if name!='debug':
            assert not any(any(bad in x for bad in ('dmatest','usbtest','k4-pm-trace','k4-mc13892-monitor')) for x in modules)
        installed=list((path/'root-modules/lib/modules').rglob('*.ko'))
        assert len(installed)==len(modules),(name,len(installed),len(modules))
        reports[name]={'modules':len(modules),'dtb_sha256':sha(dtb),'recovery_builtins':list(RECOVERY),'config_sha256':sha(path/'.config'),'zImage_sha256':sha(path/'arch/arm/boot/zImage'),'modpost':'complete ARM build; modules installed'}
    return {'profiles':reports,'device_operations':False,'physical_acceptance':'pending supervisor integration'}
def main():
    p=argparse.ArgumentParser()
    for name in ('production','debug','lifecycle','report'):p.add_argument('--'+name,required=True,type=pathlib.Path)
    a=p.parse_args();report=verify(a.production,a.debug,a.lifecycle)
    a.report.write_text(json.dumps(report,indent=2)+'\n');print('K4_DEFCONFIG_GATES_PASS')
if __name__=='__main__':main()
