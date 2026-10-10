#!/usr/bin/env python3
"""Execute production Survival-only saved-mode routing using Foundation."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parents[4]
s=(root/'ports/ios/platform/apple_engine_mode.mm').read_text()
production=s[s.index('static NSString *const kModeKey'):s.index('unsigned KisakApple_GetSurvivalBestWave')].replace('NSUserDefaults.standardUserDefaults','testDefaults')
tests=r'''
int main(){@autoreleasepool {
 NSString *suite=[@"SurvivalModeTests-" stringByAppendingString:NSUUID.UUID.UUIDString];
 testDefaults=[[NSUserDefaults alloc]initWithSuiteName:suite];
 for(NSString *legacy in @[@"",@"sp",@"mp",@"campaign",@"multiplayer",@"bad",@"survival"]){
  [testDefaults setObject:legacy forKey:@"KisakEngineMode"];
  assert(!strcmp(KisakApple_GetGameMode(),"survival") && !strcmp(KisakApple_GetEngineMode(),"sp"));
  assert(!KisakApple_SetGameMode("campaign") && !KisakApple_SetGameMode("multiplayer"));
  assert([[testDefaults stringForKey:@"KisakEngineMode"]isEqual:legacy]);
 }
 assert(!KisakApple_SetGameMode(nullptr));
 assert(KisakApple_SetGameMode("survival"));
 KisakApple_SetEngineMode("mp");assert(!strcmp(KisakApple_GetGameMode(),"survival"));
 [testDefaults setInteger:999 forKey:@"KisakSurvivalBestWave"];
 assert(KisakApple_SetGameMode("survival") && [testDefaults integerForKey:@"KisakSurvivalBestWave"]==999);
 [testDefaults removePersistentDomainForName:suite];
}}
'''
with tempfile.TemporaryDirectory(prefix='survival-mode-') as d:
 code=Path(d)/'test.mm';exe=Path(d)/'test'
 code.write_text('#import <Foundation/Foundation.h>\n#include <cassert>\n#include <cstring>\n#include "ports/ios/platform/apple_engine_mode.h"\n#include "ports/ios/survival/ModeCatalog.hpp"\nstatic NSUserDefaults *testDefaults;\n'+production+tests)
 subprocess.run(['xcrun','clang++','-std=c++17','-fobjc-arc','-framework','Foundation','-I',str(root),str(code),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('Saved Campaign/MP modes route to Survival; unsupported writes and unrelated progress stay preserved')
