import importlib.util
from pathlib import Path
import struct
import unittest

spec=importlib.util.spec_from_file_location('smoke',Path(__file__).parents[1]/'tools/iw5_preview_smoke.py')
smoke=importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke)

class SmokeTests(unittest.TestCase):
    def test_fixture_is_synthetic_octahedron(self):
        b=smoke.fixture()
        self.assertEqual(struct.unpack_from('<8s6I',b),(b'IW5GEO1\0',1,6,24,1,44,16))
        self.assertEqual(len(b),32+6*44+24*2+16)
        self.assertEqual(set(struct.unpack_from('<24H',b,32+6*44)),set(range(6)))
        self.assertEqual(struct.unpack_from('<IIHHI',b,len(b)-16),(0,0,6,8,0))
    def test_success_requires_completed_draw(self):
        self.assertTrue(smoke.valid_report({'status':'completed','index_count':24}))
        for r in [{},{'status':'error','index_count':24},{'status':'completed','index_count':0},{'status':'completed','index_count':3},{'status':'completed','index_count':'24'},None,[]]:
            self.assertFalse(smoke.valid_report(r))

if __name__=='__main__': unittest.main()
