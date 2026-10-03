#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Build Alpine eMMC, Alpine RAM and BusyBox maintenance RAM images offline."""
import argparse, json, pathlib, subprocess, sys
import build

HERE = pathlib.Path(__file__).resolve().parent

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', required=True, type=pathlib.Path,
                        help='external JSON: hashed kernel/RAM inputs and alpine paths (cache, firmware_dir, wifi_config, authorized_keys, ssh_host_key, tools_dir)')
    parser.add_argument('--out', required=True, type=pathlib.Path)
    parser.add_argument('--source', help='Linux source directory for kernel compilation')
    parser.add_argument('--mode', choices=('source', 'prebuilt'), default='source')
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    data = build.inputs(args.inputs)
    alpine = {name: str((args.inputs.resolve().parent / value).resolve())
              for name, value in data['alpine'].items()}
    if args.check_only:
        print('INPUTS_OK')
        return
    out = args.out.resolve()
    kernel = out / 'maintenance'
    command = [sys.executable, str(HERE / 'build.py'), '--inputs', str(args.inputs),
               '--out', str(kernel), '--mode', args.mode]
    if args.source:
        command += ['--source', args.source]
    subprocess.run(command, check=True)
    if args.mode == 'prebuilt':
        image = pathlib.Path(data['inputs']['zImage']['resolved'])
        dtb = pathlib.Path(data['inputs']['dtb']['resolved'])
    else:
        image = kernel / 'arch/arm/boot/zImage'
        dtb = kernel / 'arch/arm/boot/dts' / data.get('dtb', 'nxp/imx/imx50-kindle-k4.dtb')
    command = [sys.executable, str(HERE / 'alpine/build.py'),
               '--kernel', str(image), '--dtb', str(dtb),
               '--modules', str(kernel / 'root-modules/lib/modules'),
               '--out', str(out / 'alpine')]
    for name, value in alpine.items():
        command += ['--' + name.replace('_', '-'), value]
    subprocess.run(command, check=True)
    subprocess.run([sys.executable, str(HERE / 'alpine/ram.py'),
                    '--rootfs-tar', str(out / 'alpine/rootfs.tar.gz'),
                    '--out', str(out / 'alpine-ram')], check=True)
    print('IMAGES_OK alpine/rootfs.tar.gz alpine-ram/alpine-ram.cpio.gz maintenance/ram.cpio.gz')

if __name__ == '__main__':
    main()
