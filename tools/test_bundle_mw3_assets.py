import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

spec = importlib.util.spec_from_file_location('bundler', Path(__file__).with_name('bundle-mw3-assets.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class BundleTests(unittest.TestCase):
    def test_preserves_app_and_bundles_all_dependencies(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);assets=root/'assets';assets.mkdir()
            for name in ('mod.ff','z_acr.iwd','z_future.iwd'): (assets/name).write_bytes(name.encode())
            ipa=root/'input.ipa';output=root/'personal.ipa'
            with zipfile.ZipFile(ipa,'w') as z:
                z.writestr(module.PREFIX+'maps/specops_survival_v3.gsc','script')
                z.writestr('Payload/KisakCOD.app/KisakCOD',b'unchanged launcher')
                for engine in ('sp','mp'):
                    z.writestr('Payload/KisakCOD.app/Frameworks/libkisakcod_'+engine+'.dylib',b'engine MW3Assets.json')
            original=ipa.read_bytes()
            sidecar=output.with_suffix('.json');sidecar.write_text('existing report')
            with self.assertRaises(ValueError):module.bundle(ipa,assets,output)
            self.assertEqual(sidecar.read_text(),'existing report')
            self.assertFalse(output.exists())
            sidecar.unlink()
            report=module.bundle(ipa,assets,output)
            self.assertEqual(ipa.read_bytes(),original)
            self.assertEqual(len(report['assets']),3)
            with zipfile.ZipFile(output) as z:
                self.assertEqual(z.read('Payload/KisakCOD.app/KisakCOD'),b'unchanged launcher')
            with self.assertRaises(ValueError):module.bundle(ipa,assets,ipa)
            with self.assertRaises(ValueError):module.bundle(ipa,assets,output)

    def test_pregame_catalog_from_verified_local_pack(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); assets=root/'assets';assets.mkdir()
            (assets/'mod.ff').write_bytes(b'converted')
            (assets/'verification.json').write_text(json.dumps({'weapons':['mw3_usp45','mw3_mp7','mw3_acr']}))
            with zipfile.ZipFile(assets/'z_mw3_rules.iwd','w') as z:
                z.writestr('mw3/survival/rank.csv','idx,name,xp\n'+''.join(f'{i},TEST,{i*100}\n' for i in range(50)))
            ipa=root/'input.ipa'
            with zipfile.ZipFile(ipa,'w') as z:
                z.writestr(module.PREFIX+'maps/specops_survival_v4.gsc','script')
                for engine in ('sp','mp'):
                    z.writestr('Payload/KisakCOD.app/Frameworks/libkisakcod_'+engine+'.dylib',b'engine MW3Assets.json')
            module.bundle(ipa,assets,root/'personal.ipa')
            with zipfile.ZipFile(root/'personal.ipa') as z:
                catalog=json.loads(z.read(module.PREFIX+'MW3Catalog.json'))
                self.assertEqual(catalog['weapons'],['mw3_usp45','mw3_mp7','mw3_acr'])
                self.assertEqual(catalog['rankThresholds'],list(range(0,5000,100)))
            (assets/'verification.json').write_text(json.dumps({'weapons':['not_verified']}))
            with self.assertRaises(ValueError):module.bundle(ipa,assets,root/'invalid.ipa')
            self.assertFalse((root/'invalid.ipa').exists())

    def test_rejects_incomplete_pack(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with self.assertRaises(ValueError):module.bundle(root/'missing.ipa',root,root/'out.ipa')

if __name__=='__main__':unittest.main()
