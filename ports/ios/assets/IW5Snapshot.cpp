// SPDX-License-Identifier: GPL-3.0-only
#include "IW5Snapshot.hpp"
#include "iw5geo.h"
#include <algorithm>
#include <fstream>
namespace kisakcod::assets {
namespace {
iw5geo_limits nativeLimits(const BspLoadLimits& limits) {
    auto result=iw5geo_default_limits();
    result.max_file_bytes=std::min(result.max_file_bytes,limits.maxFileBytes);
    result.max_vertices=static_cast<std::uint32_t>(std::min<std::size_t>(result.max_vertices,limits.maxVertices));
    result.max_indices=static_cast<std::uint32_t>(std::min<std::size_t>(result.max_indices,limits.maxIndices));
    result.max_surfaces=static_cast<std::uint32_t>(std::min<std::size_t>(result.max_surfaces,limits.maxSurfaces));
    return result;
}
void checked(iw5geo_status result) {
    if(result!=IW5GEO_OK) throw BspError(std::string("IW5 snapshot: ")+iw5geo_status_string(result));
}
}
BspMesh loadIW5Snapshot(const std::vector<std::uint8_t>& bytes,const BspLoadLimits& limits) {
    auto budget=nativeLimits(limits);
    iw5geo_info info{};
    checked(iw5geo_inspect(bytes.data(),bytes.size(),&budget,&info));
    std::vector<iw5geo_vertex> decoded(info.vertex_count);
    BspMesh mesh;
    mesh.indices.resize(info.index_count);
    checked(iw5geo_decode(bytes.data(),bytes.size(),&budget,decoded.data(),decoded.size(),mesh.indices.data(),mesh.indices.size(),&info));
    mesh.vertices.resize(info.vertex_count);
    for(std::size_t i=0;i<decoded.size();++i) {
        std::copy_n(decoded[i].position,3,mesh.vertices[i].position.begin());
        std::copy_n(decoded[i].normal,3,mesh.vertices[i].normal.begin());
        std::copy_n(decoded[i].color,4,mesh.vertices[i].color.begin());
    }
    std::copy_n(info.min_bounds,3,mesh.minBounds.begin());
    std::copy_n(info.max_bounds,3,mesh.maxBounds.begin());
    mesh.surfaceCount=info.surface_count;
    return mesh;
}
BspMesh loadIW5Snapshot(const std::string& path,const BspLoadLimits& limits) {
    std::ifstream file(path,std::ios::binary|std::ios::ate);
    if(!file) throw BspError("IW5 snapshot: cannot open file");
    const auto size=file.tellg();
    if(size<32 || static_cast<std::uint64_t>(size)>nativeLimits(limits).max_file_bytes)
        throw BspError("IW5 snapshot: file size is outside allowed limits");
    std::vector<std::uint8_t> bytes(static_cast<std::size_t>(size));
    file.seekg(0);
    if(!file.read(reinterpret_cast<char*>(bytes.data()),static_cast<std::streamsize>(bytes.size())) || file.peek()!=std::char_traits<char>::eof())
        throw BspError("IW5 snapshot: file changed or could not be read completely");
    return loadIW5Snapshot(bytes,limits);
}
}
