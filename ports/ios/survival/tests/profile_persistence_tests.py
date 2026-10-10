#!/usr/bin/env python3
"""Exercise production Survival preferences using Foundation on macOS."""
from pathlib import Path
import subprocess, tempfile
root=Path(__file__).resolve().parents[4]
source=(root/'ports/ios/platform/apple_engine_mode.mm').read_text()
production=source[source.index('static NSDictionary *SurvivalRecord('):source.index('void KisakApple_PromptEngineRestart(')]
tests=r'''
int main() { @autoreleasepool {
 NSString *suite=[@"SurvivalProfileTests-" stringByAppendingString:NSUUID.UUID.UUIDString];
 testDefaults=[[NSUserDefaults alloc] initWithSuiteName:suite];
 auto config=[](unsigned m,unsigned d,unsigned c) { unsigned am=99,ad=99,ac=99; KisakApple_GetSurvivalConfig(&am,&ad,&ac); assert(am==m && ad==d && ac==c); };
 assert(KisakApple_GetSurvivalBank()==0 && KisakApple_GetSurvivalXP()==0); config(0,1,0);
 for(id bad in @[@"bad",@42,@[],@{@"version":@0,@"bank":@12,@"xp":@13},@{@"version":@2,@"bank":@12},@{@"version":@"1",@"bank":@12},@{@"version":@1.5,@"bank":@12},@{}]) {
  [testDefaults setObject:bad forKey:@"KisakSurvivalProgress"]; assert(KisakApple_GetSurvivalBank()==0 && KisakApple_GetSurvivalXP()==0);
  [testDefaults setObject:bad forKey:@"KisakSurvivalConfig"]; config(0,1,0);
 }
 [testDefaults setObject:@{@"version":@1,@"bank":@"42",@"xp":@[]} forKey:@"KisakSurvivalProgress"];
 assert(KisakApple_GetSurvivalBank()==0 && KisakApple_GetSurvivalXP()==0);
 [testDefaults setObject:@{@"version":@1,@"bank":@(-5),@"xp":@1.25} forKey:@"KisakSurvivalProgress"];
 assert(KisakApple_GetSurvivalBank()==0 && KisakApple_GetSurvivalXP()==0);
 [testDefaults setObject:@{@"version":@1,@"bank":@4000000000u,@"xp":@4000000000u} forKey:@"KisakSurvivalProgress"];
 assert(KisakApple_GetSurvivalBank()==1000000000 && KisakApple_GetSurvivalXP()==1000000000);
 KisakApple_StoreSurvivalProgress(12345,6789); assert(KisakApple_GetSurvivalBank()==12345 && KisakApple_GetSurvivalXP()==6789);
 NSDictionary *saved=[testDefaults dictionaryForKey:@"KisakSurvivalProgress"]; assert([saved[@"version"] unsignedIntValue]==1 && [saved[@"bank"] unsignedIntValue]==12345 && [saved[@"xp"] unsignedIntValue]==6789);
 KisakApple_StoreSurvivalProgress(UINT_MAX,UINT_MAX); assert(KisakApple_GetSurvivalBank()==1000000000 && KisakApple_GetSurvivalXP()==1000000000);
 KisakApple_StoreSurvivalProgress(0,0); assert(KisakApple_GetSurvivalBank()==0 && KisakApple_GetSurvivalXP()==0);
 assert(KisakApple_SetSurvivalConfig(4,3,2)); config(4,3,2);
 assert(!KisakApple_SetSurvivalConfig(5,3,2)); config(4,3,2);
 assert(!KisakApple_SetSurvivalConfig(4,4,2)); config(4,3,2);
 assert(!KisakApple_SetSurvivalConfig(4,3,3)); config(4,3,2);
 [testDefaults setObject:@{@"version":@1,@"map":@99,@"difficulty":@99,@"playerClass":@99} forKey:@"KisakSurvivalConfig"]; config(0,1,0);
 [testDefaults setObject:@{@"version":@1,@"map":@"4",@"difficulty":@(-1),@"playerClass":@1.5} forKey:@"KisakSurvivalConfig"]; config(0,1,0);
 KisakApple_GetSurvivalConfig(nullptr,nullptr,nullptr);
 assert(!KisakApple_HasSurvivalMW3XP() && KisakApple_GetSurvivalMW3XP()==0);
 KisakApple_StoreSurvivalMW3XP(0); assert(KisakApple_HasSurvivalMW3XP() && KisakApple_GetSurvivalMW3XP()==0);
 KisakApple_StoreSurvivalMW3XP(12345); assert(KisakApple_GetSurvivalMW3XP()==12345);
 KisakApple_StoreSurvivalMW3XP(UINT_MAX); assert(KisakApple_GetSurvivalMW3XP()==1000000000);
 for(id bad in @[@"bad",@{@"version":@2,@"xp":@100},@{@"version":@1,@"xp":@"100"},@{@"version":@1,@"xp":@(-1)},@{@"version":@1,@"xp":@1.5},@{@"version":@1}]) {
  [testDefaults setObject:bad forKey:@"KisakSurvivalMW3XP"]; assert(!KisakApple_HasSurvivalMW3XP() && KisakApple_GetSurvivalMW3XP()==0);
 }
 auto loadout=[](unsigned p,unsigned s,unsigned e,unsigned k) { unsigned ap=99,as=99,ae=99,ak=99; KisakApple_GetSurvivalLoadout(&ap,&as,&ae,&ak); assert(ap==p && as==s && ae==e && ak==k); };
 [testDefaults removeObjectForKey:@"KisakSurvivalConfig"]; loadout(0,0,0,0);
 KisakApple_StoreSurvivalProgress(888,999);
 for(unsigned c=0;c<3;++c) { assert(KisakApple_SetSurvivalConfig(4,3,c)); loadout(c==1?4:3,0,c==2?1:0,0); }
 assert(KisakApple_SetSurvivalLoadout(2,1,2,2)); loadout(2,1,2,2);
 config(4,3,2); assert(KisakApple_GetSurvivalBank()==888 && KisakApple_GetSurvivalXP()==999);
 assert(!KisakApple_SetSurvivalLoadout(5,1,2,2)); loadout(2,1,2,2);
 assert(!KisakApple_SetSurvivalLoadout(2,2,2,2)); loadout(2,1,2,2);
 assert(!KisakApple_SetSurvivalLoadout(2,1,3,2)); loadout(2,1,2,2);
 assert(!KisakApple_SetSurvivalLoadout(2,1,2,3)); loadout(2,1,2,2);
 for(id bad in @[@"bad",@[],@{@"version":@2},@{@"version":@1,@"primary":@5,@"secondary":@0,@"equipment":@0,@"perk":@0},@{@"version":@1,@"primary":@0,@"secondary":@0,@"equipment":@0,@"perk":@1.5},@{@"version":@1,@"primary":@"2",@"secondary":@0,@"equipment":@0,@"perk":@0}]) {
  [testDefaults setObject:bad forKey:@"KisakSurvivalLoadout"]; loadout(0,0,0,0);
 }
 KisakApple_GetSurvivalLoadout(nullptr,nullptr,nullptr,nullptr);
 assert(KisakApple_GetSurvivalBank()==888 && KisakApple_GetSurvivalXP()==999); config(4,3,2);
 [testDefaults removePersistentDomainForName:suite];
 } }
'''
# Redirect only the defaults dependency; all validation and writes remain production code.
production=production.replace('NSUserDefaults.standardUserDefaults','testDefaults')
with tempfile.TemporaryDirectory(prefix='survival-profile-test-') as directory:
 code=Path(directory)/'test.mm'; exe=Path(directory)/'profile-tests'
 code.write_text('#import <Foundation/Foundation.h>\n#include <algorithm>\n#include <cmath>\n#include <climits>\n#include <cassert>\n#include "ports/ios/survival/SurvivalConfig.hpp"\nstatic NSUserDefaults *testDefaults;\n'+production+tests)
 subprocess.run(['xcrun','clang++','-std=c++17','-fobjc-arc','-framework','Foundation','-I',str(root),str(code),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('Survival profile/config preferences: production validation, caps and atomic records passed')
