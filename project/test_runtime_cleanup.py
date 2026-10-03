#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Check the editable startup files, rather than the removed rewrite function."""
import pathlib, subprocess, unittest
import rootfs_sources
class RuntimeTests(unittest.TestCase):
    def test_startup_without_guard(self):
        for layer in ('busybox/maintenance','alpine','alpine-ram'):
            for name,source in rootfs_sources.files(layer).items():
                if name not in ('init','etc/init.d/rcS','etc/init.d/rcS.k4-base','etc/init.d/rcShutdown','etc/inittab','etc/k4/platform-start'):
                    continue
                data=source.read_bytes()
                for bad in (b'watchdog-probe',b'watchdog-guard',b'blockdev --setro',b'blockdev --setrw',b'ram_shutdown_timeout_ms',b'ram_shutdown_stall_ms'):
                    self.assertNotIn(bad,data,(layer,name))
                if data.startswith(b'#!'):
                    subprocess.run(['sh','-n'],input=data,check=True)
        rc=(rootfs_sources.ROOT/'busybox/maintenance/etc/init.d/rcS').read_bytes()
        self.assertIn(b'watchdog -T 30 -t 10',rc)
        self.assertIn(b'dropbearkey',rc)
        self.assertIn(b'echo ready > /run/k4-boot-ready',rc)
        self.assertNotIn(b'K4_ACCESSORY_CONTROLLER_LOAD_FAILED\n        exit 1',rc)
if __name__=='__main__':unittest.main()
