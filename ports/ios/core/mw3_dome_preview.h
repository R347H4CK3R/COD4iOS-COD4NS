#pragma once
#include "../assets/BspLoader.hpp"
#include "mw3_dome_mesh.h"
namespace mw3 {
// Rendering preview only: no BSP collision or native map entities.
kisakcod::assets::BspMesh makeDomePreviewMesh(const DomeMesh& source);
}
