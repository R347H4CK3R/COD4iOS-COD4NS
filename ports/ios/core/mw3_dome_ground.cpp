#include "mw3_dome_ground.h"
#include <cmath>
#include <algorithm>
namespace mw3 {
bool domeGroundHeight(const DomeMesh& mesh,float x,float y,float startZ,float& hitZ) {
 bool found=false;float best=-INFINITY;
 for(const auto& t:mesh.triangles()){
  const float ax=t.a.x,ay=t.a.y,bx=t.b.x,by=t.b.y,cx=t.c.x,cy=t.c.y;
  const float denom=(by-cy)*(ax-cx)+(cx-bx)*(ay-cy);
  if(!std::isfinite(denom)||std::fabs(denom)<0.00001f)continue;
  const float winding=(bx-ax)*(cy-ay)-(by-ay)*(cx-ax);
  if(winding<=0)continue;
  const float u=((by-cy)*(x-cx)+(cx-bx)*(y-cy))/denom;
  const float v=((cy-ay)*(x-cx)+(ax-cx)*(y-cy))/denom;
  if(u< -0.0001f||v< -0.0001f||u+v>1.0001f)continue;
  const float z=u*t.a.z+v*t.b.z+(1-u-v)*t.c.z;
  if(std::isfinite(z)&&z<=startZ+0.001f&&z>best){best=z;found=true;}
 }
 if(found)hitZ=best;
 return found;
}
}
