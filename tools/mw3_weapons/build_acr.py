"""Build a local experimental ACR pack from the user's read-only retail installs.

All dumps, logs and proprietary outputs go to --work (outside the source repo).
Nothing is installed into either retail game or copied into the iOS bundle.
"""
import argparse, json, subprocess
from pathlib import Path
from convert_acr import convert
from verify_pack import verify


def run(command, log):
    result=subprocess.run([str(x) for x in command],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    log.write_text(result.stdout)
    if result.returncode or 'ERROR:' in result.stdout:
        raise RuntimeError(f'Conversion failed; inspect {log}')
    return result.stdout


def build(args):
    work=args.work.resolve()
    protected=[args.mw3.resolve(),args.cod4.resolve(),Path(__file__).resolve().parents[2]]
    if any(work==root or root in work.parents for root in protected):
        raise ValueError('--work must be outside both retail installs and the source repository')
    args.work.mkdir(parents=True,exist_ok=True)
    dump=args.work/'extracted'; converted=args.work/'iw3'; roundtrip=args.work/'roundtrip'; package=args.work/'package'
    unlinker=args.oat_bin/'Unlinker.exe'; linker=args.oat_bin/'Linker.exe'
    mw3=args.mw3/'zone/english'; cod4=args.cod4/'zone/english'
    if not args.skip_extract:
        run([unlinker,'--include-assets','weapon,xmodel,material,image,xanim','--model-format','GLB','--image-format','DDS',
             '-o',dump,mw3/'common_survival.ff'],args.work/'extract-survival.log')
        run([unlinker,'--include-assets','xanim','-o',dump,mw3/'common_mp.ff'],args.work/'extract-common-mp.log')
    native=run([unlinker,'--list',cod4/'common.ff'],args.work/'native-common-list.log')
    techset='mc_l_sm_r0c0n0'
    if f'techniqueset, {techset}' not in native.splitlines():
        raise RuntimeError(f'Required genuine COD4 shader {techset} absent; refusing dummy shader')
    report=convert(dump,dump/'weapons/iw5_acr_mp',args.oat_source,converted,techset,args.oat_bin/'ImageConverter.exe')
    run([linker,'-v','-b',converted,'-l',cod4/'common.ff','-l',cod4/'code_post_gfx.ff','mod'],args.work/'link.log')
    ff=converted/'zone_out/mod/mod.ff'
    listing=run([unlinker,'--list',ff],args.work/'iw3-list.log')
    if "Zone 'mod' (IW3)" not in listing or 'weapon, mw3_acr' not in listing:
        raise RuntimeError('Output failed IW3 asset identity validation')
    run([unlinker,'--model-format','GLB','--image-format','DDS','--search-path',converted/'raw','-o',roundtrip,ff],args.work/'roundtrip.log')
    verification=verify(dump,converted,roundtrip,package)
    run([unlinker,'--model-format','GLB','--image-format','DDS','--search-path',package,'-o',args.work/'packaged-roundtrip',package/'mod.ff'],args.work/'package-check.log')
    verification['native_shader_verified']=techset
    verification['packaged_unlink_errors']=0
    (package/'verification.json').write_text(json.dumps(verification,indent=2))
    print(f'Experimental real ACR pack: {package} (device validation still required)')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('mw3','cod4','oat-bin','oat-source','work'): parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--skip-extract',action='store_true',help='Reuse existing GLB/DDS/weapon/animation dump')
    build(parser.parse_args())
