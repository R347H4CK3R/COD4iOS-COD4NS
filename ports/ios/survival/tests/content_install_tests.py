#!/usr/bin/env python3
"""Run the production installer against isolated folders using macOS Foundation."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[4]
source = (root / 'ports/ios/app/survival_ui.mm').read_text()
installer = source[source.index('BOOL KisakInstallSurvivalContent('):source.index('@implementation KISSurvivalUI')]
harness = r'''
#import <Foundation/Foundation.h>
#include <cassert>
''' + installer + r'''
int main() { @autoreleasepool {
    NSFileManager *fm = NSFileManager.defaultManager;
    NSString *bundle = NSBundle.mainBundle.resourcePath;
    NSString *source = [bundle stringByAppendingPathComponent:@"SurvivalContent/maps/specops_survival.gsc"];
    assert([fm createDirectoryAtPath:source.stringByDeletingLastPathComponent withIntermediateDirectories:YES attributes:nil error:NULL]);
    assert([@"bundled script" writeToFile:source atomically:YES encoding:NSUTF8StringEncoding error:NULL]);
    NSString *sourceV2 = [bundle stringByAppendingPathComponent:@"SurvivalContent/maps/specops_survival_v2.gsc"];
    assert([@"bundled v2 script" writeToFile:sourceV2 atomically:YES encoding:NSUTF8StringEncoding error:NULL]);
    NSString *sourceV3 = [bundle stringByAppendingPathComponent:@"SurvivalContent/maps/specops_survival_v3.gsc"];
    assert([@"bundled v3 script" writeToFile:sourceV3 atomically:YES encoding:NSUTF8StringEncoding error:NULL]);
    NSString *documents = [bundle stringByAppendingPathComponent:@"Documents"];
    assert([fm createDirectoryAtPath:documents withIntermediateDirectories:YES attributes:nil error:NULL]);
    NSError *error = nil;
    assert(KisakInstallSurvivalContent(documents, &error));
    NSString *destinationV3 = [documents stringByAppendingPathComponent:@"mods/specops_survival/maps/specops_survival_v3.gsc"];
    assert([[NSString stringWithContentsOfFile:destinationV3 encoding:NSUTF8StringEncoding error:NULL] isEqualToString:@"bundled v3 script"]);
    assert([@"user v3 script" writeToFile:destinationV3 atomically:YES encoding:NSUTF8StringEncoding error:NULL]);
    NSString *destination = [documents stringByAppendingPathComponent:@"mods/specops_survival/maps/specops_survival.gsc"];
    assert([@"user script" writeToFile:destination atomically:YES encoding:NSUTF8StringEncoding error:NULL]);
    assert(KisakInstallSurvivalContent(documents, &error));
    assert([[NSString stringWithContentsOfFile:destination encoding:NSUTF8StringEncoding error:NULL] isEqualToString:@"user script"]);
    assert([[NSString stringWithContentsOfFile:destinationV3 encoding:NSUTF8StringEncoding error:NULL] isEqualToString:@"user v3 script"]);
    NSString *assets=[bundle stringByAppendingPathComponent:@"SurvivalContent"];
    NSString *manifest=[assets stringByAppendingPathComponent:@"MW3Assets.json"];
    assert([@"[\"mod.ff\",\"z_mw3_acr.iwd\"]" writeToFile:manifest atomically:YES encoding:NSUTF8StringEncoding error:NULL]);
    assert([@"converted fastfile" writeToFile:[assets stringByAppendingPathComponent:@"mod.ff"] atomically:YES encoding:NSUTF8StringEncoding error:NULL]);
    assert([@"converted images" writeToFile:[assets stringByAppendingPathComponent:@"z_mw3_acr.iwd"] atomically:YES encoding:NSUTF8StringEncoding error:NULL]);
    assert(KisakInstallSurvivalContent(documents,&error));
    NSString *installedFF=[documents stringByAppendingPathComponent:@"mods/specops_survival/mod.ff"];
    NSString *installedIWD=[documents stringByAppendingPathComponent:@"mods/specops_survival/z_mw3_acr.iwd"];
    assert([[NSString stringWithContentsOfFile:installedFF encoding:NSUTF8StringEncoding error:NULL] isEqualToString:@"converted fastfile"]);
    assert([fm removeItemAtPath:installedIWD error:NULL]);
    assert([@"existing different mod" writeToFile:installedFF atomically:YES encoding:NSUTF8StringEncoding error:NULL]);
    assert(!KisakInstallSurvivalContent(documents,&error));
    assert(![fm fileExistsAtPath:installedIWD]);
    assert([[NSString stringWithContentsOfFile:installedFF encoding:NSUTF8StringEncoding error:NULL] isEqualToString:@"existing different mod"]);
    assert([fm removeItemAtPath:installedFF error:NULL]);
    assert(KisakInstallSurvivalContent(documents,&error));
    assert([@"[\"../mod.ff\"]" writeToFile:manifest atomically:YES encoding:NSUTF8StringEncoding error:NULL]);
    assert(!KisakInstallSurvivalContent(documents,&error));
    assert([@"[\"mod.ff\",\"z_mw3_acr.iwd\"]" writeToFile:manifest atomically:YES encoding:NSUTF8StringEncoding error:NULL]);
    assert([fm removeItemAtPath:installedIWD error:NULL]);
    assert([fm createSymbolicLinkAtPath:installedIWD withDestinationPath:installedFF error:NULL]);
    assert(!KisakInstallSurvivalContent(documents,&error));
    assert([fm removeItemAtPath:installedIWD error:NULL]);
    assert(KisakInstallSurvivalContent(documents,&error));
    assert([fm removeItemAtPath:manifest error:NULL]);
    NSString *destinationV2 = [documents stringByAppendingPathComponent:@"mods/specops_survival/maps/specops_survival_v2.gsc"];
    assert([[NSString stringWithContentsOfFile:destinationV2 encoding:NSUTF8StringEncoding error:NULL] isEqualToString:@"bundled v2 script"]);
    assert([@"user v2 script" writeToFile:destinationV2 atomically:YES encoding:NSUTF8StringEncoding error:NULL]);
    assert(KisakInstallSurvivalContent(documents, &error));
    assert([[NSString stringWithContentsOfFile:destinationV2 encoding:NSUTF8StringEncoding error:NULL] isEqualToString:@"user v2 script"]);
    assert([fm removeItemAtPath:destinationV2 error:NULL]);
    assert(KisakInstallSurvivalContent(documents, &error));
    assert([[NSString stringWithContentsOfFile:destination encoding:NSUTF8StringEncoding error:NULL] isEqualToString:@"user script"]);
    assert([[NSString stringWithContentsOfFile:destinationV2 encoding:NSUTF8StringEncoding error:NULL] isEqualToString:@"bundled v2 script"]);
    assert([fm removeItemAtPath:destinationV2 error:NULL]);
    assert([fm createSymbolicLinkAtPath:destinationV2 withDestinationPath:sourceV2 error:NULL]);
    assert(!KisakInstallSurvivalContent(documents, &error));
    assert([fm removeItemAtPath:destinationV2 error:NULL]);
    NSString *mod = [documents stringByAppendingPathComponent:@"mods/specops_survival"];
    assert([fm removeItemAtPath:mod error:NULL]);
    NSString *main = [documents stringByAppendingPathComponent:@"main"];
    assert([fm createDirectoryAtPath:main withIntermediateDirectories:YES attributes:nil error:NULL]);
    assert([fm createSymbolicLinkAtPath:mod withDestinationPath:main error:NULL]);
    assert(!KisakInstallSurvivalContent(documents, &error));
    assert(![fm fileExistsAtPath:[main stringByAppendingPathComponent:@"maps/specops_survival.gsc"]]);
    assert([fm removeItemAtPath:mod error:NULL]);
    assert([fm createSymbolicLinkAtPath:mod withDestinationPath:bundle error:NULL]);
    assert(!KisakInstallSurvivalContent(documents, &error));
    assert([fm removeItemAtPath:mod error:NULL]);
    assert([fm createDirectoryAtPath:destination withIntermediateDirectories:YES attributes:nil error:NULL]);
    assert(!KisakInstallSurvivalContent(documents, &error));
} }
'''
with tempfile.TemporaryDirectory(prefix='survival-install-test-') as directory:
    folder = Path(directory)
    code = folder / 'test.mm'
    executable = folder / 'installer-tests'
    code.write_text(harness)
    subprocess.run(['xcrun', 'clang++', '-std=c++17', '-framework', 'Foundation', str(code), '-o', str(executable)], check=True)
    subprocess.run([str(executable)], check=True)
print('Installer: copies missing versioned scripts, preserves both edits, rejects redirected paths and directories')

