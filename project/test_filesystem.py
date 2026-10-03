# SPDX-License-Identifier: GPL-2.0-or-later
import unittest,tempfile,pathlib,json,hashlib,subprocess
import rootfs
class Filesystem(unittest.TestCase):
 def test_private_payload_and_permissions(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=pathlib.Path(tmp);data=b'protected execution body\n';(p/'input').write_bytes(data)
   entries=[{'name':'bin','kind':'dir','mode':493},{'name':'bin/guard','kind':'file','mode':448,'source':'input','sha256':hashlib.sha256(data).hexdigest()}]
   recipe={'entries':entries,'image_bytes':16*1024*1024,'uuid':'11111111-2222-3333-4444-555555555555'}
   (p/'recipe').write_text(json.dumps(recipe))
   rootfs.filesystem(p/'recipe',p/'a')
   subprocess.run(['debugfs','-R','dump /bin/guard '+str(p/'readback'),str(p/'a')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   self.assertEqual((p/'readback').read_bytes(),data)
   info=subprocess.check_output(['debugfs','-R','stat /bin/guard',str(p/'a')],text=True,stderr=subprocess.DEVNULL)
   self.assertIn('Mode:  0700',info)
   self.assertRegex(info,r'User:\s+0\s+Group:\s+0')
if __name__=='__main__':unittest.main()
