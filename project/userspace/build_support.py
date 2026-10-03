# SPDX-License-Identifier: GPL-2.0-or-later
"""Shared output and toolchain handling for host-only builds."""
import pathlib, shutil, subprocess

def output(path, inputs=(), clean=False):
    out = pathlib.Path(path).resolve()
    for source in inputs:
        source = pathlib.Path(source).resolve()
        if source == out or out in source.parents or (source.is_dir() and source in out.parents):
            raise ValueError('output overlaps input: ' + str(source))
    if clean and out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    return out

def toolchain(cross='arm-linux-gnueabihf-'):
    compiler = cross + 'gcc'
    target = subprocess.check_output([compiler, '-dumpmachine'], text=True).strip()
    if target != 'arm-linux-gnueabihf':
        raise ValueError('expected arm-linux-gnueabihf target, got ' + target)
    version = subprocess.check_output([compiler, '--version'], text=True).splitlines()[0]
    return version
