#!/usr/bin/env python3
"""Run the production installer against isolated folders using macOS Foundation."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[4]
source = (root / 'ports/ios/app/survival_ui.mm').read_text(encoding='utf-8')
installer = source[source.index('BOOL KisakInstallSurvivalContent('):source.index('@implementation KISSurvivalUI')]
legacy_expression=source[source.index('BOOL trustedLegacy=')+len('BOOL trustedLegacy='):source.index(';',source.index('BOOL trustedLegacy='))]
harness = '#import <Foundation/Foundation.h>\nBOOL FixtureLegacyTrusted(NSString *name,NSString *current) {return '+legacy_expression+';}\n'+ r'''
#import <Foundation/Foundation.h>
#import <CommonCrypto/CommonDigest.h>
#include <cassert>
''' + installer + r'''
NSString *FixtureHash(NSString *path) {
    NSData *data=[NSData dataWithContentsOfFile:path]; unsigned char digest[CC_SHA256_DIGEST_LENGTH];
    CC_SHA256(data.bytes,(CC_LONG)data.length,digest); NSMutableString *result=[NSMutableString new];
    for(unsigned char byte:digest) [result appendFormat:@"%02x",byte]; return result;
}
int main() { @autoreleasepool {
    assert(FixtureLegacyTrusted(@"mod.ff",@"a1fd9764833341ab6f400bfa5dc4c2e9d3a8113b32a0223f477b987cc8fffc47"));
    assert(FixtureLegacyTrusted(@"z_mw3_acr.iwd",@"e4624e12d0e0176b130c072ba49588859c70fbb7c2e76d2e2f36e9002d2eb27a"));
    assert(!FixtureLegacyTrusted(@"other.ff",@"a1fd9764833341ab6f400bfa5dc4c2e9d3a8113b32a0223f477b987cc8fffc47"));
    assert(!FixtureLegacyTrusted(@"mod.ff",@"a1fd9764833341ab6f400bfa5dc4c2e9d3a8113b32a0223f477b987cc8fffc48"));
    NSFileManager *fm = NSFileManager.defaultManager;
    NSString *bundle = NSBundle.mainBundle.resourcePath;
    NSString *source = [bundle stringByAppendingPathComponent:@"SurvivalContent/maps/specops_survival.gsc"];
    assert([fm createDirectoryAtPath:source.stringByDeletingLastPathComponent withIntermediateDirectories:YES attributes:nil error:NULL]);
    assert([@"bundled script" writeToFile:source atomically:YES encoding:NSUTF8StringEncoding error:NULL]);
    NSString *sourceV2 = [bundle stringByAppendingPathComponent:@"SurvivalContent/maps/specops_survival_v2.gsc"];
    assert([@"bundled v2 script" writeToFile:sourceV2 atomically:YES encoding:NSUTF8StringEncoding error:NULL]);
    NSString *sourceV3 = [bundle stringByAppendingPathComponent:@"SurvivalContent/maps/specops_survival_v3.gsc"];
    assert([@"bundled v3 script" writeToFile:sourceV3 atomically:YES encoding:NSUTF8StringEncoding error:NULL]);
    assert([@"bundled v4 script" writeToFile:[bundle stringByAppendingPathComponent:@"SurvivalContent/maps/specops_survival_v4.gsc"] atomically:YES encoding:NSUTF8StringEncoding error:NULL]);
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
    NSString *managedPath=[documents stringByAppendingPathComponent:@"mods/specops_survival/.mw3-managed.json"];
    assert([fm fileExistsAtPath:managedPath]);
    assert([@"upgraded three-weapon fastfile" writeToFile:[assets stringByAppendingPathComponent:@"mod.ff"] atomically:YES encoding:NSUTF8StringEncoding error:NULL]);
    assert([@"upgraded images" writeToFile:[assets stringByAppendingPathComponent:@"z_mw3_acr.iwd"] atomically:YES encoding:NSUTF8StringEncoding error:NULL]);
    assert(KisakInstallSurvivalContent(documents,&error));
    assert([[NSString stringWithContentsOfFile:installedFF encoding:NSUTF8StringEncoding error:NULL] isEqualToString:@"upgraded three-weapon fastfile"]);
    assert([[NSString stringWithContentsOfFile:installedIWD encoding:NSUTF8StringEncoding error:NULL] isEqualToString:@"upgraded images"]);
    NSString *assetRoot=installedFF.stringByDeletingLastPathComponent;
    BOOL oldBackupFound=NO;
    for(NSString *name in [fm contentsOfDirectoryAtPath:assetRoot error:NULL]) if([name hasPrefix:@".mw3-backup-"]) {
        NSString *oldFF=[[assetRoot stringByAppendingPathComponent:name] stringByAppendingPathComponent:@"mod.ff"];
        if([[NSString stringWithContentsOfFile:oldFF encoding:NSUTF8StringEncoding error:NULL] isEqualToString:@"converted fastfile"]) oldBackupFound=YES;
    }
    assert(oldBackupFound);
    // Simulate termination between the two moves. Resume rolls back the entire
    // partial pack from verified backups before installing the current bundle.
    NSDictionary *prior=[NSJSONSerialization JSONObjectWithData:[NSData dataWithContentsOfFile:managedPath] options:0 error:NULL];
    NSString *backupName=@".mw3-backup-test-interrupted";
    NSString *backup=[assetRoot stringByAppendingPathComponent:backupName];
    assert([fm createDirectoryAtPath:backup withIntermediateDirectories:NO attributes:nil error:NULL]);
    assert([fm copyItemAtPath:installedFF toPath:[backup stringByAppendingPathComponent:@"mod.ff"] error:NULL]);
    assert([fm copyItemAtPath:installedIWD toPath:[backup stringByAppendingPathComponent:@"z_mw3_acr.iwd"] error:NULL]);
    assert([@"partial future fastfile" writeToFile:installedFF atomically:YES encoding:NSUTF8StringEncoding error:NULL]);
    NSDictionary *journal=@{@"version":@1,@"backup":backupName,@"previousManaged":prior,@"oldHashes":prior[@"hashes"],@"newHashes":@{@"mod.ff":FixtureHash(installedFF),@"z_mw3_acr.iwd":FixtureHash(installedIWD)}};
    NSString *journalPath=[assetRoot stringByAppendingPathComponent:@".mw3-update.json"];
    assert([[NSJSONSerialization dataWithJSONObject:journal options:0 error:NULL] writeToFile:journalPath atomically:YES]);
    // A terminated rollback copy leaves only its private partial temporary;
    // the final target may be absent and must recover from the verified backup.
    assert([@"incomplete copy" writeToFile:[assetRoot stringByAppendingPathComponent:@".mw3-restore-interrupted"] atomically:YES encoding:NSUTF8StringEncoding error:NULL]);
    assert([fm removeItemAtPath:installedFF error:NULL]);
    assert(KisakInstallSurvivalContent(documents,&error));
    assert(![fm fileExistsAtPath:journalPath]);
    assert([[NSString stringWithContentsOfFile:installedFF encoding:NSUTF8StringEncoding error:NULL] isEqualToString:@"upgraded three-weapon fastfile"]);
    NSData *managedData=[NSData dataWithContentsOfFile:managedPath];
    assert([fm removeItemAtPath:managedPath error:NULL]);
    assert([fm createSymbolicLinkAtPath:managedPath withDestinationPath:installedFF error:NULL]);
    assert(!KisakInstallSurvivalContent(documents,&error));
    assert([fm removeItemAtPath:managedPath error:NULL]);
    assert([managedData writeToFile:managedPath atomically:YES]);
    NSData *manifestData=[NSData dataWithContentsOfFile:manifest];
    assert([fm removeItemAtPath:manifest error:NULL]);
    assert([fm createSymbolicLinkAtPath:manifest withDestinationPath:installedFF error:NULL]);
    assert(!KisakInstallSurvivalContent(documents,&error));
    assert([fm removeItemAtPath:manifest error:NULL]);
    assert([manifestData writeToFile:manifest atomically:YES]);
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

