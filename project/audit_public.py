#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Audit tracked working files; optionally report retained Git history separately.

In a full Linux checkout, unchanged v6.6.157 upstream files are outside the
project audit. The exported patch tree has no such exclusion. Findings contain
locations and categories, never matched credential values.
"""
import argparse
import hashlib
import json
import pathlib
import re
import subprocess

PATTERNS = {
    'private-key': rb'-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY-----',
    'home-path': rb'(?i)(?:/(?:home|Users)/[a-z0-9_][a-z0-9_.-]*(?:/|\b)|\\+home\\+[a-z0-9_][a-z0-9_.-]*(?:\\|\b))',
    'mounted-drive-path': rb'(?i)/mnt/[a-z]/',
    'windows-drive-path': rb'(?<![a-zA-Z0-9_%])[A-Z]:[\\/]',
    'wsl-unc-path': rb'(?i)(?:\\{2,}|//)wsl[.]localhost(?:\\|/)',
    'private-ipv4': rb'(?<![\w.])(?:10[.]\d{1,3}[.]\d{1,3}[.]\d{1,3}|172[.](?:1[6-9]|2\d|3[01])[.]\d{1,3}[.]\d{1,3}|192[.]168[.]\d{1,3}[.]\d{1,3})(?![\w.])',
    'credential-value': rb'(?im)^\+?\s*(?:ssid|psk|password|secret|serial_number)\s*=\s*(?:"([^"\r\n]*)"|\x27([^\x27\r\n]*)\x27|([^\s#\r\n]+))',
}
MAC_PATTERN = rb'(?i)(?<![a-z0-9])(?:[0-9a-f]{2}:){5}[0-9a-f]{2}(?![a-z0-9])'
PRIVATE_SUFFIXES = {'.wbf', '.wrf', '.pem', '.cpio', '.img', '.pyc', '.pyo', '.bin', '.ko', '.dtb', '.gz'}


def scan(data, path, oid=None):
    findings = []
    for category, pattern in PATTERNS.items():
        for match in re.finditer(pattern, data):
            if category == 'private-ipv4' and any(int(n) > 255 for n in match[0].split(b'.')):
                continue
            if category == 'credential-value':
                value = next(v for v in match.groups() if v is not None)
                # Empty fields and explicit variable/placeholder examples carry no value.
                if not value or value.startswith((b'$', b'<')):
                    continue
            row = {'path': path, 'line': data[:match.start()].count(b'\n') + 1, 'category': category}
            if oid is not None:
                row['oid'] = oid
            findings.append(row)
    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repo', type=pathlib.Path)
    parser.add_argument('--out', required=True, type=pathlib.Path)
    parser.add_argument('--history', action='store_true', help='also report every reachable historical blob; does not gate the current tree')
    args = parser.parse_args()
    repo = args.repo.resolve()

    def git(*words):
        return subprocess.check_output(['git', '-C', str(repo), *words])

    tracked = git('ls-files', '-z').decode().split('\0')[:-1]
    upstream = subprocess.run(['git', '-C', str(repo), 'rev-parse', '--verify', 'v6.6.157^{tree}'], capture_output=True)
    excluded = []
    if upstream.returncode == 0 and (repo/'arch').is_dir():
        changed = set(git('diff', '--name-only', 'v6.6.157', '--').decode().splitlines())
        excluded = [name for name in tracked if name not in changed]
        tracked = [name for name in tracked if name in changed]
    findings, binary, missing, manifest, mac = [], [], [], {}, []
    for name in tracked:
        path = repo/name
        if not path.exists() or path.is_symlink():
            continue
        data = path.read_bytes()
        # Some historical console captures were written by Windows PowerShell.
        text = data.decode('utf-16').encode('utf-8') if data.startswith((b'\xff\xfe', b'\xfe\xff')) else data
        try:
            text.decode('utf-8')
        except UnicodeError:
            text = b''  # compressed images are checked by type, not regex on random bytes
        findings.extend(scan(text, name))
        mac.extend({'path': name, 'line': text[:m.start()].count(b'\n') + 1, 'category': 'mac'} for m in re.finditer(MAC_PATTERN, text))
        manifest[name] = {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
        if data.startswith((b'\x7fELF', b'\x1f\x8b', b'070701')) or path.suffix.lower() in PRIVATE_SUFFIXES:
            binary.append(name)
        if path.suffix in ('.py', '.sh', '.c', '.h', '.S', '.md'):
            if b'SPDX-License-Identifier:' not in data[:2048] and not pathlib.Path(str(path)+'.license').exists():
                missing.append(name)
    historical = []
    if args.history:
        objects = git('rev-list', '--objects', '--all').decode().splitlines()
        # A single batch subprocess avoids a process per object.
        batch = subprocess.run(['git', '-C', str(repo), 'cat-file', '--batch'], input=''.join(line.split(' ', 1)[0]+'\n' for line in objects).encode(), capture_output=True, check=True).stdout
        offset = 0
        for line in objects:
            end = batch.index(b'\n', offset)
            oid, kind, size = batch[offset:end].split()
            size = int(size); data = batch[end+1:end+1+size]; offset = end+size+2
            if kind == b'blob':
                path = line.split(' ', 1)[1] if ' ' in line else ''
                historical.extend(scan(data, path, oid.decode()))
    report = {'scope': 'tracked working tree; unchanged upstream Linux excluded',
              'checked_files': len(manifest), 'upstream_unchanged_files': len(excluded),
              'upstream_exclusions': excluded, 'manifest': manifest, 'findings': findings,
              'binary_or_private_extension': binary, 'missing_spdx_selected_files': missing,
              'history_findings': historical, 'history_checked': args.history,
              'manual_license_review_required': True, 'mac_findings_for_manual_review': mac}
    args.out.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('manifest', 'upstream_exclusions', 'history_findings', 'mac_findings_for_manual_review')}, indent=2))
    if args.history:
        print('HISTORY_FINDINGS', len(historical), '(retained history; see report)')
    return bool(findings or binary)


if __name__ == '__main__':
    raise SystemExit(main())
