#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Prepare a full Alpine newc initramfs."""
import argparse,gzip,hashlib,io,json,pathlib,stat,tarfile
from build import sha
import rootfs_sources
def pack(entries):
    raw=io.BytesIO()
    for ino,(n,(mode,data,major,minor)) in enumerate(sorted(entries.items())+[('TRAILER!!!',(0,b'',0,0))],1):
        name=n.encode()+b'\0';fields=[ino,mode,0,0,2 if stat.S_ISDIR(mode) else 1,0,len(data),0,0,major,minor,len(name),0]
        raw.write(b'070701'+b''.join(('%08x'%x).encode() for x in fields));raw.write(name);raw.write(b'\0'*(-raw.tell()%4));raw.write(data);raw.write(b'\0'*(-raw.tell()%4))
    raw.write(b'\0'*(-raw.tell()%512));return raw.getvalue()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--rootfs-tar',type=pathlib.Path,required=True);ap.add_argument('--out',type=pathlib.Path,required=True);a=ap.parse_args();a.out.mkdir(mode=0o700,exist_ok=True);entries={}
    with tarfile.open(a.rootfs_tar) as t:
        for m in t.getmembers():
            data=t.extractfile(m).read() if m.isfile() else m.linkname.encode() if m.issym() else b''
            kind=stat.S_IFREG if m.isfile() else stat.S_IFDIR if m.isdir() else stat.S_IFLNK if m.issym() else stat.S_IFCHR if m.ischr() else None
            assert kind is not None,m.name;entries[m.name]=(kind|m.mode,data,m.devmajor,m.devminor)
    def put(n,data,mode=0o644):entries[n]=(stat.S_IFREG|mode,data.encode() if isinstance(data,str) else data,0,0)
    for n,p in rootfs_sources.files('alpine-ram').items():
        put(n,p.read_bytes(),stat.S_IMODE(p.stat().st_mode))
    sums=''.join(hashlib.sha256(v[1]).hexdigest()+'  '+n+'\n' for n,v in sorted(entries.items()) if stat.S_ISREG(v[0]) and n!='etc/k4-rootfs.sha256');put('etc/k4-rootfs.sha256',sums)
    for n in ('zImage','imx50-kindle-k4.dtb'):
        (a.out/n).write_bytes(entries['boot/'+n][1])
    image=pack(entries);path=a.out/'alpine-ram.cpio.gz'
    with path.open('wb') as f,gzip.GzipFile(fileobj=f,mode='wb',filename='',mtime=0) as gz:gz.write(image)
    path.chmod(0o600)
    report=dict(sha256=sha(path),bytes=path.stat().st_size,uncompressed_bytes=len(image),entries=len(entries),rootfs_tar_sha256=sha(a.rootfs_tar),emmc_mounts=False,device_executed=False)
    (a.out/'ram-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
