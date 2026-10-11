#pragma once
#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>
namespace mw3 {
struct DomeVertex {float x,y,z;};
struct DomeTriangle {DomeVertex a,b,c;};
class DomeMesh {
public:
 bool load(const std::string& path);
 const std::vector<DomeTriangle>& triangles() const {return triangles_;}
 std::size_t triangle_count() const {return triangles_.size();}
 const std::string& error() const {return error_;}
private:
 std::vector<DomeTriangle> triangles_;
 std::string error_;
};
}
