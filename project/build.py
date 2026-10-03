#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Offline K4 builder. Inputs are explicit, hashed and never copied into Git."""
import argparse, hashlib, json, os, pathlib, shutil, subprocess, re
from userspace.build_support import output, toolchain
SOURCE = pathlib.Path(__file__).resolve().parents[1]
def digest(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def inputs(path):
    path = pathlib.Path(path).resolve()
    data = json.loads(path.read_text())
    for name, item in data['inputs'].items():
        p = (path.parent / item['path']).resolve()
        if not p.is_file() or digest(p) != item['sha256']:
            raise ValueError('input hash mismatch: ' + name)
        item['resolved'] = str(p)
    return data

def main():
    global SOURCE
    ap = argparse.ArgumentParser()
    ap.add_argument('--inputs', help='JSON with hashed external inputs')
    ap.add_argument('--source', help='external Linux source directory')
    ap.add_argument('--out', default=os.environ.get('OUT', str(SOURCE/'out/kernel')))
    ap.add_argument('--clean', action='store_true', help='remove output before building')
    ap.add_argument('--mode', choices=('source','prebuilt'), default='source')
    ap.add_argument('--preset', choices=('production','debug','lifecycle'), help='default configuration preset')
    ap.add_argument('--config', help='configuration fragment applied after the preset')
    ap.add_argument('--jobs', type=int, default=8)
    ap.add_argument('--check-only', action='store_true')
    a = ap.parse_args()
    d = inputs(a.inputs) if a.inputs else {'inputs': {}}
    if a.source: SOURCE=pathlib.Path(a.source).resolve()
    elif 'kernel_source' in d: SOURCE=(pathlib.Path(a.inputs).resolve().parent/d['kernel_source']).resolve()
    if a.mode != 'prebuilt' and not (SOURCE/'Makefile').is_file():raise ValueError('Linux source missing; set --source or kernel_source')
    out = pathlib.Path(a.out).resolve()
    if out == SOURCE or out in SOURCE.parents:
        raise ValueError('output overlaps source')
    if a.check_only:
        print('INPUTS_OK'); return
    supplied = [item['resolved'] for item in d['inputs'].values()]
    if a.config: supplied.append(a.config)
    if 'ram_recipe' in d['inputs']:
        import rootfs
        supplied += rootfs.input_paths(d['inputs']['ram_recipe']['resolved'])
    supplied += [pathlib.Path(__file__).resolve().parent, SOURCE/'Makefile']
    if out.is_relative_to(SOURCE):
        tracked=subprocess.run(['git','-C',str(SOURCE),'ls-files','-z','--',str(out.relative_to(SOURCE))],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
        supplied += [SOURCE/os.fsdecode(p) for p in tracked.stdout.split(b'\0') if p]
    out = output(out, supplied, a.clean)
    profile=a.preset or d.get('kernel_profile','production')
    if profile not in ('production','debug','lifecycle'): raise ValueError('unknown kernel profile')
    config=d['inputs'].get('config',{}).get('resolved',str(pathlib.Path(__file__).resolve().parent/'configs'/('k4-'+profile+'.config')))
    d.setdefault('release','6.6.157-k4-'+profile)
    d.setdefault('dtb','nxp/imx/imx50-kindle-k4.dtb')
    d.setdefault('metadata',{})
    if not re.fullmatch(r'[A-Za-z0-9_.+-]{1,64}',d['release']):raise ValueError('invalid kernel release')
    dt_source=SOURCE/'arch/arm/boot/dts'/pathlib.Path(d['dtb']).with_suffix('.dts')
    if a.mode != 'prebuilt' and not dt_source.is_file():raise ValueError('DTB source missing: '+str(dt_source))
    env = dict(os.environ, **d['metadata'])
    cmd = ['make', '-C', str(SOURCE), 'O='+str(out), 'ARCH=arm',
           'CROSS_COMPILE='+d.get('cross_compile', 'arm-linux-gnueabihf-'),
           'KERNELRELEASE='+d['release']]
    if a.mode == 'prebuilt':
        artifacts = {name: pathlib.Path(d['inputs'][name]['resolved']) for name in ('zImage','dtb')}
        module_root=out/'root-modules'
        if module_root.exists():shutil.rmtree(module_root)
        with __import__('tarfile').open(d['inputs']['modules']['resolved']) as archive:
            archive.extractall(module_root, filter='data')
    else:
        toolchain(d.get('cross_compile','arm-linux-gnueabihf-'))
        if not (out/'.config').exists() or a.clean:
            subprocess.run(cmd+['k4_defconfig'],env=env,check=True)
            subprocess.run(['bash',str(SOURCE/'scripts/kconfig/merge_config.sh'),'-m','-O',str(out),str(out/'.config'),config],env=env,check=True)
        elif 'config' in d['inputs'] or a.preset:
            subprocess.run(['bash',str(SOURCE/'scripts/kconfig/merge_config.sh'),'-m','-O',str(out),str(out/'.config'),config],env=env,check=True)
        if a.config:
            subprocess.run(['bash',str(SOURCE/'scripts/kconfig/merge_config.sh'),'-m','-O',str(out),str(out/'.config'),a.config],env=env,check=True)
        subprocess.run(cmd+['olddefconfig'],env=env,check=True)
        cfg=(out/'.config').read_text()
        # Direct MMC/ext4 root and the early userspace watchdog must work
        # before coldplug can load any modules. Charging and PM are optional.
        required=('IMX2_WDT','DEVTMPFS','DEVTMPFS_MOUNT','EXT4_FS','MMC','MMC_BLOCK','MMC_SDHCI','MMC_SDHCI_PLTFM','MMC_SDHCI_ESDHC_IMX')
        for key in required:
            if 'CONFIG_'+key+'=y\n' not in cfg:raise ValueError('boot path requires builtin: '+key)
        subprocess.run(cmd+['-j'+str(a.jobs),'zImage','modules',d['dtb']],env=env,check=True)
        artifacts={'zImage':out/'arch/arm/boot/zImage','dtb':out/'arch/arm/boot/dts'/d['dtb']}
        module_root=out/'root-modules'
        if module_root.exists():shutil.rmtree(module_root)
        subprocess.run(cmd+['modules_install','INSTALL_MOD_PATH='+str(module_root),'INSTALL_MOD_STRIP=1'],env=env,check=True)
    if a.mode == 'prebuilt':
        import importlib.util
        spec=importlib.util.spec_from_file_location('alpine_builder',pathlib.Path(__file__).parent/'alpine/build.py')
        alpine=importlib.util.module_from_spec(spec);spec.loader.exec_module(alpine)
        d['release']=alpine.kernel_release(artifacts['zImage'])
        alpine.compatible_modules(artifacts['zImage'],module_root/'lib/modules'/d['release'])
    if 'ram_recipe' in d['inputs']:
        import rootfs
        rd=rootfs.load(d['inputs']['ram_recipe']['resolved'])
        if profile!='debug':
            if rd.get('automatic_diagnostics',False):raise ValueError('production root cannot auto-enable diagnostics')
            if any(e['name']=='rootfs.ext3' for e in rd['entries']) and 'filesystem_recipe' not in rd:
                raise ValueError('production ext3 requires a structured filesystem recipe')
        report_root = rootfs.build(d['inputs']['ram_recipe']['resolved'], out/'ram.cpio.gz',module_root,d['release'],modalias_coldplug=profile in ('production','lifecycle') and (a.mode=='prebuilt' or 'CONFIG_KEYBOARD_GPIO=m\n' in (out/'.config').read_text()),formal_modules=profile!='debug')
        artifacts['ram_recipe'] = out/'ram.cpio.gz'
    # Retain explicitly supplied precompiled inputs byte-for-byte.
    # The builder does not unpack credentials or automatically execute diagnostics.
    for name in ('ram_root', 'barebox'):
        if name in d['inputs']:
            artifacts[name] = pathlib.Path(d['inputs'][name]['resolved'])
    report = {'mode':a.mode,'kernel_release':d['release'],'artifacts': {k:digest(v) for k,v in artifacts.items()},
              'modules': sorted(str(p.relative_to(module_root)) for p in module_root.rglob('*.ko')),
              'config_sha256': digest(out/'.config') if (out/'.config').exists() else None, 'device_operations': False,
              'root_recipe': report_root if 'ram_recipe' in d['inputs'] else None}
    (out/'build-report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['artifacts'], indent=2))
if __name__ == '__main__': main()
