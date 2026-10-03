#!/usr/bin/env python3
import hashlib, json, struct, sys
from pathlib import Path

def parse(data):
 assert len(data) >= 4096, 'short image'
 o=0x400
 assert data[o:o+4] == bytes.fromhex('d1002040'), 'IVT header'
 entry,res,dcd,bd,selfptr,csf,res2=struct.unpack_from('<7I',data,o+4)
 assert res==res2==csf==0
 assert selfptr==0x70020400 and entry==0x70021000
 start,size,plugin=struct.unpack_from('<3I',data,bd-selfptr+o)
 assert start==0x70020000 and plugin==0
 assert len(data)<=size<=1048576 and size%4096==0
 do=dcd-start
 assert do==0x42c and data[do]==0xd2 and data[do+3]==0x40
 dl=int.from_bytes(data[do+1:do+3],'big')
 assert do+dl<=4096 and dl>=4
 d=data[do:do+dl]; i=4; writes=[]
 while i<len(d):
  tag,n,flags=d[i],int.from_bytes(d[i+1:i+3],'big'),d[i+3]
  assert n>=4 and i+n<=len(d)
  if tag==0xcc:
   assert flags==4 and (n-4)%8==0
   writes += list(struct.iter_unpack('>II',d[i+4:i+n]))
  else: assert tag==0xcf, 'unknown DCD command'
  i+=n
 assert i==len(d)
 assert not any(a in (0x14000050,0x14000054,0x14000058) for a,v in writes), 'USB baseline skips mode4 words'
 zq=[v for a,v in writes if a==0x1400012c]
 assert zq==[0x817], zq
 return dict(ivt_offset=o,entry=entry,load_address=start,declared_size=size,dcd_offset=do,dcd_size=dl,dcd_sha256=hashlib.sha256(d).hexdigest(),write_count=len(writes)),d

def require_rom_compliance(meta):
 assert meta['dcd_size']<=1024, 'RM Table 6-22 eMMC DCD limit exceeded'
 assert meta['dcd_offset']+meta['dcd_size']<=2048, 'DCD outside documented initial 2KiB image'

def audit(image,usb):
 a,ad=parse(image); b,bd=parse(usb)
 assert ad==bd, 'DCD differs from frozen USB baseline'
 a.update(emmc_rom_window_pass=(a['dcd_size']<=1024 and a['dcd_offset']+a['dcd_size']<=2048),raw_size=len(image),usb_raw_size=len(usb),usb_sha256=hashlib.sha256(usb).hexdigest(),dcd_equal=True)
 return a

if __name__=='__main__':
 image,usb=map(lambda n:Path(n).read_bytes(),sys.argv[1:3])
 result=audit(image,usb)
 padded=image+bytes(result['declared_size']-len(image))
 Path(sys.argv[3]).write_bytes(padded)
 result['padded_sha256']=hashlib.sha256(padded).hexdigest()
 print(json.dumps(result,indent=2))
