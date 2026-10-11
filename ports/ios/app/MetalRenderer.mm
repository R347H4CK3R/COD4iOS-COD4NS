#import "MetalRenderer.h"
#import <QuartzCore/QuartzCore.h>
#include <cstddef>
#include <vector>
#include <fstream>
#include <cstdint>
#include <cstring>
#include <cmath>
#include <algorithm>

using namespace kisakcod;
static NSError *KISError(NSString *message) {
    return [NSError errorWithDomain:@"KisakCOD.Metal" code:1
                           userInfo:@{NSLocalizedDescriptionKey:message}];
}

// First Metal backend milestone: original BSP world positions/normals/colors.
// Materials, texture stages, animated models and the engine's draw commands are
// not implemented here. This shader intentionally does not emulate D3D9 shaders.
static NSString *const shaderSource = @R"metal(
#include <metal_stdlib>
using namespace metal;
struct Vertex { packed_float3 position; packed_float3 normal; packed_float4 color; };
struct Out { float4 position [[position]]; float3 normal; float4 color; };
vertex Out map_vertex(uint id [[vertex_id]], const device Vertex* verts [[buffer(0)]],
                      constant float4x4& matrix [[buffer(1)]]) {
    Out out;
    out.position=matrix*float4(float3(verts[id].position),1);
    out.normal=float3(verts[id].normal);
    out.color=float4(verts[id].color);
    return out;
}
fragment float4 map_fragment(Out in [[stage_in]]) {
    float len=length(in.normal);
    float3 normal=len>0.001f ? in.normal/len : float3(0,0,1);
    float light=0.35f+0.65f*abs(dot(normal,normalize(float3(0.4f,0.6f,1))));
    return float4(max(in.color.rgb,float3(0.22f))*light,1);
}
struct TexVertex { packed_float3 position; packed_float2 uv; };
struct TexOut { float4 position [[position]]; float2 uv; };
vertex TexOut tex_vertex(uint id [[vertex_id]], const device TexVertex* verts [[buffer(0)]],
                         constant float4x4& matrix [[buffer(1)]]) {
 TexOut o; o.position=matrix*float4(float3(verts[id].position),1);o.uv=float2(verts[id].uv);return o;
}
fragment float4 tex_fragment(TexOut in [[stage_in]],
 texture2d<float> diffuse [[texture(0)]], sampler smp [[sampler(0)]]) {
 return diffuse.sample(smp,in.uv);
}
)metal";

@implementation KISMetalRenderer {
    __weak MTKView *_view;
    id<MTLDevice> _device;
    id<MTLCommandQueue> _queue;
    id<MTLRenderPipelineState> _pipeline, _texPipeline;
    id<MTLSamplerState> _texSampler;
    id<MTLTexture> _fallback;
    NSMutableArray *_texturePaths;
    NSMutableDictionary *_textureCache;
    NSMutableArray<NSNumber *> *_textureRecency;
    std::vector<std::pair<NSUInteger,NSUInteger>> _materialRanges;
    BOOL _textured;
    id<MTLDepthStencilState> _depth;
    id<MTLBuffer> _vertices, _indices;
    NSUInteger _indexCount;
    ios::Camera _camera, _initialCamera;
    BOOL _boundedPreview;
    ios::Vec3 _worldMin{}, _worldMax{};

    CFTimeInterval _lastFrame;
    dispatch_semaphore_t _inflight;
}
- (instancetype)initWithView:(MTKView *)view error:(NSError **)error {
    if(!(self=[super init])) return nil;
    _view=view;
    _device=view.device;
    _queue=[_device newCommandQueue];
    _inflight=dispatch_semaphore_create(3);
    if(!_device || !_queue) {
        if(error) *error=KISError(@"Metal non è disponibile su questo dispositivo.");
        return nil;
    }
    id<MTLLibrary> library=[_device newLibraryWithSource:shaderSource options:nil error:error];
    if(!library) return nil;
    MTLRenderPipelineDescriptor *descriptor=[MTLRenderPipelineDescriptor new];
    descriptor.vertexFunction=[library newFunctionWithName:@"map_vertex"];
    descriptor.fragmentFunction=[library newFunctionWithName:@"map_fragment"];
    descriptor.colorAttachments[0].pixelFormat=view.colorPixelFormat;
    descriptor.depthAttachmentPixelFormat=view.depthStencilPixelFormat;
    _pipeline=[_device newRenderPipelineStateWithDescriptor:descriptor error:error];
    if(!_pipeline) return nil;
    MTLRenderPipelineDescriptor *texdesc=[MTLRenderPipelineDescriptor new];
    texdesc.vertexFunction=[library newFunctionWithName:@"tex_vertex"];
    texdesc.fragmentFunction=[library newFunctionWithName:@"tex_fragment"];
    texdesc.colorAttachments[0].pixelFormat=view.colorPixelFormat;
    texdesc.depthAttachmentPixelFormat=view.depthStencilPixelFormat;
    _texPipeline=[_device newRenderPipelineStateWithDescriptor:texdesc error:error];
    if(!_texPipeline) return nil;
    MTLSamplerDescriptor *sam=[MTLSamplerDescriptor new];sam.minFilter=MTLSamplerMinMagFilterLinear;
    sam.magFilter=MTLSamplerMinMagFilterLinear;sam.sAddressMode=MTLSamplerAddressModeRepeat;
    sam.tAddressMode=MTLSamplerAddressModeRepeat;
    _texSampler=[_device newSamplerStateWithDescriptor:sam];
    MTLTextureDescriptor *fb=[MTLTextureDescriptor texture2DDescriptorWithPixelFormat:MTLPixelFormatRGBA8Unorm width:1 height:1 mipmapped:NO];
    _fallback=[_device newTextureWithDescriptor:fb];
    const uint8_t pixel[4]={180,180,180,255};[_fallback replaceRegion:MTLRegionMake2D(0,0,1,1) mipmapLevel:0 withBytes:pixel bytesPerRow:4];
    _textureCache=[NSMutableDictionary new];
    _textureRecency=[NSMutableArray new];
    MTLDepthStencilDescriptor *depth=[MTLDepthStencilDescriptor new];
    depth.depthCompareFunction=MTLCompareFunctionLess;
    depth.depthWriteEnabled=YES;
    _depth=[_device newDepthStencilStateWithDescriptor:depth];
    if(!_depth) {if(error) *error=KISError(@"Impossibile creare il depth buffer Metal.");return nil;}
    return self;
}
- (BOOL)loadMesh:(const assets::BspMesh &)mesh error:(NSError **)error {
    static_assert(sizeof(assets::BspVertex)==40);
    static_assert(offsetof(assets::BspVertex,normal)==12);
    static_assert(offsetof(assets::BspVertex,color)==24);
    if(mesh.vertices.empty() || mesh.indices.empty()) {
        if(error) *error=KISError(@"La mappa non contiene geometria visualizzabile.");return NO;
    }
    id<MTLBuffer> vertices=[_device newBufferWithBytes:mesh.vertices.data()
                                            length:mesh.vertices.size()*sizeof(assets::BspVertex)
                                           options:MTLResourceStorageModeShared];
    id<MTLBuffer> indices=[_device newBufferWithBytes:mesh.indices.data()
                                           length:mesh.indices.size()*sizeof(uint32_t)
                                          options:MTLResourceStorageModeShared];
    if(!vertices || !indices) {
        if(error) *error=KISError(@"Memoria GPU insufficiente per questa mappa.");return NO;
    }
    // Commit the new map only after both allocations succeed.
    _vertices=vertices; _indices=indices; _indexCount=mesh.indices.size(); _textured=NO;
    _camera.frameBounds(mesh.minBounds,mesh.maxBounds);
    _worldMin=mesh.minBounds; _worldMax=mesh.maxBounds; _boundedPreview=NO;

    if(mesh.spawn) {
        _camera.position=mesh.spawn->position;
        _camera.position[2]+=60; // Approximate standing view height for inspection.
        // Spawn angles are already COD4 PITCH/YAW/ROLL degrees; only the viewer's
        // own pitch limit is applied, and roll is left out of the free camera.
        _camera.angles={std::clamp(mesh.spawn->angles[PITCH],
                                   -ios::Camera::kPitchLimit,ios::Camera::kPitchLimit),
                        mesh.spawn->angles[YAW],0};
    }
    _initialCamera=_camera;
    [self resetClock];
    return YES;
}
- (BOOL)loadMW3TexturedMesh:(NSURL *)url error:(NSError **)error {
    std::ifstream f(url.fileSystemRepresentation,std::ios::binary|std::ios::ate);
    if(!f){if(error)*error=KISError(@"Missing MW3MESH2");return NO;}
    const std::streamoff bytes=f.tellg();f.seekg(0);
    char magic[8];uint64_t vertexCount=0,triangleCount=0,materialCount=0;
    f.read(magic,8);f.read(reinterpret_cast<char*>(&vertexCount),8);
    f.read(reinterpret_cast<char*>(&triangleCount),8);f.read(reinterpret_cast<char*>(&materialCount),8);
    if(!f || std::memcmp(magic,"MW3MESH2",8) || triangleCount==0 || triangleCount>1000000 ||
       materialCount==0 || materialCount>2000 || bytes!=std::streamoff(32+64*triangleCount)){
      if(error)*error=KISError(@"Malformed MW3MESH2");return NO;
    }
    struct TV {float x,y,z,u,v;};
    std::vector<TV> verts;verts.reserve(size_t(triangleCount)*3);
    auto byMaterial=std::vector<std::vector<uint32_t>>(static_cast<size_t>(materialCount));
    kisakcod::ios::Vec3 low{INFINITY,INFINITY,INFINITY},high{-INFINITY,-INFINITY,-INFINITY};
    for(uint64_t t=0;t<triangleCount;t++) {
      TV a[3];uint32_t m;
      f.read(reinterpret_cast<char*>(a),sizeof a);f.read(reinterpret_cast<char*>(&m),4);
      if(!f || m>=materialCount){if(error)*error=KISError(@"Bad MW3 material");return NO;}
      for(auto v:a) {
        if(!std::isfinite(v.x)||!std::isfinite(v.y)||!std::isfinite(v.z)||!std::isfinite(v.u)||!std::isfinite(v.v)){
          if(error)*error=KISError(@"Invalid MW3 vertex");return NO;
        }
        const float xyz[3]={v.x,v.y,v.z};
        for(int k=0;k<3;k++){low[k]=std::min(low[k],xyz[k]);high[k]=std::max(high[k],xyz[k]);}
        byMaterial[m].push_back(uint32_t(verts.size()));verts.push_back(v);
      }
    }
    std::vector<uint32_t> sorted;sorted.reserve(verts.size());std::vector<std::pair<NSUInteger,NSUInteger>> ranges;
    for(auto& group:byMaterial){ranges.push_back({sorted.size(),group.size()});sorted.insert(sorted.end(),group.begin(),group.end());}
    id<MTLBuffer> vb=[_device newBufferWithBytes:verts.data() length:verts.size()*sizeof(TV) options:MTLResourceStorageModeShared];
    id<MTLBuffer> ib=[_device newBufferWithBytes:sorted.data() length:sorted.size()*4 options:MTLResourceStorageModeShared];
    if(!vb||!ib){if(error)*error=KISError(@"Not enough Metal memory");return NO;}
    NSString *base=[url.lastPathComponent stringByDeletingPathExtension];
    base=[base stringByReplacingOccurrencesOfString:@"_textured" withString:@""];
    NSURL *manifestURL=[[url URLByDeletingLastPathComponent] URLByAppendingPathComponent:[base stringByAppendingString:@"_texture_manifest.json"]];
    NSDictionary *manifest=[NSJSONSerialization JSONObjectWithData:[NSData dataWithContentsOfURL:manifestURL] options:0 error:nil];
    NSArray *entries=[manifest isKindOfClass:[NSDictionary class]]?manifest[@"materials"]:nil;
    _texturePaths=[NSMutableArray new];
    for(NSUInteger i=0;i<materialCount;i++) {
      NSString *relative=(i<entries.count && [entries[i] isKindOfClass:[NSDictionary class]])?entries[i][@"texture"]:nil;
      if(![relative isKindOfClass:[NSString class]])relative=@"";
      [_texturePaths addObject:relative.length?[[url URLByDeletingLastPathComponent] URLByAppendingPathComponent:relative].path:[NSNull null]];
    }
    [_textureCache removeAllObjects];[_textureRecency removeAllObjects];
    _vertices=vb;_indices=ib;_indexCount=sorted.size();_materialRanges=std::move(ranges);_textured=YES;
    _camera.frameBounds(low,high);_worldMin=low;_worldMax=high;_initialCamera=_camera;[self resetClock];
    return YES;
}
- (id<MTLTexture>)textureForMaterial:(NSUInteger)index {
    NSNumber *key=@(index);
    id<MTLTexture> cached=_textureCache[key];
    if(cached) {
        [_textureRecency removeObject:key];
        [_textureRecency addObject:key];
        return cached;
    }
    // Evict a single least-recently-used item instead of discarding all textures.
    if(_textureRecency.count>=48) {
        NSNumber *oldest=_textureRecency.firstObject;
        [_textureCache removeObjectForKey:oldest];
        [_textureRecency removeObjectAtIndex:0];
    }
    id<MTLTexture> tex=_fallback;
    if(index<_texturePaths.count && _texturePaths[index]!=[NSNull null]) {
        NSURL *source=[NSURL fileURLWithPath:_texturePaths[index]];
        MTKTextureLoader *loader=[[MTKTextureLoader alloc] initWithDevice:_device];
        id<MTLTexture> loaded=[loader newTextureWithContentsOfURL:source
            options:@{MTKTextureLoaderOptionSRGB:@YES} error:nil];
        if(loaded)tex=loaded;
    }
    _textureCache[key]=tex;
    [_textureRecency addObject:key];
    return tex;
}
- (void)setDomePreviewBoundariesEnabled:(BOOL)enabled { _boundedPreview=enabled; }
- (void)resetCamera { _camera=_initialCamera; [self resetClock]; }
- (void)resetClock { _lastFrame=0; }
- (void)mtkView:(MTKView *)view drawableSizeWillChange:(CGSize)size {
    (void)view; (void)size;
}
- (void)drawInMTKView:(MTKView *)view {
    // Drop a frame if the GPU is behind; never block the UI thread.
    if(dispatch_semaphore_wait(_inflight,DISPATCH_TIME_NOW)!=0) return;
    id<MTLCommandBuffer> command=[_queue commandBuffer];
    MTLRenderPassDescriptor *pass=view.currentRenderPassDescriptor;
    id<CAMetalDrawable> drawable=view.currentDrawable;
    if(!command || !pass || !drawable) {dispatch_semaphore_signal(_inflight);return;}
    CFTimeInterval now=CACurrentMediaTime();
    double elapsed=_lastFrame?now-_lastFrame:0;
    _lastFrame=now;
    ios::CameraInput input=self.readInput?self.readInput():ios::CameraInput{};
    _camera.update(input,elapsed);
    // Preview-only map extents safeguard, not polygonal wall/floor collision.
    if(_boundedPreview) for(int k=0;k<3;k++)
        _camera.position[k]=std::clamp(_camera.position[k],_worldMin[k],_worldMax[k]);

    id<MTLRenderCommandEncoder> encoder=[command renderCommandEncoderWithDescriptor:pass];
    if(!encoder) {dispatch_semaphore_signal(_inflight);return;}
    if(_indexCount) {
        auto matrix=_camera.viewProjection((float)(view.drawableSize.width/std::max(view.drawableSize.height,1.0)));
        [encoder setRenderPipelineState:_textured?_texPipeline:_pipeline];
        [encoder setDepthStencilState:_depth];
        [encoder setCullMode:MTLCullModeNone];
        [encoder setVertexBuffer:_vertices offset:0 atIndex:0];
        [encoder setVertexBytes:matrix.data() length:sizeof(matrix) atIndex:1];
        if(_textured) {
            [encoder setFragmentSamplerState:_texSampler atIndex:0];
            for(NSUInteger m=0;m<_materialRanges.size();m++) {
                auto range=_materialRanges[m];if(!range.second)continue;
                [encoder setFragmentTexture:[self textureForMaterial:m] atIndex:0];
                [encoder drawIndexedPrimitives:MTLPrimitiveTypeTriangle indexCount:range.second
                              indexType:MTLIndexTypeUInt32 indexBuffer:_indices indexBufferOffset:range.first*4];
            }
        } else {
            [encoder drawIndexedPrimitives:MTLPrimitiveTypeTriangle indexCount:_indexCount
                              indexType:MTLIndexTypeUInt32 indexBuffer:_indices indexBufferOffset:0];
        }
    }
    [encoder endEncoding];
    [command presentDrawable:drawable];
    dispatch_semaphore_t semaphore=_inflight;
    __weak KISMetalRenderer *weakSelf=self;
    [command addCompletedHandler:^(id<MTLCommandBuffer> done) {
        dispatch_semaphore_signal(semaphore);
        if(done.status==MTLCommandBufferStatusError) {
            NSString *message=done.error.localizedDescription?:@"Errore durante il rendering Metal.";
            dispatch_async(dispatch_get_main_queue(),^{
                KISMetalRenderer *renderer=weakSelf;
                if(renderer.renderFailure) renderer.renderFailure(message);
            });
        }
    }];
    [command commit];
}
@end
