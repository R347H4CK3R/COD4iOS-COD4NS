#include "../core/mw3_dome_mesh.h"
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <fstream>
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
 std::remove(path);
 assert(!mesh.load(path));assert(mesh.triangle_count()==0);
}
