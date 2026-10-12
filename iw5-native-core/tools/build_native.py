"""Build/test the portable snapshot core and verify its ARM64 iOS object.

All generated files stay in --build-dir. Optional snapshot input is read-only.
No game asset bytes are included in the build record or static library.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess


def inspect_ios_object(data):
    if len(data) < 32:
        raise ValueError('truncated Mach-O header')
    magic, cpu, _, kind, commands, command_bytes, _, _ = struct.unpack_from('<8I', data)
    if (magic, cpu, kind) != (0xfeedfacf, 0x100000c, 1):
        raise ValueError('expected an ARM64 Mach-O relocatable object')
    end = 32 + command_bytes
    if end > len(data) or commands > command_bytes // 8:
        raise ValueError('invalid load command bounds')
    offset, versions = 32, []
    for _ in range(commands):
        if offset + 8 > end:
            raise ValueError('truncated load command')
        command, size = struct.unpack_from('<II', data, offset)
        if size < 8 or size % 8 or offset + size > end:
            raise ValueError('invalid load command size')
        if command == 0x32:
            if size < 24:
                raise ValueError('truncated build-version command')
            platform, minimum, sdk, tools = struct.unpack_from('<4I', data, offset + 8)
            if tools > (size - 24) // 8:
                raise ValueError('truncated build tools')
            versions.append((platform, minimum, sdk))
        offset += size
    if offset != end or len(versions) != 1 or versions[0][:2] != (2, 17 << 16):
        raise ValueError('expected exactly one iOS 17.0 build-version command')
    return {'format': 'Mach-O object', 'architecture': 'arm64', 'platform': 'iOS',
            'minimum_os': '17.0.0', 'sdk_version_field': versions[0][2],
            'size': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
            'limitation': 'Object metadata only; not an Xcode app link, IPA, signing or device execution test.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zig', type=Path, required=True)
    parser.add_argument('--build-dir', type=Path, required=True)
    parser.add_argument('--snapshot', type=Path)
    parser.add_argument('--prior-repo', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    build = args.build_dir.resolve()
    if build == root or build.is_relative_to(root / 'native'):
        parser.error('build directory must be separate from native source')
    build.mkdir(parents=True, exist_ok=True)
    zig = args.zig.resolve()
    record = {'schema_version': 1, 'steps': [], 'native_gameplay': False}

    def run(command):
        command = list(map(str, command))
        result = subprocess.run(command, cwd=build, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        step = {'command': command, 'exit_code': result.returncode, 'output': result.stdout}
        record['steps'].append(step)
        (build / 'build-record.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
        if result.returncode:
            raise RuntimeError(f'Command failed: {command[1:]}\n{result.stdout}')
        return result.stdout.strip()

    record['zig_version'] = run([zig, 'version'])
    record['zig_sha256'] = hashlib.sha256(zig.read_bytes()).hexdigest()
    native = root / 'native'
    source = native / 'src/iw5geo.c'
    common = [zig, 'cc', '-std=c11', '-Wall', '-Wextra', '-Wpedantic', '-Werror', '-I', native / 'include']
    suffix = '.exe' if os.name == 'nt' else ''
    tests = build / ('iw5geo-tests' + suffix)
    run(common + ['-O1', '-g', '-fsanitize=undefined', '-fno-sanitize-recover=all', source, native / 'tests/iw5geo_tests.c', '-o', tests])
    record['native_tests'] = run([tests])
    inspect = build / ('iw5geo-inspect' + suffix)
    run(common + ['-O2', source, native / 'tools/iw5geo_inspect.c', '-o', inspect])
    obj = build / 'iw5geo-ios-arm64.o'
    run(common + ['-O2', '-ffreestanding', '-target', 'aarch64-ios.17.0', '-c', source, '-o', obj])
    record['ios_object'] = inspect_ios_object(obj.read_bytes())
    archive = build / 'libiw5geo-ios-arm64.a'
    # Delete only this generated archive before ar, avoiding stale members across builds.
    if archive.exists():
        archive.unlink()
    run([zig, 'ar', 'rcs', archive, obj])
    record['archive_members'] = run([zig, 'ar', 't', archive]).splitlines()
    if record['archive_members'] != [obj.name]:
        raise RuntimeError('unexpected static archive members')
    record['archive_sha256'] = hashlib.sha256(archive.read_bytes()).hexdigest()
    record['source_sha256'] = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in sorted(native.rglob('*')) if p.is_file()}
    if args.snapshot:
        snapshot = args.snapshot.resolve()
        record['snapshot_summary'] = json.loads(run([inspect, snapshot]))
        # Hash the separately held local input without copying it into a deliverable.
        with snapshot.open('rb') as stream:
            digest = hashlib.sha256()
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(chunk)
        record['snapshot_sha256'] = digest.hexdigest()
        if args.prior_repo:
            prior = args.prior_repo.resolve()
            record['prior_commit'] = run(['git', '-C', prior, 'rev-parse', 'HEAD'])
            assets = prior / 'ports/ios/assets'
            host_object = build / 'iw5geo-host.o'
            run(common + ['-O1', '-g', '-fsanitize=undefined', '-fno-sanitize-recover=all', '-c', source, '-o', host_object])
            compare = build / ('iw5geo-compare' + suffix)
            run([zig, 'c++', '-std=c++17', '-O1', '-g', '-fsanitize=undefined', '-fno-sanitize-recover=all',
                 '-I', native / 'include', '-I', assets, native / 'tests/compare_prior.cpp',
                 assets / 'IW5Geometry.cpp', host_object, '-o', compare])
            record['prior_comparison'] = json.loads(run([compare, snapshot]))
            record['prior_file_sha256'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                           for p in [assets / n for n in ('IW5Geometry.cpp', 'IW5Geometry.hpp', 'BspLoader.hpp')]}
    (build / 'build-record.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print(record['native_tests'])
    print('Verified ARM64 iOS 17.0 object and archive:', archive)
    if 'prior_comparison' in record:
        print('All decoded positions, normals, colors, indices and bounds match the prior reader.')
    print('Build evidence:', build / 'build-record.json')


if __name__ == '__main__':
    main()
