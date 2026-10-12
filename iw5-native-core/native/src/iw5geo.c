/* SPDX-License-Identifier: GPL-3.0-only
 * Format and decoding approach informed by R347H4CK3R/COD4iOS-COD4NS
 * IW5Geometry.cpp at 40532296b59e44f71904874cad8bfc9d04251e94 (GPLv3).
 * New bounded C ABI implementation; see THIRD_PARTY_NOTICES.md.
 */
#include "iw5geo.h"
#include <float.h>

_Static_assert(sizeof(float)==4 && FLT_RADIX==2 && FLT_MANT_DIG==24 && FLT_MAX_EXP==128,
               "IEEE-754 binary32 floats required");

static uint16_t u16(const unsigned char *p) {
    return (uint16_t)((uint16_t)p[0] | ((uint16_t)p[1]<<8));
}
static uint32_t u32(const unsigned char *p) {
    return (uint32_t)p[0] | ((uint32_t)p[1]<<8) | ((uint32_t)p[2]<<16) | ((uint32_t)p[3]<<24);
}
static float f32(const unsigned char *p) {
    union { uint32_t u; float f; } value;
    value.u=u32(p); return value.f;
}
static int finite32(const unsigned char *p) { return (u32(p)&0x7f800000u)!=0x7f800000u; }
static uint32_t min32(uint32_t a,uint32_t b) { return a<b?a:b; }

iw5geo_limits iw5geo_default_limits(void) {
    const iw5geo_limits result={128u*1024u*1024u,1000000,6000000,65536};
    return result;
}

iw5geo_status iw5geo_inspect(const void *data, size_t size,
                           const iw5geo_limits *requested, iw5geo_info *info) {
    if (!data || !info) return IW5GEO_INVALID_ARGUMENT;
    iw5geo_limits limits=iw5geo_default_limits();
    if (requested) {
        if(requested->max_file_bytes<limits.max_file_bytes) limits.max_file_bytes=requested->max_file_bytes;
        limits.max_vertices=min32(requested->max_vertices,limits.max_vertices);
        limits.max_indices=min32(requested->max_indices,limits.max_indices);
        limits.max_surfaces=min32(requested->max_surfaces,limits.max_surfaces);
    }
    if(size>limits.max_file_bytes) return IW5GEO_LIMIT;
    if(size<32) return IW5GEO_BAD_LAYOUT;
    const unsigned char *bytes=(const unsigned char *)data;
    const unsigned char magic[8]={'I','W','5','G','E','O','1',0};
    for(unsigned i=0;i<8;++i) if(bytes[i]!=magic[i]) return IW5GEO_BAD_MAGIC;
    if(u32(bytes+8)!=1 || u32(bytes+24)!=44 || u32(bytes+28)!=16) return IW5GEO_UNSUPPORTED;
    const uint32_t vc=u32(bytes+12), ic=u32(bytes+16), sc=u32(bytes+20);
    if(!vc || !ic || !sc || vc>limits.max_vertices || ic>limits.max_indices || sc>limits.max_surfaces) return IW5GEO_LIMIT;
    if(ic%3) return IW5GEO_BAD_LAYOUT;
    /* Hard caps keep these offsets below 2^32, including on a 32-bit host. */
    const size_t indices_at=32+(size_t)vc*44;
    const size_t surfaces_at=indices_at+(size_t)ic*2;
    if(surfaces_at+(size_t)sc*16!=size) return IW5GEO_BAD_LAYOUT;
    for(uint32_t i=0;i<vc;++i) {
        const unsigned char *v=bytes+32+(size_t)i*44;
        for(unsigned axis=0;axis<3;++axis) {
            if(!finite32(v+axis*4)) return IW5GEO_BAD_VERTEX;
            const float position=f32(v+axis*4);
            if(position < -1e7f || position > 1e7f) return IW5GEO_BAD_VERTEX;
        }
        if(!finite32(v+20) || !finite32(v+24)) return IW5GEO_BAD_VERTEX;
    }
    iw5geo_info parsed={0};
    parsed.vertex_count=vc; parsed.source_index_count=ic; parsed.surface_count=sc;
    int first_point=1;
    for(uint32_t i=0;i<sc;++i) {
        const unsigned char *s=bytes+surfaces_at+(size_t)i*16;
        const uint32_t first=u32(s+4), count=u16(s+8), num=(uint32_t)u16(s+10)*3, start=u32(s+12);
        if(!count || !num || first>vc || count>vc-first || start>ic || num>ic-start) return IW5GEO_BAD_SURFACE;
        if(num>limits.max_indices-parsed.index_count) return IW5GEO_LIMIT;
        parsed.index_count+=num;
        for(uint32_t j=0;j<num;++j) {
            const uint32_t local=u16(bytes+indices_at+(size_t)(start+j)*2);
            if(local>=count) return IW5GEO_BAD_INDEX;
            const unsigned char *vertex=bytes+32+(size_t)(first+local)*44;
            for(unsigned axis=0;axis<3;++axis) {
                const float value=f32(vertex+axis*4);
                if(first_point || value<parsed.min_bounds[axis]) parsed.min_bounds[axis]=value;
                if(first_point || value>parsed.max_bounds[axis]) parsed.max_bounds[axis]=value;
            }
            first_point=0;
        }
    }
    *info=parsed;
    return IW5GEO_OK;
}

iw5geo_status iw5geo_decode(const void *data,size_t size,const iw5geo_limits *limits,
                          iw5geo_vertex *vertices,size_t vertex_capacity,
                          uint32_t *indices,size_t index_capacity,iw5geo_info *info) {
    if(!vertices || !indices || !info) return IW5GEO_INVALID_ARGUMENT;
    iw5geo_info parsed;
    const iw5geo_status result=iw5geo_inspect(data,size,limits,&parsed);
    if(result!=IW5GEO_OK) return result;
    if(vertex_capacity<parsed.vertex_count || index_capacity<parsed.index_count) return IW5GEO_CAPACITY;
    const unsigned char *bytes=(const unsigned char *)data;
    for(uint32_t i=0;i<parsed.vertex_count;++i) {
        const unsigned char *v=bytes+32+(size_t)i*44;
        const float scale=(v[39]+192.f)/32385.f;
        for(unsigned axis=0;axis<3;++axis) {
            vertices[i].position[axis]=f32(v+axis*4);
            vertices[i].normal[axis]=(v[36+axis]-127.f)*scale;
        }
        vertices[i].color[0]=v[18]/255.f;
        vertices[i].color[1]=v[17]/255.f;
        vertices[i].color[2]=v[16]/255.f;
        vertices[i].color[3]=1.f;
        vertices[i].uv[0]=f32(v+20); vertices[i].uv[1]=f32(v+24);
    }
    const size_t indices_at=32+(size_t)parsed.vertex_count*44;
    const size_t surfaces_at=indices_at+(size_t)parsed.source_index_count*2;
    size_t output=0;
    for(uint32_t i=0;i<parsed.surface_count;++i) {
        const unsigned char *s=bytes+surfaces_at+(size_t)i*16;
        const uint32_t first=u32(s+4), num=(uint32_t)u16(s+10)*3, start=u32(s+12);
        for(uint32_t j=0;j<num;++j) indices[output++]=first+u16(bytes+indices_at+(size_t)(start+j)*2);
    }
    *info=parsed;
    return IW5GEO_OK;
}

const char *iw5geo_status_string(iw5geo_status status) {
    switch(status) {
        case IW5GEO_OK: return "ok";
        case IW5GEO_INVALID_ARGUMENT: return "invalid argument";
        case IW5GEO_BAD_LAYOUT: return "truncated, trailing or invalid record layout";
        case IW5GEO_BAD_MAGIC: return "not an IW5GEO1 snapshot";
        case IW5GEO_UNSUPPORTED: return "unsupported version or stride";
        case IW5GEO_LIMIT: return "count or byte budget exceeded";
        case IW5GEO_BAD_VERTEX: return "invalid vertex position or UV";
        case IW5GEO_BAD_SURFACE: return "surface range outside arrays";
        case IW5GEO_BAD_INDEX: return "surface-local index outside vertices";
        case IW5GEO_CAPACITY: return "output buffer capacity insufficient";
        default: return "unknown status";
    }
}
