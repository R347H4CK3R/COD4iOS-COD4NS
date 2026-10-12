// SPDX-License-Identifier: GPL-3.0-only
// Optional local comparison. Build against the separately pinned prior project.
#include "iw5geo.h"
#include "IW5Geometry.hpp"
#include <cmath>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <vector>
static void check(bool value) { if(!value) throw std::runtime_error("reader comparison mismatch"); }
int main(int argc,char **argv) {
    if(argc!=2) return 2;
    try {
        std::ifstream file(argv[1],std::ios::binary|std::ios::ate);
        check(bool(file)); const auto end=file.tellg();
        check(end>=0 && static_cast<uint64_t>(end)<=iw5geo_default_limits().max_file_bytes);
        std::vector<uint8_t> bytes(static_cast<size_t>(end)); file.seekg(0);
        check(bool(file.read(reinterpret_cast<char*>(bytes.data()),static_cast<std::streamsize>(bytes.size()))));
        const auto prior=kisakcod::assets::loadIW5Geometry(bytes);
        iw5geo_info info;
        check(iw5geo_inspect(bytes.data(),bytes.size(),nullptr,&info)==IW5GEO_OK);
        std::vector<iw5geo_vertex> vertices(info.vertex_count); std::vector<uint32_t> indices(info.index_count);
        check(iw5geo_decode(bytes.data(),bytes.size(),nullptr,vertices.data(),vertices.size(),indices.data(),indices.size(),&info)==IW5GEO_OK);
        check(prior.vertices.size()==vertices.size() && prior.indices==indices && prior.surfaceCount==info.surface_count);
        for(size_t i=0;i<vertices.size();++i) {
            for(unsigned a=0;a<3;++a) {
                check(vertices[i].position[a]==prior.vertices[i].position[a]);
                check(std::abs(vertices[i].normal[a]-prior.vertices[i].normal[a])<1e-6f);
            }
            for(unsigned a=0;a<4;++a) check(std::abs(vertices[i].color[a]-prior.vertices[i].color[a])<1e-6f);
        }
        for(unsigned a=0;a<3;++a) check(prior.minBounds[a]==info.min_bounds[a] && prior.maxBounds[a]==info.max_bounds[a]);
        std::cout<<"{\"comparison\":\"every position, normal, color, index and bounds\",\"vertices\":"<<vertices.size()
                 <<",\"indices\":"<<indices.size()<<",\"surfaces\":"<<info.surface_count<<",\"result\":\"match\"}\n";
        return 0;
    } catch(const std::exception& e) { std::cerr<<e.what()<<"\n"; return 1; }
}
