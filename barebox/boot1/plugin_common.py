#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Offline wrapper of the already built barebox PBL; no device access."""
import hashlib,json,struct,subprocess,sys,os,pwd
from pathlib import Path
from inspect_image import parse
HERE=Path(__file__).resolve().parent

def decode(d):
 rows=[]; i=4
 while i<len(d):
  tag,n,f=d[i],int.from_bytes(d[i+1:i+3],'big'),d[i+3]
  assert tag in (0xcc,0xcf)
  pairs=list(struct.iter_unpack('>II',d[i+4:i+n]))
  assert tag!=0xcf or len(pairs)==1
  rows.extend((tag,a,v,f) for a,v in pairs); i+=n
 return rows

def ivt(entry,bd,selfptr):
 return bytes.fromhex('d1002040')+struct.pack('<7I',entry,0,0,bd,selfptr,0,0)
