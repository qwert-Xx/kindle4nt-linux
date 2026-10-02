# SPDX-License-Identifier: GPL-2.0-or-later
from pathlib import Path
import unittest
class Layout(unittest.TestCase):
    def test_no_rom_overlap(self):
        # ROM owns below 0xf8006000; 128 run rows plus checks end at 0x6a40.
        log_end=0xf8006000+(528+128)*4
        marker=0xf8007b00
        self.assertLessEqual(log_end,marker)
        self.assertGreaterEqual(marker,0xf8006000)
        # Private stack starts at 0x7ff0, >1KiB away from this 32-byte marker.
        self.assertLess(marker+32,0xf8007ff0-1024)
        for name in ('build.sh','early-trace.c','zqcal.c'):
            t=Path(__file__).with_name(name).read_text()
            self.assertNotIn('0xf8005fc',t)
            self.assertIn('0xf8007b00',t)
if __name__=='__main__':unittest.main()
