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
 if(!f){error_="invalid header";return false;}
 if(std::memcmp(magic,"MW3MESH2",8)==0) {
  std::uint64_t material_count=0;
  f.read(reinterpret_cast<char*>(&material_count),8);
  if(!f || !vertex_count || !triangle_count || triangle_count>1000000 ||
     material_count==0 || material_count>100000 ||
     static_cast<std::uint64_t>(bytes)!=32+64*triangle_count){
   error_="invalid MW3MESH2 dimensions";return false;
  }
  triangles_.reserve(static_cast<std::size_t>(triangle_count));
  for(std::uint64_t i=0;i<triangle_count;++i){
   DomeTriangle t{};
   DomeVertex* dst[3]={&t.a,&t.b,&t.c};
   for(auto* v:dst){
    float record[5]{};
    f.read(reinterpret_cast<char*>(record),sizeof record);
    if(!f || !std::isfinite(record[0]) || !std::isfinite(record[1]) ||
       !std::isfinite(record[2]) || !std::isfinite(record[3]) ||
       !std::isfinite(record[4])){
     triangles_.clear();error_="nonfinite textured vertex";return false;
    }
    *v={record[0],record[1],record[2]};
   }
   std::uint32_t material=0;
   f.read(reinterpret_cast<char*>(&material),4);
   if(!f || material>=material_count){
    triangles_.clear();error_="invalid textured material index";return false;
   }
   triangles_.push_back(t);
  }
  return true;
 }
 if(std::memcmp(magic,"DOMMESH1",8)!=0){error_="invalid magic";return false;}
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
