#include "mw3_dome_preview.h"
#include <algorithm>
#include <cmath>
#include <limits>
#include <stdexcept>
namespace mw3 {
kisakcod::assets::BspMesh makeDomePreviewMesh(const DomeMesh& source) {
 kisakcod::assets::BspMesh result;
 if(source.triangle_count()==0 || source.triangle_count()>1000000)
  throw std::runtime_error("invalid Dome triangle count");
 result.vertices.reserve(source.triangle_count()*3);
 result.indices.reserve(source.triangle_count()*3);
 result.minBounds.fill(std::numeric_limits<float>::infinity());
 result.maxBounds.fill(-std::numeric_limits<float>::infinity());
 for(const auto& tri:source.triangles()) {
  const auto& a=tri.a;const auto& b=tri.b;const auto& c=tri.c;
  const float ux=b.x-a.x,uy=b.y-a.y,uz=b.z-a.z;
  const float vx=c.x-a.x,vy=c.y-a.y,vz=c.z-a.z;
  float nx=uy*vz-uz*vy,ny=uz*vx-ux*vz,nz=ux*vy-uy*vx;
  const float len=std::sqrt(nx*nx+ny*ny+nz*nz);
  if(!std::isfinite(len))throw std::runtime_error("nonfinite Dome triangle");
  if(len>0){nx/=len;ny/=len;nz/=len;}else{nx=0;ny=0;nz=1;}
  const DomeVertex verts[]={a,b,c};
  for(const auto& v:verts) {
   kisakcod::assets::BspVertex dst;
   dst.position={v.x,v.y,v.z};dst.normal={nx,ny,nz};
   dst.color={0.68f,0.73f,0.78f,1.0f};
   for(int k=0;k<3;k++) {
    result.minBounds[k]=std::min(result.minBounds[k],dst.position[k]);
    result.maxBounds[k]=std::max(result.maxBounds[k],dst.position[k]);
   }
   result.indices.push_back(static_cast<std::uint32_t>(result.vertices.size()));
   result.vertices.push_back(dst);
  }
 }
 result.surfaceCount=static_cast<std::uint32_t>(source.triangle_count());
 return result;
}
}
