#include "IW5Geometry.hpp"
#include <fstream>
#include <iostream>
int main(int argc,char** argv) {
 if(argc<2 || argc>3){std::cerr<<"Usage: iw5-inspect snapshot.iw5geo [output.obj]\n";return 2;}
 try {
  const auto mesh=kisakcod::assets::loadIW5Geometry(std::string(argv[1]));
  std::cout<<"vertices="<<mesh.vertices.size()<<" triangles="<<mesh.indices.size()/3<<" surfaces="<<mesh.surfaceCount<<"\n";
  std::cout<<"bounds=";for(int axis=0;axis<3;++axis)std::cout<<mesh.minBounds[axis]<<","<<mesh.maxBounds[axis]<<" ";std::cout<<"\n";
  if(argc==3){std::ofstream obj(argv[2]);if(!obj)throw std::runtime_error("cannot create OBJ");
   for(const auto& v:mesh.vertices)obj<<"v "<<v.position[0]<<" "<<v.position[1]<<" "<<v.position[2]<<"\n";
   for(std::size_t i=0;i<mesh.indices.size();i+=3)obj<<"f "<<mesh.indices[i]+1<<" "<<mesh.indices[i+1]+1<<" "<<mesh.indices[i+2]+1<<"\n";
   if(!obj)throw std::runtime_error("OBJ write failed");
  }
 }catch(const std::exception& error){std::cerr<<error.what()<<"\n";return 1;}
}
