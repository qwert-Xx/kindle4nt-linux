# SPDX-License-Identifier: GPL-2.0-or-later
import struct,unittest
from compare import compare

def elf():
    b=bytearray(256);struct.pack_into('<16sHHIIIIIHHHHHH',b,0,b"\x7fELF\x01\x01\x01"+bytes(9),2,40,1,0,0,52,0,52,0,0,40,3,1)
    names=b'\0.shstrtab\0.note.gnu.build-id\0';b[172:172+len(names)]=names
    struct.pack_into('<10I',b,92,1,3,0,0,172,len(names),0,0,1,0)
    struct.pack_into('<10I',b,132,11,7,2,0,208,36,0,0,4,0)
    struct.pack_into('<III',b,208,4,20,3);b[220:224]=b'GNU\0';return bytes(b)
class Test(unittest.TestCase):
    def test_identical(self):self.assertTrue(compare(elf(),elf())['byte_identical'])
    def test_id(self):
        a=elf();b=bytearray(a);b[224]=1;self.assertTrue(compare(a,b)['only_build_id_diff'])
    def test_code(self):
        a=elf();b=bytearray(a);b[250]=1;self.assertFalse(compare(a,b)['only_build_id_diff'])
    def test_length(self):self.assertFalse(compare(elf(),elf()+b'x')['only_build_id_diff'])
    def test_invalid(self):
        with self.assertRaises(ValueError):compare(bytes(256),bytes(256))
if __name__=='__main__':unittest.main()
