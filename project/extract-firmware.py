#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Extract K4 AR6003 firmware from a stock eMMC user-area image, read-only."""
import argparse
import json
import os
import pathlib
import shutil
import subprocess
import tempfile


def run(*args):
    return subprocess.check_output(args, text=True).strip()


def extract(image, output):
    table = json.loads(run('sfdisk', '--json', str(image)))['partitiontable']
    partition = table['partitions'][0]
    sector = table['sectorsize']
    offset = partition['start'] * sector
    length = partition['size'] * sector
    destination = output / 'firmware/ath6k/AR6003/hw2.1.1'
    destination.mkdir(parents=True, exist_ok=True)
    loop = run('losetup', '--find', '--show', '--read-only',
               '--offset', str(offset), '--sizelimit', str(length), str(image))
    copied = []
    try:
        with tempfile.TemporaryDirectory(prefix='k4-firmware-') as temporary:
            mount = pathlib.Path(temporary)
            mounted = False
            try:
                subprocess.run(['mount', '-o', 'ro,noload', loop, str(mount)], check=True)
                mounted = True
                stock = mount / 'opt/ar6k/target/AR6003/hw2.1.1/bin'
                calibration = stock / 'active_calibration'
                while calibration.is_symlink():
                    target = pathlib.Path(os.readlink(calibration))
                    calibration = (mount / str(target).lstrip('/') if target.is_absolute()
                                   else calibration.parent / target)
                files = {'otp.bin': stock / 'otp.bin',
                         'athwlan.bin': stock / 'athwlan.bin',
                         'data.patch.bin': stock / 'data.patch.hw3_0.bin',
                         'bdata.bin': calibration}
                for name, source in files.items():
                    target = destination / name
                    shutil.copyfile(source, target)
                    target.chmod(0o644)
                    copied.append(dict(source='/' + source.relative_to(mount).as_posix(),
                                       destination=target.relative_to(output).as_posix(),
                                       bytes=target.stat().st_size))
                    print(f'{name}: {target.stat().st_size} bytes')
            finally:
                if mounted:
                    subprocess.run(['umount', str(mount)], check=True)
    finally:
        subprocess.run(['losetup', '-d', loop], check=True)
    report = output / 'firmware-extraction.json'
    report.write_text(json.dumps(dict(partition=1, sector_bytes=sector,
                                     start_sector=partition['start'],
                                     sectors=partition['size'], offset_bytes=offset,
                                     mount_options='ro,noload', files=copied),
                                 indent=2) + '\n')
    if 'SUDO_UID' in os.environ:
        for path in [output, report, output / 'firmware',
                     *list((output / 'firmware').rglob('*'))]:
            os.chown(path, int(os.environ['SUDO_UID']), int(os.environ['SUDO_GID']))
    print('EXTRACT_OK firmware/ath6k/AR6003/hw2.1.1 (4 files)')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('user_image', type=pathlib.Path, help='stock backup user.bin')
    parser.add_argument('output', type=pathlib.Path, help='private input directory')
    args = parser.parse_args()
    extract(args.user_image.resolve(), args.output.resolve())


if __name__ == '__main__':
    main()
