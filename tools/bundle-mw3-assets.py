#!/usr/bin/env python3
"""Bundle locally converted MW3 FF/IWD dependencies into a personal unsigned IPA.

Never uploads retail data. Run after the public source-only CI build. The app
installs this manifest's files into its isolated Survival mod without replacing
existing differing files. Keep the source installation and public IPA intact.
"""
import argparse
import csv
import io
import hashlib
import json
from pathlib import Path
import zipfile

PREFIX = 'Payload/KisakCOD.app/SurvivalContent/'

def bundle(ipa, assets, output):
    ipa, assets, output = map(Path, (ipa, assets, output))
    if output.suffix.lower() != '.ipa' or output.with_suffix('.json').exists():
        raise ValueError('Use a new IPA and checksum report destination')
    if output.resolve() == ipa.resolve() or output.exists():
        raise ValueError('Use a new output file; input IPA is preserved')
    files = sorted(p for p in assets.iterdir() if p.suffix in {'.ff', '.iwd'})
    if not any(p.name == 'mod.ff' for p in files) or not any(p.suffix == '.iwd' for p in files):
        raise ValueError('Converted mod.ff and its texture IWD are required')
    if any(not p.is_file() or p.is_symlink() for p in files):
        raise ValueError('Asset inputs must be regular files')
    catalog = None
    verification = assets/'verification.json'
    rules = assets/'z_mw3_rules.iwd'
    if verification.is_file() and rules.is_file():
        verified = json.loads(verification.read_text())
        weapons = verified.get('weapons', [])
        if not isinstance(weapons, list) or any(w not in {'mw3_usp45','mw3_mp7','mw3_acr'} for w in weapons):
            raise ValueError('Invalid converted weapon catalog')
        with zipfile.ZipFile(rules) as data:
            ranks = [int(row[2]) for row in csv.reader(io.StringIO(data.read('mw3/survival/rank.csv').decode('utf-8-sig'))) if row and row[0].isdigit()]
        if len(ranks)!=50 or ranks[0]!=0 or any(a>=b for a,b in zip(ranks,ranks[1:])):
            raise ValueError('Invalid original rank thresholds')
        catalog = {'version':1,'weapons':weapons,'rankThresholds':ranks}
    with zipfile.ZipFile(ipa) as source:
        if source.testzip() is not None:
            raise ValueError('Input IPA is corrupt')
        names = source.namelist()
        engine_paths = ['Payload/KisakCOD.app/Frameworks/libkisakcod_sp.dylib',
                        'Payload/KisakCOD.app/Frameworks/libkisakcod_mp.dylib']
        if any(path not in names or b'MW3Assets.json' not in source.read(path) for path in engine_paths):
            raise ValueError('IPA lacks automatic bundled-asset installation support')
        if not any(PREFIX+'maps/specops_survival_'+version+'.gsc' in names for version in ('v3','v4')):
            raise ValueError('IPA lacks the converted-weapon Survival entry')
        if any(n == PREFIX+'MW3Assets.json' or n == PREFIX+p.name for n in names for p in files):
            raise ValueError('IPA already contains an asset pack')
        if any('_CodeSignature/' in n or n.endswith('embedded.mobileprovision') for n in names):
            raise ValueError('Bundle before signing the IPA')
        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output, 'x', zipfile.ZIP_DEFLATED) as target:
            for entry in source.infolist():
                target.writestr(entry, source.read(entry.filename))
            for path in files:
                target.write(path, PREFIX+path.name)
            target.writestr(PREFIX+'MW3Assets.json', json.dumps([p.name for p in files]))
            if catalog is not None:
                target.writestr(PREFIX+'MW3Catalog.json', json.dumps(catalog))
    with zipfile.ZipFile(output) as result:
        assert result.testzip() is None
        for path in files:
            assert result.read(PREFIX+path.name) == path.read_bytes()
    return {'personalAssetsIncluded': True, 'unsigned': True,
            'ipaSHA256': hashlib.sha256(output.read_bytes()).hexdigest(),
            'assets': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ipa', required=True, type=Path)
    parser.add_argument('--assets', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    report = bundle(args.ipa, args.assets, args.output)
    with args.output.with_suffix('.json').open('x') as sidecar:
        sidecar.write(json.dumps(report, indent=2)+'\n')
    print('Personal unsigned IPA bundled and verified')
