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
   e={'name':'bin/external','kind':'file','mode':0o755,'source':'payload','sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
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
 def test_busybox_install_preserves_tools_and_validates_paths(self):
  from unittest.mock import patch
  entries=[{'name':'bin','kind':'dir','mode':0o755},
           {'name':'bin/busybox','kind':'file','mode':0o755,'resolved':'busybox'},
           {'name':'sbin/modprobe','kind':'link','mode':0o777,'target':'/bin/busybox-modutils'}]
  with patch('pathlib.Path.read_text',return_value='/bin/cat\n/bin/uname\n/sbin/modprobe\n/usr/bin/awk\n/usr/sbin/crond\n'):
   result=rootfs.busybox_applet_entries(entries, "busybox.links")
  indexed={e['name']:e for e in result}
  self.assertEqual(indexed['bin/cat']['target'],'/bin/busybox')
  self.assertEqual(indexed['usr/sbin/crond']['kind'],'link')
  self.assertEqual(indexed['sbin/modprobe']['target'],'/bin/busybox-modutils')
  self.assertEqual(indexed['usr']['kind'],'dir')
  self.assertEqual(entries[0]['name'],'bin')
  with patch('pathlib.Path.read_text',return_value='../cat\n'):
   with self.assertRaises(ValueError):rootfs.busybox_applet_entries(entries, "busybox.links")
 def test_busybox_links_hash_and_input_tracking(self):
  import hashlib
  with tempfile.TemporaryDirectory() as td:
   p=pathlib.Path(td); links=p/'busybox.links';links.write_text('/bin/cat\n')
   recipe=p/'recipe.json';recipe.write_text(json.dumps({'entries':[], 'busybox_links':{'path':'busybox.links','sha256':hashlib.sha256(links.read_bytes()).hexdigest()}}))
   self.assertIn(links,rootfs.input_paths(recipe))
   links.write_text('/bin/uname\n')
   with self.assertRaises(ValueError):rootfs.load(recipe)
if __name__=='__main__':unittest.main()
