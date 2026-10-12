/* SPDX-License-Identifier: GPL-3.0-only */
#include "iw5geo.h"
#include <stdio.h>
#include <stdlib.h>

int main(int argc,char **argv) {
    if(argc!=2) { fprintf(stderr,"Usage: iw5geo-inspect snapshot.iw5geo\n"); return 2; }
    FILE *file=fopen(argv[1],"rb");
    if(!file) { fprintf(stderr,"Cannot open snapshot\n"); return 1; }
    if(fseek(file,0,SEEK_END)) { fclose(file); return 1; }
    long end=ftell(file);
    if(end<0 || (unsigned long)end>iw5geo_default_limits().max_file_bytes || fseek(file,0,SEEK_SET)) {
        fprintf(stderr,"File size/seek failed or exceeds 128 MiB\n"); fclose(file); return 1;
    }
    unsigned char *bytes=(unsigned char *)malloc(end ? (size_t)end : 1);
    if(!bytes) { fclose(file); return 1; }
    size_t got=fread(bytes,1,(size_t)end,file); int io_error=ferror(file); fclose(file);
    if(got!=(size_t)end || io_error) { free(bytes); return 1; }
    iw5geo_info info;
    iw5geo_status result=iw5geo_inspect(bytes,got,NULL,&info);
    free(bytes);
    if(result!=IW5GEO_OK) { fprintf(stderr,"%s\n",iw5geo_status_string(result)); return 1; }
    printf("{\"format\":\"IW5GEO1 snapshot\",\"vertices\":%u,\"source_indices\":%u,\"decoded_indices\":%u,\"triangles\":%u,\"surfaces\":%u,"
           "\"bounds_min\":[%.9g,%.9g,%.9g],\"bounds_max\":[%.9g,%.9g,%.9g],\"gameplay_ready\":false}\n",
           info.vertex_count,info.source_index_count,info.index_count,info.index_count/3,info.surface_count,
           info.min_bounds[0],info.min_bounds[1],info.min_bounds[2],info.max_bounds[0],info.max_bounds[1],info.max_bounds[2]);
    return 0;
}
