#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Ignore only GNU build-id payload; compare ALL remaining ELF file bytes."""
import argparse,json,pathlib,struct,hashlib

def normalized(b):
    if b[:7]!=b"\x7fELF\x01\x01\x01":raise ValueError('require little-endian ELF32')
    h=struct.unpack_from('<16sHHIIIIIHHHHHH',b);off,size,count,index=h[6],h[11],h[12],h[13]
    sections=[struct.unpack_from('<10I',b,off+i*size) for i in range(count)]
    s=sections[index];names=b[s[4]:s[4]+s[5]];result=bytearray(b);ranges=[]
    for s in sections:
        name=names[s[0]:].split(b'\0')[0]
        if name==b'.note.gnu.build-id':
            start=s[4];ns,ds,typ=struct.unpack_from('<III',b,start)
            if typ!=3 or b[start+12:start+12+ns]!=b'GNU\0':raise ValueError('unexpected build-id note')
            first=start+12+((ns+3)&~3)
            if first+ds>start+s[5]:raise ValueError('invalid note length')
            result[first:first+ds]=bytes(ds);ranges.append([first,ds])
    return bytes(result),ranges

def compare(a,b):
    na,ra=normalized(a);nb,rb=normalized(b)
    return {'byte_identical':a==b,'only_build_id_diff':a!=b and ra==rb and na==nb,
            'normalized_sha256':hashlib.sha256(na).hexdigest(),'build_id_ranges':ra,
            'differing_offsets':[i for i,(x,y) in enumerate(zip(a,b)) if x!=y][:64],
            'differing_offset_count':sum(x!=y for x,y in zip(a,b)),
            'same_length':len(a)==len(b)}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('rebuilt');p.add_argument('reference');v=p.parse_args()
    print(json.dumps(compare(pathlib.Path(v.rebuilt).read_bytes(),pathlib.Path(v.reference).read_bytes()),indent=2))
