#!/usr/bin/env python3
"""Windows research exporter for decoded IW5 GfxWorld geometry in OAT 0.33 x86.

Launches its own read-only Unlinker --list child. The unread stdout pipe keeps
large map listings blocked after zone loading, while ReadProcessMemory copies
bounded readable regions. No injection, game process access or file mutation.
Fails if the process exits, layouts differ or multiple valid worlds exist.
"""
import argparse, ctypes, json, math, os, re, struct, subprocess, time
from pathlib import Path

MAX_MEMORY=512<<20
MAX_VERTICES=1_000_000
MAX_INDICES=6_000_000
MAX_SURFACES=65_536
class ExportError(RuntimeError): pass

def read(regions,address,size):
    if address<=0 or size<0 or address+size>0x100000000: raise ExportError('Invalid x86 pointer range')
    for base,data in regions:
        if base<=address and address+size<=base+len(data):
            return data[address-base:address-base+size]
    raise ExportError('Decoded array lies outside captured readable memory')

def world_geometry(regions,address,base_name):
    world=read(regions,address,640)
    name_ptr,base_ptr=struct.unpack_from('<II',world)
    expected=('maps/mp/'+base_name+'.d3dbsp').encode()+b'\0'
    if read(regions,name_ptr,len(expected))!=expected or read(regions,base_ptr,len(base_name)+1)!=base_name.encode()+b'\0':
        raise ExportError('World identity does not match requested map')
    surfaces_count=struct.unpack_from('<I',world,16)[0]
    vertices_count,vertices_ptr=struct.unpack_from('<II',world,132)
    indices_count,indices_ptr=struct.unpack_from('<II',world,156)
    surfaces_ptr=struct.unpack_from('<I',world,552)[0]
    if not (0<vertices_count<=MAX_VERTICES and 0<indices_count<=MAX_INDICES and indices_count%3==0 and 0<surfaces_count<=MAX_SURFACES):
        raise ExportError('Geometry count limits exceeded')
    vertices=read(regions,vertices_ptr,vertices_count*44)
    indices=read(regions,indices_ptr,indices_count*2)
    surfaces=read(regions,surfaces_ptr,surfaces_count*24)
    positions=[]
    for i in range(vertices_count):
        xyz=struct.unpack_from('<3f',vertices,i*44)
        if not all(math.isfinite(x) and abs(x)<=1e7 for x in xyz): raise ExportError('Invalid vertex position')
        positions.append(xyz)
    output_surfaces=bytearray(); used=0; bounds_min=[math.inf]*3; bounds_max=[-math.inf]*3
    for i in range(surfaces_count):
        _,first,count,triangles,start=struct.unpack_from('<IIHHI',surfaces,i*24)
        n=triangles*3
        if not count or not n or first+count>vertices_count or start+n>indices_count: raise ExportError('Surface geometry range is invalid')
        used+=n
        if used>MAX_INDICES: raise ExportError('Expanded surface indices exceed budget')
        for j in range(n):
            local=struct.unpack_from('<H',indices,(start+j)*2)[0]
            if local>=count: raise ExportError('Surface-local vertex index is out of bounds')
            for axis,value in enumerate(positions[first+local]):
                bounds_min[axis]=min(bounds_min[axis],value);bounds_max[axis]=max(bounds_max[axis],value)
        # No material or process pointers leave the tool.
        output_surfaces+=surfaces[i*24:i*24+16]
    header=b'IW5GEO1\0'+struct.pack('<6I',1,vertices_count,indices_count,surfaces_count,44,16)
    return header+vertices+indices+output_surfaces,dict(map=base_name,vertices=vertices_count,triangles=used//3,surfaces=surfaces_count,minBounds=bounds_min,maxBounds=bounds_max)

def find_world(regions,base_name):
    needle=('maps/mp/'+base_name+'.d3dbsp').encode()+b'\0'
    name_pointers=[]
    for base,data in regions:
        start=0
        while (at:=data.find(needle,start))!=-1:
            name_pointers.append(base+at);start=at+1
            if len(name_pointers)>4096: raise ExportError('Too many world-name aliases')
    matches={}; attempts=0
    for pointer in name_pointers:
        needle_pointer=struct.pack('<I',pointer)
        for base,data in regions:
            start=0
            while (at:=data.find(needle_pointer,start))!=-1:
                start=at+1;address=base+at;attempts+=1
                if attempts>100000: raise ExportError('Too many world-record candidates')
                if address%4: continue
                try: result=world_geometry(regions,address,base_name)
                except ExportError: continue
                matches[address]=result
    if len(matches)!=1: raise ExportError(f'Expected one validated IW5 world, found {len(matches)}; only OAT 0.33 x86 layouts are supported')
    return next(iter(matches.values()))

def capture(unlinker,fastfile,wait_seconds):
    if os.name!='nt': raise ExportError('Live OAT capture requires Windows; the exported mesh loader is portable')
    exe=unlinker.read_bytes()
    if len(exe)<64: raise ExportError('Invalid Unlinker executable')
    pe=struct.unpack_from('<I',exe,60)[0]
    if pe+6>len(exe) or exe[pe:pe+4]!=b'PE\0\0' or struct.unpack_from('<H',exe,pe+4)[0]!=0x14c: raise ExportError('Requires an x86 Unlinker executable')
    version=subprocess.run([str(unlinker),'--version'],capture_output=True,text=True,check=True).stdout
    if not re.search(r'\bv?0\.33(?:\.0)?\b',version): raise ExportError('Requires OpenAssetTools Unlinker 0.33')
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    class Region(ctypes.Structure):
        _fields_=[('base',ctypes.c_void_p),('allocation',ctypes.c_void_p),('protection',ctypes.c_uint32),('size',ctypes.c_size_t),('state',ctypes.c_uint32),('access',ctypes.c_uint32),('kind',ctypes.c_uint32)]
    kernel.OpenProcess.argtypes=[ctypes.c_uint32,ctypes.c_int,ctypes.c_uint32];kernel.OpenProcess.restype=ctypes.c_void_p
    kernel.VirtualQueryEx.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.POINTER(Region),ctypes.c_size_t];kernel.VirtualQueryEx.restype=ctypes.c_size_t
    kernel.ReadProcessMemory.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
    kernel.CloseHandle.argtypes=[ctypes.c_void_p]
    process=subprocess.Popen([str(unlinker),'--list',str(fastfile)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    handle=None
    try:
        time.sleep(wait_seconds)
        if process.poll() is not None: raise ExportError('Unlinker exited before capture; map listing must be large enough to block its output pipe')
        handle=kernel.OpenProcess(0x410,False,process.pid)
        if not handle: raise ExportError('Cannot open the tool child for read-only memory access')
        regions=[];address=0;total=0
        while address<0x100000000:
            info=Region()
            if not kernel.VirtualQueryEx(handle,address,ctypes.byref(info),ctypes.sizeof(info)):break
            base=info.base or 0
            if not info.size or base+info.size<=address: raise ExportError('Invalid memory region enumeration')
            address=base+info.size
            if info.state!=0x1000 or info.access&0x101 or info.access&0xff not in (2,4,8,0x20,0x40,0x80):continue
            if info.size>128<<20 or total+info.size>MAX_MEMORY: raise ExportError('Readable child memory exceeds capture budget')
            buffer=ctypes.create_string_buffer(info.size);got=ctypes.c_size_t()
            if kernel.ReadProcessMemory(handle,base,buffer,info.size,ctypes.byref(got)) and got.value==info.size:
                regions.append((base,buffer.raw));total+=info.size
        if process.poll() is not None: raise ExportError('Unlinker exited during capture')
        return regions
    finally:
        if handle:kernel.CloseHandle(handle)
        if process.poll() is None:process.terminate()
        process.wait(timeout=10)
        if process.stdout:process.stdout.close()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--unlinker',required=True,type=Path);parser.add_argument('--fastfile',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path);parser.add_argument('--wait-seconds',type=float,default=7)
    args=parser.parse_args()
    if not 1<=args.wait_seconds<=30:parser.error('wait-seconds must be between 1 and 30')
    base=args.fastfile.stem
    if not re.fullmatch(r'mp_[A-Za-z0-9_]{1,60}',base):parser.error('use the original mp_* map fastfile name')
    if not args.fastfile.is_file():parser.error('fastfile does not exist')
    if args.output.exists():parser.error('output already exists; choose a new output path')
    try:
        mesh,metadata=find_world(capture(args.unlinker.resolve(),args.fastfile.resolve(),args.wait_seconds),base)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        with args.output.open('xb') as file:file.write(mesh)
        print(json.dumps(metadata,indent=2))
    except (ExportError,OSError,subprocess.SubprocessError) as error:parser.exit(1,str(error)+'\n')
if __name__=='__main__':main()
