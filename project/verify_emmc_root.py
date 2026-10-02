#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Read-only offline gates for production/debug/persistent-root artifacts."""
import argparse,hashlib,json,pathlib,re,subprocess,tarfile
import rootfs
from verify_k4_defconfig import RECOVERY

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(a):
    prod,repeat,debug,emmc=a.production,a.repeat,a.debug,a.emmc
    reports={}
    for name,p in [('production',prod),('debug',debug),('emmc-root',emmc)]:
        cfg=(p/'.config').read_text();symbols=subprocess.check_output(['arm-linux-gnueabihf-nm',str(p/'vmlinux')],text=True)
        for k in RECOVERY+('EXT4_FS','DEVTMPFS','DEVTMPFS_MOUNT'):
            assert 'CONFIG_'+k+'=y\n' in cfg,(name,k)
        assert ('CONFIG_K4_DIAGNOSTICS=y\n' in cfg)==(name=='debug')
        assert ('CONFIG_ATH6KL_DEBUG=y\n' in cfg)==(name=='debug')
        for k in ('imx50_ocram_cache_enter','imx50_ocram_stop_prepare','imx50_ocram_stop_finish'):assert ' T '+k+'\n' in symbols,(name,k)
        assert (' T k4_ram_trace_mark\n' in symbols)==(name=='debug')
        if name!='debug':
            for k in ('k4_trace_early','__param_clock_snapshot','__param_sdio_init_diag','__param_k4_diagnostic_cycle_ms'):
                assert not any(l.split()[-1]==k for l in symbols.splitlines()),(name,k)
        modules=(p/'modules.order').read_text().splitlines()
        assert len(list((p/'root-modules/lib/modules').rglob('*.ko')))==len(modules)
        assert (p/'Module.symvers').stat().st_size>0
        dtb=p/'arch/arm/boot/dts/nxp/imx'/('k4-debug/imx50-kindle-k4-debug.dtb' if name=='debug' else 'imx50-kindle-k4.dtb')
        reports[name]={'zImage':sha(p/'arch/arm/boot/zImage'),'dtb':sha(dtb),'config':sha(p/'.config'),'modules':len(modules),'linked_symbols_and_builtins':'pass','modpost':'completed by successful kernel build'}
    paths=['.config','vmlinux','Module.symvers','modules.order','arch/arm/boot/zImage','arch/arm/boot/dts/nxp/imx/imx50-kindle-k4.dtb','ram.cpio.gz','ram.cpio.ext3']
    paths += [str(p.relative_to(prod)) for p in sorted(prod.rglob('*.ko')) if 'root-modules' not in p.parts]
    paths += [str(p.relative_to(prod)) for p in sorted((prod/'root-modules').rglob('*')) if p.is_file() and not p.is_symlink()]
    clean=[]
    for n in paths:
        assert (prod/n).read_bytes()==(repeat/n).read_bytes(),('clean build mismatch',n)
        clean.append({'path':n,'sha256':sha(prod/n)})
    for n in paths:
        if n.startswith('ram.cpio'):continue
        assert (prod/n).read_bytes()==(emmc/n).read_bytes(),('production vs emmc',n)
    outer=rootfs.load(a.recipe);nested=a.recipe.parent/outer['filesystem_recipe']
    assert sha(nested)==outer['filesystem_recipe_sha256']
    old={e['name']:e for e in rootfs.load(nested)['entries']}
    with tarfile.open(emmc/'rootfs.tar.gz') as t:
        members={m.name:m for m in t};files={n:t.extractfile(m).read() for n,m in members.items() if m.isfile()}
        assert all(m.uid==m.gid==m.mtime==0 for m in members.values())
        for line in files['etc/k4-rootfs.sha256'].decode().splitlines():
            digest,n=line.split('  ',1);assert hashlib.sha256(files[n]).hexdigest()==digest,n
        boot={'boot/zImage':prod/'arch/arm/boot/zImage','boot/imx50-kindle-k4.dtb':prod/'arch/arm/boot/dts/nxp/imx/imx50-kindle-k4.dtb'}
        for n,p in boot.items():assert files[n]==p.read_bytes(),n
        assert 'boot/k4.dtb' not in members
        template_modes={tuple(pathlib.PurePosixPath(n).parts[3:]):e['mode'] for n,e in old.items() if n.startswith('lib/modules/')}
        for n,m in members.items():
            if n.startswith('lib/modules/') and tuple(pathlib.PurePosixPath(n).parts[3:]) in template_modes:
                assert m.mode==template_modes[tuple(pathlib.PurePosixPath(n).parts[3:])],('module mode',n)
        assert members['sbin/init'].issym() and members['sbin/init'].linkname=='/bin/busybox'
        rc=files['etc/init.d/rcS.k4-base']
        for bad in (b'setro',b'watchdog-guard',b'watchdog-probe',b'root_device='):assert bad not in rc,bad
        assert b'watchdog -T 30 -t 10 /dev/watchdog' in rc
        assert b'guard' not in files['etc/inittab']
        assert all('mke2fs' not in n and 'watchdog-guard' not in n and 'watchdog-probe' not in n for n in members)
        unchanged=[];changed=[]
        for n,e in old.items():
            if e['kind']!='file' or n.startswith('lib/modules/') or n not in files:continue
            expected=b'#!/bin/busybox sh\nexit 0\n' if n=='bin/k4-bootmark' else pathlib.Path(e['resolved']).read_bytes()
            (unchanged if files[n]==expected else changed).append(n)
        assert set(changed)=={'etc/init.d/rcS','etc/init.d/rcShutdown','etc/inittab','etc/k4-root-profile'} | ({'etc/fstab'} if 'etc/fstab' in old else set()),changed
        for n in ('etc/init.d/rcS','etc/init.d/rcS.k4-base','etc/init.d/rcShutdown'):subprocess.run(['sh','-n',str(emmc/'rootfs'/n)],check=True)
        entry_checks={'entries':len(members),'files':len(files),'unchanged_ram_files':unchanged,'changed_ram_files':changed,'tar_all_file_checksums':'pass','tar_ownership_and_times':'all zero','no_guard_or_mke2fs':'pass'}
    v7=(a.v7/'barebox/boot1/emmc-v7').read_text();defaults=(a.v7/'barebox/boot1/usbconsole-v7').read_text()
    assert 'global k4.kernel=/boot/zImage' in defaults and 'global k4.dtb=/boot/imx50-kindle-k4.dtb' in defaults
    args=re.search(r'global linux.bootargs.k4="([^"]+)"',v7).group(1)
    for val in ('root=/dev/mmcblk2p1','rw','rootwait','watchdog.open_timeout=120','imx2_wdt.nowayout=1','ath6kl_sdio.force_virtual_scatter=0','fbcon=map:1','logo.nologo'):assert val in args.split(),val
    assert 'global.bootm.initrd=""' in v7 and 'rdinit=' not in args
    assert 'CONFIG_INITRAMFS_SOURCE=""\n' in (emmc/'.config').read_text()
    return {'profiles':reports,'production_clean_exact':clean,'production_emmc_kernel_modules_byte_equal':True,'rootfs':dict(entry_checks,path=str(emmc/'rootfs.tar.gz'),size=(emmc/'rootfs.tar.gz').stat().st_size,sha256=sha(emmc/'rootfs.tar.gz')),'v7_contract':{'commit':subprocess.check_output(['git','-C',str(a.v7),'rev-parse','HEAD'],text=True).strip(),'bootargs':args,'paths_match':True,'rootfstype':'v7 filesystem probing; ext4 builtin','initrd':False},'device_operations':False}
def main():
    p=argparse.ArgumentParser()
    for n in ('production','repeat','debug','emmc','recipe','v7','report'):p.add_argument('--'+n,required=True,type=pathlib.Path)
    a=p.parse_args();r=verify(a);a.report.write_text(json.dumps(r,indent=2)+'\n');print('PRODUCTION_DEBUG_EMMC_GATES_PASS')
if __name__=='__main__':main()
