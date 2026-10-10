"""Build a real combined ACR / USP .45 / MP7 conversion in a fresh local work folder.
No retail files are modified. Original data is never written into the repository.
"""
import argparse
import json
import shutil
import subprocess
from pathlib import Path
from build_acr import run
from convert_acr import convert, WEAPONS
from verify_pack import verify


def merge_raw(sources, target):
    for source in sources:
        for path in sorted(source.rglob('*')):
            if not path.is_file(): continue
            relative=path.relative_to(source); destination=target/relative
            if destination.exists():
                if destination.read_bytes()!=path.read_bytes(): raise ValueError(f'Conflicting converted asset: {relative}')
            else:
                destination.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(path,destination)


def extract_common(command, log):
    result=subprocess.run([str(value) for value in command],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    log.write_text(result.stdout)
    errors=[line for line in result.stdout.splitlines() if 'ERROR:' in line]
    if result.returncode or any(line.strip()!='ERROR: Unsupported IWI format: 9' for line in errors):
        raise RuntimeError(f'Common dependency extraction failed: {log}')
    # Some unrelated common images use an unsupported source encoding. Each
    # required weapon image is checked again by conversion and package roundtrip.
    return errors


def build(args):
    work=args.work.resolve()
    protected=[args.mw3.resolve(),args.cod4.resolve(),Path(__file__).resolve().parents[2]]
    if any(work==root or root in work.parents for root in protected):
        raise ValueError('--work must be outside retail installs and repository')
    if (work/'package/z_mw3_acr.iwd').exists(): raise ValueError('Refusing to overwrite an existing standalone ACR deliverable')
    work.mkdir(parents=True,exist_ok=True)
    dump=work/'extracted'; converted=work/'iw3'; roundtrip=work/'roundtrip'; package=work/'package'
    unlinker=args.oat_bin/'Unlinker.exe'; linker=args.oat_bin/'Linker.exe'
    mw3=args.mw3/'zone/english'; cod4=args.cod4/'zone/english'
    dump_warnings=[]
    if args.skip_extract and (work/'extract-common.log').exists():
        dump_warnings=[line for line in (work/'extract-common.log').read_text().splitlines() if 'ERROR:' in line]
    if not args.skip_extract:
        run([unlinker,'--include-assets','weapon,xmodel,material,image,xanim','--model-format','GLB','--image-format','DDS','-o',dump,mw3/'common_survival.ff'],work/'extract-survival.log')
        run([unlinker,'--include-assets','xanim','-o',dump,mw3/'common_mp.ff'],work/'extract-common-mp.log')
        dump_warnings=extract_common([unlinker,'--include-assets','material,image,xanim','--image-format','DDS','-o',dump,mw3/'common.ff'],work/'extract-common.log')
    native=run([unlinker,'--list',cod4/'common.ff'],work/'native-common-list.log')
    techset='mc_l_sm_r0c0n0'
    if f'techniqueset, {techset}' not in native.splitlines(): raise RuntimeError('Required native IW3 shader absent')
    reports=[]; roots=[]
    for target, identity in WEAPONS.items():
        folder=work/'individual'/target
        reports.append(convert(dump,dump/'weapons'/identity[0],args.oat_source,folder,techset,args.oat_bin/'ImageConverter.exe',target))
        roots.append(folder/'raw')
    merge_raw(roots,converted/'raw')
    report={'experimental':True,'weapon':'mw3_acr','weapons':list(WEAPONS), 'external_techsets':[techset]}
    for key in ('models','animations','materials','images','omitted_fields','limitations'):
        report[key]=sorted({item for source in reports for item in source[key]})
    report['individual_reports']=reports
    report['source_dump_warnings']=dump_warnings
    (converted/'conversion-report.json').write_text(json.dumps(report,indent=2))
    zone=converted/'zone_source/mod.zone'; zone.parent.mkdir(parents=True,exist_ok=True)
    zone.write_text('>game,IW3\n>name,mod\n'+f'techniqueset,,{techset}\n'+''.join(f'xanim,{name}\n' for name in report['animations'])+''.join(f'weapon,{name}\n' for name in WEAPONS))
    run([linker,'-v','-b',converted,'-l',cod4/'common.ff','-l',cod4/'code_post_gfx.ff','mod'],work/'link.log')
    ff=converted/'zone_out/mod/mod.ff'
    listing=run([unlinker,'--list',ff],work/'iw3-list.log')
    if "Zone 'mod' (IW3)" not in listing or any('weapon, '+name not in listing for name in WEAPONS): raise RuntimeError('IW3 asset identity validation failed')
    run([unlinker,'--model-format','GLB','--image-format','DDS','--search-path',converted/'raw','-o',roundtrip,ff],work/'roundtrip.log')
    result=verify(dump,converted,roundtrip,package)
    run([unlinker,'--model-format','GLB','--image-format','DDS','--search-path',package,'-o',work/'packaged-roundtrip',package/'mod.ff'],work/'package-check.log')
    result=verify(dump,converted,work/'packaged-roundtrip',package)
    result['source_dump_warnings']=dump_warnings
    result['native_shader_verified']=techset; result['packaged_unlink_errors']=0
    (package/'verification.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({'package':str(package),'weapons':result['weapons'],'models':len(result['models']),'animations':result['animations_identical'],'images':result['external_images']}))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('mw3','cod4','oat-bin','oat-source','work'): parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--skip-extract',action='store_true')
    build(parser.parse_args())
