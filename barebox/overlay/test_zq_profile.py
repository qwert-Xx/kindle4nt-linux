# SPDX-License-Identifier: GPL-2.0-or-later
# Run in the overlay directory with existing Python stdlib, no packages.
import struct, unittest
import zq_profile as z

def header():
    return "# preamble\nwm 32 0x53fd4078 0xffffffff\n" + "".join(
        f"wm 32 0x{a:x} 0x{v:x}\n" for a,v in zip(z.ADDRESSES,z.UPSTREAM)) + "wm 32 0x14000000 0x101\n"

def fragment(pu=8,pd=4):
    return "".join(f"wm 32 0x{a:x} 0x{v:x}\n" for a,v in z.expected(pu,pd))

def image():
    data=bytearray(0x500)
    data[0x400:0x404]=b"\xd1\x00\x20\x40"
    struct.pack_into('<I',data,0x40c,0x70020440)
    struct.pack_into('<I',data,0x414,0x70020400)
    pairs=z.expected(8,4)
    payload=b"".join(struct.pack('>II',a,v) for a,v in pairs)
    command=b"\xcc"+(len(payload)+4).to_bytes(2,'big')+b"\x04"+payload
    dcd=b"\xd2"+(len(command)+4).to_bytes(2,'big')+b"\x40"+command
    data[0x440:0x440+len(dcd)]=dcd
    return data

class ProfileTests(unittest.TestCase):
    def test_other_writes_preserved(self):
        result,pu,pd=z.apply(header(),fragment())
        self.assertEqual((pu,pd),(8,4))
        self.assertTrue(result.startswith('# preamble\nwm 32 0x53fd4078 0xffffffff\n'))
        self.assertTrue(result.endswith('wm 32 0x14000000 0x101\n'))
        self.assertEqual(z.parse_fragment(fragment())[0],z.expected(8,4))
    def test_no_implicit_current_machine(self):
        self.assertEqual(z.expected(23,8),list(zip(z.ADDRESSES,z.UPSTREAM)))
    def test_valid_limits(self):
        for pu,pd in [(0,0),(30,14),(8,4)]:
            self.assertEqual(z.parse_fragment(fragment(pu,pd))[1:],(pu,pd))
    def test_reject_unrelated_or_extra_write(self):
        for text in [fragment()+'wm 32 0x14000000 0x101\n',fragment().replace('0x408','0x409'),
                     fragment().replace('0x5090000','0x7090000'),fragment().replace('wm 32','wm 16',1)]:
            with self.assertRaises(ValueError):z.parse_fragment(text)
    def test_reject_overflow(self):
        for pu,pd in [(31,4),(8,15),(-1,4)]:
            with self.assertRaises(ValueError):z.expected(pu,pd)
    def test_upstream_drift_or_duplicate(self):
        for base in [header().replace('0x817','0x408'),header()+'wm 32 0x14000124 0x0\n']:
            with self.assertRaises(ValueError):z.apply(base,fragment())
    def test_binary_addresses_and_order(self):
        self.assertEqual(z.dcd_writes(image()),z.expected(8,4))
    def test_truncated_and_bad_dcd(self):
        for data in [b'',image()[:0x420],image()[:0x450]]:
            with self.assertRaises(ValueError):z.dcd_writes(data)
        for offset,value in [(0x400,0),(0x440,0),(0x444,0),(0x446,255),(0x447,2)]:
            data=image();data[offset]=value
            with self.assertRaises(ValueError):z.dcd_writes(data)
    def test_measurement_missing_bad_and_unstable(self):
        good="\n".join(f"record run {i}: PU=8 PD=4 status=0 checks=00000007" for i in range(1,17))
        self.assertEqual(z.measurement(good),(8,4))
        for text in [good.replace('run 16','run 15'),good.replace('checks=00000007','checks=00000003',1),
                     good.replace('PU=8','PU=9',1),good.replace('status=0','status=-5',1)]:
            with self.assertRaises(ValueError):z.measurement(text)

if __name__=='__main__':unittest.main()
