#!/usr/bin/env python3
"""Bundle locally converted MW3 FF/IWD dependencies into a personal unsigned IPA.

Never uploads retail data. Run after the public source-only CI build. The app
installs this manifest's files into its isolated Survival mod without replacing
existing differing files. Keep the source installation and public IPA intact.
"""
import argparse
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
    with zipfile.ZipFile(ipa) as source:
        if source.testzip() is not None:
            raise ValueError('Input IPA is corrupt')
        names = source.namelist()
        if b'MW3Assets.json' not in source.read('Payload/KisakCOD.app/KisakCOD'):
            raise ValueError('IPA lacks automatic bundled-asset installation support')
        if PREFIX+'maps/specops_survival_v3.gsc' not in names:
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
