#!/usr/bin/env python3
"""Extract real IW5 static collision primitives and unchanged tokenized entities.

Research format only; not an IW3 clipmap. Uses the same bounded read-only OAT
child capture as export_oat_world. Retail outputs must remain outside Git.
"""
import argparse, json, math, struct, subprocess
from pathlib import Path
from export_oat_world import capture, read, ExportError

MAX_VERTICES=1_000_000
MAX_TRIANGLES=2_000_000
MAX_PLANES=1_000_000
MAX_SIDES=1_000_000
MAX_ENTITY_BYTES=4<<20

def finite(values, positive=False):
    if not all(math.isfinite(x) and abs(x)<=1e7 and (not positive or x>=0) for x in values):
        raise ExportError('Invalid collision coordinates or bounds')
    return list(values)

def array_index(pointer,base,count,stride,extent=1):
    if pointer<base or (pointer-base)%stride or extent<0:
        raise ExportError('Unaligned or out-of-array collision pointer')
    index=(pointer-base)//stride
    if index>count or extent>count-index:
        raise ExportError('Collision pointer range exceeds source array')
    return index

def collision_geometry(regions,address,map_name):
    c=read(regions,address,256)
    name=struct.unpack_from('<I',c)[0]
    expected=('maps/mp/'+map_name+'.d3dbsp').encode()+b'\0'
    if read(regions,name,len(expected))!=expected:raise ExportError('Wrong clipmap identity')
    vc,vp,tc,tp=struct.unpack_from('<4I',c,100)
    if not (0<vc<=MAX_VERTICES and 0<tc<=MAX_TRIANGLES):raise ExportError('Collision triangle count budget exceeded')
    raw_vertices=read(regions,vp,vc*12); raw_indices=read(regions,tp,tc*6)
    vertices=[finite(struct.unpack_from('<3f',raw_vertices,i*12)) for i in range(vc)]
    triangles=[]
    for i in range(tc):
        triangle=list(struct.unpack_from('<3H',raw_indices,i*6))
        if any(index>=vc for index in triangle):raise ExportError('Collision triangle index out of bounds')
        triangles.append(triangle)

    # OAT's x86 offsetof probe: inline ClipInfo is 64 bytes at offset 8.
    info=c[8:72]
    pc,pp=struct.unpack_from('<II',info)
    material_count=struct.unpack_from('<I',info,8)[0]
    sc,sp=struct.unpack_from('<II',info,16)
    bc=struct.unpack_from('<H',info,48)[0]
    bp,bounds_pointer,contents_pointer=struct.unpack_from('<3I',info,52)
    if not (0<pc<=MAX_PLANES and 0<=sc<=MAX_SIDES and 0<bc<=65535 and 0<material_count<=65535):
        raise ExportError('Collision brush count budget exceeded')
    raw_planes=read(regions,pp,pc*20)
    raw_sides=read(regions,sp,sc*8) if sc else b''
    raw_brushes=read(regions,bp,bc*36)
    raw_bounds=read(regions,bounds_pointer,bc*24)
    raw_contents=read(regions,contents_pointer,bc*4)
    planes=[]
    for i in range(pc):
        normal_distance=finite(struct.unpack_from('<4f',raw_planes,i*20))
        if not .25<=sum(x*x for x in normal_distance[:3])<=2.25:raise ExportError('Invalid brush plane normal')
        planes.append(normal_distance)
    sides=[]
    for i in range(sc):
        plane,material,adjacent,edge_count=struct.unpack_from('<IHBB',raw_sides,i*8)
        if material>=material_count:raise ExportError('Brush side material out of bounds')
        sides.append(dict(plane=array_index(plane,pp,pc,20),material=material,
                          adjacentOffset=adjacent,edgeCount=edge_count))
    brushes=[]
    for i in range(bc):
        offset=i*36
        side_count,glass,side_pointer=struct.unpack_from('<HHI',raw_brushes,offset)
        first=array_index(side_pointer,sp,sc,8,side_count) if side_count else 0
        midpoint=finite(struct.unpack_from('<3f',raw_bounds,i*24))
        halfsize=finite(struct.unpack_from('<3f',raw_bounds,i*24+12),positive=True)
        axial=list(struct.unpack_from('<6h',raw_brushes,offset+12))
        if any(material<0 or material>=material_count for material in axial):raise ExportError('Axial brush material out of bounds')
        brushes.append(dict(firstSide=first,sideCount=side_count,glassPieceIndex=glass,
                            midpoint=midpoint,halfsize=halfsize,axialMaterials=axial,
                            contents=struct.unpack_from('<i',raw_contents,i*4)[0]))
    entities_pointer=struct.unpack_from('<I',c,152)[0]
    entity_header=read(regions,entities_pointer,96)
    entity_name,entity_pointer,entity_size=struct.unpack_from('<IIi',entity_header)
    if read(regions,entity_name,len(expected))!=expected:raise ExportError('Wrong linked MapEnts identity')
    if not 1<entity_size<=MAX_ENTITY_BYTES:raise ExportError('Entity text budget exceeded')
    entities=read(regions,entity_pointer,entity_size)
    if not entities.endswith(b'\0') or b'\0' in entities[:-1] or not entities.lstrip().startswith(b'{'):
        raise ExportError('Invalid entity text framing')
    result=dict(format='IW5 static collision primitives',version=1,map=map_name,
                vertices=vertices,triangles=triangles,planes=planes,sides=sides,brushes=brushes,
                limitations=['Not an IW3 clipmap', 'Entity keys retain numeric IW5 tokens',
                             'No acceleration trees, partition metadata, walkable edges, brush adjacency arrays',
                             'No material names/flags, static-model collision, triggers, submodels or dynamic entities',
                             'No path-data conversion or gameplay integration'])
    return entities[:-1],result

def find_collision(regions,map_name):
    needle=('maps/mp/'+map_name+'.d3dbsp').encode()+b'\0'
    aliases=[]
    for base,data in regions:
        start=0
        while (at:=data.find(needle,start))>=0:
            aliases.append(base+at);start=at+1
            if len(aliases)>4096:raise ExportError('Too many clipmap-name aliases')
    matches={};attempts=0
    for alias in aliases:
        pointer=struct.pack('<I',alias)
        for base,data in regions:
            start=0
            while (at:=data.find(pointer,start))>=0:
                start=at+1;address=base+at;attempts+=1
                if attempts>100000:raise ExportError('Too many clipmap candidates')
                if address%4:continue
                try:result=collision_geometry(regions,address,map_name)
                except ExportError:continue
                matches[address]=result
    if len(matches)!=1:raise ExportError(f'Expected one validated clipmap, found {len(matches)}')
    return next(iter(matches.values()))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--unlinker',type=Path,required=True);p.add_argument('--fastfile',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--wait-seconds',type=float,default=7)
    args=p.parse_args()
    import re
    if not re.fullmatch(r'mp_[A-Za-z0-9_]{1,60}',args.fastfile.stem):p.error('Use original mp_* fastfile name')
    if not args.fastfile.is_file():p.error('Fastfile does not exist')
    if args.output_dir.exists():p.error('Output directory already exists; choose a fresh path')
    if not 1<=args.wait_seconds<=30:p.error('wait-seconds must be between 1 and 30')
    try:
        entities,geometry=find_collision(capture(args.unlinker.resolve(),args.fastfile.resolve(),args.wait_seconds),args.fastfile.stem)
        args.output_dir.mkdir(parents=True,exist_ok=False)
        (args.output_dir/'entities.iw5.txt').write_bytes(entities)
        (args.output_dir/'collision.iw5.json').write_text(json.dumps(geometry,separators=(',',':')),encoding='utf-8')
        print(json.dumps(dict(map=geometry['map'],entityBytes=len(entities),vertices=len(geometry['vertices']),
                              triangles=len(geometry['triangles']),planes=len(geometry['planes']),
                              sides=len(geometry['sides']),brushes=len(geometry['brushes'])),indent=2))
    except (ExportError,OSError,subprocess.SubprocessError) as error:p.exit(1,str(error)+'\n')
if __name__=='__main__':main()
