# SPDX-License-Identifier: GPL-2.0-or-later
"""Project-owned target files, laid out under rootfs by installation path."""
import pathlib, shutil, stat
ROOT = pathlib.Path(__file__).resolve().parents[1] / 'rootfs'

DIAGNOSTIC_TOOLS = {'k4-dual-rtc', 'k4-network-stream', 'k4-pmic-rtc-alarm', 'k4-watchdog-guard'}

def diagnostic(name):
    tool = pathlib.PurePosixPath(name).name
    return tool.endswith('-probe') or tool in DIAGNOSTIC_TOOLS

def files(*layers):
    result = {}
    for layer in layers:
        for source in sorted((ROOT / layer).rglob('*')):
            if (source.is_file() or source.is_symlink()) and not source.name.endswith('.license'):
                result[source.relative_to(ROOT / layer).as_posix()] = source
    return result

def entries(*layers):
    result = {}
    for name, source in files(*layers).items():
        if source.is_symlink():
            result[name] = {'name': name, 'kind': 'link', 'mode': 0o777,
                            'target': source.readlink().as_posix()}
        else:
            result[name] = {'name': name, 'kind': 'file',
                            'mode': stat.S_IMODE(source.stat().st_mode), 'resolved': str(source)}
    return result

def copy(root, *layers, exclude=()):
    copied = []
    for name, source in files(*layers).items():
        if name in exclude:
            continue
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_symlink():
            target.unlink()
        if source.is_symlink():
            if target.exists():
                target.unlink()
            target.symlink_to(source.readlink())
        else:
            shutil.copyfile(source, target)
            target.chmod(stat.S_IMODE(source.stat().st_mode))
        copied.append(name)
    return copied
