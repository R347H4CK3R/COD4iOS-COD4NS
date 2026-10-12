/* SPDX-License-Identifier: GPL-3.0-only
 * Portable reader for the IW5GEO1 research snapshot format. Not a fastfile loader.
 */
#ifndef IW5GEO_H
#define IW5GEO_H
#include <stddef.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    IW5GEO_OK = 0, IW5GEO_INVALID_ARGUMENT, IW5GEO_BAD_LAYOUT, IW5GEO_BAD_MAGIC,
    IW5GEO_UNSUPPORTED, IW5GEO_LIMIT, IW5GEO_BAD_VERTEX, IW5GEO_BAD_SURFACE,
    IW5GEO_BAD_INDEX, IW5GEO_CAPACITY
} iw5geo_status;

typedef struct {
    size_t max_file_bytes;
    uint32_t max_vertices, max_indices, max_surfaces;
} iw5geo_limits;

typedef struct {
    uint32_t vertex_count, source_index_count, index_count, surface_count;
    float min_bounds[3], max_bounds[3];
} iw5geo_info;

typedef struct {
    float position[3], normal[3], color[4], uv[2];
} iw5geo_vertex;

/* Requested limits can only lower defaults. No allocation, file or OS APIs.
 * All buffers must be valid for their stated size/capacity, mutually disjoint,
 * and not concurrently modified. Floats require IEEE-754 binary32.
 * Every error leaves outputs unchanged. NULL limits selects defaults.
 * info is required; vertex/index capacities count elements, not bytes.
 */
iw5geo_limits iw5geo_default_limits(void);
iw5geo_status iw5geo_inspect(const void *data, size_t size,
                           const iw5geo_limits *limits, iw5geo_info *info);
iw5geo_status iw5geo_decode(const void *data, size_t size,
                          const iw5geo_limits *limits,
                          iw5geo_vertex *vertices, size_t vertex_capacity,
                          uint32_t *indices, size_t index_capacity,
                          iw5geo_info *info);
const char *iw5geo_status_string(iw5geo_status status);

#ifdef __cplusplus
}
#endif
#endif
