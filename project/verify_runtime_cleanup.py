#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Inspect generated runtime artifacts without starting services or devices."""
import argparse, hashlib, json, pathlib, runpy, subprocess, tarfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
def inspect(directory,maintenance):
    out=pathlib.Path(directory);maint=pathlib.Path(maintenance)
    read=runpy.run_path(str(ROOT/'porting/package-rootfs.py'))['read_newc']
    alpine=read(out/'alpine-ram-final/alpine-ram.cpio.gz')
    boot=read(maint/'initramfs.cpio.gz')
    with tarfile.open(maint/'rootfs.tar.gz') as archive:
        root={m.name:(m,archive.extractfile(m).read() if m.isfile() else m.linkname.encode()) for m in archive}
    with tarfile.open(out/'alpine-emmc-final/rootfs.tar.gz') as archive:
        emmc={m.name:(m,archive.extractfile(m).read() if m.isfile() else m.linkname.encode()) for m in archive}
    for label,entries in [('Alpine RAM',alpine),('Alpine eMMC',emmc),('maintenance bootstrap',boot),('maintenance root',root)]:
        assert not any('watchdog-guard' in n or 'watchdog-probe' in n for n in entries),label
        for n in ('init','etc/inittab','etc/init.d/rcS','etc/init.d/rcShutdown','etc/k4/platform-start'):
            if n in entries:
                data=entries[n][1]
                for bad in (b'setro',b'setrw',b'watchdog-guard',b'heartbeat',b'ram_shutdown_timeout_ms',b'ram_shutdown_stall_ms'):
                    assert bad not in data,(label,n,bad)
                if data.startswith(b'#!'):subprocess.run(['sh','-n'],input=data,check=True)
    for entries in (alpine,emmc):
        assert 'etc/runlevels/boot/watchdog' in entries
        assert b'-T 30 -t 10' in entries['etc/conf.d/watchdog'][1]
        assert 'etc/init.d/k4-filesystems' not in entries
    rc=root['etc/init.d/rcS'][1]
    assert b'watchdog -T 30 -t 10 /dev/watchdog' in rc
    assert b'dropbearkey' in rc and b'echo ready > /run/k4-boot-ready' in rc
    assert b'mark K4_ACCESSORY_CONTROLLER_LOAD_FAILED\n    exit 1' not in rc
    assert b' -j' not in root['bin/k4-userspace-service'][1] and b' -k ' not in root['bin/k4-userspace-service'][1]
    assert b'"$loop" /newroot' in boot['init'][1]
    assert b'/dev/mmc' not in alpine['etc/fstab'][1]
    for profile in ('production','debug'):
        build=out/profile;config=(build/'.config').read_text()
        assert 'CONFIG_K4_PM_HEALTH_CLOCK' not in config
        symbols=subprocess.check_output(['arm-linux-gnueabihf-nm',str(build/'vmlinux')])
        for bad in (b'k4_pm_health_init',b'__param_ram_shutdown_timeout_ms',b'__param_ram_shutdown_stall_ms'):
            assert bad not in symbols,(profile,bad)
        dtb=build/'arch/arm/boot/dts/nxp/imx/imx50-kindle-k4.dtb'
        text=subprocess.check_output(['dtc','-I','dtb','-O','dts',str(dtb)],stderr=subprocess.DEVNULL)
        assert b'pm-health' not in text and b'pm_health' not in text
    return dict(startup_without_guard_or_block_locks=True,watchdog='continuous -T 30 -t 10',alpine_watchdog_runlevel='boot',maintenance_user_area_automount=False,ssh_hostkey_first_start=True,ssh_forwarding_allowed=True,pm_health_and_shutdown_test_parameters_absent=True,dtb_pm_health_absent=True,device_operations=False)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('output',type=pathlib.Path);parser.add_argument('maintenance',type=pathlib.Path);args=parser.parse_args()
    result=inspect(args.output,args.maintenance)
    (args.output/'runtime-checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print('RUNTIME_ARTIFACT_CHECKS_PASS '+json.dumps(result))
