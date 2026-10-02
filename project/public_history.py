#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Make standalone local draft history; no remote, no research refs."""
import argparse,pathlib,subprocess,json,hashlib,os
p=argparse.ArgumentParser();p.add_argument('export');a=p.parse_args();r=pathlib.Path(a.export).resolve()
if (r/'.git').exists():raise ValueError('requires unversioned export')
def git(*args):return subprocess.check_output(['git','-C',str(r),*args],text=True).strip()
git('init','-b','draft/public');git('config','user.name','codex');git('config','user.email','codex@localhost')
series=(r/'kernel/patches/series').read_text().splitlines()
for name in series:
 git('add','-f','kernel/patches/'+name);git('commit','-m','kernel: '+pathlib.Path(name).stem)
git('add','-f','kernel/patches/series','kernel/debug-patches');git('commit','-m','kernel: separate explicit debug series')
git('add','-A');git('commit','-m','project: build recipes documentation and diagnostic barebox overlay')
print(json.dumps({'branch':git('branch','--show-current'),'head':git('rev-parse','HEAD'),'refs':git('for-each-ref','--format=%(refname)').splitlines(),'remotes':git('remote')},indent=2))
