// SPDX-License-Identifier: GPL-3.0-only
#include "IW5Snapshot.hpp"
#include <cmath>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iostream>
#include <stdexcept>
using namespace kisakcod::assets;
static unsigned checks;
#define CHECK(x) do { ++checks; if (!(x)) throw std::runtime_error(#x); } while(0)
static void put32(std::vector<std::uint8_t>& b, size_t p, std::uint32_t v) {
    for(unsigned i=0;i<4;++i) b[p+i]=static_cast<std::uint8_t>(v>>(8*i));
}
static void putfloat(std::vector<std::uint8_t>& b, size_t p, float f) {
    std::uint32_t v; std::memcpy(&v,&f,4); put32(b,p,v);
}
static std::vector<std::uint8_t> fixture() {
    std::vector<std::uint8_t> b(186);
    std::memcpy(b.data(),"IW5GEO1",8);
    put32(b,8,1);put32(b,12,3);put32(b,16,3);put32(b,20,1);put32(b,24,44);put32(b,28,16);
    putfloat(b,32,1);putfloat(b,80,2);putfloat(b,128,3);
    for(unsigned i=0;i<3;i++){ b[48+i*44]=10;b[49+i*44]=20;b[50+i*44]=30;b[68+i*44]=127;b[69+i*44]=127;b[70+i*44]=254; }
    b[166]=1;b[168]=2;b[178]=3;b[180]=1;
    return b;
}
template<class F> static void rejects(F f) { bool threw=false; try { f(); } catch(const BspError&) { threw=true; } CHECK(threw); }
int main(int argc,char** argv) {
    const auto b=fixture();auto m=loadIW5Snapshot(b);
    CHECK(m.vertices.size()==3 && m.indices==std::vector<std::uint32_t>({0,1,2}));
    CHECK(m.vertices[0].position[0]==1 && m.vertices[1].position[1]==2 && m.vertices[2].position[2]==3);
    CHECK(std::abs(m.vertices[0].color[0]-30.f/255)<1e-6f);
    CHECK(m.vertices[0].normal[0]==0 && m.vertices[0].normal[2]>0);
    CHECK((m.minBounds==std::array<float,3>({0,0,0})));
    CHECK((m.maxBounds==std::array<float,3>({1,2,3})));
    CHECK(m.surfaceCount==1 && !m.spawn && !m.layered);
    for(size_t n=0;n<b.size();++n) rejects([&]{loadIW5Snapshot(std::vector<std::uint8_t>(b.begin(),b.begin()+n));});
    auto bad=b;bad[164]=3;rejects([&]{loadIW5Snapshot(bad);});
    auto limits=BspLoadLimits{};limits.maxVertices=2;rejects([&]{loadIW5Snapshot(b,limits);});
    limits=BspLoadLimits{};limits.maxFileBytes=185;rejects([&]{loadIW5Snapshot(b,limits);});
    const std::string path="iw5-snapshot-test.tmp";
    {std::ofstream f(path,std::ios::binary);f.write(reinterpret_cast<const char*>(b.data()),b.size());CHECK(bool(f));}
    CHECK(loadIW5Snapshot(path).indices==m.indices);
    rejects([&]{loadIW5Snapshot(path,limits);});
    {std::ofstream f(path,std::ios::binary);f.write("bad",3);}
    rejects([&]{loadIW5Snapshot(path);});
    CHECK(std::remove(path.c_str())==0);rejects([&]{loadIW5Snapshot(path);});
    if(argc==2) { auto real=loadIW5Snapshot(std::string(argv[1])); std::cout<<"Private snapshot: "<<real.vertices.size()<<" vertices, "<<real.indices.size()/3<<" triangles, "<<real.surfaceCount<<" surfaces\n"; }
    std::cout<<checks<<" adapter checks passed\n";
}
