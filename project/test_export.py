# SPDX-License-Identifier: GPL-2.0-or-later
import export,subprocess,unittest
class ExportFold(unittest.TestCase):
 def equivalent(self,s):
  t=export.fold_debug(s);self.assertEqual(len(s.splitlines()),len(t.splitlines()))
  command=['cc','-E','-P','-x','c','-']
  a=subprocess.check_output(command,input=s.encode());b=subprocess.check_output(command,input=t.encode())
  self.assertEqual(a,b)
 def test_nested_known_and_unknown(self):
  self.equivalent('#ifdef CONFIG_K4_DIAGNOSTICS\nint debug=1;\n#ifdef OTHER\nint hidden;\n#endif\n#else\n#ifdef OTHER\nint other;\n#else\nint safe=0;\n#endif\n#endif\n')
 def test_stub_and_ifndef(self):
  self.equivalent('#ifndef CONFIG_K4_BOOT_TRACE\nint mark(void){return -1;}\n#else\nint mark(void){return 1;}\n#endif\n')
 def test_rejects_unbalanced_and_unknown_debug_elif(self):
  for s in ('#ifdef CONFIG_K4_DIAGNOSTICS\n', '#endif\n','#ifdef CONFIG_K4_DIAGNOSTICS\n#elif OTHER\n#endif\n'):
   with self.assertRaises(ValueError):export.fold_debug(s)
if __name__=='__main__':unittest.main()
