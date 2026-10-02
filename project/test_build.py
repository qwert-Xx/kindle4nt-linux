# SPDX-License-Identifier: GPL-2.0-or-later
import importlib.util, json, pathlib, tempfile, unittest
spec=importlib.util.spec_from_file_location('builder',pathlib.Path(__file__).with_name('build.py'))
b=importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
class Inputs(unittest.TestCase):
 def test_relative_and_corruption(self):
  with tempfile.TemporaryDirectory() as td:
   p=pathlib.Path(td); (p/'data').write_bytes(b'input')
   m={'inputs':{'config':{'path':'data','sha256':b.digest(p/'data')}}}
   (p/'inputs.json').write_text(json.dumps(m))
   self.assertEqual(b.inputs(p/'inputs.json')['inputs']['config']['resolved'],str(p/'data'))
   (p/'data').write_bytes(b'changed')
   with self.assertRaises(ValueError): b.inputs(p/'inputs.json')
 def test_public_rejects_opaque_private_images(self):
  with tempfile.TemporaryDirectory() as td:
   p=pathlib.Path(td)/'inputs.json'; p.write_text('{"inputs":{"ram_root":{}}}')
   with self.assertRaises(ValueError): b.inputs(p)
 def test_missing(self):
  with tempfile.TemporaryDirectory() as td:
   p=pathlib.Path(td)/'inputs.json'; p.write_text('{"inputs":{"config":{"path":"missing","sha256":"0"}}}')
   with self.assertRaises(ValueError): b.inputs(p)
if __name__=='__main__': unittest.main()
