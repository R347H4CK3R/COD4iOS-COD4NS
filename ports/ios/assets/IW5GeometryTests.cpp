#include "IW5Geometry.hpp"
#include <cassert>
#include <cmath>
#include <cstring>
#include <limits>
using namespace kisakcod::assets;
using Bytes=std::vector<std::uint8_t>;
static void put(Bytes& b,std::size_t p,std::uint32_t v) {for(int i=0;i<4;++i)b.at(p+i)=std::uint8_t(v>>(i*8));}
static void number(Bytes& b,std::size_t p,float v) {std::uint32_t x;std::memcpy(&x,&v,4);put(b,p,x);}
static Bytes fixture() {
 Bytes b(32+3*44+6+16);std::memcpy(b.data(),"IW5GEO1\0",8);
 put(b,8,1);put(b,12,3);put(b,16,3);put(b,20,1);put(b,24,44);put(b,28,16);
 number(b,32,1);number(b,32+44+4,2);number(b,32+88+8,3);
 for(int i=0;i<3;++i){b[32+i*44+16]=10;b[32+i*44+17]=20;b[32+i*44+18]=30;b[32+i*44+36]=127;b[32+i*44+37]=127;b[32+i*44+38]=254;}
 b[32+132+2]=1;b[32+132+4]=2;
 const auto s=32+132+6;put(b,s+4,0);b[s+8]=3;b[s+10]=1;put(b,s+12,0);return b;
}
template<class F> static void rejected(F f) {bool failed=false;try{f();}catch(const BspError&){failed=true;}assert(failed);}
int main() {
 const auto good=fixture();const auto mesh=loadIW5Geometry(good);
 assert(mesh.vertices.size()==3 && mesh.indices==std::vector<std::uint32_t>({0,1,2}) && mesh.surfaceCount==1);
 assert(mesh.minBounds[0]==0 && mesh.maxBounds[0]==1 && mesh.maxBounds[1]==2 && mesh.maxBounds[2]==3);
 assert(std::abs(mesh.vertices[0].color[0]-30.f/255)<.001f);
 for(std::size_t n=0;n<good.size();++n) rejected([&]{loadIW5Geometry(Bytes(good.begin(),good.begin()+n));});
 auto b=good;b.push_back(0);rejected([&]{loadIW5Geometry(b);});
 b=good;put(b,12,0xffffffff);rejected([&]{loadIW5Geometry(b);});
 b=good;put(b,24,48);rejected([&]{loadIW5Geometry(b);});
 b=good;number(b,32,std::numeric_limits<float>::quiet_NaN());rejected([&]{loadIW5Geometry(b);});
 b=good;number(b,32,std::numeric_limits<float>::infinity());rejected([&]{loadIW5Geometry(b);});
 b=good;number(b,32,1e8f);rejected([&]{loadIW5Geometry(b);});
 b=good;b[32+132]=3;rejected([&]{loadIW5Geometry(b);});
 b=good;put(b,32+132+6+4,2);rejected([&]{loadIW5Geometry(b);});
 b=good;put(b,32+132+6+12,1);rejected([&]{loadIW5Geometry(b);});
 BspLoadLimits limits;limits.maxVertices=2;rejected([&]{loadIW5Geometry(good,limits);});
 limits={};limits.maxFileBytes=good.size()-1;rejected([&]{loadIW5Geometry(good,limits);});
}
