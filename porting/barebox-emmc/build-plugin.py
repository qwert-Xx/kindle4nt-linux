#!/usr/bin/env python3
"""Stock-sized i.MX50 ROM plugin; offline only."""
import hashlib,importlib.util,json,struct,subprocess,sys,os
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('legacy',HERE/'plugin_common.py')
legacy=importlib.util.module_from_spec(spec); spec.loader.exec_module(legacy)
# i.MX50 ROM plugin IVT and boot data, matching the factory ABI.
STOCK_HEADER=legacy.ivt(0xf8006004,0xf8006420,0xf8006400)+struct.pack('<3I',0xf8006000,0x800,1)
STOCK=bytes(0x400)+STOCK_HEADER
STOCK_PUSH=struct.pack('<I',0xe92d417f) # push {r0-r6,r8,lr}
def compact(rows):
 result=[]
 for op,a,v,f in rows:
  assert a&3==0
  tag=0 if op==0xcc and f==4 else {0x19:1,0x04:2,0x1c:3}[f]
  result.append((a|tag,v))
 return result
def expand(data):
 rows=[]
 for encoded,v in struct.iter_unpack('<II',data):
  tag=encoded&3
  rows.append((0xcc if tag==0 else 0xcf,encoded&~3,v,{0:4,1:0x19,2:0x04,3:0x1c}[tag]))
 return rows
def check(image,usb,raw,stock,table_offsets):
 _,d=legacy.parse(usb); rows=legacy.decode(d)
 assert image[0x400:0x42c]==stock[0x400:0x42c]
 assert image[0x42c:0x44c]==legacy.ivt(0x70021000,0x7002044c,0x7002042c)
 assert struct.unpack_from('<3I',image,0x44c)==(0x70020000,len(image),0)
 assert 0x458<=0x800 and len(image)<=1048576 and len(image)%4096==0
 assert table_offsets[0]+35*8<=0x400 and table_offsets[1]==0x480
 assert table_offsets[1]+100*8<=0x800
 table=image[table_offsets[0]:table_offsets[0]+280]+image[0x480:0x7a0]
 assert expand(table)==rows and len(rows)==135
 assert image[4:8]==STOCK_PUSH # Exact stock push instruction.
 payload=raw[0x1000:]
 assert image[0x1000:0x1000+len(payload)]==payload
 assert b'k4_boot0' not in image
 return dict(size=len(image),sha256=hashlib.sha256(image).hexdigest(),dcd_size=0,
  initial_read_size=2048,complete_plugin_window_pass=True,first_ivt_bootdata_stock_byte_equal=True,
  sequence_equal=True,writes=132,checks=3,table_offsets=table_offsets,
  sequence_sha256=hashlib.sha256(b''.join(struct.pack('<4I',*r) for r in rows)).hexdigest(),
  source_image_sha256=hashlib.sha256(raw).hexdigest(),payload_offset=4096,payload_size=len(payload),
  source_payload_sha256=hashlib.sha256(payload).hexdigest(),
  image_payload_sha256=hashlib.sha256(image[4096:4096+len(payload)]).hexdigest(),
  payload_equal=True,no_k4_boot0_literal=True)
def build(raw,out):
 usb=raw
 stock=STOCK
 _,d=legacy.parse(raw); _,ud=legacy.parse(usb); assert d==ud
 rows=legacy.decode(d); encoded=compact(rows)
 out.mkdir(exist_ok=False,parents=True)
 for name,part in [('before',encoded[:35]),('after',encoded[35:])]:
  (out/(name+'.inc')).write_text(''.join('.word 0x%x,0x%x\n'%r for r in part))
 size=(4096+len(raw)-4096+4095)&~4095
 (out/'plugin.ld').write_text("""SECTIONS {
 . = 0xf8006000;
 .text : { *(.entry) }
 .table_before : { *(.table_before) }
 ASSERT(. <= 0xf8006400, "code/table exceed first IVT")
 . = 0xf8006480;
 .table_after : { *(.table_after) }
 ASSERT(. <= 0xf8006800, "plugin exceeds initial 2 KiB")
 /DISCARD/ : { *(.ARM.exidx*) *(.ARM.extab*) *(.comment*) *(.note*) }
}""")
 subprocess.run([os.environ.get('CROSS_COMPILE','arm-linux-gnueabihf-')+'gcc','-nostdlib','-static','-no-pie','-marm','-mcpu=cortex-a8','-mfloat-abi=soft','-Wl,-T,'+str(out/'plugin.ld'),'-Wl,-e,plugin_entry','-Wl,--build-id=none','-I'+str(out),'-DIMAGE_SIZE='+str(size),str(HERE/'ocram-stock-entry.S'),'-o',str(out/'plugin.elf')],check=True)
 subprocess.run([os.environ.get('CROSS_COMPILE','arm-linux-gnueabihf-')+'objcopy','-O','binary',str(out/'plugin.elf'),str(out/'plugin.bin')],check=True)
 symbols=subprocess.check_output([os.environ.get('CROSS_COMPILE','arm-linux-gnueabihf-')+'nm','-n',str(out/'plugin.elf')],text=True)
 (out/'symbols.txt').write_text(symbols)
 offsets=[int(next(line.split()[0] for line in symbols.splitlines() if line.split()[-1]==s),16)-0xf8006000 for s in ['table_before','table_after']]
 code=(out/'plugin.bin').read_bytes()
 image=bytearray(size); image[:len(code)]=code
 image[0x400:0x42c]=stock[0x400:0x42c]
 image[0x42c:0x44c]=legacy.ivt(0x70021000,0x7002044c,0x7002042c)
 struct.pack_into('<3I',image,0x44c,0x70020000,size,0)
 image[4096:len(raw)]=raw[4096:]
 result=check(image,usb,raw,stock,offsets)
 (out/'barebox-boot1-plugin-candidate.img').write_bytes(image)
 (out/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
 (out/'sequence.json').write_text(json.dumps(rows,indent=2)+'\n')
 (out/'SHA256SUMS').write_text(result['sha256']+'  barebox-boot1-plugin-candidate.img\n')
 print(json.dumps(result,indent=2))
if __name__=='__main__': build(Path(sys.argv[1]).read_bytes(),Path(sys.argv[2]))
