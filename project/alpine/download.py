#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Run on Windows when WSL networking is unavailable; download locked inputs."""
import argparse,concurrent.futures,hashlib,json,pathlib,urllib.request
HERE=pathlib.Path(__file__).resolve().parent
BASE='https://dl-cdn.alpinelinux.org/alpine/v3.24/'
QEMU='https://archive.ubuntu.com/ubuntu/pool/universe/q/qemu/qemu-user-static_8.2.2%2bds-0ubuntu1.18_amd64.deb'
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=pathlib.Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True);lock=json.loads((HERE/'packages.lock.json').read_text())
    tasks=[(d['file'],lock['repository']+d['file'],d['sha256'],'sha256') for d in lock['packages']]
    for key,subdir in [('minirootfs','releases/armv7/'),('host_apk','main/x86_64/'),('host_mini','releases/x86_64/')]:
        d=lock[key];remote='alpine-minirootfs-3.24.2-x86_64.tar.gz' if key=='host_mini' else d['file'];tasks.append((d['file'],BASE+subdir+remote,d['sha256'],'sha256'))
    tasks.extend([('APKINDEX-armv7.tar.gz',lock['repository']+'APKINDEX.tar.gz',lock['index_sha256'],'sha256'),(lock['qemu']['file'],QEMU,lock['qemu']['sha512'],'sha512')])
    def get(task):
        name,url,expected,algorithm=task;p=a.out/name
        if not p.exists():urllib.request.urlretrieve(url,p)
        actual=hashlib.new(algorithm,p.read_bytes()).hexdigest();assert actual==expected,name
        return name
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
        for name in ex.map(get,tasks):print(name+' verified',flush=True)
if __name__=='__main__':main()
