"""Verify real ACR conversion roundtrip and package its external IW3 images."""
import argparse, hashlib, json, shutil, struct, zipfile
from pathlib import Path
from convert_acr import info_parse, WEAPONS


def glb_metadata(path):
    blob = path.read_bytes()
    length = struct.unpack_from('<I', blob, 12)[0]
    data = json.loads(blob[20:20+length])
    binary = blob[28+length:]
    positions = [data['accessors'][primitive['attributes']['POSITION']]['count']
                 for mesh in data['meshes'] for primitive in mesh['primitives']]
    joints = sorted(data['nodes'][j]['name'] for skin in data.get('skins',[]) for j in skin['joints'])
    parents = {data['nodes'][child]['name']:node['name'] for node in data['nodes']
               for child in node.get('children',[]) if data['nodes'][child].get('name') in joints}
    # The loader may reorder vertices/bones. Compare actual coordinates by value
    # with 0.0001-unit tolerance, not binary order or just matching vertex counts.
    position_ids = {primitive['attributes']['POSITION'] for mesh in data['meshes'] for primitive in mesh['primitives']}
    points = []
    for index in position_ids:
        accessor=data['accessors'][index]; view=data['bufferViews'][accessor['bufferView']]
        if accessor['componentType']!=5126 or accessor['type']!='VEC3': raise ValueError('Requires float3 GLB positions')
        offset=view.get('byteOffset',0)+accessor.get('byteOffset',0); stride=view.get('byteStride',12)
        points.extend(tuple(round(v,4) for v in struct.unpack_from('<3f',binary,offset+i*stride)) for i in range(accessor['count']))
    geometry_hash=hashlib.sha256(json.dumps(sorted(points)).encode()).hexdigest()
    return {'meshes':len(data['meshes']), 'positions':positions, 'position_hash':geometry_hash, 'joints':joints, 'parents':parents}


def verify(source, converted, roundtrip, package):
    report = json.loads((converted/'conversion-report.json').read_text())
    checked = {}
    for name in report['models']:
        original = json.loads((source/'xmodel'/f'{name}.json').read_text())
        result = json.loads((roundtrip/'xmodel'/f'{name}.json').read_text())
        assert result['_game']=='iw3' and len(original['lods'])==len(result['lods']), name
        checked[name] = []
        for a,b in zip(original['lods'], result['lods']):
            before,after = glb_metadata(source/a['file']),glb_metadata(roundtrip/b['file'])
            assert before==after, f'{name}: geometry counts/bone identity changed'
            checked[name].append(before)
    for name in report['animations']:
        assert (source/'xanim'/name).read_bytes()==(roundtrip/'xanim'/name).read_bytes(), name
    weapons=report.get('weapons', [report['weapon']])
    for target in weapons:
        fields=info_parse((roundtrip/'weapons'/target).read_text())
        original=info_parse((source/'weapons'/WEAPONS[target][0]).read_text())
        for field in ('gunModel','worldModel','reloadAnim','reloadEmptyAnim','fireAnim','weaponClass','clipSize','damage'):
            assert fields[field]==original[field], f'{target}: retained {field} differs'
    for name in report['images']:
        before=(source/'images'/f'{name}.dds').read_bytes()
        after=(roundtrip/'images'/f'{name}.dds').read_bytes()
        assert before[:4]==after[:4]==b'DDS ', name
        assert before[12:20]==after[12:20] and before[84:88]==after[84:88], f'{name}: image dimensions/encoding changed'
        assert before[128:]==after[128:], f'{name}: image mip payload changed'
        assert (converted/'raw/images'/f'{name}.iwi').read_bytes()[:4]==b'IWi\x06', name
    package.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(converted/'zone_out/mod/mod.ff',package/'mod.ff')
    archive_name='z_mw3_primary.iwd' if len(weapons)>1 else 'z_mw3_acr.iwd'
    with zipfile.ZipFile(package/archive_name,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for name in report['images']:
            archive.write(converted/'raw/images'/f'{name}.iwi',f'images/{name}.iwi')
    result = {'experimental':True,'models':checked,'animations_identical':len(report['animations']),
              'images_payload_identical':len(report['images']),'weapons':weapons,'external_images':len(report['images']),'limitations':report['limitations'],
              'sha256':{name:hashlib.sha256((package/name).read_bytes()).hexdigest() for name in ('mod.ff',archive_name)}}
    (package/'verification.json').write_text(json.dumps(result,indent=2))
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('source','converted','roundtrip','package'): parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    result=verify(args.source,args.converted,args.roundtrip,args.package)
    print(f"Verified {len(result['models'])} real models, {result['animations_identical']} byte-identical animations, {result['external_images']} external images")
