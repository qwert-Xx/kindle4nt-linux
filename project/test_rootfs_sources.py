# SPDX-License-Identifier: GPL-2.0-or-later
import gzip, hashlib, json, pathlib, subprocess, tempfile, unittest
from unittest.mock import patch
import rootfs, rootfs_sources
class Sources(unittest.TestCase):
    def test_project_file_needs_no_external_payload_and_edits_are_literal(self):
        with tempfile.TemporaryDirectory() as td:
            base=pathlib.Path(td);source=base/'common/bin/k4-charge-policy'
            source.parent.mkdir(parents=True);source.write_bytes(b'#!/bin/sh\n# literal -j -k blockdev --setro\nexit 0\n');source.chmod(0o755)
            recipe=base/'recipe.json';recipe.write_text(json.dumps({'entries':[{'name':'bin/k4-charge-policy','kind':'file','mode':0o755,'source':'absent','sha256':'old input'}]}))
            with patch.object(rootfs_sources,'ROOT',base):
                first=gzip.decompress(rootfs.archive(rootfs.load(recipe)))
                self.assertIn(source.read_bytes(),first)
                source.write_bytes(b'#!/bin/sh\necho edited\n')
                second=gzip.decompress(rootfs.archive(rootfs.load(recipe)))
                self.assertIn(source.read_bytes(),second);self.assertNotEqual(first,second)
    def test_overlay_copies_exact_bytes_and_modes(self):
        with tempfile.TemporaryDirectory() as td:
            root=pathlib.Path(td)
            names=rootfs_sources.copy(root,'alpine')
            for name,source in rootfs_sources.files('alpine').items():
                self.assertIn(name,names)
                if source.is_symlink():
                    self.assertEqual((root/name).readlink(),source.readlink())
                else:
                    self.assertEqual((root/name).read_bytes(),source.read_bytes())
                    self.assertEqual((root/name).stat().st_mode & 0o777,source.stat().st_mode & 0o777)
    def test_sources_are_lf_shell_syntax_and_contain_no_private_material(self):
        for source in rootfs_sources.ROOT.rglob('*'):
            if not source.is_file():continue
            data=source.read_bytes();self.assertNotIn(b'\r',data,str(source))
            self.assertNotIn(b'PRIVATE KEY',data,str(source));self.assertNotIn(b'psk=',data,str(source))
            self.assertFalse(source.name in ('wpa_supplicant.conf','authorized_keys','k4-hostkey'),str(source))
            if data.startswith(b'#!') and b'python' not in data.splitlines()[0]:
                subprocess.run(['sh','-n'],input=data,check=True)
if __name__=='__main__':unittest.main()
