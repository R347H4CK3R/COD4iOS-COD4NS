#pragma once
#include "mw3_dome_mesh.h"
namespace mw3 {
// Vertical downward cast against upward-facing triangles only.
// This is a terrain-support query, not complete FPS collision.
bool domeGroundHeight(const DomeMesh& mesh,float x,float y,float startZ,float& hitZ);
}
