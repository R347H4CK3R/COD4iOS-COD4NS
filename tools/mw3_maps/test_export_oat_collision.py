#!/usr/bin/env python3
"""Synthetic decoded x86 clipmap fixtures; no retail data required."""
import struct,unittest
from export_oat_collision import collision_geometry,find_collision,ExportError

BASE=0x10000
def fixture():
    data=bytearray(4096)
    name=b'maps/mp/mp_test.d3dbsp\0'
    data[300:300+len(name)]=name
    struct.pack_into('<I',data,0,BASE+300)
    struct.pack_into('<II',data,8,1,BASE+600) # ClipInfo planes
    struct.pack_into('<I',data,16,1) # materials
    struct.pack_into('<II',data,24,1,BASE+640) # sides
    struct.pack_into('<H',data,56,1) # brushes
    struct.pack_into('<III',data,60,BASE+660,BASE+704,BASE+728)
    struct.pack_into('<IIII',data,100,3,BASE+500,1,BASE+540)
    struct.pack_into('<I',data,152,BASE+340)
    struct.pack_into('<9f',data,500,0,0,0,1,0,0,0,1,0)
    struct.pack_into('<3H',data,540,0,1,2)
    struct.pack_into('<4f',data,600,1,0,0,5)
    struct.pack_into('<IHBB',data,640,BASE+600,0,0,0)
    struct.pack_into('<HHI',data,660,1,65535,BASE+640)
    struct.pack_into('<6f',data,704,0,0,0,5,5,5)
    struct.pack_into('<i',data,728,1)
    text=b'{\n1668 "worldspawn"\n}\n\0'
    data[800:800+len(text)]=text
    struct.pack_into('<IIi',data,340,BASE+300,BASE+800,len(text))
    return data

class CollisionTests(unittest.TestCase):
    def load(self,data):return collision_geometry([(BASE,bytes(data))],BASE,'mp_test')
    def test_real_primitives_and_exact_tokens(self):
        entities,geometry=find_collision([(BASE,bytes(fixture()))],'mp_test')
        self.assertEqual(entities,b'{\n1668 "worldspawn"\n}\n')
        self.assertEqual(geometry['triangles'],[[0,1,2]])
        self.assertEqual(geometry['planes'],[[1,0,0,5]])
        self.assertEqual(geometry['sides'][0]['plane'],0)
        self.assertEqual(geometry['brushes'][0]['halfsize'],[5,5,5])
        self.assertEqual(geometry['brushes'][0]['contents'],1)
    def test_bad_triangle(self):
        data=fixture();struct.pack_into('<H',data,540,3)
        with self.assertRaises(ExportError):self.load(data)
    def test_invalid_plane_pointer(self):
        for pointer in (BASE+601,BASE+620,0xfffffff0):
            data=fixture();struct.pack_into('<I',data,640,pointer)
            with self.assertRaises(ExportError):self.load(data)
    def test_invalid_brush_side_pointer(self):
        data=fixture();struct.pack_into('<I',data,664,BASE+648)
        with self.assertRaises(ExportError):self.load(data)
    def test_nonfinite_or_negative_bounds(self):
        for offset,value in ((500,float('nan')),(600,float('inf')),(716,-1)):
            data=fixture();struct.pack_into('<f',data,offset,value)
            with self.assertRaises(ExportError):self.load(data)
    def test_bad_material(self):
        data=fixture();struct.pack_into('<H',data,644,1)
        with self.assertRaises(ExportError):self.load(data)
    def test_entity_size_and_framing(self):
        for size in (-1,0,5<<20):
            data=fixture();struct.pack_into('<i',data,348,size)
            with self.assertRaises(ExportError):self.load(data)
        data=fixture();data[801]=0
        with self.assertRaises(ExportError):self.load(data)
    def test_count_budget(self):
        data=fixture();struct.pack_into('<I',data,100,0xffffffff)
        with self.assertRaises(ExportError):self.load(data)
    def test_ambiguity(self):
        data=fixture();data[1000:1256]=data[:256]
        with self.assertRaises(ExportError):find_collision([(BASE,bytes(data))],'mp_test')
    def test_truncated_regions(self):
        for length in (0,12,255,300,540,640,727,810):
            with self.assertRaises(ExportError):self.load(fixture()[:length])
if __name__=='__main__':unittest.main()
