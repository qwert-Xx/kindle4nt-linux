#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Export production/debug patch series without research history or private inputs."""
import argparse,difflib,json,pathlib,re,shutil,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1]
GROUPS={'01-platform':['arch/arm/configs/k4_defconfig','arch/arm/mach-imx','arch/arm/include','arch/arm/kernel','arch/arm/boot/compressed','init'],
'02-clocks':['drivers/clk','drivers/pinctrl','include/dt-bindings/clock'],
'03-power':['drivers/i2c','drivers/nvmem','drivers/mfd','drivers/regulator','drivers/power','drivers/rtc','drivers/watchdog','drivers/soc','include/linux/mfd','include/linux/k4'],
'04-usb':['drivers/usb'],'05-wifi-mmc':['drivers/mmc','drivers/net/wireless/ath/ath6kl'],
'06-display-input':['drivers/video','drivers/dma','drivers/input','drivers/hwmon','drivers/leds','drivers/misc','include/linux/imx50','include/linux/k4'],
'07-device-tree':['arch/arm/boot/dts','Documentation/devicetree/bindings']}
DEBUG_CONFIGS={'CONFIG_K4_DIAGNOSTICS','CONFIG_K4_BOOT_TRACE','CONFIG_K4_PM_RAM_TRACE','CONFIG_IMX50_OCRAM_PROBE'}
DEBUG_ONLY={'drivers/soc/imx/k4-pm-trace.c','drivers/power/supply/k4-mc13892-monitor.c','arch/arm/include/asm/k4-boot-trace.h'}
def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args]).replace(b'\r\n',b'\n')
def fold_debug(text):
    """Select disabled debug branches, without placeholder padding."""
    stack=[];result=[]
    for line in text.splitlines(keepends=True):
        m=re.match(r'^\s*#\s*(ifdef|ifndef|if|else|elif|endif)\b(.*)',line)
        active=all(enabled for known,enabled in stack)
        if not m:result.append(line if active else '');continue
        op,expr=m.group(1),m.group(2).strip()
        if op in ('if','ifdef','ifndef'):
            selected=re.fullmatch(r'(?:defined|IS_ENABLED)\s*\(\s*(CONFIG_\w+)\s*\)',expr)
            config=selected.group(1) if selected else expr
            known=config in DEBUG_CONFIGS
            result.append('' if known or not active else line)
            stack.append((known,op=='ifndef' if known else True))
        elif op=='endif':
            if not stack:raise ValueError('unbalanced conditional')
            known,_=stack.pop();result.append('' if known or not all(v for _,v in stack) else line)
        elif op=='else':
            known,enabled=stack[-1];stack[-1]=(known,not enabled if known else True)
            result.append('' if known or not all(v for _,v in stack[:-1]) else line)
        else:
            if stack[-1][0]:raise ValueError('unsupported debug elif')
            result.append(line if active else '')
    if stack:raise ValueError('unclosed conditional')
    return ''.join(result)
def patch(path,old,new):
    if old==new:return ''
    return ''.join(difflib.unified_diff(old.splitlines(keepends=True),new.splitlines(keepends=True),
        fromfile='a/'+path if old else '/dev/null',tofile='b/'+path if new else '/dev/null'))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);a=ap.parse_args();out=pathlib.Path(a.out).resolve()
    if out.exists():raise ValueError('export output must be new')
    files=git('diff','--name-only','v6.6.157','--','arch','drivers','include','init','Documentation/devicetree/bindings').decode().splitlines()
    grouped={k:[] for k in GROUPS};debug=[];ccm=[]
    for path in files:
        old=subprocess.run(['git','-C',str(ROOT),'show','v6.6.157:'+path],capture_output=True).stdout.decode().replace('\r\n','\n')
        p=ROOT/path;new=(p.read_text().rstrip('\n')+'\n') if p.exists() else ''
        formal='' if '/k4-debug/' in path or '/mach-imx/debug/' in path or path in DEBUG_ONLY else (fold_debug(new) if pathlib.Path(path).suffix in ('.c','.h','.S') else new)
        if path=='arch/arm/boot/dts/nxp/imx/imx50.dtsi':
            before= formal.replace('interrupts = <71>, <72>;', 'interrupts = <0 71 0x04 0 72 0x04>;')
            ccm.append(patch(path,before,formal));formal=before
        group=next((k for k,v in GROUPS.items() if any(path.startswith(x) for x in v)),None)
        if group is None:raise ValueError('unclassified kernel path: '+path)
        grouped[group].append(patch(path,old,formal));debug.append(patch(path,new if path=="arch/arm/boot/dts/nxp/imx/imx50.dtsi" else formal,new))
    out.mkdir();(out/'kernel/patches').mkdir(parents=True);(out/'kernel/debug-patches').mkdir()
    series=[]
    for group,parts in grouped.items():
        data=''.join(parts)
        if data:(out/'kernel/patches'/(group+'.patch')).write_text(data);series.append(group+'.patch')
    if any(ccm):
        (out/'kernel/patches/08-ccm-interrupts.patch').write_text(''.join(ccm));series.append('08-ccm-interrupts.patch')
    (out/'kernel/patches/series').write_text('\n'.join(series)+'\n')
    (out/'kernel/debug-patches/01-k4-diagnostics.patch').write_text(''.join(debug))
    shutil.copyfile(ROOT/'project/debug-patches/02-k4-trace-hooks.patch',out/'kernel/debug-patches/02-k4-trace-hooks.patch')
    (out/'kernel/debug-patches/series').write_text('01-k4-diagnostics.patch\n02-k4-trace-hooks.patch\n')
    # Copy tracked inputs only, preserving target-side symlinks and modes.
    selections = ['project', 'rootfs', 'diagnostics', 'sources']
    barebox = ['build.py', 'board.patch', 'v9_defconfig', 'defaultenv-v9',
               'build-plugin.py', 'plugin_common.py', 'ocram-stock-entry.S',
               'boot-trace.c', 'maintenance.its', 'inspect_image.py']
    selections += ['porting/barebox-emmc/' + name for name in barebox]
    selections += ['porting/inspect-waveform.py', 'porting/RELEASE-DEPLOY-PUBLIC-20261003.md',
                   'porting/STOCK-CONFIG-DIFFERENCES.md',
                   'porting/PUBLIC-SOURCE-CLEANUP-20261003.md',
                   'porting/CLOCK-DEPENDENCIES-20261003.md',
                   'porting/DISPLAY-LIFECYCLE-20261003.md',
                   'porting/DRIVER-ACCEPTANCE-20261003.md',
                   'porting/FIRMWARE-EXTRACTION-VALIDATION-20261003.md',
                   'porting/ROM-BACKUP-20261003.md',
                   'porting/CLEANUP-VALIDATION-20261003.md',
                   'porting/DRIVER-LIMITS-VALIDATION-20261003.md',
                   'porting/CHARGE-SOURCE-MAPPING.md', 'porting/WIFI.md']
    for name in git('ls-files', '--', *selections).decode().splitlines():
        source = ROOT/name
        target = out/name
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_symlink():
            target.symlink_to(source.readlink())
        else:
            shutil.copy2(source, target)
    (out/'.gitignore').write_text('__pycache__/\n*.pyc\nout/\n')
    (out/'README.md').write_text(
        '<!-- SPDX-License-Identifier: CC-BY-4.0 -->\n# Kindle 4 Non-Touch Linux\n\n'
        '从 [项目入口](project/README.md)开始：先备份整机 eMMC，再构建、准备 RAM 维护并安装 boot1 与 Alpine。\n\n'
        '公开树提供源码补丁与配方，不分发固件、校准、波形、凭据或设备备份。'
        '上游版本与 SHA256 见 sources/manifest.json 及 project 的锁文件；不使用子模块。\n\n'
        '先取得 Linux v6.6.157，在独立源码目录按 kernel/patches/series 顺序应用补丁；'
        'debug 另按 kernel/debug-patches/series 应用。按构建指南执行 '
        '`make -C project images SOURCE=/path/to/linux INPUTS="$PRIVATE/inputs.json" OUT="$OUT/images"`。\n')
    (out/'LICENSES').mkdir()
    for identifier in ('GPL-2.0-only', 'GPL-2.0-or-later', 'CC-BY-4.0', 'BSD-2-Clause'):
        source = ROOT/'LICENSES'/('dual/CC-BY-4.0' if identifier == 'CC-BY-4.0' else ('preferred/BSD-2-Clause' if identifier == 'BSD-2-Clause' else 'preferred/GPL-2.0'))
        shutil.copyfile(source, out/'LICENSES'/(identifier+'.txt'))
    shutil.copyfile(ROOT/'project/THIRD-PARTY.md',out/'THIRD-PARTY.md')
    shutil.copyfile(ROOT/'project/public/LICENSE-POLICY.md',out/'LICENSE-POLICY.md')
    notices = json.loads((ROOT/'project/public/copyrights.json').read_text())
    licenses = json.loads((ROOT/'project/public/licenses.json').read_text())
    provenance = []
    (out/'REUSE.toml').write_text('version = 1\n\n[[annotations]]\npath = ["porting/barebox-emmc/defaultenv-v9/**"]\nprecedence = "aggregate"\nSPDX-FileCopyrightText = "2026 qwert-Xx"\nSPDX-License-Identifier = "GPL-2.0-or-later"\n')
    for target in sorted(out.rglob('*')):
        if not target.is_file() or target.is_symlink() or target.suffix == '.license' or target.is_relative_to(out/'LICENSES'):
            continue
        name = target.relative_to(out).as_posix()
        if name.startswith('porting/barebox-emmc/defaultenv-v9/'):
            continue  # REUSE annotations keep packed environment bytes unchanged.
        identifier = 'CC-BY-4.0' if target.suffix == '.md' else 'GPL-2.0-or-later'
        if target.suffix == '.patch': identifier = 'GPL-2.0-only'
        identifier = licenses.get(name, identifier)
        authors = ['2026 qwert-Xx'] + notices.get(name, [])
        pathlib.Path(str(target)+'.license').write_text(''.join('SPDX-FileCopyrightText: '+x+'\n' for x in authors)+'SPDX-License-Identifier: '+identifier+'\n')
        if len(authors) > 1:
            provenance.append(dict(file=name, copyright_lines=authors[1:], basis='Retained public attribution, current source headers and upstream notices', status='retained; current export awaits owner review'))
    (out/'COPYRIGHT-PROVENANCE.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n')
    (out/'COPYRIGHT-PROVENANCE.json.license').write_text('SPDX-FileCopyrightText: 2026 qwert-Xx\nSPDX-License-Identifier: CC-BY-4.0\n')
    (out/'COPYRIGHT-PROVENANCE.md').write_text('<!-- SPDX-License-Identifier: CC-BY-4.0 -->\n# Copyright provenance\n\nOriginal authors are retained in source headers and REUSE sidecars. Per-file notices are listed in COPYRIGHT-PROVENANCE.json and maintained in project/public/copyrights.json. Kernel and barebox patches retain upstream and stock-derived attribution. The boot1 plugin refers to the stock ROM interface; no stock image is distributed. Earlier owner-approved classifications remain retained where their files are exported. New source-header attribution and the current export await the owner review before pushing.\n')
    (out/'COPYRIGHT-PROVENANCE.md.license').write_text('SPDX-FileCopyrightText: 2026 qwert-Xx\nSPDX-License-Identifier: CC-BY-4.0\n')
    print('EXPORTED_WITHOUT_RESEARCH_HISTORY')
if __name__=='__main__':main()
