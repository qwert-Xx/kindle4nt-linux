#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Export production/debug patch series without research history or private inputs."""
import argparse,difflib,pathlib,re,shutil,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1]
GROUPS={'01-platform':['arch/arm/mach-imx','arch/arm/include','arch/arm/kernel','arch/arm/boot/compressed','init'],
'02-clocks':['drivers/clk','drivers/pinctrl','include/dt-bindings/clock'],
'03-power':['drivers/i2c','drivers/nvmem','drivers/mfd','drivers/regulator','drivers/power','drivers/rtc','drivers/watchdog','drivers/soc','include/linux/mfd','include/linux/k4'],
'04-usb':['drivers/usb'],'05-wifi-mmc':['drivers/mmc','drivers/net/wireless/ath/ath6kl'],
'06-display-input':['drivers/video','drivers/dma','drivers/input','drivers/hwmon','drivers/leds','drivers/misc','include/linux/imx50','include/linux/k4'],
'07-device-tree':['arch/arm/boot/dts','Documentation/devicetree/bindings']}
DEBUG_CONFIGS={'CONFIG_K4_DIAGNOSTICS','CONFIG_K4_BOOT_TRACE','CONFIG_K4_PM_RAM_TRACE','CONFIG_IMX50_OCRAM_PROBE'}
DEBUG_ONLY={'drivers/soc/imx/k4-pm-trace.c','drivers/power/supply/k4-mc13892-monitor.c','arch/arm/include/asm/k4-boot-trace.h'}
def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args]).replace(b'\r\n',b'\n')
def fold_debug(text):
    """Select disabled debug branches, preserving physical line numbers."""
    stack=[];result=[]
    for line in text.splitlines(keepends=True):
        m=re.match(r'^\s*#\s*(ifdef|ifndef|if|else|elif|endif)\b(.*)',line)
        active=all(enabled for known,enabled in stack)
        if not m:result.append(line if active else '\n');continue
        op,expr=m.group(1),m.group(2).strip()
        if op in ('if','ifdef','ifndef'):
            selected=re.fullmatch(r'(?:defined|IS_ENABLED)\s*\(\s*(CONFIG_\w+)\s*\)',expr)
            config=selected.group(1) if selected else expr
            known=config in DEBUG_CONFIGS
            result.append('\n' if known or not active else line)
            stack.append((known,op=='ifndef' if known else True))
        elif op=='endif':
            if not stack:raise ValueError('unbalanced conditional')
            known,_=stack.pop();result.append('\n' if known or not all(v for _,v in stack) else line)
        elif op=='else':
            known,enabled=stack[-1];stack[-1]=(known,not enabled if known else True)
            result.append('\n' if known or not all(v for _,v in stack[:-1]) else line)
        else:
            if stack[-1][0]:raise ValueError('unsupported debug elif')
            result.append(line if active else '\n')
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
    grouped={k:[] for k in GROUPS};debug=[]
    for path in files:
        old=subprocess.run(['git','-C',str(ROOT),'show','v6.6.157:'+path],capture_output=True).stdout.decode().replace('\r\n','\n')
        p=ROOT/path;new=(p.read_text().rstrip('\n')+'\n') if p.exists() else ''
        formal='' if '/k4-debug/' in path or '/mach-imx/debug/' in path or path in DEBUG_ONLY else (fold_debug(new) if pathlib.Path(path).suffix in ('.c','.h','.S') else new)
        group=next((k for k,v in GROUPS.items() if any(path.startswith(x) for x in v)),None)
        if group is None:raise ValueError('unclassified kernel path: '+path)
        grouped[group].append(patch(path,old,formal));debug.append(patch(path,formal,new))
    out.mkdir();(out/'kernel/patches').mkdir(parents=True);(out/'kernel/debug-patches').mkdir()
    series=[]
    for group,parts in grouped.items():
        data=''.join(parts)
        if data:(out/'kernel/patches'/(group+'.patch')).write_text(data);series.append(group+'.patch')
    (out/'kernel/patches/series').write_text('\n'.join(series)+'\n')
    (out/'kernel/debug-patches/01-k4-diagnostics.patch').write_text(''.join(debug))
    (out/'kernel/debug-patches/series').write_text('01-k4-diagnostics.patch\n')
    shutil.copytree(ROOT/'project',out/'project',ignore=shutil.ignore_patterns('__pycache__'))
    (out/'README.md').write_text('<!-- SPDX-License-Identifier: CC-BY-4.0 -->\n# Kindle 4 NT\n\nApply kernel/patches/series to a separate Linux v6.6.157 worktree. Debug additionally requires kernel/debug-patches/series. Build with make -C project images SOURCE=/path/to/linux INPUTS=/path/to/inputs.json OUT=/path/to/out. Read project/README.md. No device deployment is performed.\n')
    # A selected source overlay, not the frozen loader image or stock binaries.
    overlay=ROOT/'porting/barebox-zqcal'
    shutil.copytree(overlay,out/'barebox/overlay',ignore=shutil.ignore_patterns('__pycache__'))
    (out/'LICENSES').mkdir()
    for name,location in [('GPL-2.0','preferred'),('LGPL-2.1','preferred'),('BSD-2-Clause','preferred'),('BSD-3-Clause','preferred'),('MIT','preferred'),('CC-BY-4.0','dual')]:
        shutil.copyfile(ROOT/'LICENSES'/location/name,out/'LICENSES'/name)
    (out/'README.md').write_text('<!-- SPDX-License-Identifier: CC-BY-4.0 -->\n# Kindle 4 NT D01100\n\nLocal public-history draft, not a hardware-accepted release. Read [scope and status](project/docs/README.md), [build](project/docs/BUILD.md), [RAM recovery](project/docs/RAM-BOOT.md), [ZQ](project/docs/ZQCAL.md) and [known issues](project/docs/KNOWN-ISSUES.md). Apply kernel/patches/series to separate Linux v6.6.157 sources; debug additionally applies kernel/debug-patches/series. No device operation or deployment is automatic. Firmware/waveforms/credentials and raw evidence are excluded.\n')
    shutil.copyfile(ROOT/'project/THIRD-PARTY.md',out/'THIRD-PARTY.md')
    print('EXPORTED_WITHOUT_RESEARCH_HISTORY')
if __name__=='__main__':main()
