#!/usr/bin/env python3
"""Synthetic x86-memory fixtures; no retail data required."""
import struct,unittest
from export_oat_world import find_world,world_geometry,ExportError
def fixture():
    arena=bytearray(2048);base=0x10000
    arena[640:664]=b'maps/mp/mp_test.d3dbsp\0'.ljust(24,b'\0')
    arena[680:688]=b'mp_test\0'
    struct.pack_into('<II',arena,0,base+640,base+680)
    struct.pack_into('<I',arena,16,1)
    struct.pack_into('<II',arena,132,3,base+800)
    struct.pack_into('<II',arena,156,3,base+1000)
    struct.pack_into('<I',arena,552,base+1100)
    struct.pack_into('<3f',arena,800,1,2,3);struct.pack_into('<3f',arena,844,4,5,6);struct.pack_into('<3f',arena,888,7,8,9)
    struct.pack_into('<3H',arena,1000,0,1,2)
    struct.pack_into('<IIHHI',arena,1100,0,0,3,1,0)
    return [(base,bytes(arena))]
class ExportTests(unittest.TestCase):
    def test_valid(self):
        data,info=find_world(fixture(),'mp_test')
        self.assertEqual(data[:8],b'IW5GEO1\0');self.assertEqual(len(data),32+132+6+16)
        self.assertEqual(info['triangles'],1);self.assertEqual(info['maxBounds'],[7,8,9])
    def test_wrong_identity(self):
        with self.assertRaises(ExportError):find_world(fixture(),'mp_other')
    def test_bad_index(self):
        regions=fixture();data=bytearray(regions[0][1]);struct.pack_into('<H',data,1000,3)
        with self.assertRaises(ExportError):world_geometry([(0x10000,bytes(data))],0x10000,'mp_test')
    def test_nonfinite(self):
        data=bytearray(fixture()[0][1]);struct.pack_into('<f',data,800,float('nan'))
        with self.assertRaises(ExportError):world_geometry([(0x10000,bytes(data))],0x10000,'mp_test')
    def test_outside_pointer(self):
        data=bytearray(fixture()[0][1]);struct.pack_into('<I',data,136,0xfffffff0)
        with self.assertRaises(ExportError):world_geometry([(0x10000,bytes(data))],0x10000,'mp_test')
    def test_ambiguous_worlds(self):
        regions=fixture(); data=bytearray(regions[0][1])
        data[1200:1840]=data[:640]
        with self.assertRaises(ExportError):find_world([(0x10000,bytes(data))],'mp_test')
    def test_surface_range(self):
        data=bytearray(fixture()[0][1]);struct.pack_into('<I',data,1112,2)
        with self.assertRaises(ExportError):world_geometry([(0x10000,bytes(data))],0x10000,'mp_test')
if __name__=='__main__':unittest.main()
