# SPDX-License-Identifier: GPL-2.0-or-later
import os,pathlib,subprocess,tempfile,unittest
import rootfs
ROOT=pathlib.Path(__file__).resolve().parents[1]/'rootfs'
COLDPLUG=ROOT/'common/bin/k4-modalias-coldplug'
STARTUP=ROOT/'busybox/coldplug/etc/init.d/rcS'
class Coldplug(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.p=pathlib.Path(self.tmp.name)
  self.bb=self.p/'bb';self.bb.write_text('#!/bin/sh\nif [ "$1" = timeout ]; then shift; shift; exec /usr/bin/timeout 0.2 "$@"; fi\nexec "$@"\n');self.bb.chmod(0o755)
  self.env=dict(os.environ,K4_COLDPLUG_BB=str(self.bb))
 def tearDown(self):self.tmp.cleanup()
 def test_generic_aliases_failure_and_bound_skip(self):
  sys=self.p/'sys';sys.mkdir();calls=self.p/'calls'
  for name,alias in [('spi','spi:kindle-panel-flash'),('keys','of:Nfiveway-keysT(null)Cgpio-keys'),('fail','platform:missing'),('bound','platform:skip'),('empty','')]:
   d=sys/name;d.mkdir();(d/'modalias').write_text(alias)
   if name=='bound':(d/'driver').mkdir()
  probe=self.p/'probe';probe.write_text('#!/bin/sh\necho "$*" >> "'+str(calls)+'"\n[ "$2" != platform:missing ]\n');probe.chmod(0o755)
  q=subprocess.run(['sh',str(COLDPLUG),str(sys),str(probe)],env=self.env,capture_output=True,text=True)
  self.assertEqual(q.returncode,0);rows=calls.read_text().splitlines();self.assertEqual(len(rows),3)
  self.assertTrue(all(x.startswith('-- ') for x in rows));self.assertNotIn('skip',calls.read_text());self.assertIn('REQUEST_FAILED',q.stdout)
 def test_startup_order_failure_and_global_timeout(self):
  base=self.p/'base';helper=self.p/'helper';order=self.p/'order'
  base.write_text('echo protected >> "'+str(order)+'"\nexit 0\n')
  helper.write_text('echo modules >> "'+str(order)+'"\nexit 9\n')
  env=dict(self.env,K4_COLDPLUG_BASE_STARTUP=str(base),K4_COLDPLUG_HELPER=str(helper),K4_COLDPLUG_LOG=str(self.p/'log'))
  q=subprocess.run(['sh',str(STARTUP)],env=env);self.assertEqual(q.returncode,0);self.assertEqual(order.read_text(),'protected\nmodules\n')
  base.write_text('exit 29\n');order.unlink();q=subprocess.run(['sh',str(STARTUP)],env=env);self.assertEqual(q.returncode,29);self.assertFalse(order.exists())
  base.write_text('exit 0\n');helper.write_text('sleep 5\n');q=subprocess.run(['sh',str(STARTUP)],env=env,timeout=2);self.assertEqual(q.returncode,0)
 def test_production_packages_diagnostic_module_without_enabling_tests(self):
  import json
  recipe=self.p/'recipe';recipe.write_text(json.dumps({
   'entries':[{'name':n,'kind':'dir','mode':0o755} for n in ('lib','lib/modules')],
   'image_bytes':16*1024*1024,'uuid':'11111111-2222-3333-4444-555555555555'}))
  modules=self.p/'modules';diagnostic=modules/'lib/modules/r/kernel/drivers/usb/usbtest.ko'
  diagnostic.parent.mkdir(parents=True);diagnostic.write_bytes(b'diagnostic module fixture')
  image=self.p/'image'
  rootfs.filesystem(recipe,image,diagnostics=False,modules=modules,release='r',formal_modules=True)
  result=subprocess.run(['debugfs','-R','cat /lib/modules/r/kernel/drivers/usb/usbtest.ko',str(image)],capture_output=True,check=True)
  self.assertEqual(result.stdout,diagnostic.read_bytes())
  self.assertFalse(rootfs.load(recipe).get('automatic_diagnostics',False))
 def test_recipe_keeps_original_startup_bytes(self):
  base=self.p/'base';base.write_bytes(b'guard; storage_ro; exit 0\n')
  entries=[{'name':'etc/init.d/rcS','kind':'file','mode':0o755,'resolved':str(base)}]
  new=rootfs.modalias_startup_entries(entries)
  self.assertEqual(entries[0]['name'],'etc/init.d/rcS');self.assertEqual(new[0]['name'],'etc/init.d/rcS.k4-base');self.assertEqual(pathlib.Path(new[0]['resolved']).read_bytes(),base.read_bytes())
  self.assertEqual(len(new),3)
  with self.assertRaises(ValueError):rootfs.modalias_startup_entries(new)
  with self.assertRaises(ValueError):rootfs.modalias_startup_entries([])
if __name__=='__main__':unittest.main()
