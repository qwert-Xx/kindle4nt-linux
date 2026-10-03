#!/usr/bin/env python3
"""Build K4 boot1 from the locked upstream release and board inputs."""
import argparse, os, shutil, subprocess, sys
from pathlib import Path
P = Path(__file__).resolve().parent
R = P.parents[1]
sys.path.insert(0, str(R/'sources'))
from fetch import extract

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=R/'out/barebox-v9')
    parser.add_argument('--cache', type=Path, default=R/'out/sources')
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--config', type=Path, default=P/'v9_defconfig')
    parser.add_argument('--jobs', type=int, default=8)
    args = parser.parse_args()
    out = args.output.resolve()
    # A fresh source/output directory prevents stale inputs from affecting builds.
    out.mkdir(parents=True, exist_ok=False)
    args.cache.mkdir(parents=True, exist_ok=True)
    source = extract(args.cache, 'barebox', out/'source', args.offline)
    with (P/'board.patch').open('rb') as patch:
        subprocess.run(['patch', '--batch', '-p1'], cwd=source, stdin=patch, check=True)
    boardenv = source/'arch/arm/boards/kindle-mx50/defaultenv-kindle-mx50'
    shutil.rmtree(boardenv)
    shutil.copytree(P/'defaultenv-v9', boardenv)
    build = out/'build'
    build.mkdir()
    shutil.copyfile(args.config, build/'.config')
    env = dict(os.environ, KBUILD_BUILD_TIMESTAMP='Fri Oct 2 20:48:05 CST 2026', KBUILD_BUILD_VERSION='1')
    cmd = ['make', '-C', str(source), 'O='+str(build), 'ARCH=arm',
           'CROSS_COMPILE='+os.environ.get('CROSS_COMPILE', 'arm-linux-gnueabihf-')]
    subprocess.run(cmd+['olddefconfig'], check=True, env=env)
    subprocess.run(cmd+['-j'+str(args.jobs)], check=True, env=env)
    subprocess.run([sys.executable, str(P/'build-plugin.py'),
                    str(build/'images/barebox-kindle-d01100.img'), str(out/'plugin')], check=True)
    print('Image: '+str(out/'plugin/barebox-boot1-plugin-candidate.img'))

if __name__ == '__main__':
    main()
