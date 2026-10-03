#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Package existing verified static K4 binaries as deterministic signed APK v2."""
import argparse,gzip,hashlib,io,json,pathlib,subprocess,tarfile
from build import HERE,sha,run

def tgz(entries,cut=False):
    entries=dict(entries)
    for n in list(entries):
        for parent in pathlib.PurePosixPath(n).parents:
            if str(parent)!='.':entries.setdefault(str(parent),(None,0o755))
    raw=io.BytesIO()
    with tarfile.open(fileobj=raw,mode='w',format=tarfile.PAX_FORMAT) as t:
        for n,(data,mode) in sorted(entries.items()):
            ti=tarfile.TarInfo(n);ti.uid=ti.gid=ti.mtime=0;ti.mode=mode;ti.size=len(data) if data is not None else 0
            if data is None:ti.type=tarfile.DIRTYPE;t.addfile(ti);continue
            if not n.startswith('.'):ti.pax_headers={'APK-TOOLS.checksum.SHA1':hashlib.sha1(data).hexdigest()}
            t.addfile(ti,io.BytesIO(data))
        end=t.offset
    return gzip.compress(raw.getvalue()[:end] if cut else raw.getvalue(),mtime=0)
def signed(payload,key,keyname):
    sig=subprocess.run(['openssl','dgst','-sha256','-sign',str(key)],input=payload,capture_output=True,check=True).stdout
    return tgz({'.SIGN.RSA256.'+keyname:(sig,0o644)},True)+payload

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--bin-dir',type=pathlib.Path,required=True);ap.add_argument('--copying',type=pathlib.Path,required=True);ap.add_argument('--key',type=pathlib.Path,required=True);ap.add_argument('--apk',type=pathlib.Path,required=True);ap.add_argument('--out',type=pathlib.Path,required=True);a=ap.parse_args();a.out.mkdir(mode=0o700);lock=json.loads((HERE/'wpa-static.lock.json').read_text());pub=HERE/'k4-alpine.rsa.pub';assert sha(pub)==lock['public_key_sha256']
    assert subprocess.run(['openssl','pkey','-in',str(a.key),'-pubout'],capture_output=True,check=True).stdout==pub.read_bytes()
    entries={}
    for n,expected in lock['binary_sha256'].items():
        p=a.bin_dir/n;assert sha(p)==expected,n
        header=run(['readelf','-h',p]);assert 'ELF32' in header and 'ARM' in header and 'hard-float ABI' in header
        assert 'INTERP' not in run(['readelf','-l',p])
        entries['sbin/'+n]=(p.read_bytes(),0o755)
    assert sha(a.copying)==lock['copying_sha256'];entries['usr/share/licenses/wpa_supplicant/COPYING']=(a.copying.read_bytes(),0o644)
    data=tgz(entries)
    info='pkgname = wpa_supplicant\npkgver = 2.12-r0\npkgdesc = '+lock['pkgdesc']+'\nurl = https://w1.fi/wpa_supplicant/\nbuilddate = 0\npackager = K4 local build\nsize = '+str(sum(len(d) for d,m in entries.values()))+'\narch = armv7\norigin = wpa_supplicant\nlicense = BSD-3-Clause\nprovides = cmd:wpa_supplicant=2.12-r0\nprovides = cmd:wpa_cli=2.12-r0\ndatahash = '+hashlib.sha256(data).hexdigest()+'\n'
    control=tgz({'.PKGINFO':(info.encode(),0o644)},True)
    repo=a.out/'armv7';repo.mkdir();pkg=repo/'wpa_supplicant-2.12-r0.apk';pkg.write_bytes(signed(control,a.key,pub.name)+data)
    run([a.apk,'--keys-dir',HERE,'verify',pkg],a.out/'package-signature.log')
    unsigned=a.out/'unsigned-index.tar.gz';run([a.apk,'--keys-dir',HERE,'index','-o',unsigned,pkg],a.out/'index.log')
    with tarfile.open(unsigned) as t:files={m.name:(t.extractfile(m).read(),m.mode) for m in t.getmembers() if m.isfile()}
    (repo/'APKINDEX.tar.gz').write_bytes(signed(tgz(files),a.key,pub.name))
    (a.out/'package-report.json').write_text(json.dumps(dict(version='2.12-r0',apk_sha256=sha(pkg),index_sha256=sha(repo/'APKINDEX.tar.gz'),binary_sha256=lock['binary_sha256'],public_key_sha256=sha(pub),device_operations=False),indent=2)+'\n')
    print((a.out/'package-report.json').read_text())
if __name__=='__main__':main()
