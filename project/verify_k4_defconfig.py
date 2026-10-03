#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Read-only config/recovery/clean-artifact gates for three K4 profiles."""
import argparse,hashlib,json,pathlib,re,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1]
RECOVERY=('IMX50_PM','IMX50_OCRAM','K4_MC13892_STANDBY',
          'POWER_RESET_K4_MC13892','CHARGER_K4_MC13892','USB_K4_PHY','IMX2_WDT',
          'KEXEC','BLK_DEV_INITRD','BLK_DEV_RAM','BLK_DEV_LOOP','EXT3_FS','MMC_BLOCK',
          'MMC_SDHCI_ESDHC_IMX','USB_CONFIGFS','USB_CONFIGFS_ACM','USB_CONFIGFS_RNDIS',
          'CFG80211','MAC80211','CFG80211_REQUIRE_SIGNED_REGDB')
LIFECYCLE={'CONFIG_FB_IMX50_EPDC','CONFIG_IMX50_EPDC','CONFIG_REGULATOR_K4_PAPYRUS','CONFIG_IMX50_EPDC_IMAGE','CONFIG_IMX50_EPDC_BUFFER',
           'CONFIG_IMX50_EPDC_HW','CONFIG_IMX50_EPDC_WAVEFORM'}
def values(p): return dict(re.findall(r'^(CONFIG_\w+)=(.*)$',p.read_text(),re.M))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(production,repeat,debug,lifecycle,baseline_dtb):
    reference=values(ROOT/'project/configs/reference-a8accb2a8/k4-production.config')
    protected = re.compile(r'CONFIG_(?:K4_|IMX50_|MC13|REGULATOR_MC13|CHARGER_K4|POWER_RESET_K4|FB_IMX50|REGULATOR_K4|BATTERY_BQ27XXX_I2C|RTC_DRV_(?:MXC|MC13)|SERIAL_IMX|SPI_IMX|I2C_IMX|KEYBOARD_(?:GPIO|MATRIX)|NVMEM_K4|USB_SERIAL(?:_|$)|CRC7$)')
    reports={}
    for name,path in [('production',production),('debug',debug),('lifecycle',lifecycle)]:
        cfg=values(path/'.config')
        for key in RECOVERY: assert cfg.get('CONFIG_'+key)=='y',(name,key)
        for key in ('ATH6KL','ATH6KL_SDIO'): assert cfg.get('CONFIG_'+key)=='m',(name,key)
        assert (cfg.get('CONFIG_ATH6KL_DEBUG')=='y')==(name=='debug'),name
        assert (cfg.get('CONFIG_K4_DIAGNOSTICS')=='y')==(name=='debug'),name
        for key,val in reference.items():
            if val not in ('y','m') or not protected.match(key): continue
            if name=='lifecycle' and key in LIFECYCLE: continue
            if key=='CONFIG_USB_SERIAL_GENERIC': continue  # no bound generic endpoint
            assert cfg.get(key,'n')==val,(name,key,cfg.get(key),val)
        for key in LIFECYCLE: assert cfg.get(key,'n')==('n' if name=='lifecycle' else 'y'),(name,key)
        # Numeric hardware/policy settings in surviving options must not change.
        for key,val in reference.items():
            if val not in ('y','m') and key in cfg: assert cfg[key]==val,(name,key,val,cfg[key])
        dtb=path/'arch/arm/boot/dts/nxp/imx/imx50-kindle-k4.dtb'
        assert dtb.read_bytes()==baseline_dtb.read_bytes(),name
        modules=(path/'modules.order').read_text().splitlines()
        if name!='debug':
            assert not any(any(bad in x for bad in ('dmatest','usbtest','k4-pm-trace','k4-mc13892-monitor')) for x in modules)
        installed=list((path/'root-modules/lib/modules').rglob('*.ko'))
        assert len(installed)==len(modules),(name,len(installed),len(modules))
        reports[name]={'modules':len(modules),'dtb_sha256':sha(dtb),'recovery_builtins':list(RECOVERY),'config_sha256':sha(path/'.config'),'zImage_sha256':sha(path/'arch/arm/boot/zImage'),'modpost':'complete ARM build; modules installed','retained_and_numeric_policy':'pass'}
    candidates=['.config','vmlinux','Module.symvers','modules.order','arch/arm/boot/zImage',
                'arch/arm/boot/dts/nxp/imx/imx50-kindle-k4.dtb','ram.cpio.gz','ram.cpio.ext3']
    candidates += [str(p.relative_to(production)) for p in sorted(production.rglob('*.ko')) if 'root-modules' not in p.parts]
    candidates += [str(p.relative_to(production)) for p in sorted((production/'root-modules').rglob('*')) if p.is_file() and not p.is_symlink()]
    compared=[]
    for rel in candidates:
        a,b=production/rel,repeat/rel
        assert a.read_bytes()==b.read_bytes(),('clean mismatch',rel)
        compared.append({'path':rel,'sha256':sha(a)})
    return {'profiles':reports,'clean_build_exact':compared,'device_operations':False,'physical_acceptance':'pending supervisor integration'}
def main():
    p=argparse.ArgumentParser()
    for name in ('production','repeat','debug','lifecycle','baseline-dtb','report'):p.add_argument('--'+name,required=True,type=pathlib.Path)
    a=p.parse_args();report=verify(a.production,a.repeat,a.debug,a.lifecycle,a.baseline_dtb)
    a.report.write_text(json.dumps(report,indent=2)+'\n');print('K4_DEFCONFIG_GATES_PASS')
if __name__=='__main__':main()
