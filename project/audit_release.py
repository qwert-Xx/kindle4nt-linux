#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Audit all refs, commit identities, LF and current REUSE sidecar coverage."""
import argparse, hashlib, json, pathlib, re, subprocess
def audit(repo):
 repo=pathlib.Path(repo)
 def git(*args):return subprocess.check_output(['git','-C',str(repo),*args])
 files=git('ls-files').decode().splitlines();missing=[];license_missing=[];copyright_missing=[]
 for name in files:
  if name.startswith('LICENSES/') or name.endswith('.license'):continue
  p=repo/name;side=repo/(name+'.license');data=(side.read_bytes() if side.exists() else b'')+p.read_bytes()[:2048]
  if b'SPDX-License-Identifier:' not in data:missing.append(name)
  if b'SPDX-FileCopyrightText:' not in data:copyright_missing.append(name)
  for expression in re.findall(rb'(?m)^[ +]*(?:[/\*#]+[ ]*|<!--[ ]*)?SPDX-License-Identifier:[ ]*([^\r\n*]+)',data):
   expression=expression.decode().removesuffix('-->').strip()
   for token in re.findall(r'[A-Za-z0-9.+-]+',expression):
    if token in ('AND','OR','WITH'):continue
    if not any((repo/'LICENSES'/(token+suffix)).exists() for suffix in ('.txt','')):license_missing.append({'file':name,'license':token})
 patterns={'private_key':rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----','local_path':rb'(?:/home/(?!user(?:/|\b)|example(?:/|\b))[^\s/\"\']+|[CD]:\\(?:Users|MyWork)\\[^\s\"\']+)','mac':rb'(?i)(?<![a-z0-9])(?:[0-9a-f]{2}:){5}[0-9a-f]{2}(?![a-z0-9])','credential':rb'(?im)^\+?\s*(?:ssid|psk|password|secret|serial_number)\s*=\s*[\"\'][^\"\'\n]{2,}[\"\']'}
 findings=[];crlf=[];binaries=[];count=0
 for entry in git('rev-list','--objects','--all').decode().splitlines():
  oid,*names=entry.split(' ',1);name=names[0] if names else '';kind=git('cat-file','-t',oid).strip()
  if kind==b'blob':
   count+=1;data=git('cat-file','blob',oid)
   if b'\r\n' in data:crlf.append({'oid':oid,'file':name})
   if data.startswith((b'\x7fELF',b'\x1f\x8b',b'070701')) or pathlib.Path(name).suffix.lower() in ('.img','.ko','.dtb','.apk','.tar','.gz','.xz','.bz2','.wbf','.wrf','.bin','.pyc'):binaries.append({'oid':oid,'file':name})
  elif kind in (b'commit',b'tag'):data=git('cat-file',kind.decode(),oid)
  else:continue
  for category,pattern in patterns.items():
   for m in re.finditer(pattern,data):
    finding={'oid':oid,'file':name,'object_type':kind.decode(),'category':category,'line':data[:m.start()].count(b'\n')+1}
    findings.append(finding)
 authors=git('log','--all','--format=%an <%ae>%n%cn <%ce>').decode().splitlines()
 expected='qwert-Xx <128706845+qwert-Xx@users.noreply.github.com>'
 bad=sorted(set(x for x in authors if x!=expected))
 refs=git('for-each-ref','--format=%(refname)').decode().splitlines()
 return dict(refs=refs,remotes=git('remote').decode().splitlines(),reachable_blobs=count,findings=findings,crlf=crlf,binary_or_private_files=binaries,missing_spdx=missing,missing_copyright=copyright_missing,missing_license_texts=license_missing,unexpected_identities=bad,manual_copyright_review_required=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('repo');p.add_argument('--out',required=True);a=p.parse_args();d=audit(a.repo);pathlib.Path(a.out).write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d,indent=2))
