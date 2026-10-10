"""Export the bounded complete decoded IW5 GfxWorld pointer graph.
Original records stay local; process pointers become explicit graph/asset references.
This archive is not an IW3 fastfile. Conversion blockers prevent registration.
"""
import argparse
import hashlib
import json
import math
import struct
import sys
import zipfile
from convert_records import brush as convert_brush, surface as convert_surface, static_model as convert_model
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'mw3_maps'))
from export_oat_world import read, ExportError, capture, world_geometry

MAX_ARRAY=8_000_000
MAX_GRAPH=512<<20
SIZES={'GfxWorld':640,'GfxSky':16,'GfxCell':48,'GfxPortal':60,'GfxAabbTree':44,'GfxStaticModelInst':36,'GfxStaticModelDrawInst':76,'GfxSurface':24,'Bounds':24,'GfxBrushModel':60,'MaterialMemory':8,'GfxShadowGeometry':12,'GfxLightRegion':8,'GfxLightRegionHull':80,'GfxLightRegionAxis':20,'GfxHeroOnlyLight':64}

def u32(data,offset):return struct.unpack_from('<I',data,offset)[0]
def bounded(count,maximum=MAX_ARRAY):
    if count<0 or count>maximum:raise ExportError('Array count outside format budget')
    return count

def bounds(data,offset=0):
    center=struct.unpack_from('<3f',data,offset);half=struct.unpack_from('<3f',data,offset+12)
    if not all(math.isfinite(x) and abs(x)<=1e7 for x in center+half) or any(x<0 for x in half):raise ExportError('Invalid original bounds')
    return [center[i]-half[i] for i in range(3)],[center[i]+half[i] for i in range(3)]

def string(regions,pointer):
    if not pointer:raise ExportError('Null required string')
    for base,data in regions:
        if base<=pointer<base+len(data):
            start=pointer-base;end=data.find(b'\0',start,min(start+4096,len(data)))
            if end<0:raise ExportError('Unterminated asset name')
            value=data[start:end]
            if not value or any(c<32 or c>126 for c in value):raise ExportError('Invalid asset-name encoding')
            return value.decode('ascii')
    raise ExportError('Asset name outside capture')

class Graph:
    def __init__(self,regions):self.regions=regions;self.nodes={};self.assets={};self.total=0;self.conversions={};self.blockers=[]
    def add(self,name,kind,pointer,count,stride,pointers=(),runtime=False):
        bounded(count);bounded(stride,1024)
        if count==0:return None
        size=count*stride;self.total+=size
        if self.total>MAX_GRAPH:raise ExportError('World graph exceeds byte budget')
        original=read(self.regions,pointer,size)
        blob=bytearray(original)
        for index in range(count):
            for offset in pointers:
                if offset<0 or offset+4>stride:raise ExportError('Invalid pointer-field schema')
                struct.pack_into('<I',blob,index*stride+offset,0)
        self.nodes[name]={'type':kind,'count':count,'stride':stride,'pointer_fields':list(pointers),'runtime':runtime,'data':bytes(blob),'refs':[]}
        return original
    def ref(self,node,index,offset,target):
        if node not in self.nodes or offset not in self.nodes[node]['pointer_fields'] or not 0<=index<self.nodes[node]['count']:raise ExportError('Invalid graph relocation')
        self.nodes[node]['refs'].append({'record':index,'offset':offset,'target':target})
    def asset(self,node,index,offset,kind,pointer):
        if not pointer:return
        name_offset=28 if kind=='image' else 0
        name=string(self.regions,u32(read(self.regions,pointer,name_offset+4),name_offset))
        self.assets.setdefault(kind,set()).add(name)
        self.ref(node,index,offset,{'asset_type':kind,'name':name})
    def array_ref(self,node,index,offset,name,kind,pointer,count,stride,pointers=(),runtime=False):
        blob=self.add(name,kind,pointer,count,stride,pointers,runtime)
        if blob is not None:self.ref(node,index,offset,{'node':name})
        return blob
    def conversion(self,name,kind,blob,stride):
        if len(blob)%stride:raise ExportError('Converted record stride mismatch')
        self.conversions[name]={'type':kind,'count':len(blob)//stride,'stride':stride,'data':bytes(blob)}

def export_world(regions,address,map_name):
    # Reuse real geometry validation; every index references an actual vertex.
    _,geometry=world_geometry(regions,address,map_name)
    g=Graph(regions)
    pointer_offsets=[0,4,24,56,60,64,68,72,76,84,88,92,100,104,112,116,120,124,128,136,140,148,152,160,192,200,208,216,224,260,268,272,424,428,432,436,440,444,448,452,456,460,464,520,524,528,532,536,540,544,548,552,556,560,564,568,592,596,600,604,608,612,616,620,632]
    w=g.add('world','GfxWorld',address,1,640,pointer_offsets)
    for offset in [0,4]:g.ref('world',0,offset,{'string':string(regions,u32(w,offset))})
    planes,nodes,surfaces,skies=struct.unpack_from('<4I',w,8)
    bounded(planes,1_000_000);bounded(nodes,1_000_000);bounded(surfaces,65536);bounded(skies,256)
    cell_count=u32(w,52);bounded(cell_count,65535)
    primary_count=u32(w,32);sun_index=u32(w,28)
    if not primary_count or sun_index>=primary_count:raise ExportError('Invalid primary light range')
    draw=struct.unpack_from('<21I',w,80);dpvs=struct.unpack_from('<27I',w,468);dyn=struct.unpack_from('<12I',w,576)
    smodel_count=bounded(dpvs[0],65535)
    def root_array(offset,name,kind,count,stride,pointers=(),runtime=False):return g.array_ref('world',0,offset,name,kind,u32(w,offset),count,stride,pointers,runtime)
    sky=root_array(24,'skies','GfxSky',skies,16,[4,8])
    if sky:
        for i in range(skies):
            count=bounded(u32(sky,i*16),surfaces)
            values=g.array_ref('skies',i,4,f'skies/{i}/surfaces','u32',u32(sky,i*16+4),count,4)
            if values and any(x[0]>=surfaces for x in struct.iter_unpack('<I',values)):raise ExportError('Sky surface index outside world')
            g.asset('skies',i,8,'image',u32(sky,i*16+8))
    root_array(56,'planes','cplane',planes,20)
    root_array(60,'nodes','u16',nodes,2)
    root_array(64,'runtime/sceneEntCellBits','u32',cell_count*0x200,4,runtime=True)
    tree_counts=root_array(68,'aabbTreeCounts','u32',cell_count,4)
    trees=root_array(72,'aabbTrees','GfxCellTree',cell_count,4,[0])
    cells=root_array(76,'cells','GfxCell',cell_count,48,[28,36,44])
    for i in range(cell_count):
        n=bounded(u32(tree_counts,i*4),65535)
        tree_name=f'cells/{i}/aabbs'
        raw=g.array_ref('aabbTrees',i,0,tree_name,'GfxAabbTree',u32(trees,i*4),n,44,[36])
        converted=bytearray()
        for j in range(n):
            row=raw[j*44:(j+1)*44];mins,maxs=bounds(row)
            child_count,surf_count,start,no_decal,start_no_decal,model_indexes=struct.unpack_from('<6H',row,24)
            children_offset=struct.unpack_from('<i',row,40)[0]
            if start+surf_count>dpvs[1]+dpvs[2] or start_no_decal+no_decal>dpvs[1]+dpvs[2]:raise ExportError('AABB surface range outside world')
            if child_count and (children_offset%44 or j+children_offset//44<0 or j+children_offset//44+child_count>n):raise ExportError('AABB children outside tree')
            indices=g.array_ref(tree_name,j,36,f'{tree_name}/{j}/smodels','u16',u32(row,36),model_indexes,2)
            if indices and any(x[0]>=smodel_count for x in struct.iter_unpack('<H',indices)):raise ExportError('AABB static-model index outside world')
            converted+=struct.pack('<6f',*(mins+maxs))+row[24:36]+b'\0'*4+row[40:44]
        g.conversion(tree_name,'IW3_GfxAabbTree',converted,44)
        row=cells[i*48:(i+1)*48];bounds(row)
        portals=bounded(u32(row,24),65535)
        pname=f'cells/{i}/portals'
        pdata=g.array_ref('cells',i,28,pname,'GfxPortal',u32(row,28),portals,60,[4,8,28])
        for j in range(portals):
            portal=pdata[j*60:(j+1)*60]
            target,count=struct.unpack_from('<HB',portal,32)
            if target>=cell_count or count<3:raise ExportError('Invalid portal destination or hull size')
            vertices=g.array_ref(pname,j,28,f'{pname}/{j}/vertices','vec3',u32(portal,28),count,12)
            if not all(math.isfinite(x) and abs(x)<=1e7 for values in struct.iter_unpack('<3f',vertices) for x in values):raise ExportError('Invalid portal vertex')
        probes=g.array_ref('cells',i,36,f'cells/{i}/probes','u8',u32(row,36),row[32],1)
        if probes and any(x>=draw[0] for x in probes):raise ExportError('Cell probe index outside world')
        references=g.array_ref('cells',i,44,f'cells/{i}/probeRefs','u8',u32(row,44),row[40],1)
        if references and any(x>=draw[4] for x in references):raise ExportError('Cell probe reference outside world')
    probe_ptrs=root_array(84,'draw/reflectionProbes','GfxImageRef',draw[0],4,[0])
    for i in range(draw[0]):g.asset('draw/reflectionProbes',i,0,'image',u32(probe_ptrs,i*4))
    root_array(88,'draw/probeOrigins','vec3',draw[0],12)
    root_array(92,'runtime/probeTextures','GfxTexture',draw[0],4,[0],True)
    root_array(100,'draw/probeReferenceOrigins','vec3',draw[4],12)
    root_array(104,'draw/probeReferences','u8',draw[4],1)
    lightmaps=root_array(112,'draw/lightmaps','GfxLightmapArray',draw[7],8,[0,4])
    for i in range(draw[7]):
        for offset in [0,4]:g.asset('draw/lightmaps',i,offset,'image',u32(lightmaps,i*8+offset))
    for offset in [116,120]:root_array(offset,f'runtime/lightmapTextures/{offset}','GfxTexture',draw[7],4,[0],True)
    for offset in [124,128]:g.asset('world',0,offset,'image',u32(w,offset))
    vertices=root_array(136,'draw/vertices','GfxWorldVertex',draw[13],44)
    for i in range(draw[13]):
        row=vertices[i*44:(i+1)*44]
        floats=struct.unpack_from('<4f',row)+struct.unpack_from('<4f',row,20)
        if not all(math.isfinite(x) and abs(x)<=1e7 for x in floats):raise ExportError('Invalid vertex position/UV/binormal')
    root_array(148,'draw/vertexLayers','u8',draw[16],1)
    root_array(160,'draw/indices','u16',draw[19],2)
    lg=w[164:220];mins=struct.unpack_from('<3H',lg,8);maxs=struct.unpack_from('<3H',lg,14);row_axis=u32(lg,20);col_axis=u32(lg,24)
    if row_axis>=3 or col_axis>=3 or row_axis==col_axis or any(a>b for a,b in zip(mins,maxs)):raise ExportError('Invalid light-grid axes or bounds')
    root_array(192,'lightGrid/rowDataStart','u16',maxs[row_axis]-mins[row_axis]+1,2)
    root_array(200,'lightGrid/rawRows','u8',u32(lg,32),1)
    entries=root_array(208,'lightGrid/entries','GfxLightGridEntry',u32(lg,40),4)
    root_array(216,'lightGrid/colors','GfxLightGridColors',u32(lg,48),168)
    if entries and any(x[0]>=u32(lg,48) for x in struct.iter_unpack('<HBB',entries)):raise ExportError('Light-grid color index outside table')
    models=root_array(224,'brushModels','GfxBrushModel',u32(w,220),60)
    converted=bytearray()
    for i in range(u32(w,220)):
        row=models[i*60:(i+1)*60];a,b=bounds(row);c,d=bounds(row,24);n,start,nd=struct.unpack_from('<3H',row,52)
        if (n and start+n>surfaces) or nd>n:raise ExportError('Brush-model surface range outside world')
        converted+=convert_brush(row,surfaces)
    g.conversion('brushModels','IW3_GfxBrushModel',converted,56)
    bounds(w,228)
    memory=root_array(260,'materialMemory','MaterialMemory',u32(w,256),8,[0])
    for i in range(u32(w,256)):g.asset('materialMemory',i,0,'material',u32(memory,i*8))
    for offset in [268,272]:g.asset('world',0,offset,'material',u32(w,offset))
    g.asset('world',0,424,'image',u32(w,424))
    root_array(428,'runtime/cellCasterBits','u32',cell_count*((cell_count+31)//32),4,runtime=True)
    if u32(w,432):root_array(432,'runtime/cellSunBits','u32',(cell_count+31)//32,4,runtime=True)
    root_array(436,'runtime/sceneDynModels','GfxSceneDynModel',dyn[2],6,runtime=True)
    root_array(440,'runtime/sceneDynBrushes','GfxSceneDynBrush',dyn[3],4,runtime=True)
    nonsun=primary_count-sun_index-1
    root_array(444,'runtime/entityShadowVis','u32',nonsun*0x2000,4,runtime=True)
    for i in range(2):root_array(448+i*4,f'runtime/dynShadowVis/{i}','u32',dyn[2+i]*nonsun,4,runtime=True)
    root_array(456,'runtime/nonSunLights','u8',dyn[2],1,runtime=True)
    shadow=root_array(460,'shadowGeom','GfxShadowGeometry',primary_count,12,[4,8])
    for i in range(primary_count):
        row=shadow[i*12:(i+1)*12];ns,nm=struct.unpack_from('<2H',row)
        ss=g.array_ref('shadowGeom',i,4,f'shadowGeom/{i}/surfaces','u16',u32(row,4),ns,2)
        mm=g.array_ref('shadowGeom',i,8,f'shadowGeom/{i}/models','u16',u32(row,8),nm,2)
        if ss and any(x[0]>=surfaces for x in struct.iter_unpack('<H',ss)):raise ExportError('Shadow surface outside world')
        if mm and any(x[0]>=smodel_count for x in struct.iter_unpack('<H',mm)):raise ExportError('Shadow model outside world')
    light=root_array(464,'lightRegions','GfxLightRegion',primary_count,8,[4])
    for i in range(primary_count):
        count=bounded(u32(light,i*8),65535);name=f'lightRegions/{i}/hulls'
        hulls=g.array_ref('lightRegions',i,4,name,'GfxLightRegionHull',u32(light,i*8+4),count,80,[76])
        for j in range(count):g.array_ref(name,j,76,f'{name}/{j}/axes','GfxLightRegionAxis',u32(hulls,j*80+76),u32(hulls,j*80+72),20)
    for i in range(3):
        root_array(520+i*4,f'runtime/smodelVis/{i}','u8',smodel_count,1,runtime=True)
        root_array(532+i*4,f'runtime/surfaceVis/{i}','u8',dpvs[1],1,runtime=True)
    sorted_indices=root_array(544,'dpvs/sortedSurfaces','u16',dpvs[1]+dpvs[2],2)
    if sorted_indices and any(x[0]>=surfaces for x in struct.iter_unpack('<H',sorted_indices)):raise ExportError('Sorted surface outside world')
    instances=root_array(548,'dpvs/smodelInsts','GfxStaticModelInst',smodel_count,36)
    surface_data=root_array(552,'dpvs/surfaces','GfxSurface',surfaces,24,[16])
    surface_bounds=root_array(556,'dpvs/surfaceBounds','Bounds',surfaces,24)
    converted=bytearray()
    for i in range(surfaces):
        g.asset('dpvs/surfaces',i,16,'material',u32(surface_data,i*24+16))
        low,high=bounds(surface_bounds,i*24)
        converted+=convert_surface(surface_data[i*24:(i+1)*24],surface_bounds[i*24:(i+1)*24])
    g.conversion('surfaces','IW3_GfxSurface',converted,48)
    draws=root_array(560,'dpvs/smodelDraws','GfxStaticModelDrawInst',smodel_count,76,[52])
    converted_draws=bytearray();converted_instances=bytearray();skins=set()
    for i in range(smodel_count):
        row=draws[i*76:(i+1)*76];g.asset('dpvs/smodelDraws',i,52,'xmodel',u32(row,52))
        low,high=bounds(instances,i*36);skins.add(row[63])
        if not all(math.isfinite(x) and abs(x)<=1e7 for x in struct.unpack_from('<13f',row)):raise ExportError('Invalid static-model placement')
        cull,lighting=struct.unpack_from('<2H',row,56)
        draw_record,instance_record=convert_model(row,instances[i*36:(i+1)*36])
        converted_draws+=draw_record
        converted_instances+=instance_record
    g.conversion('smodelDraws','IW3_GfxStaticModelDrawInst',converted_draws,76)
    g.conversion('smodelInsts','IW3_GfxStaticModelInst',converted_instances,28)
    root_array(564,'runtime/surfaceDrawKeys','GfxDrawSurf',surfaces,8,runtime=True)
    root_array(568,'runtime/sunShadowBits','u32',dpvs[12],4,runtime=True)
    for i in range(2):
        root_array(592+i*4,f'runtime/dynCellBits/{i}','u32',dyn[i]*cell_count,4,runtime=True)
        for j in range(3):root_array(600+i*12+j*4,f'runtime/dynVis/{i}/{j}','u8',32*dyn[i],1,runtime=True)
    root_array(632,'heroOnlyLights','GfxHeroOnlyLight',u32(w,628),64)
    if skies!=1:g.blockers.append('IW3 supports one sky; multi-sky behavior requires adaptation')
    if draw[4]:g.blockers.append('Reflection probe references require explicit resolution to IW3 probe slots')
    if lg[1]:g.blockers.append('Light grid useSkyForLowZ has no IW3 field')
    if skins-{0}:g.blockers.append('Nonzero static-model firstMtlSkinIndex requires material-skin adaptation')
    if u32(w,628):g.blockers.append('Hero-only lighting is not represented by IW3 GfxWorld')
    if w[636]:g.blockers.append('IW5 fogTypesAllowed requires explicit renderer behavior mapping')
    g.blockers.extend(['IW5 opaque/trans/shadow DPVS partitions require verified IW3 lit/decal classification', 'IW5 surface draw keys require native IW3 key reconstruction', 'Primary lights and sun parsing require matching converted ComWorld', 'Referenced world materials, images and static models must be converted and registered', 'Full native pointer fixup / asset registration stage is not yet implemented'])
    metadata={'format':'IW5_WORLD_GRAPH_1','map':map_name,'geometry':geometry,'cellCount':cell_count,'staticModelCount':smodel_count,'reflectionProbeCount':draw[0],'lightmapCount':draw[7],'primaryLightCount':primary_count,'heroOnlyLightCount':u32(w,628),'fogTypesAllowed':w[636],'dpvsPartitions':list(dpvs[3:11]),'assets':{key:sorted(value) for key,value in sorted(g.assets.items())},'registrationReady':False,'blockers':g.blockers,'nodes':{},'convertedRecords':{}}
    for name,node in g.nodes.items():metadata['nodes'][name]={key:value for key,value in node.items() if key!='data'}|{'sha256':hashlib.sha256(node['data']).hexdigest(),'path':f'source/{name}.bin'}
    for name,node in g.conversions.items():metadata['convertedRecords'][name]={key:value for key,value in node.items() if key!='data'}|{'sha256':hashlib.sha256(node['data']).hexdigest(),'path':f'iw3-records/{name}.bin'}
    return g,metadata

def load_capture(path):
    data=path.read_bytes();regions=[];at=0;total=0
    while at<len(data):
        if len(data)-at<12:raise ExportError('Truncated capture header')
        base,size=struct.unpack_from('<QI',data,at);at+=12;total+=size
        if not size or size>128<<20 or total>MAX_GRAPH or at+size>len(data):raise ExportError('Invalid capture extent')
        regions.append((base,data[at:at+size]));at+=size
    return regions

def write_archive(graph,metadata,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as stream, zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('manifest.json',json.dumps(metadata,indent=2))
        for name,node in graph.nodes.items():archive.writestr(f'source/{name}.bin',node['data'])
        for name,node in graph.conversions.items():archive.writestr(f'iw3-records/{name}.bin',node['data'])

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture',type=Path,required=True);parser.add_argument('--address',type=lambda value:int(value,0),required=True)
    parser.add_argument('--map',required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    repository=Path(__file__).resolve().parents[2]
    if args.output.resolve().is_relative_to(repository):parser.error('Original world data must stay outside the repository')
    graph,metadata=export_world(load_capture(args.capture),args.address,args.map)
    write_archive(graph,metadata,args.output)
    print(json.dumps({key:metadata[key] for key in ['geometry','staticModelCount','cellCount','registrationReady','blockers']},indent=2))

if __name__=='__main__':main()
