#pragma once
#include "BspLoader.hpp"
namespace kisakcod::assets {
// Reads the pointer-free IW5GEO1 snapshot emitted by tools/mw3_maps.
// This is actual IW5 world geometry, not an IW5 fastfile decoder. It omits
// materials, textures, placed models, collision, entities and navigation.
BspMesh loadIW5Geometry(const std::vector<std::uint8_t>& bytes,const BspLoadLimits& limits={});
BspMesh loadIW5Geometry(const std::string& path,const BspLoadLimits& limits={});
}
