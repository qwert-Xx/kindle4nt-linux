#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Safety control-flow review of copied OCRAM assembly; not ARM execution."""
from pathlib import Path
import unittest
s=Path(__file__).with_name('zqcal-sram.S').read_text()
class ControlFlow(unittest.TestCase):
 def test_no_edge_returns_without_apply(self):
  section=s.split('.Lno_edge:')[1].split('.Lapply:')[0]
  self.assertIn('b .Lrestore_zq',section)
 def test_load_calls_only_explicit_and_rollback(self):
  self.assertEqual(s.count('bl k4_zq_load_pair'),2)
  self.assertIn('ldr r0, [r12, #56]\n cmp r0, #1\n beq .Lapply',s)
  search=s.split('.Lpu:')[1].split('.Lapply:')[0]
  self.assertNotIn('bl k4_zq_load_pair',search)
 def test_no_c_return_before_rollback(self):
  self.assertIn('cmp r0, #1\n bne .Lrestore_cpu',s.split('.Lrestore:')[1])
  self.assertIn('mov r0, #3\n str r0, [r12, #84]\n b .Lexit',s)
  self.assertNotIn('pop ',s.split('.Ltest_candidate:')[1].split('.Lrestore_cpu:')[0])
 def test_park_does_not_feed(self):
  park=s.split('.Lpark:')[1].split('k4_zq_load_pair:')[0]
  self.assertNotIn('strh',park)
  self.assertNotIn('bl .Lfeed',park)
 def test_default_restores_without_loading(self):
  restore=s.split('.Lrestore_zq:')[1].split('.Lentry_fail:')[0]
  self.assertNotIn('bl k4_zq_load_pair',restore)
  self.assertIn('b .Lexit',restore)
if __name__=='__main__':unittest.main()
