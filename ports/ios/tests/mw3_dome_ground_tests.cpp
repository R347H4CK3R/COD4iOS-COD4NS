#include "../core/mw3_dome_mesh.h"
#include "../core/mw3_dome_ground.h"
#include <cassert>
#include <cstdio>
#include <cstdint>
int main(){
 const char* p="ground_query_test.bin";
 FILE* f=std::fopen(p,"wb");assert(f);
 const std::uint64_t vertices=3,triangles=1;
 const float xyz[]={0,0,10, 10,0,10, 0,10,10};
 assert(std::fwrite("DOMMESH1",1,8,f)==8);
 assert(std::fwrite(&vertices,8,1,f)==1);
 assert(std::fwrite(&triangles,8,1,f)==1);
 assert(std::fwrite(xyz,sizeof(float),9,f)==9);
 std::fclose(f);
 mw3::DomeMesh m;assert(m.load(p));std::remove(p);
 float z=0;assert(mw3::domeGroundHeight(m,2,2,50,z));assert(z==10);
 assert(!mw3::domeGroundHeight(m,20,20,50,z));
 assert(!mw3::domeGroundHeight(m,2,2,5,z));
}
