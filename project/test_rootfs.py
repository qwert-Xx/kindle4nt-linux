# SPDX-License-Identifier: GPL-2.0-or-later
import gzip,json,pathlib,tempfile,unittest
import rootfs
class RootRecipe(unittest.TestCase):
 def test_unsafe_names(self):
  for s in ('/etc/passwd','../secret','a/../b','a//b','a/./b','a\x00b',''):
   with self.assertRaises(ValueError):rootfs.name(s)
 def test_duplicate_and_changed_payload(self):
  with tempfile.TemporaryDirectory() as td:
   p=pathlib.Path(td);f=p/'payload';f.write_bytes(b'content')
   import hashlib
   e={'name':'init','kind':'file','mode':0o755,'source':'payload','sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
   q=p/'recipe';q.write_text(json.dumps({'entries':[e,e]}))
   with self.assertRaises(ValueError):rootfs.load(q)
   q.write_text(json.dumps({'entries':[e]}));f.write_bytes(b'changed')
   with self.assertRaises(ValueError):rootfs.load(q)
 def test_default_bootmark_is_stub_and_deterministic(self):
  with tempfile.TemporaryDirectory() as td:
   p=pathlib.Path(td)/'bootmark';p.write_bytes(b'RAW_RAM_DIAGNOSTIC')
   d={'entries':[{'name':'bin/k4-bootmark','kind':'file','mode':0o755,'resolved':str(p)}]}
   a=rootfs.archive(d);self.assertEqual(a,rootfs.archive(d))
   self.assertNotIn(b'RAW_RAM_DIAGNOSTIC',gzip.decompress(a))
   d['automatic_diagnostics']=True;self.assertIn(b'RAW_RAM_DIAGNOSTIC',gzip.decompress(rootfs.archive(d)))
if __name__=='__main__':unittest.main()
