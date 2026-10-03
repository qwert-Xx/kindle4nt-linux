# SPDX-License-Identifier: GPL-2.0-or-later
"""Exercise the deployment shell in a temporary fake-device environment."""
import hashlib,io,json,pathlib,subprocess,tarfile,tempfile,unittest
SCRIPT=pathlib.Path(__file__).resolve().parent/'tools/deploy-emmc-root'
class Deploy(unittest.TestCase):
 def scenario(self,mounted=False,bad_sha=False,direct=False):
  with tempfile.TemporaryDirectory() as name:
   p=pathlib.Path(name);tools=p/'tools';tools.mkdir()
   (p/'mmcblk2p1').touch()
   (p/'mounts').write_text(str(p/'mmcblk2p1')+' / ext4 rw 0 0\n' if direct else '')
   (p/'mountinfo').write_text('1 0 0:0 / / rw - ext4 /dev/root rw\n' if mounted or direct else '')
   (tools/'mke2fs.conf').write_text('')
   (tools/'mke2fs').write_text('#!/bin/sh\necho mkfs >> "'+str(p/'events')+'"\n')
   (tools/'mke2fs').chmod(0o755)
   data=b'offline fixture\n';sums=hashlib.sha256(data).hexdigest()+'  payload\n'
   archive=p/'root.tar.gz'
   with tarfile.open(archive,'w:gz') as t:
    for n,b in [('payload',data),('etc/k4-rootfs.sha256',sums.encode())]:
     m=tarfile.TarInfo(n);m.size=len(b);t.addfile(m,io.BytesIO(b))
   fake=p/'bb'
   fake.write_text("""#!/usr/bin/python3
import sys,pathlib,subprocess,json
p=pathlib.Path(__file__).parent
args=sys.argv[1:]
with (p/'events').open('a') as f:f.write(json.dumps(args)+'\\n')
if args[0]=='mount':
 (p/'mounts').write_text(args[-2]+' '+args[-1]+' ext4 ro 0 0\\n');sys.exit(0)
if args[0]=='umount':
 (p/'mounts').write_text('');sys.exit(0)
if args[0] in ('blockdev','sync'):sys.exit(0)
sys.exit(subprocess.call(args))
""");fake.chmod(0o755)
   text=SCRIPT.read_text().replace('bb=/bin/busybox','bb='+str(fake))
   text=text.replace('/dev/mmcblk2',str(p/'mmcblk2')).replace('/sys/class/block/mmcblk2p1/start',str(p/'start')).replace('/sys/class/block/mmcblk2p1/size',str(p/'size'))
   text=text.replace('/proc/self/mountinfo',str(p/'mountinfo')).replace('/proc/mounts',str(p/'mounts')).replace('/tmp/k4-emmc-root',str(p/'mnt')).replace('[ -b "$part" ]','[ -f "$part" ]')
   shell=p/'deploy';shell.write_text(text)
   expected='0'*64 if bad_sha else hashlib.sha256(archive.read_bytes()).hexdigest()
   result=subprocess.run(['sh',str(shell),str(archive),expected,str(tools),str(p/'mmcblk2p1')],capture_output=True,text=True)
   events=(p/'events').read_text() if (p/'events').exists() else ''
   return result,events
 def test_mounted_dev_root_rejected_before_writes(self):
  r,e=self.scenario(mounted=True);self.assertNotEqual(r.returncode,0);self.assertNotIn('mkfs',e);self.assertNotIn('--setrw',e)
 def test_mounted_partition_rejected_before_writes(self):
  r,e=self.scenario(direct=True);self.assertNotEqual(r.returncode,0);self.assertNotIn('mkfs',e);self.assertNotIn('--setrw',e)
 def test_bad_archive_sha_rejected_before_writes(self):
  r,e=self.scenario(bad_sha=True);self.assertNotEqual(r.returncode,0);self.assertNotIn('mkfs',e);self.assertNotIn('--setrw',e)
 def test_format_extract_readback_without_block_locks(self):
  r,e=self.scenario();self.assertEqual(r.returncode,0,r.stdout+r.stderr);self.assertIn('mkfs',e);self.assertIn('["sync"]',e)
  self.assertIn('Partition deployment and file readback verified',r.stdout);self.assertNotIn('--setro',e);self.assertNotIn('--setrw',e)
if __name__=='__main__':unittest.main()
