#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Regression coverage for public audit leaks and diagnostic route selection."""
import importlib.util
import pathlib
import re
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('audit_public', ROOT/'project/audit_public.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class PublicAuditTests(unittest.TestCase):
    def test_workstation_and_credentials(self):
        bs = chr(92)
        samples = {
            'mounted-drive-path': '/mnt/' + 'q/private/file',
            'windows-drive-path': 'Z:' + bs + 'private/file',
            'home-path': bs + 'home' + bs + 'alice' + bs + 'file',
            'wsl-unc-path': bs * 2 + 'wsl.' + 'localhost' + bs + 'example' + bs + 'file',
            'private-key': '-----BEGIN ' + 'PRIVATE KEY-----',
            'credential-value': 'psk=' + 'a' * 64,
        }
        for category, sample in samples.items():
            with self.subTest(category=category):
                self.assertIn(category, [row['category'] for row in audit.scan(sample.encode(), 'fixture')])
        for path in ('Z:' + '/private/file', '/home/' + 'alice/file', '/Users/' + 'alice/file'):
            self.assertTrue(audit.scan(path.encode(), 'fixture'))
        for field in ('psk="value"', "password='value'", 'psk=value'):
            self.assertTrue(audit.scan(field.encode(), 'fixture'))

    def test_address_ranges_and_placeholders(self):
        for octets in ((10, 0, 0, 1), (172, 16, 0, 1), (172, 31, 255, 254), (192, 168, 1, 1)):
            sample = '.'.join(map(str, octets)).encode()
            self.assertEqual(audit.scan(sample, 'fixture')[0]['category'], 'private-ipv4')
        for sample in (b'192.0.2.1', b'198.51.100.2', b'203.0.113.3', b'169.254.212.2',
                       b'172.15.0.1', b'172.32.0.1', b'psk=""', b'psk=<PSK>', b'psk="$PSK"'):
            self.assertEqual(audit.scan(sample, 'fixture'), [])

    def test_dirty_tree_and_retained_history(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = pathlib.Path(directory)
            subprocess.run(['git', 'init', '-q', str(repo)], check=True)
            path = repo/'example.txt'
            path.write_text('psk=' + 'private-fixture-value' + '\n')
            subprocess.run(['git', '-C', str(repo), 'add', '.'], check=True)
            subprocess.run(['git', '-C', str(repo), '-c', 'user.name=Test', '-c', 'user.email=test@example.org', 'commit', '-qm', 'fixture'], check=True)
            command = ['python3', str(ROOT/'project/audit_public.py'), str(repo), '--out', str(repo/'report.json')]
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 1)
            path.write_text('psk=<PSK>\n')
            result = subprocess.run(command + ['--history'], capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            import json
            report = json.loads((repo/'report.json').read_text())
            self.assertEqual(report['findings'], [])
            self.assertTrue(report['history_findings'])

    def test_probe_routes(self):
        # Execute the exact route/ping stanza with a fake BusyBox; never access a network.
        probes = sorted((ROOT/'diagnostics').rglob('*probe'))
        checked = 0
        for path in probes:
            if not path.is_file():
                continue
            text = path.read_text()
            start = text.find('gateway=$(')
            if start == -1 or 'SKIP gateway ping: no default route' not in text:
                continue
            stanza = re.search(r'gateway=\$\(.*?^\s*fi$', text[start:], re.M | re.S)[0]
            with tempfile.TemporaryDirectory() as directory:
                fake = pathlib.Path(directory)/'bb'
                fake.write_text('#!/bin/sh\ncase "$1" in\nip) printf "%s\\n" "$ROUTE";;\nawk) shift; exec awk "$@";;\nping) printf "PING %s\\n" "$*";;\nesac\n')
                fake.chmod(0o755)
                code = 'bb='+str(fake)+'\nBB=$bb\n'+stanza
                for route, expected in (('default via 192.0.2.1 dev wlan0', 'PING'), ('', 'SKIP'), ('default dev usb0', 'SKIP')):
                    result = subprocess.run(['sh', '-c', code], env={'ROUTE': route, 'PATH': '/usr/bin:/bin'}, capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn(expected, result.stdout)
            checked += 1
        self.assertEqual(checked, 12)


if __name__ == '__main__':
    unittest.main()
