#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Compare accepted DTBs and audit hardware properties, using only stdlib + dtc."""
import argparse,hashlib,json,pathlib,struct,subprocess

def parse(data):
    h=struct.unpack_from('>10I',data)
    if h[0]!=0xd00dfeed or h[1]!=len(data):raise ValueError('invalid FDT header/size')
    strings=data[h[3]:h[3]+h[8]];pos=h[2];end=pos+h[9];stack=[];nodes={}
    while pos<end:
        token=struct.unpack_from('>I',data,pos)[0];pos+=4
        if token==1:
            stop=data.index(b'\0',pos);name=data[pos:stop].decode();pos=(stop+4)&~3
            stack.append(name);path='/'+('/'.join(stack[1:]));nodes[path]={}
        elif token==2:stack.pop()
        elif token==3:
            size,off=struct.unpack_from('>II',data,pos);pos+=8
            stop=strings.index(b'\0',off);name=strings[off:stop].decode()
            nodes['/'+('/'.join(stack[1:]))][name]=data[pos:pos+size].hex();pos=(pos+size+3)&~3
        elif token==4:continue
        elif token==9:break
        else:raise ValueError('invalid FDT token')
    reservations=[];pos=h[4]
    while True:
        addr,size=struct.unpack_from('>QQ',data,pos);pos+=16
        if not (addr or size):break
        reservations.append([addr,size])
    return {'nodes':nodes,'reservations':reservations,'boot_cpuid_phys':h[7]}

def category(name,path):
    result=[]
    if name.startswith('regulator-') or name.endswith('-supply') or '/regulators/' in path:result.append('regulator')
    if name in ('clocks','clock-names','clock-frequency','#clock-cells') or name.startswith('assigned-clock'):result.append('clock')
    if 'gpio' in name:result.append('gpio')
    if name.startswith('opp') or name in ('operating-points','operating-points-v2','clock-latency'):result.append('opp')
    if name.startswith('pinctrl') or name=='fsl,pins' or name in ('fsl,sd2-low-voltage','fsl,nandf-low-voltage'):result.append('pinctrl')
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--baseline',required=True);ap.add_argument('--candidate',required=True);ap.add_argument('--report',required=True);ap.add_argument('--dtc',default='dtc');a=ap.parse_args()
    old=pathlib.Path(a.baseline).read_bytes();new=pathlib.Path(a.candidate).read_bytes();ob=parse(old);nb=parse(new)
    diffs=[]
    for path in sorted(set(ob['nodes'])|set(nb['nodes'])):
        before=ob['nodes'].get(path);after=nb['nodes'].get(path)
        if before!=after:diffs.append({'path':path,'before':before,'after':after})
    props={k:[] for k in ('regulator','clock','gpio','opp','pinctrl')}
    for path,values in ob['nodes'].items():
        for name,value in values.items():
            for group in category(name,path):props[group].append({'node':path,'property':name,'value_hex':value,'candidate_equal':nb['nodes'].get(path,{}).get(name)==value})
    normalized=[]
    for file in (a.baseline,a.candidate):
        q=subprocess.run([a.dtc,'-I','dtb','-O','dts','-s',file],capture_output=True,check=True);normalized.append(q.stdout)
    result={'baseline_sha256':hashlib.sha256(old).hexdigest(),'candidate_sha256':hashlib.sha256(new).hexdigest(),'bytes_equal':old==new,'normalized_dts_equal':normalized[0]==normalized[1],'nodes':len(ob['nodes']),'all_properties':sum(len(p) for p in ob['nodes'].values()),'semantic_tree_equal':ob==nb,'differences':diffs,'hardware_property_counts':{k:len(v) for k,v in props.items()},'hardware_properties':props,'schema_validation':'not run by this equivalence checker; see separate schema report'}
    pathlib.Path(a.report).write_text(json.dumps(result,indent=2)+'\n')
    if ob!=nb or normalized[0]!=normalized[1]:raise SystemExit('DTB semantic difference; stop before hardware validation')
    print(json.dumps({k:v for k,v in result.items() if k not in ('hardware_properties','differences')},indent=2))
if __name__=='__main__':main()