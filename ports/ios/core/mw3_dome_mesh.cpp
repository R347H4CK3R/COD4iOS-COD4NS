#include "mw3_dome_mesh.h"
#include <cmath>
#include <cstring>
#include <fstream>
#include <limits>
namespace mw3 {
bool DomeMesh::load(const std::string& path) {
 triangles_.clear();error_.clear();
 std::ifstream f(path,std::ios::binary|std::ios::ate);
 if(!f){error_="file missing";return false;}
 const auto bytes=f.tellg();
 if(bytes<24){error_="truncated header";return false;}
 f.seekg(0);
 char magic[8];
 std::uint64_t vertex_count=0,triangle_count=0;
 f.read(magic,8);f.read(reinterpret_cast<char*>(&vertex_count),8);
 f.read(reinterpret_cast<char*>(&triangle_count),8);
 if(!f || std::memcmp(magic,"DOMMESH1",8)!=0){error_="invalid magic";return false;}
 if(vertex_count==0 || triangle_count==0 || triangle_count>1000000){
  error_="invalid dimensions";return false;
 }
 if(static_cast<std::uint64_t>(bytes)!=24+triangle_count*9*4){
  error_="unexpected file length";return false;
 }
 triangles_.resize(static_cast<std::size_t>(triangle_count));
 for(auto& tri:triangles_) {
  f.read(reinterpret_cast<char*>(&tri),sizeof tri);
  if(!f || !std::isfinite(tri.a.x)||!std::isfinite(tri.a.y)||!std::isfinite(tri.a.z)||
    !std::isfinite(tri.b.x)||!std::isfinite(tri.b.y)||!std::isfinite(tri.b.z)||
    !std::isfinite(tri.c.x)||!std::isfinite(tri.c.y)||!std::isfinite(tri.c.z)){
   triangles_.clear();error_="invalid triangle data";return false;
  }
 }
 return true;
}
}
