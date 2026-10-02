#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Offline K4 builder. Inputs are explicit, hashed and never copied into Git."""
import argparse, hashlib, json, os, pathlib, shutil, subprocess, re
SOURCE = pathlib.Path(__file__).resolve().parents[1]
def digest(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def inputs(path):
    path = pathlib.Path(path).resolve()
    data = json.loads(path.read_text())
    if data.get('profile', 'public') == 'public' and any(k in data['inputs'] for k in ('ram_root', 'barebox')):
        raise ValueError('opaque accepted images require explicit private-replay profile')
    for name, item in data['inputs'].items():
        p = (path.parent / item['path']).resolve()
        if not p.is_file() or digest(p) != item['sha256']:
            raise ValueError('input hash mismatch: ' + name)
        item['resolved'] = str(p)
    return data

def main():
    global SOURCE
    ap = argparse.ArgumentParser()
    ap.add_argument('--inputs', required=True)
    ap.add_argument('--source', help='external Linux source directory')
    ap.add_argument('--out', required=True)
    ap.add_argument('--jobs', type=int, default=8)
    ap.add_argument('--check-only', action='store_true')
    a = ap.parse_args()
    d = inputs(a.inputs)
    if a.source: SOURCE=pathlib.Path(a.source).resolve()
    elif 'kernel_source' in d: SOURCE=(pathlib.Path(a.inputs).resolve().parent/d['kernel_source']).resolve()
    if not (SOURCE/'Makefile').is_file():raise ValueError('Linux source missing; set --source or kernel_source')
    out = pathlib.Path(a.out).resolve()
    if out == SOURCE or SOURCE in out.parents:
        raise ValueError('build output must be outside source tree')
    if a.check_only:
        print('INPUTS_OK'); return
    out.mkdir(parents=True, exist_ok=True)
    profile=d.get('kernel_profile','production')
    if profile not in ('production','debug'): raise ValueError('unknown kernel profile')
    config=d['inputs'].get('config',{}).get('resolved',str(pathlib.Path(__file__).resolve().parent/'configs'/('k4-'+profile+'.config')))
    shutil.copyfile(config, out / '.config')
    d.setdefault('release','6.6.157-k4-'+profile)
    d.setdefault('dtb','nxp/imx/imx50-kindle-k4.dtb')
    d.setdefault('metadata',{'KBUILD_BUILD_VERSION':'1','KBUILD_BUILD_TIMESTAMP':'2026-10-01 00:00:00 UTC','KBUILD_BUILD_USER':'k4','KBUILD_BUILD_HOST':'builder'})
    if not re.fullmatch(r'[A-Za-z0-9_.+-]{1,64}',d['release']):raise ValueError('invalid kernel release')
    if not re.fullmatch(r'[A-Za-z0-9_./+-]+',d.get('cross_compile','arm-linux-gnueabihf-')):raise ValueError('invalid cross compiler prefix')
    if not re.fullmatch(r'nxp/imx/(?:k4-debug/)?imx50-kindle-k4(?:-[A-Za-z0-9_-]+)?\.dtb',d['dtb']):raise ValueError('invalid K4 DTB target')
    env = dict(os.environ, **d['metadata'])
    cmd = ['make', '-C', str(SOURCE), 'O='+str(out), 'ARCH=arm',
           'CROSS_COMPILE='+d.get('cross_compile', 'arm-linux-gnueabihf-'),
           'KERNELRELEASE='+d['release']]
    subprocess.run(cmd+['olddefconfig'], env=env, check=True)
    if d.get('profile','public')!='private-replay':
        cfg=(out/'.config').read_text()
        for key in ('IMX50_OCRAM','IMX50_PM','K4_PM_HEALTH_CLOCK','POWER_RESET_K4_MC13892','CHARGER_K4_MC13892','USB_K4_PHY','IMX2_WDT'):
            if 'CONFIG_'+key+'=y\n' not in cfg:raise ValueError('required recovery builtin: '+key)
        if ('CONFIG_K4_DIAGNOSTICS=y\n' in cfg)!=(profile=='debug'):
            raise ValueError('kernel profile diagnostic selection mismatch')
    if 'baseline_metadata' in d:
        if d.get('profile') != 'private-replay':
            raise ValueError('baseline metadata override is private-replay only')
        bm = d['baseline_metadata']
        header = out / 'baseline-uts.h'
        header.write_text('#define UTS_VERSION '+json.dumps(bm['temporary_uts'])+'\n')
        subprocess.run(cmd+['usr/gen_init_cpio'], env=env, check=True)
        cpio = out / 'baseline-empty.cpio'
        with cpio.open('wb') as f:
            subprocess.run([str(out/'usr/gen_init_cpio'), '-t', str(bm['empty_cpio_epoch']),
                            str(SOURCE/'usr/default_cpio_list')], stdout=f, check=True)
        cmd += ['CFLAGS_version.o=-include '+str(header), 'cpio-data='+str(cpio)]
    subprocess.run(cmd+['-j'+str(a.jobs), 'zImage', 'modules', d['dtb']], env=env, check=True)
    artifacts = {'zImage': out/'arch/arm/boot/zImage',
                 'dtb': out/'arch/arm/boot/dts'/d['dtb']}
    if 'ram_recipe' in d['inputs']:
        import rootfs
        module_root=out/'root-modules'
        subprocess.run(cmd+['modules_install','INSTALL_MOD_PATH='+str(module_root),'INSTALL_MOD_STRIP=1'],env=env,check=True)
        rd=rootfs.load(d['inputs']['ram_recipe']['resolved'])
        if d.get('profile','public')!='private-replay' and profile=='production':
            if rd.get('automatic_diagnostics',False):raise ValueError('production root cannot auto-enable diagnostics')
            if any(e['name']=='rootfs.ext3' for e in rd['entries']) and 'filesystem_recipe' not in rd:
                raise ValueError('production ext3 requires a structured filesystem recipe')
        report_root = rootfs.build(d['inputs']['ram_recipe']['resolved'], out/'ram.cpio.gz',module_root,d['release'],modalias_coldplug=profile=='production' and 'CONFIG_KEYBOARD_GPIO=m\n' in (out/'.config').read_text(),formal_modules=profile=='production')
        artifacts['ram_recipe'] = out/'ram.cpio.gz'
    # Retain an explicitly supplied, private, accepted RAM payload byte-for-byte.
    # The builder does not unpack credentials or automatically execute diagnostics.
    for name in ('ram_root', 'barebox'):
        if name in d['inputs']:
            artifacts[name] = pathlib.Path(d['inputs'][name]['resolved'])
    report = {'artifacts': {k:digest(v) for k,v in artifacts.items()},
              'modules': (out/'modules.order').read_text().splitlines(),
              'config_sha256': digest(out/'.config'), 'device_operations': False,
              'root_recipe': report_root if 'ram_recipe' in d['inputs'] else None}
    (out/'build-report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['artifacts'], indent=2))
if __name__ == '__main__': main()
