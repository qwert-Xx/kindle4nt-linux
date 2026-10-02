# SPDX-License-Identifier: GPL-2.0-or-later
import gzip,hashlib,json,pathlib,tarfile,tempfile,unittest
import emmc_root
class PersistentRoot(unittest.TestCase):
 def test_real_recipe_conversion_and_reproducibility(self):
  # Supplied local recipe is optional; fixtures exercise the same conversion.
  with tempfile.TemporaryDirectory() as td:
   p=pathlib.Path(td);(p/'out').mkdir();(p/'modules').mkdir()
   payload={'etc/init.d/rcS':'#!/bin/busybox sh\nPATH=/bin\nmount_one tmpfs tmpfs /run\nroot_device=old\n/bin/k4-watchdog-probe 900\n# Resolve SPI module aliases\n/bin/k4-charge-policy start\n','etc/inittab':'::sysinit:/etc/init.d/rcS\n::respawn:/bin/k4-userspace-service wifi\n::respawn:/bin/k4-watchdog-guard heartbeat\n','bin/k4-bootmark':'diagnostic','bin/k4-userspace-service':'service','bin/k4-watchdog-guard':'finite'}
   entries=[]
   for i,(n,text) in enumerate(payload.items()):
    src=p/str(i);src.write_text(text);entries.append({'name':n,'kind':'file','mode':0o755,'source':str(src),'sha256':hashlib.sha256(src.read_bytes()).hexdigest()})
   mod=p/'modules/lib/modules/test/kernel/example.ko';mod.parent.mkdir(parents=True);mod.write_bytes(b'module')
   entries.append({'name':'lib/modules/old/kernel/example.ko','kind':'file','mode':0o600,'source':str(mod),'sha256':hashlib.sha256(mod.read_bytes()).hexdigest()})
   entries += [{'name':'sbin/init','kind':'link','mode':0o777,'target':'../bin/busybox'},{'name':'dev/console','kind':'char','mode':0o600,'major':5,'minor':1}]
   fs=p/'fs.json';fs.write_text(json.dumps({'entries':entries}));outer=p/'recipe.json';outer.write_text(json.dumps({'entries':[],'filesystem_recipe':'fs.json','filesystem_recipe_sha256':hashlib.sha256(fs.read_bytes()).hexdigest()}))
   kernel=p/'kernel';kernel.write_bytes(b'zImage');dtb=p/'dtb';dtb.write_bytes(b'dtb')
   emmc_root.build(outer,p/'out',p/'modules','test',kernel,dtb);first=(p/'out/rootfs.tar.gz').read_bytes()
   emmc_root.build(outer,p/'out',p/'modules','test',kernel,dtb);self.assertEqual(first,(p/'out/rootfs.tar.gz').read_bytes())
   with tarfile.open(p/'out/rootfs.tar.gz') as tar:
    members={t.name:t for t in tar};self.assertNotIn('bin/k4-watchdog-guard',members)
    self.assertTrue(all(t.uid==t.gid==t.mtime==0 for t in members.values()))
    rc=tar.extractfile('etc/init.d/rcS.k4-base').read();self.assertIn(b'watchdog -T 30 -t 10',rc);self.assertNotIn(b'root_device=',rc)
    self.assertNotIn(b'guard',tar.extractfile('etc/inittab').read());self.assertEqual(tar.extractfile('boot/zImage').read(),b'zImage')
    self.assertEqual(members['lib/modules/test/kernel/example.ko'].mode,0o600)
    self.assertEqual(tar.extractfile('boot/imx50-kindle-k4.dtb').read(),b'dtb');self.assertNotIn('boot/k4.dtb',members)
    self.assertTrue(members['dev/console'].ischr());self.assertTrue(members['sbin/init'].issym())
    self.assertEqual(tar.extractfile('bin/k4-userspace-service').read(),b'service')
if __name__=='__main__':unittest.main()
