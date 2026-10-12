import importlib.util
from pathlib import Path
import struct
import unittest
from unittest.mock import patch
import json
import tempfile
from types import SimpleNamespace

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
    def run_probe(self,result,screenshot_fails=False):
        calls=[]
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'data/Documents').mkdir(parents=True)
            def fake_run(args,**kwargs):
                action=args[2];calls.append(args[2:]);out='';code=0
                if action=='list':out=json.dumps({'devices':{'com.apple.CoreSimulator.SimRuntime.iOS-18-5':[{'isAvailable':True,'name':'iPhone Test','deviceTypeIdentifier':'test-type'}]}})
                elif action=='create':out='own-device-id'
                elif action=='get_app_container':out=str(root/'data')
                elif action=='launch':(root/'data/Documents/iw5-render-smoke.json').write_text(json.dumps(result))
                elif action=='io' and screenshot_fails:code=1
                return SimpleNamespace(returncode=code,stdout=out,stderr='failure' if code else '')
            with patch.object(smoke.subprocess,'run',side_effect=fake_run),patch.object(smoke.time,'sleep'):
                if not smoke.valid_report(result) or screenshot_fails:
                    with self.assertRaises(RuntimeError):smoke.probe(root/'app',root/'out')
                else:smoke.probe(root/'app',root/'out')
            self.assertIn(['shutdown','own-device-id'],calls)
            self.assertEqual(calls[-1],['delete','own-device-id'])
            record=json.loads((root/'out/probe.json').read_text())
            self.assertEqual(record['render_verified'],smoke.valid_report(result))
    def test_probe_success_cleans_up(self):self.run_probe({'status':'completed','index_count':24})
    def test_probe_gpu_error_fails_and_cleans_up(self):self.run_probe({'status':'error','index_count':24})
    def test_screenshot_failure_still_cleans_up(self):self.run_probe({'status':'completed','index_count':24},True)

if __name__=='__main__': unittest.main()
