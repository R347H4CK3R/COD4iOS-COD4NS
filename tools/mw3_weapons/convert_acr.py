"""Experimental real MW3 ACR -> IW3 source conversion; no retail data bundled.

Requires an OAT dump (GLB, DDS, xanim), the IW5 weapon dump,
and the matching official OAT source checkout for IW3 field/technique enums.
Native IW3 techsets are external dependencies, never fabricated shader assets.
"""
import argparse, json, re, shutil, struct, subprocess
from pathlib import Path


def info_parse(text):
    parts = text.split('\\')
    if parts[0] != 'WEAPONFILE' or len(parts) % 2 != 1:
        raise ValueError('Invalid WEAPONFILE key/value serialization')
    return dict(zip(parts[1::2], parts[2::2]))


def info_write(fields):
    return 'WEAPONFILE' + ''.join('\\' + k + '\\' + v for k, v in fields.items())


def techniques(header):
    body = header.split('enum MaterialTechniqueType')[1].split('};')[0]
    return {name: int(value, 0) for name, value in re.findall(r'(TECHNIQUE_\w+)\s*=\s*(0x[0-9A-Fa-f]+|\d+)', body)
            if not name.endswith(('_BEGIN', '_END', '_COUNT', '_NONE'))}


def convert_material(data, target_techset, iw3, iw5):
    data = json.loads(json.dumps(data))
    data['_game'] = 'iw3'
    data['cameraRegion'] = 'emissive' if data['cameraRegion'] == 'emissive' else 'lit'
    data['techniqueSet'] = target_techset
    entries = [-1] * 34
    for name, index in iw3.items():
        if index < len(entries) and name in iw5:
            entries[index] = data['stateBitsEntry'][iw5[name]]
    data['stateBitsEntry'] = entries
    for state in data['stateBits']:
        state.pop('gammaWrite', None)
    # Detail/specular channel encodings differ. Prototype uses original color
    # and normal images; no MW3 packed specular channel is misrepresented.
    data['textures'] = [t for t in data['textures'] if t['name'] in ('colorMap', 'normalMap')]
    return data


WEAPONS = {
    'mw3_acr': ('iw5_acr_mp', 'viewmodel_remington_acr_iw5', 'weapon_remington_acr_iw5', 'MW3 ACR'),
    'mw3_usp45': ('iw5_usp45_mp', 'viewmodel_usp45_iw5', 'weapon_usp45_iw5', 'MW3 USP .45'),
    'mw3_mp7': ('iw5_mp7_mp', 'viewmodel_mp7_iw5', 'weapon_mp7_iw5', 'MW3 MP7'),
}

def validate_weapon(fields, target):
    if target not in WEAPONS: raise ValueError('Unsupported original weapon identity')
    _, gun, world, _ = WEAPONS[target]
    if fields.get('gunModel') != gun or fields.get('worldModel') != world:
        raise ValueError('Requires actual original MW3 weapon models, not a renamed replacement')

def convert(dump, weapon, oat_source, output, techset, image_converter=None, target='mw3_acr'):
    raw = output / 'raw'; raw.mkdir(parents=True, exist_ok=True)
    report = {'experimental': True, 'weapon': target, 'external_techsets': [techset],
              'omitted_fields': [], 'models': [], 'animations': [], 'materials': [], 'images': []}
    fields_source = (oat_source/'src/ObjCommon/Game/IW3/Weapon/WeaponFields.h').read_text()
    types = dict(re.findall(r'\{"([^"]+)"[^\n]*?,\s*(\w+)\s*\}', fields_source))
    original_fields = info_parse(weapon.read_text())
    validate_weapon(original_fields, target)
    fields = {k: v for k, v in original_fields.items() if k in types}
    iw3 = techniques((oat_source/'src/Common/Game/IW3/IW3_Assets.h').read_text())
    iw5 = techniques((oat_source/'src/Common/Game/IW5/IW5_Assets.h').read_text())
    materials = set(); images = set(); models = set(); animations = set()

    def copy(rel):
        src = dump / rel; dst = raw / rel
        if not src.is_file(): raise FileNotFoundError(src)
        dst.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(src, dst)

    for key, value in list(fields.items()):
        kind = types[key]
        if kind == 'CSPFT_XMODEL':
            # Base ACR variant only. MW3 hand rig replaces its unresolved base-hand reference.
            if key == 'handModel': value = fields[key] = 'viewhands_delta'
            if key not in ('gunModel', 'worldModel', 'handModel'): fields[key] = ''; continue
            if value: models.add(value)
        elif kind == 'WFT_ANIM_NAME' and value:
            animations.add(value)
        elif kind == 'CSPFT_MATERIAL' and value:
            # HUD/reticle references need separate IW3 UI shader conversion.
            report['omitted_fields'].append(key); fields[key] = ''
        elif kind in ('CSPFT_SOUND', 'CSPFT_FX', 'WFT_BOUNCE_SOUND', 'WFT_NOTETRACKSOUNDMAP') and value:
            report['omitted_fields'].append(key); fields[key] = ''
    fields['displayName'] = WEAPONS[target][3] + ' (conversion prototype)'
    # ACR has no usable alt attachment in this base-only pack.
    if 'altWeapon' in fields: fields['altWeapon'] = ''
    for model in sorted(models):
        data = json.loads((dump/'xmodel'/f'{model}.json').read_text()); data['_game'] = 'iw3'
        data.pop('physCollmap', None); data.pop('physPreset', None)
        for lod in data['lods']:
            copy(lod['file'])
            model_file = dump/lod['file']
            if model_file.suffix != '.glb':
                raise ValueError('OAT Linker requires GLB/GLTF; re-export models as GLB')
            blob = model_file.read_bytes()
            magic, version, size, json_size, chunk_type = struct.unpack_from('<5I', blob)
            if magic != 0x46546C67 or version != 2 or size != len(blob) or chunk_type != 0x4E4F534A:
                raise ValueError('Invalid GLB model')
            model_json = json.loads(blob[20:20+json_size])
            materials.update(m['name'] for m in model_json.get('materials', []))
        dst = raw/'xmodel'/f'{model}.json'; dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(json.dumps(data, indent=2))
    for material in sorted(materials):
        data = json.loads((dump/'materials'/f'{material}.json').read_text())
        data = convert_material(data, techset, iw3, iw5)
        for texture in data['textures']: images.add(texture['image'])
        dst = raw/'materials'/f'{material}.json'; dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(json.dumps(data, indent=2))
    for image in sorted(images): copy(f'images/{image}.dds')
    if image_converter:
        subprocess.run([str(image_converter), '--iw3'] + [str(raw/'images'/f'{image}.dds') for image in sorted(images)], check=True)
    for anim in sorted(animations): copy(f'xanim/{anim}')
    for field, directory in [('aiVsAiAccuracyGraph','aivsai'), ('aiVsPlayerAccuracyGraph','aivsplayer')]:
        name = fields.get(field)
        if name:
            rel = Path('accuracy')/directory/name
            src = weapon.parent.parent/rel
            dst = raw/rel; dst.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(src,dst)
    dst = raw/'weapons'/target; dst.parent.mkdir(parents=True, exist_ok=True); dst.write_text(info_write(fields))
    zone = output/'zone_source'/'mod.zone'; zone.parent.mkdir(parents=True, exist_ok=True)
    zone.write_text('>game,IW3\n>name,mod\n' + f'techniqueset,,{techset}\n' +
                    ''.join(f'xanim,{a}\n' for a in sorted(animations)) + f'weapon,{target}\n')
    for key, value in [('models',models),('animations',animations),('materials',materials),('images',images)]: report[key] = sorted(value)
    report['limitations'] = ['External native IW3 techset must be verified against retail common.ff',
                             'Sound and muzzle FX deliberately omitted; original audio conversion not implemented',
                             'MW3 viewhands and animation rig require device pose validation',
                             'Specular/detail textures omitted pending channel and shader conversion',
                             'Binary roundtrip does not prove in-game rendering or gameplay']
    (output/'conversion-report.json').write_text(json.dumps(report, indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('dump','weapon','oat-source','output'): parser.add_argument('--'+name, required=True, type=Path)
    parser.add_argument('--techset', required=True, help='Verified native IW3 model techset name')
    parser.add_argument('--image-converter', type=Path, help='OAT ImageConverter executable; required to produce IW3 IWI images')
    args = parser.parse_args()
    report = convert(args.dump,args.weapon,args.oat_source,args.output,args.techset,args.image_converter)
    print(json.dumps({k: len(report[k]) for k in ('models','animations','materials','images')}))
