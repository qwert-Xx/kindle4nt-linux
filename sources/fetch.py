#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Acquire manifest inputs or verify an offline cache; no device access."""
import argparse, hashlib, json, pathlib, subprocess, urllib.request, tarfile
HERE=pathlib.Path(__file__).resolve().parent
def manifest(): return json.loads((HERE/'manifest.json').read_text())['components']
def checked(cache,item,offline=False):
 p=pathlib.Path(cache)/item['file']
 if not p.exists():
  if offline:raise FileNotFoundError(p)
  temporary=p.with_suffix(p.suffix+'.part')
  with urllib.request.urlopen(item['url']) as source,temporary.open('wb') as dest:
   import shutil
   shutil.copyfileobj(source,dest)
  if hashlib.sha256(temporary.read_bytes()).hexdigest()!=item['sha256']:
   temporary.unlink()
   raise ValueError('SHA256 mismatch: '+item['file'])
  temporary.replace(p)
 if hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('SHA256 mismatch: '+item['file'])
 return p
def extract(cache,name,out,offline=False):
 item=next(d for d in manifest() if d['name']==name)
 p=checked(cache,item,offline);out=pathlib.Path(out);out.mkdir(parents=True)
 with tarfile.open(p) as t:t.extractall(out,filter='data')
 return next(x for x in out.iterdir() if x.is_dir())
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--cache',type=pathlib.Path,required=True);ap.add_argument('--offline',action='store_true');ap.add_argument('--name',action='append');ap.add_argument('--extract',type=pathlib.Path);a=ap.parse_args();a.cache.mkdir(parents=True,exist_ok=True)
 for d in manifest():
  if a.name and d['name'] not in a.name:continue
  p=checked(a.cache,d,a.offline)
  if d['name']=='Linux':
   sig=a.cache/'linux-6.6.157.tar.sign'
   if not sig.exists():
    if a.offline:raise FileNotFoundError(sig)
    urllib.request.urlretrieve(d['signature_url'],sig)
   keydir=a.cache/'gnupg';keydir.mkdir(mode=0o700,exist_ok=True)
   if not a.offline:subprocess.run(['gpg','--homedir',str(keydir),'--batch','--auto-key-locate','clear,wkd','--locate-keys','gregkh@kernel.org'],check=True)
   xz=subprocess.Popen(['xz','-cd',str(p)],stdout=subprocess.PIPE)
   result=subprocess.run(['gpg','--homedir',str(keydir),'--batch','--status-fd','1','--verify',str(sig),'-'],stdin=xz.stdout,stdout=subprocess.PIPE,text=True)
   xz.stdout.close();code=xz.wait()
   if code or result.returncode or 'VALIDSIG '+d['signer_fingerprint'] not in result.stdout:raise ValueError('Linux developer signature verification failed')
  if a.extract:
   with tarfile.open(p) as t:t.extractall(a.extract,filter='data')
  print(d['file']+' verified')
if __name__=='__main__':main()
