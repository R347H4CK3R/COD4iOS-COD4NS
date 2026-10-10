import struct,unittest
from test_export_oat_collision import fixture,BASE
from export_oat_brushes import serialize_brushes,ExportError

def full_fixture():
    data=fixture()
    struct.pack_into('<I',data,20,BASE+900)
    struct.pack_into('<Iii',data,900,BASE+940,123,456)
    data[940:945]=b'test\0'
    return data
class BrushExportTests(unittest.TestCase):
    def load(self,data):return serialize_brushes([(BASE,bytes(data))],BASE,'mp_test')
    def test_full_record(self):
        data=self.load(full_fixture())
        self.assertEqual(data[:8],b'IW5BRSH1')
        self.assertEqual(struct.unpack_from('<6I',data,8),(1,1,1,1,0,1))
        self.assertEqual(len(data),32+20+8+36+24+4+72)
        self.assertEqual(struct.unpack_from('<I',data,52)[0],0)
        self.assertEqual(data[-72:-68],b'test')
    def test_long_material_fatal(self):
        data=full_fixture();data[940:1005]=b'x'*64+b'\0'
        with self.assertRaises(ExportError):self.load(data)
    def test_edge_pointer_and_face_index(self):
        data=full_fixture();struct.pack_into('<II',data,32,3,BASE+1100)
        struct.pack_into('<I',data,668,BASE+1100);data[690]=3
        data[1100:1103]=bytes([0,1,2])
        self.load(data)
        data[1100]=7
        with self.assertRaises(ExportError):self.load(data)
    def test_unreadable_material_name(self):
        data=full_fixture();struct.pack_into('<I',data,900,0xfffffff0)
        with self.assertRaises(ExportError):self.load(data)
if __name__=='__main__':unittest.main()
