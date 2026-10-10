#include "IW5Geometry.hpp"
#include <algorithm>
#include <cmath>
#include <cstring>
#include <fstream>
#include <limits>
namespace kisakcod::assets {
namespace {
[[noreturn]] void fail(const char* reason){throw BspError(std::string("IW5 geometry: ")+reason);}
struct Reader {
 const std::vector<std::uint8_t>& bytes;
 std::uint16_t u16(std::size_t p)const {return std::uint16_t(bytes[p])|(std::uint16_t(bytes[p+1])<<8);}
 std::uint32_t u32(std::size_t p)const {return u16(p)|(std::uint32_t(u16(p+2))<<16);}
 float f32(std::size_t p)const {const auto bits=u32(p);float v;std::memcpy(&v,&bits,4);if(!std::isfinite(v)||std::abs(v)>1e7f)fail("invalid vertex position");return v;}
};
}
BspMesh loadIW5Geometry(const std::vector<std::uint8_t>& bytes,const BspLoadLimits& requested) {
 const BspLoadLimits defaults;
 const auto fileLimit=std::min(requested.maxFileBytes,defaults.maxFileBytes);
 if(bytes.size()<32 || bytes.size()>fileLimit)fail("truncated header or file budget exceeded");
 if(std::memcmp(bytes.data(),"IW5GEO1\0",8))fail("expected an IW5GEO1 snapshot");
 const Reader r{bytes};
 if(r.u32(8)!=1 || r.u32(24)!=44 || r.u32(28)!=16)fail("unsupported snapshot version or record strides");
 const std::size_t vc=r.u32(12),ic=r.u32(16),sc=r.u32(20);
 if(!vc || vc>std::min(requested.maxVertices,defaults.maxVertices) || !ic || ic%3 || ic>std::min(requested.maxIndices,defaults.maxIndices) || !sc || sc>std::min(requested.maxSurfaces,defaults.maxSurfaces))fail("invalid geometry counts or budget exceeded");
 // Hard count caps above keep all arithmetic bounded even on a 32-bit host.
 const std::size_t indices=32+vc*44,surfaces=indices+ic*2;
 if(surfaces+sc*16!=bytes.size())fail("truncated records or trailing data");
 BspMesh mesh;mesh.surfaceCount=static_cast<std::uint32_t>(sc);mesh.vertices.reserve(vc);mesh.indices.reserve(ic);
 mesh.minBounds.fill(std::numeric_limits<float>::max());mesh.maxBounds.fill(std::numeric_limits<float>::lowest());
 for(std::size_t i=0;i<vc;++i) {
  const auto p=32+i*44;BspVertex v;
  for(int axis=0;axis<3;++axis)v.position[axis]=r.f32(p+axis*4);
  const float scale=(bytes[p+39]+192.f)/32385.f;
  for(int axis=0;axis<3;++axis)v.normal[axis]=(bytes[p+36+axis]-127.f)*scale;
  v.color={bytes[p+18]/255.f,bytes[p+17]/255.f,bytes[p+16]/255.f,1.f};mesh.vertices.push_back(v);
 }
 for(std::size_t i=0;i<sc;++i) {
  const auto p=surfaces+i*16;const std::size_t first=r.u32(p+4),count=r.u16(p+8),num=std::size_t(r.u16(p+10))*3,start=r.u32(p+12);
  if(!count || !num || first>vc || count>vc-first || start>ic || num>ic-start)fail("surface exceeds vertex or index arrays");
  if(num>std::min(requested.maxIndices,defaults.maxIndices)-mesh.indices.size())fail("expanded index budget exceeded");
  for(std::size_t j=0;j<num;++j) {
   const auto local=r.u16(indices+(start+j)*2);if(local>=count)fail("surface-local index out of bounds");
   const auto absolute=static_cast<std::uint32_t>(first+local);mesh.indices.push_back(absolute);
   for(int axis=0;axis<3;++axis){const float value=mesh.vertices[absolute].position[axis];mesh.minBounds[axis]=std::min(mesh.minBounds[axis],value);mesh.maxBounds[axis]=std::max(mesh.maxBounds[axis],value);}
  }
 }
 return mesh;
}
BspMesh loadIW5Geometry(const std::string& path,const BspLoadLimits& limits) {
 std::ifstream file(path,std::ios::binary|std::ios::ate);if(!file)fail("cannot open snapshot");
 const auto end=file.tellg();if(end<0 || static_cast<std::uint64_t>(end)>std::min(limits.maxFileBytes,BspLoadLimits{}.maxFileBytes))fail("file budget exceeded");
 std::vector<std::uint8_t> bytes(static_cast<std::size_t>(end));file.seekg(0);
 if(!bytes.empty() && !file.read(reinterpret_cast<char*>(bytes.data()),static_cast<std::streamsize>(bytes.size())))fail("cannot read complete snapshot");
 return loadIW5Geometry(bytes,limits);
}
}
