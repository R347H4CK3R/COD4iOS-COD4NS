import struct
import tempfile
import unittest
from pathlib import Path
from convert_records import ConversionError,brush,surface,static_model
from export_graph import Graph,ExportError,load_capture,write_archive

class Records(unittest.TestCase):
    def test_surface_preserves_triangles_flags_and_exact_bounds(self):
        row=struct.pack('<4I',1,2,3,4)+struct.pack('<I',0xDEADBEEF)+bytes([1,2,3,4])
        bound=struct.pack('<6f',10,20,30,1,2,3)
        out=surface(row,bound)
        self.assertEqual(len(out),48)
        self.assertEqual(out[:16],row[:16]);self.assertEqual(out[16:20],bytes(4))
        self.assertEqual(out[20:24],row[20:24])
        self.assertEqual(struct.unpack_from('<6f',out,24),(9,18,27,11,22,33))
    def test_empty_brush_sentinel_and_nonempty_range(self):
        row=bytearray(60);struct.pack_into('<3H',row,52,0,65535,0)
        self.assertEqual(struct.unpack_from('<3H',brush(row,10),48),(0,65535,0))
        struct.pack_into('<3H',row,52,2,9,1)
        with self.assertRaises(ConversionError):brush(row,10)
    def test_static_model_reorders_lighting_without_process_pointer(self):
        draw=bytearray(76);struct.pack_into('<13f',draw,0,*([0]*12+[1]));struct.pack_into('<IHH',draw,52,0xDEADBEEF,321,17)
        draw[60:64]=bytes([2,3,4,5]);draw[64:68]=b'RGBA';draw[68:76]=b'12345678'
        out,inst=static_model(draw,bytes(36))
        self.assertEqual(len(out),76);self.assertEqual(struct.unpack_from('<f',out)[0],321)
        self.assertEqual(out[56:60],bytes(4));self.assertEqual(out[60:68],b'12345678')
        self.assertEqual(out[68:73],bytes([2,3,17,0,4]));self.assertEqual(inst[24:],b'RGBA')
    def test_invalid_bounds_and_scale(self):
        with self.assertRaises(ConversionError):surface(bytes(24),struct.pack('<6f',0,0,0,-1,0,0))
        with self.assertRaises(ConversionError):static_model(bytes(76),bytes(36))
    def test_graph_pointer_sanitization_and_capture_bounds(self):
        graph=Graph([(100,struct.pack('<II',0xDEADBEEF,7))])
        graph.add('a','record',100,1,8,[0]);graph.ref('a',0,0,{'asset_type':'image','name':'test'})
        self.assertEqual(graph.nodes['a']['data'],struct.pack('<II',0,7))
        with self.assertRaises(ExportError):graph.add('bad','record',108,1,8)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'capture';path.write_bytes(struct.pack('<QI',100,9)+bytes(8))
            with self.assertRaises(ExportError):load_capture(path)
            out=Path(tmp)/'graph';write_archive(graph,{'registrationReady':False},out)
            with self.assertRaises(FileExistsError):write_archive(graph,{},out)

if __name__=='__main__':unittest.main()
