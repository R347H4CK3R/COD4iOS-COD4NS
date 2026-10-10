#!/usr/bin/env python3
"""Instantiate production adapter with actual stock native engine structures."""
from pathlib import Path
import os,shlex,shutil,subprocess,tempfile,sys
root=Path(__file__).resolve().parents[2]
def structure(path,name):
    source=(root/path).read_text();start=source.index('struct '+name) if name!='cbrush_t' else source.index('struct __declspec(align(16)) cbrush_t')
    at=source.index('{',start);depth=1;end=at+1
    while depth:
        depth+=(source[end]=='{')-(source[end]=='}');end+=1
    result=source[start:end]+';\n'
    return result.replace('__declspec(align(16))','alignas(16)').replace('unsigned __int8','uint8_t').replace('__int16','int16_t')
code=r'''
#include <cassert>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <iterator>
#include <limits>
'''+structure('src/universal/com_math.h','cplane_s')+''.join(structure('src/xanim/xanim.h',name) for name in ('dmaterial_t','cbrushside_t','cbrush_t'))+r'''
#include "ports/ios/assets/IW5ClipBrushAdapter.hpp"
using namespace kisakcod::assets;
using Bytes=std::vector<uint8_t>;
void put(Bytes& b,size_t p,uint32_t x){for(unsigned i=0;i<4;++i)b.at(p+i)=uint8_t(x>>(i*8));}
void real(Bytes& b,size_t p,float f){uint32_t x;memcpy(&x,&f,4);put(b,p,x);}
auto convert(const Bytes& b){return convertIW5Brushes<cplane_s,cbrushside_t,cbrush_t,dmaterial_t>(b);}
Bytes fixture(){
 Bytes b(32+20+8+36+24+4+21+72);memcpy(b.data(),"IW5BRSH1",8);
 put(b,8,1);put(b,12,1);put(b,16,1);put(b,20,1);put(b,24,21);put(b,28,1);
 real(b,32,-1);real(b,44,5);b[48]=3;
 put(b,52,0);b[58]=18;b[59]=3;
 b[60]=1;b[62]=42;put(b,64,0);put(b,68,0);
 for(unsigned i=0;i<6;++i){b[84+i]=i*3;b[90+i]=3;}
 real(b,96,1);real(b,100,2);real(b,104,3);real(b,108,4);real(b,112,5);real(b,116,6);
 put(b,120,0x2000001);
 for(unsigned i=0;i<21;++i)b[124+i]=i%7;
 memcpy(b.data()+145,"stone",6);put(b,209,0x400);put(b,213,0x2000001);
 return b;
}
template<class F>void rejects(F f){bool error=false;try{f();}catch(const IW5BrushError&){error=true;}assert(error);}
int main(int argc,char** argv){
 const auto b=fixture();auto graph=convert(b);
 assert(graph.planes.size()==1 && graph.sides.size()==1 && graph.brushes.size()==1);
 assert(graph.sides[0].plane==graph.planes.data() && graph.planes[0].signbits==1);
 assert(graph.brushes[0].sides==graph.sides.data() && graph.brushes[0].baseAdjacentSide==graph.edges.data());
 assert(graph.brushes[0].mins[0]==-3 && graph.brushes[0].maxs[2]==9 && graph.brushes[0].contents==0x2000001);
 assert(graph.brushes[0].firstAdjacentSideOffsets[1][2]==15 && graph.sides[0].firstAdjacentSideOffset==18);
 assert(graph.brushes[0].edgeCount[0][0]==3 && graph.glassPieceIndices[0]==42);
 assert(!strcmp(graph.materials[0].material,"stone") && graph.materials[0].surfaceFlags==0x400);
 auto moved=std::move(graph);assert(moved.brushes[0].sides==moved.sides.data());
 for(size_t n=0;n<b.size();++n)rejects([&]{convert(Bytes(b.begin(),b.begin()+n));});
 auto bad=b;bad.push_back(0);rejects([&]{convert(bad);});
 bad=b;put(bad,12,0xffffffff);rejects([&]{convert(bad);});
 bad=b;put(bad,52,1);rejects([&]{convert(bad);});
 bad=b;put(bad,64,1);rejects([&]{convert(bad);});
 bad=b;put(bad,68,21);rejects([&]{convert(bad);});
 bad=b;bad[124]=7;rejects([&]{convert(bad);});
 bad=b;bad[58]=255;rejects([&]{convert(bad);});
 bad=b;real(bad,108,-1);rejects([&]{convert(bad);});
 bad=b;real(bad,32,std::numeric_limits<float>::quiet_NaN());rejects([&]{convert(bad);});
 bad=b;bad[56]=1;rejects([&]{convert(bad);});
 bad=b;memset(bad.data()+145,'x',64);rejects([&]{convert(bad);});
 bad=b;put(bad,209,29u<<20);rejects([&]{convert(bad);});
 bad=b;bad[48]=0;rejects([&]{convert(bad);});
 if(argc==2){std::ifstream f(argv[1],std::ios::binary);assert(f);Bytes snapshot((std::istreambuf_iterator<char>(f)),{});auto dome=convert(snapshot);
  assert(dome.brushes.size()==7087 && dome.planes.size()==13005 && dome.sides.size()==29440 && dome.edges.size()==134224);
  std::cout<<"Actual Dome converted to stock native types: "<<dome.brushes.size()<<" brushes, "<<dome.materials.size()<<" materials\n";
 }
}
'''
compiler=['xcrun','clang++'] if shutil.which('xcrun') else shlex.split(os.environ.get('CXX','clang++'))
with tempfile.TemporaryDirectory(prefix='iw5-brush-adapter-') as directory:
    folder=Path(directory);source=folder/'test.cpp';binary=folder/('test.exe' if os.name=='nt' else 'test')
    source.write_text(code)
    subprocess.run(compiler+['-std=c++17','-UNDEBUG','-Wall','-Wextra','-Werror','-pedantic','-I',str(root),str(source),'-o',str(binary)],check=True)
    subprocess.run([str(binary)]+sys.argv[1:],check=True)
print('Production IW5 brush adapter: stock structs, pointer ownership, bounds, adjacency and malformed inputs passed')
