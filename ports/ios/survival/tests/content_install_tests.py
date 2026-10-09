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
    NSString *documents = [bundle stringByAppendingPathComponent:@"Documents"];
    assert([fm createDirectoryAtPath:documents withIntermediateDirectories:YES attributes:nil error:NULL]);
    NSError *error = nil;
    assert(KisakInstallSurvivalContent(documents, &error));
    NSString *destination = [documents stringByAppendingPathComponent:@"mods/specops_survival/maps/specops_survival.gsc"];
    assert([@"user script" writeToFile:destination atomically:YES encoding:NSUTF8StringEncoding error:NULL]);
    assert(KisakInstallSurvivalContent(documents, &error));
    assert([[NSString stringWithContentsOfFile:destination encoding:NSUTF8StringEncoding error:NULL] isEqualToString:@"user script"]);
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
print('Installer: copies missing script, preserves edits, rejects redirected paths and directories')

