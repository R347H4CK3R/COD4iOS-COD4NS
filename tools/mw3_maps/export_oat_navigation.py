#!/usr/bin/env python3
"""Extract decoded IW5 Survival-overlay path graph and exact addon entity text.

Pointer-free research output, not COD4 path-data conversion or playable maps.
"""
import argparse,json,re,struct,subprocess
from pathlib import Path
from export_oat_world import capture,read,ExportError
from export_oat_collision import finite,MAX_ENTITY_BYTES

MAX_NODES=65535
MAX_LINKS=6_000_000

def path_graph(regions,address,map_name):
    header=read(regions,address,44)
    name_pointer,count,nodes_pointer=struct.unpack_from('<III',header)
    expected=('maps/mp/'+map_name+'.d3dbsp').encode()+b'\0'
    if read(regions,name_pointer,len(expected))!=expected:raise ExportError('Wrong PathData identity')
    if not 0<count<=MAX_NODES:raise ExportError('Path-node budget exceeded')
    raw=read(regions,nodes_pointer,count*136)
    nodes=[];total_links=0
    for i in range(count):
        offset=i*136
        kind=struct.unpack_from('<I',raw,offset)[0]
        error=struct.unpack_from('<I',raw,offset+48)[0]
        if kind>20 or error>8:raise ExportError('Invalid IW5 path-node enum')
        position=finite(struct.unpack_from('<3f',raw,offset+20))
        angle=finite(struct.unpack_from('<f',raw,offset+32))[0]
        link_count=struct.unpack_from('<H',raw,offset+56)[0]
        link_pointer=struct.unpack_from('<I',raw,offset+60)[0]
        total_links+=link_count
        if total_links>MAX_LINKS:raise ExportError('Path-link budget exceeded')
        links=[]
        link_data=read(regions,link_pointer,link_count*12) if link_count else b''
        for j in range(link_count):
            distance,target,disconnect,negotiation,flags=struct.unpack_from('<fHBBB',link_data,j*12)
            finite((distance,),positive=True)
            if target>=count:raise ExportError('Path link target outside node array')
            links.append(dict(target=target,distance=distance,disconnectCount=disconnect,
                              negotiationLink=negotiation,flags=flags))
        nodes.append(dict(type=kind,spawnflags=struct.unpack_from('<H',raw,offset+4)[0],
                          position=position,angle=angle,error=error,links=links))
    return dict(format='IW5 path graph',version=1,map=map_name,nodes=nodes,
                limitations=['Not IW3 PathData', 'No script-string name resolution or animscript functions',
                             'No path visibility, spatial trees, chain maps, overlap nodes or runtime state',
                             'No native navigation integration'])

def addon_entities(regions,address,map_name):
    header=read(regions,address,52)
    name_pointer,text_pointer,count=struct.unpack_from('<IIi',header)
    expected=('maps/so_survival_'+map_name+'.mapents').encode()+b'\0'
    if read(regions,name_pointer,len(expected))!=expected:raise ExportError('Wrong AddonMapEnts identity')
    if not 1<count<=MAX_ENTITY_BYTES:raise ExportError('Addon entity text budget exceeded')
    text=read(regions,text_pointer,count)
    if not text.endswith(b'\0') or b'\0' in text[:-1] or not text.lstrip().startswith(b'{'):
        raise ExportError('Invalid addon entity text framing')
    info=struct.unpack_from('<I',header,36)[0]
    if info:read(regions,info,64)
    submodel_count=struct.unpack_from('<I',header,40)[0]
    if submodel_count>65535:raise ExportError('Addon submodel count budget exceeded')
    return text[:-1],dict(entityBytes=count-1,hasAdditionalClipInfo=bool(info),submodels=submodel_count,
                          limitations=['Entity keys retain numeric IW5 tokens',
                                       'Additional addon clip info, trigger data and submodels are not exported',
                                       'No native entity execution or spawner conversion'])

def find_named(regions,name,decode):
    aliases=[]
    for base,data in regions:
        start=0
        while (at:=data.find(name,start))>=0:
            start=at+1;aliases.append(base+at)
            if len(aliases)>4096:raise ExportError('Too many asset-name aliases')
    matches={};attempts=0
    for alias in aliases:
        pointer=struct.pack('<I',alias)
        for base,data in regions:
            start=0
            while (at:=data.find(pointer,start))>=0:
                start=at+1;address=base+at;attempts+=1
                if attempts>100000:raise ExportError('Too many asset candidates')
                if address%4:continue
                try:result=decode(regions,address)
                except ExportError:continue
                matches[address]=result
    if len(matches)!=1:raise ExportError(f'Expected one validated asset for {name!r}, found {len(matches)}')
    return next(iter(matches.values()))

def overlay_data(regions,map_name):
    graph=find_named(regions,('maps/mp/'+map_name+'.d3dbsp').encode()+b'\0',
                     lambda r,a:path_graph(r,a,map_name))
    entities,metadata=find_named(regions,('maps/so_survival_'+map_name+'.mapents').encode()+b'\0',
                                 lambda r,a:addon_entities(r,a,map_name))
    return graph,entities,metadata

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--unlinker',type=Path,required=True);p.add_argument('--fastfile',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--wait-seconds',type=float,default=7)
    args=p.parse_args()
    match=re.fullmatch(r'so_survival_(mp_[A-Za-z0-9_]{1,60})',args.fastfile.stem)
    if not match:p.error('Use original so_survival_mp_* fastfile name')
    if not args.fastfile.is_file():p.error('Fastfile does not exist')
    if args.output_dir.exists():p.error('Output directory already exists; choose a fresh path')
    if not 1<=args.wait_seconds<=30:p.error('wait-seconds must be between 1 and 30')
    try:
        graph,entities,metadata=overlay_data(capture(args.unlinker.resolve(),args.fastfile.resolve(),args.wait_seconds),match[1])
        args.output_dir.mkdir(parents=True,exist_ok=False)
        (args.output_dir/'addon-entities.iw5.txt').write_bytes(entities)
        (args.output_dir/'path.iw5.json').write_text(json.dumps(graph,separators=(',',':')),encoding='utf-8')
        (args.output_dir/'addon-metadata.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
        print(json.dumps(dict(map=graph['map'],nodes=len(graph['nodes']),
                              links=sum(len(n['links']) for n in graph['nodes']),addon=metadata),indent=2))
    except (ExportError,OSError,subprocess.SubprocessError) as error:p.exit(1,str(error)+'\n')
if __name__=='__main__':main()
