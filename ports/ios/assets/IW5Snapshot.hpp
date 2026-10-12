// SPDX-License-Identifier: GPL-3.0-only
#pragma once
#include "BspLoader.hpp"
namespace kisakcod::assets {
// Geometry preview only: IW5GEO1 is a research export, not a retail fastfile.
// UV/material data is not represented by BspMesh and is not rendered here.
// Invalid files/limits throw BspError; allocation errors propagate normally.
BspMesh loadIW5Snapshot(const std::vector<std::uint8_t>& bytes, const BspLoadLimits& limits = {});
BspMesh loadIW5Snapshot(const std::string& path, const BspLoadLimits& limits = {});
}
