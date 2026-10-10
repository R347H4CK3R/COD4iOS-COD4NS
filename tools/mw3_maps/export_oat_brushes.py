#!/usr/bin/env python3
"""Export complete IW5 brush collision subgraph for native IW3 conversion.

Preserves all brush fields, adjacency bytes, materials/flags and glass indices.
This is not a full clipmap and cannot enable a playable map by itself.
"""
import argparse,struct,re,subprocess
from pathlib import Path
from export_oat_world import capture,read,ExportError
from export_oat_collision import collision_geometry,array_index
from export_oat_navigation import find_named

MAX_EDGES=8_000_000
def material_name(regions,pointer):
    result=bytearray()
    for i in range(64):
        byte=read(regions,pointer+i,1)[0]
        if not byte:
            if not result:raise ExportError('Empty collision material name')
            return bytes(result)
        result.append(byte)
    raise ExportError('IW5 material name does not fit native IW3 64-byte field')

def serialize_brushes(regions,address,map_name):
    # Validate actual geometric ranges, identities, coordinates and references.
    collision_geometry(regions,address,map_name)
    info=read(regions,address+8,64)
    pc,pp,mc,mp,sc,sp,ec,ep=struct.unpack_from('<8I',info)
    bc=struct.unpack_from('<H',info,48)[0]
    bp,bounds,contents=struct.unpack_from('<3I',info,52)
    if ec>MAX_EDGES:raise ExportError('Brush adjacency-byte budget exceeded')
    planes=read(regions,pp,pc*20)
    if any(planes[i*20+16]>3 for i in range(pc)):raise ExportError('Unsupported brush plane type')
    sides=bytearray(read(regions,sp,sc*8)) if sc else bytearray()
    brushes=bytearray(read(regions,bp,bc*36))
    edges=read(regions,ep,ec) if ec else b''
    for i in range(sc):
        pointer=struct.unpack_from('<I',sides,i*8)[0]
        struct.pack_into('<I',sides,i*8,array_index(pointer,pp,pc,20))
    for i in range(bc):
        at=i*36;count=struct.unpack_from('<H',brushes,at)[0]
        side_pointer,edge_pointer=struct.unpack_from('<II',brushes,at+4)
        first=array_index(side_pointer,sp,sc,8,count) if count else 0
        edge_start=array_index(edge_pointer,ep,ec,1) if edge_pointer else 0xffffffff
        struct.pack_into('<II',brushes,at+4,first,edge_start)
        offsets=list(brushes[at+24:at+30]);counts=list(brushes[at+30:at+36])
        for side in range(first,first+count):
            offsets.append(sides[side*8+6]);counts.append(sides[side*8+7])
        for offset,edge_count in zip(offsets,counts):
            if not edge_count:continue
            if edge_start==0xffffffff or edge_start+offset+edge_count>ec:
                raise ExportError('Brush face adjacency range exceeds edge array')
            if any(face>=count+6 for face in edges[edge_start+offset:edge_start+offset+edge_count]):
                raise ExportError('Adjacent face index exceeds this brush face count')
    material_data=read(regions,mp,mc*12);materials=bytearray()
    for i in range(mc):
        pointer=struct.unpack_from('<I',material_data,i*12)[0]
        name=material_name(regions,pointer)
        materials+=name.ljust(64,b'\0')+material_data[i*12+4:i*12+12]
    header=b'IW5BRSH1'+struct.pack('<6I',1,pc,sc,bc,ec,mc)
    return header+planes+sides+brushes+read(regions,bounds,bc*24)+read(regions,contents,bc*4)+edges+materials

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--unlinker',type=Path,required=True);p.add_argument('--fastfile',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--wait-seconds',type=float,default=7)
    args=p.parse_args();map_name=args.fastfile.stem
    if not re.fullmatch(r'mp_[A-Za-z0-9_]{1,60}',map_name):p.error('Use original mp_* fastfile name')
    if not args.fastfile.is_file():p.error('Fastfile does not exist')
    if args.output.exists():p.error('Preserve existing output; choose a fresh path')
    if not 1<=args.wait_seconds<=30:p.error('wait-seconds must be between 1 and 30')
    try:
        regions=capture(args.unlinker.resolve(),args.fastfile.resolve(),args.wait_seconds)
        name=('maps/mp/'+map_name+'.d3dbsp').encode()+b'\0'
        snapshot=find_named(regions,name,lambda r,a:serialize_brushes(r,a,map_name))
        args.output.parent.mkdir(parents=True,exist_ok=True)
        with args.output.open('xb') as output:output.write(snapshot)
        print('Exported complete pointer-free brush subgraph:',len(snapshot),'bytes; not a full clipmap')
    except (ExportError,OSError,subprocess.SubprocessError) as error:p.exit(1,str(error)+'\n')
if __name__=='__main__':main()
