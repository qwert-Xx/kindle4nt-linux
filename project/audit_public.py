#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Read every reachable public blob; report locations without secret values."""
import argparse,subprocess,pathlib,re,json,hashlib
p=argparse.ArgumentParser();p.add_argument('repo');p.add_argument('--out',required=True);a=p.parse_args();r=pathlib.Path(a.repo)
def git(*x):return subprocess.check_output(['git','-C',str(r),*x])
patterns={'private-key':rb'-----BEGIN (?:OPENSSH|RSA|EC|DSA) PRIVATE KEY-----','home-path':rb'(?:/home/(?!user(?:/|\b)|example(?:/|\b))[^\s/\"\']+|[CD]:\\(?:Users|MyWork)\\[^\s\"\']+)','mac':rb'(?i)(?<![a-z0-9])(?:[0-9a-f]{2}:){5}[0-9a-f]{2}(?![a-z0-9])','credential-value':rb'(?im)^\+?\s*(?:ssid|psk|password|secret|serial_number)\s*=\s*[\"\'][^\"\'\n]{2,}[\"\']'}
findings=[];blobs={};magic=[]
for line in git('rev-list','--objects','--all').decode().splitlines():
 parts=line.split(' ',1);oid=parts[0];path=parts[1] if len(parts)>1 else ''
 if git('cat-file','-t',oid).strip()!=b'blob':continue
 data=git('cat-file','blob',oid);blobs[oid]={'path':path,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
 for category,pattern in patterns.items():
  for m in re.finditer(pattern,data):findings.append({'oid':oid,'path':path,'line':data[:m.start()].count(b'\n')+1,'category':category})
 if data.startswith((b'\x7fELF',b'\x1f\x8b',b'070701')) or pathlib.Path(path).suffix.lower() in ('.wbf','.wrf','.pem','.cpio','.img','.pyc','.pyo','.bin','.ko','.dtb','.gz'):magic.append({'oid':oid,'path':path})
spdx_missing=[]
for line in git('ls-files').decode().splitlines():
 if pathlib.Path(line).suffix in ('.py','.sh','.c','.h','.S','.md'):
  d=(r/line).read_bytes()
  if b'SPDX-License-Identifier:' not in d[:2048]:spdx_missing.append(line)
report={'refs':git('for-each-ref','--format=%(refname)').decode().splitlines(),'remotes':git('remote').decode().splitlines(),'reachable_blobs':len(blobs),'manifest':blobs,'findings':findings,'binary_or_private_extension':magic,'missing_spdx_selected_files':spdx_missing,'manual_license_review_required':True}
pathlib.Path(a.out).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='manifest'},indent=2))