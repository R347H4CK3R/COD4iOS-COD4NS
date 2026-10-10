#pragma once
// Converts the complete decoded IW5 brush subgraph into the caller's actual
// IW3 native structures. No reduced render-mesh substitution or registration.
// The owner must outlive every clipmap pointer referencing these arrays.
#include <cmath>
#include <cstdint>
#include <cstring>
#include <stdexcept>
#include <utility>
#include <vector>

namespace kisakcod::assets {
class IW5BrushError:public std::runtime_error {
public:explicit IW5BrushError(const char* text):std::runtime_error(text){}
};
template<class Plane,class Side,class Brush,class Material>
struct IW5BrushGraph {
    std::vector<Plane> planes;
    std::vector<Side> sides;
    std::vector<Brush> brushes;
    std::vector<Material> materials;
    std::vector<std::uint8_t> edges;
    // IW3 cbrush_t has no glass field. Retain associations for later glass-map
    // conversion rather than silently discarding their source semantics.
    std::vector<std::uint16_t> glassPieceIndices;
    IW5BrushGraph()=default;
    IW5BrushGraph(const IW5BrushGraph&)=delete;
    IW5BrushGraph& operator=(const IW5BrushGraph&)=delete;
    IW5BrushGraph(IW5BrushGraph&&)=default;
    IW5BrushGraph& operator=(IW5BrushGraph&&)=default;
};
namespace iw5_brush_detail {
[[noreturn]] inline void fail(const char* reason){throw IW5BrushError(reason);}
struct Reader {
    const std::vector<std::uint8_t>& data;
    std::uint16_t u16(std::size_t p)const{return data[p]|(std::uint16_t(data[p+1])<<8);}
    std::uint32_t u32(std::size_t p)const{return u16(p)|(std::uint32_t(u16(p+2))<<16);}
    std::int32_t i32(std::size_t p)const{const auto bits=u32(p);std::int32_t value;std::memcpy(&value,&bits,4);return value;}
    float f32(std::size_t p)const{const auto bits=u32(p);float value;std::memcpy(&value,&bits,4);
        if(!std::isfinite(value)||std::abs(value)>1e7f)fail("Invalid IW5 brush coordinate");return value;}
};
inline void range(std::size_t first,std::size_t count,std::size_t size){
    if(first>size||count>size-first)fail("IW5 brush array reference out of bounds");
}
}

template<class Plane,class Side,class Brush,class Material>
IW5BrushGraph<Plane,Side,Brush,Material> convertIW5Brushes(const std::vector<std::uint8_t>& bytes) {
    using namespace iw5_brush_detail;
    if(bytes.size()<32||bytes.size()>64u*1024u*1024u||std::memcmp(bytes.data(),"IW5BRSH1",8))fail("Invalid IW5 brush snapshot header or budget");
    const Reader r{bytes};
    if(r.u32(8)!=1)fail("Unsupported IW5 brush snapshot version");
    const std::size_t pc=r.u32(12),sc=r.u32(16),bc=r.u32(20),ec=r.u32(24),mc=r.u32(28);
    if(!pc||pc>1'000'000||sc>1'000'000||!bc||bc>65535||ec>8'000'000||!mc||mc>65535)fail("IW5 brush count budget exceeded");
    // Hard caps bound all arithmetic on 32-bit and 64-bit hosts before reads.
    const std::size_t sidesAt=32+pc*20,brushesAt=sidesAt+sc*8,boundsAt=brushesAt+bc*36,
                      contentsAt=boundsAt+bc*24,edgesAt=contentsAt+bc*4,materialsAt=edgesAt+ec;
    if(materialsAt+mc*72!=bytes.size())fail("Truncated IW5 brush records or trailing data");
    IW5BrushGraph<Plane,Side,Brush,Material> graph;
    graph.planes.resize(pc);graph.sides.resize(sc);graph.brushes.resize(bc);graph.materials.resize(mc);
    graph.edges.assign(bytes.begin()+edgesAt,bytes.begin()+materialsAt);graph.glassPieceIndices.resize(bc);
    for(std::size_t i=0;i<mc;++i){
        const auto at=materialsAt+i*72;
        const void* terminator=std::memchr(bytes.data()+at,0,64);
        if(!terminator||bytes[at]==0)fail("IW5 material name does not fit native field");
        auto& material=graph.materials[i];
        static_assert(sizeof(material.material)==64,"Expected native IW3 material name field");
        std::memcpy(material.material,bytes.data()+at,64);
        material.surfaceFlags=r.i32(at+64);material.contentFlags=r.i32(at+68);
        // IW3/IW5 have identical surface type indices 0..28; IW5's additional
        // riot-shield/slush types have no native equivalent and must not alias.
        if(((r.u32(at+64)>>20)&31u)>28)fail("Unsupported IW5 surface type for native IW3");
    }
    for(std::size_t i=0;i<pc;++i){
        const auto at=32+i*20;auto& plane=graph.planes[i];float length=0;unsigned type=3,signbits=0;
        for(unsigned axis=0;axis<3;++axis){
            plane.normal[axis]=r.f32(at+axis*4);length+=plane.normal[axis]*plane.normal[axis];
            if(plane.normal[axis]<0)signbits|=1u<<axis;
        }
        if(length<.25f||length>2.25f||bytes[at+16]>3)fail("Invalid IW5 brush plane normal or type");
        for(unsigned axis=0;axis<3;++axis)
            if(plane.normal[axis]==1 && plane.normal[(axis+1)%3]==0 && plane.normal[(axis+2)%3]==0)type=axis;
        if(bytes[at+16]!=type)fail("IW5 brush plane type disagrees with its normal");
        plane.dist=r.f32(at+12);plane.type=static_cast<std::uint8_t>(type);plane.signbits=static_cast<std::uint8_t>(signbits);
    }
    for(std::size_t i=0;i<sc;++i){
        const auto at=sidesAt+i*8;const auto plane=r.u32(at);const auto material=r.u16(at+4);
        range(plane,1,pc);range(material,1,mc);auto& side=graph.sides[i];
        side.plane=&graph.planes[plane];side.materialNum=material;
        side.firstAdjacentSideOffset=bytes[at+6];side.edgeCount=bytes[at+7];
    }
    for(std::size_t i=0;i<bc;++i){
        const auto at=brushesAt+i*36;auto& brush=graph.brushes[i];
        const std::size_t count=r.u16(at),first=r.u32(at+4),base=r.u32(at+8);
        range(first,count,sc);
        brush.numsides=static_cast<std::uint32_t>(count);brush.sides=count ? &graph.sides[first]:nullptr;
        graph.glassPieceIndices[i]=r.u16(at+2);brush.contents=r.i32(contentsAt+i*4);
        if(base!=0xffffffffu){range(base,1,ec);brush.baseAdjacentSide=&graph.edges[base];}
        for(unsigned axis=0;axis<3;++axis){
            const float midpoint=r.f32(boundsAt+i*24+axis*4),half=r.f32(boundsAt+i*24+12+axis*4);
            if(half<0||std::abs(midpoint-half)>1e7f||std::abs(midpoint+half)>1e7f)fail("Invalid IW5 brush bounds");
            brush.mins[axis]=midpoint-half;brush.maxs[axis]=midpoint+half;
        }
        auto validateEdges=[&](std::size_t offset,std::size_t num){
            if(!num)return;
            if(base==0xffffffffu)fail("IW5 brush face has adjacency but no edge array");
            range(base,offset,ec);range(base+offset,num,ec);
            for(std::size_t j=0;j<num;++j)if(graph.edges[base+offset+j]>=count+6)fail("IW5 adjacent face index out of bounds");
        };
        for(unsigned axial=0;axial<6;++axial){
            const auto material=r.u16(at+12+axial*2);range(material,1,mc);
            if(material>32767)fail("IW5 axial material cannot fit native signed index");
            const unsigned end=axial/3,axis=axial%3;
            brush.axialMaterialNum[end][axis]=static_cast<std::int16_t>(material);
            brush.firstAdjacentSideOffsets[end][axis]=bytes[at+24+axial];brush.edgeCount[end][axis]=bytes[at+30+axial];
            validateEdges(bytes[at+24+axial],bytes[at+30+axial]);
        }
        for(std::size_t side=first;side<first+count;++side)
            validateEdges(graph.sides[side].firstAdjacentSideOffset,graph.sides[side].edgeCount);
    }
    return graph;
}
} // namespace kisakcod::assets
