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

def toolchain(cross='arm-linux-gnueabihf-', expected=None):
    compiler = cross + 'gcc'
    target = subprocess.check_output([compiler, '-dumpmachine'], text=True).strip()
    if target != 'arm-linux-gnueabihf':
        raise ValueError('expected arm-linux-gnueabihf target, got ' + target)
    version = subprocess.check_output([compiler, '--version'], text=True).splitlines()[0]
    if expected is not None:
        compiler_version = expected['compiler'] if isinstance(expected,dict) else expected
        if version != compiler_version:raise ValueError('release toolchain mismatch: '+version)
        if isinstance(expected,dict) and 'linker' in expected:
            linker=subprocess.check_output([cross+'ld','--version'],text=True).splitlines()[0]
            if linker!=expected['linker']:raise ValueError('release linker mismatch: '+linker)
    return version
