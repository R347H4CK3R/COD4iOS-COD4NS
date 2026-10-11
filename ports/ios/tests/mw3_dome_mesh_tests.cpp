#include "../core/mw3_dome_mesh.h"
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <fstream>
#include <limits>
int main() {
 const char* path="test_dome_mesh.bin";
 {
  std::ofstream f(path,std::ios::binary);
  f.write("DOMMESH1",8);
  std::uint64_t n=3,t=1;
  f.write(reinterpret_cast<const char*>(&n),8);
  f.write(reinterpret_cast<const char*>(&t),8);
  const float v[9]={0,0,0,1,0,0,0,1,0};
  f.write(reinterpret_cast<const char*>(v),sizeof v);
 }
 mw3::DomeMesh mesh;
 assert(mesh.load(path));assert(mesh.triangle_count()==1);
 {
  std::ofstream f(path,std::ios::binary);
  f.write("MW3MESH2",8);
  std::uint64_t n=3,t=1,m=2;
  f.write(reinterpret_cast<const char*>(&n),8);
  f.write(reinterpret_cast<const char*>(&t),8);
  f.write(reinterpret_cast<const char*>(&m),8);
  const float vert[15]={0,0,0,0,0, 1,0,0,1,0, 0,1,0,0,1};
  f.write(reinterpret_cast<const char*>(vert),sizeof vert);
  std::uint32_t material=1;f.write(reinterpret_cast<const char*>(&material),4);
 }
 assert(mesh.load(path));assert(mesh.triangle_count()==1);
 {
  std::fstream f(path,std::ios::binary|std::ios::in|std::ios::out);
  f.seekp(32+60);
  std::uint32_t bad=3;f.write(reinterpret_cast<const char*>(&bad),4);
 }
 assert(!mesh.load(path));assert(mesh.triangle_count()==0);
 std::remove(path);
 assert(!mesh.load(path));assert(mesh.triangle_count()==0);
}
