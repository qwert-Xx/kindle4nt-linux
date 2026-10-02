# SPDX-License-Identifier: GPL-2.0-or-later
import unittest,tempfile,pathlib,json,hashlib,subprocess,time
import rootfs
class Repro(unittest.TestCase):
 def test_exact_image_and_private_payload_unchanged(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=pathlib.Path(tmp);data=b'protected execution body\n';(p/'input').write_bytes(data)
   entries=[{'name':'bin','kind':'dir','mode':493},{'name':'bin/guard','kind':'file','mode':448,'source':'input','sha256':hashlib.sha256(data).hexdigest()}]
   recipe={'entries':entries,'image_bytes':16*1024*1024,'uuid':'11111111-2222-3333-4444-555555555555','reproducible_metadata':True}
   (p/'recipe').write_text(json.dumps(recipe))
   rootfs.filesystem(p/'recipe',p/'a');time.sleep(1.1);rootfs.filesystem(p/'recipe',p/'b')
   self.assertEqual(hashlib.sha256((p/'a').read_bytes()).hexdigest(),hashlib.sha256((p/'b').read_bytes()).hexdigest())
   subprocess.run(['debugfs','-R','dump /bin/guard '+str(p/'readback'),str(p/'a')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   self.assertEqual((p/'readback').read_bytes(),data)
if __name__=='__main__':unittest.main()
