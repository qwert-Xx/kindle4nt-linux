#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Exercise real apk solver with tagged package and higher untagged fixture."""
import argparse,json,pathlib,shutil,subprocess,tarfile
from build import run,HERE
from package_wpa import signed,tgz

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--build',type=pathlib.Path,required=True);ap.add_argument('--official-index',type=pathlib.Path,required=True);ap.add_argument('--key',type=pathlib.Path,required=True);ap.add_argument('--out',type=pathlib.Path,required=True);a=ap.parse_args();a.out.mkdir(mode=0o700);root=a.out/'root';shutil.copytree(a.build/'rootfs',root,symlinks=True)
    with tarfile.open(a.official_index) as t:index=t.extractfile('APKINDEX').read().decode()
    blocks=[]
    for block in index.strip().split('\n\n'):
        if '\nP:wpa_supplicant\n' in '\n'+block+'\n':block=block.replace('V:2.11-r4','V:99.0-r0')
        blocks.append(block)
    repo=a.out/'untagged/armv7';repo.mkdir(parents=True)
    (repo/'APKINDEX.tar.gz').write_bytes(signed(tgz({'APKINDEX':(('\n\n'.join(blocks)+'\n\n').encode(),0o644)}),a.key,'k4-alpine.rsa.pub'))
    repos=a.out/'repositories';repos.write_text(str(repo.parent.resolve())+'\n@k4 '+str((root/'var/lib/apk/k4').resolve())+'\n')
    apk=a.build/'host/sbin/apk.static';common=[apk,'--root',root,'--arch','armv7','--keys-dir',root/'etc/apk/keys','--repositories-file',repos,'--no-network','--no-scripts','--simulate']
    tagged=run(common+['upgrade'],a.out/'tagged.log');assert '99.0-r0' not in tagged,tagged
    world=root/'etc/apk/world';world.write_text(world.read_text().replace('wpa_supplicant@k4','wpa_supplicant'))
    untagged=run(common+['upgrade'],a.out/'untagged-control.log');assert 'Upgrading wpa_supplicant' in untagged and '99.0-r0' in untagged,untagged
    # Signature/payload corruption must be rejected by actual apk.
    bad=a.out/'corrupt.apk';data=bytearray((root/'var/lib/apk/k4/armv7/wpa_supplicant-2.12-r0.apk').read_bytes());data[-12]^=1;bad.write_bytes(data)
    r=subprocess.run([str(apk),'--keys-dir',str(root/'etc/apk/keys'),'verify',str(bad)],capture_output=True,text=True);assert r.returncode!=0
    (a.out/'corrupt-rejection.log').write_text(r.stdout+r.stderr)
    report={'tagged_version':'2.12-r0','untagged_higher_fixture':'99.0-r0','tagged_keeps_k4':True,'untagged_control_upgrades':True,'corrupt_apk_rejected':True,'simulation_only':True,'device_operations':False}
    (a.out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
