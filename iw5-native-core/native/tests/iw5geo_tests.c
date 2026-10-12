/* SPDX-License-Identifier: GPL-3.0-only */
#include "iw5geo.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static unsigned checks;
#define CHECK(x) do { ++checks; if (!(x)) { fprintf(stderr,"FAIL line %d: %s\n",__LINE__,#x); exit(1); } } while(0)
enum { FIXTURE_SIZE = 32 + 3 * 44 + 6 + 16, SURFACE_AT = 32 + 3 * 44 + 6 };
static void put32(unsigned char *p, unsigned v) { for(unsigned i=0;i<4;++i) p[i]=(unsigned char)(v>>(8*i)); }
static void putfloat(unsigned char *p, float f) { unsigned v; memcpy(&v,&f,4); put32(p,v); }
static void fixture(unsigned char *p) {
    memset(p,0,FIXTURE_SIZE); memcpy(p,"IW5GEO1",8);
    put32(p+8,1); put32(p+12,3); put32(p+16,3); put32(p+20,1); put32(p+24,44); put32(p+28,16);
    putfloat(p+32,1); putfloat(p+32+44+4,2); putfloat(p+32+88+8,3);
    for(unsigned i=0;i<3;++i) {
        unsigned char *v=p+32+i*44;
        v[16]=10; v[17]=20; v[18]=30; v[19]=255;
        putfloat(v+20,0.25f); putfloat(v+24,0.75f);
        v[36]=127; v[37]=127; v[38]=254;
    }
    p[32+132+2]=1; p[32+132+4]=2;
    p[SURFACE_AT+8]=3; p[SURFACE_AT+10]=1;
}
static void rejected(unsigned char *bytes, size_t size, iw5geo_status expected) {
    iw5geo_info before, info; memset(&before,0xa5,sizeof(before)); info=before;
    CHECK(iw5geo_inspect(bytes,size,NULL,&info)==expected);
    CHECK(memcmp(&before,&info,sizeof(info))==0);
}
int main(void) {
    unsigned char good[FIXTURE_SIZE], bad[FIXTURE_SIZE+16], unaligned[FIXTURE_SIZE+1];
    fixture(good); iw5geo_info info;
    CHECK(iw5geo_inspect(good,sizeof(good),NULL,&info)==IW5GEO_OK);
    CHECK(info.vertex_count==3 && info.source_index_count==3 && info.index_count==3 && info.surface_count==1);
    CHECK(info.min_bounds[0]==0 && info.max_bounds[0]==1 && info.max_bounds[1]==2 && info.max_bounds[2]==3);
    iw5geo_vertex vertices[3]; uint32_t indices[6];
    CHECK(iw5geo_decode(good,sizeof(good),NULL,vertices,3,indices,3,&info)==IW5GEO_OK);
    CHECK(indices[0]==0 && indices[1]==1 && indices[2]==2);
    CHECK(vertices[0].uv[0]==0.25f && vertices[0].uv[1]==0.75f);
    CHECK(vertices[0].color[0]==30.f/255.f && vertices[0].normal[0]==0.f);
    memcpy(unaligned+1,good,sizeof(good));
    CHECK(iw5geo_inspect(unaligned+1,sizeof(good),NULL,&info)==IW5GEO_OK);
    for(size_t i=0;i<sizeof(good);++i) rejected(good,i,IW5GEO_BAD_LAYOUT);
    memcpy(bad,good,sizeof(good)); bad[sizeof(good)]=0; rejected(bad,sizeof(good)+1,IW5GEO_BAD_LAYOUT);
    memcpy(bad,good,sizeof(good)); bad[0]='X'; rejected(bad,sizeof(good),IW5GEO_BAD_MAGIC);
    memcpy(bad,good,sizeof(good)); put32(bad+8,2); rejected(bad,sizeof(good),IW5GEO_UNSUPPORTED);
    memcpy(bad,good,sizeof(good)); put32(bad+24,48); rejected(bad,sizeof(good),IW5GEO_UNSUPPORTED);
    memcpy(bad,good,sizeof(good)); put32(bad+12,0xffffffffu); rejected(bad,sizeof(good),IW5GEO_LIMIT);
    memcpy(bad,good,sizeof(good)); put32(bad+16,4); rejected(bad,sizeof(good),IW5GEO_BAD_LAYOUT);
    memcpy(bad,good,sizeof(good)); put32(bad+32,0x7fc00000); rejected(bad,sizeof(good),IW5GEO_BAD_VERTEX);
    memcpy(bad,good,sizeof(good)); put32(bad+32+20,0x7f800000); rejected(bad,sizeof(good),IW5GEO_BAD_VERTEX);
    memcpy(bad,good,sizeof(good)); put32(bad+32,0xff800000); rejected(bad,sizeof(good),IW5GEO_BAD_VERTEX);
    memcpy(bad,good,sizeof(good)); putfloat(bad+32,1e8f); rejected(bad,sizeof(good),IW5GEO_BAD_VERTEX);
    memcpy(bad,good,sizeof(good)); bad[SURFACE_AT+8]=0; rejected(bad,sizeof(good),IW5GEO_BAD_SURFACE);
    memcpy(bad,good,sizeof(good)); put32(bad+SURFACE_AT+4,2); rejected(bad,sizeof(good),IW5GEO_BAD_SURFACE);
    memcpy(bad,good,sizeof(good)); put32(bad+SURFACE_AT+12,1); rejected(bad,sizeof(good),IW5GEO_BAD_SURFACE);
    memcpy(bad,good,sizeof(good)); bad[32+132]=3; rejected(bad,sizeof(good),IW5GEO_BAD_INDEX);
    iw5geo_limits limits=iw5geo_default_limits(); limits.max_vertices=2;
    CHECK(iw5geo_inspect(good,sizeof(good),&limits,&info)==IW5GEO_LIMIT);
    limits=iw5geo_default_limits(); limits.max_file_bytes=sizeof(good)-1;
    CHECK(iw5geo_inspect(good,sizeof(good),&limits,&info)==IW5GEO_LIMIT);
    limits=iw5geo_default_limits(); limits.max_vertices=UINT32_MAX;
    memcpy(bad,good,sizeof(good)); put32(bad+12,1000001);
    CHECK(iw5geo_inspect(bad,sizeof(good),&limits,&info)==IW5GEO_LIMIT);
    /* Duplicate surface is legal, but expanded indices have an independent budget. */
    memcpy(bad,good,sizeof(good)); memcpy(bad+sizeof(good),good+SURFACE_AT,16); put32(bad+20,2);
    CHECK(iw5geo_inspect(bad,sizeof(bad),NULL,&info)==IW5GEO_OK && info.index_count==6);
    limits=iw5geo_default_limits(); limits.max_indices=3;
    CHECK(iw5geo_inspect(bad,sizeof(bad),&limits,&info)==IW5GEO_LIMIT);
    /* Capacity and malformed-input failures leave every output byte unchanged. */
    unsigned char saved_vertices[sizeof(vertices)], saved_indices[sizeof(indices)];
    memset(vertices,0xcc,sizeof(vertices)); memset(indices,0xdd,sizeof(indices));
    memcpy(saved_vertices,vertices,sizeof(vertices)); memcpy(saved_indices,indices,sizeof(indices));
    iw5geo_info saved_info; memset(&saved_info,0xee,sizeof(saved_info)); info=saved_info;
    CHECK(iw5geo_decode(good,sizeof(good),NULL,vertices,2,indices,3,&info)==IW5GEO_CAPACITY);
    CHECK(memcmp(vertices,saved_vertices,sizeof(vertices))==0 && memcmp(indices,saved_indices,sizeof(indices))==0 && memcmp(&info,&saved_info,sizeof(info))==0);
    CHECK(iw5geo_decode(good,sizeof(good),NULL,vertices,3,indices,2,&info)==IW5GEO_CAPACITY);
    memcpy(bad,good,sizeof(good)); bad[32+132]=3;
    CHECK(iw5geo_decode(bad,sizeof(good),NULL,vertices,3,indices,3,&info)==IW5GEO_BAD_INDEX);
    CHECK(memcmp(vertices,saved_vertices,sizeof(vertices))==0 && memcmp(indices,saved_indices,sizeof(indices))==0 && memcmp(&info,&saved_info,sizeof(info))==0);
    CHECK(iw5geo_inspect(NULL,sizeof(good),NULL,&info)==IW5GEO_INVALID_ARGUMENT);
    CHECK(iw5geo_inspect(good,sizeof(good),NULL,NULL)==IW5GEO_INVALID_ARGUMENT);
    CHECK(iw5geo_decode(good,sizeof(good),NULL,NULL,3,indices,3,&info)==IW5GEO_INVALID_ARGUMENT);
    /* Fixed-seed mutation corpus: accepted inputs must also decode within capacity. */
    unsigned seed=0x12345678u;
    for(unsigned attempt=0;attempt<4000;++attempt) {
        memcpy(bad,good,sizeof(good)); seed=seed*1664525u+1013904223u;
        bad[seed%sizeof(good)]^=(unsigned char)((seed>>24)|1);
        iw5geo_status result=iw5geo_inspect(bad,sizeof(good),NULL,&info);
        if(result==IW5GEO_OK) {
            CHECK(info.vertex_count==3 && info.index_count==3);
            CHECK(iw5geo_decode(bad,sizeof(good),NULL,vertices,3,indices,3,&info)==IW5GEO_OK);
            CHECK(indices[0]<3 && indices[1]<3 && indices[2]<3);
        }
    }
    printf("iw5geo: %u checks passed, including 4000 deterministic mutations\n",checks);
    return 0;
}
