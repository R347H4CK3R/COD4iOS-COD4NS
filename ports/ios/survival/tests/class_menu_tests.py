#!/usr/bin/env python3
"""Exercise production pregame class availability across both engine menus."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parents[4]
s=(root/'ports/ios/app/survival_ui.mm').read_text(encoding='utf-8')
methods=s[s.index('- (unsigned)classRank {'):s.index('- (void)renderClass {')]
fixture=r'''#import <Foundation/Foundation.h>
#include <cassert>
#include "ports/ios/survival/SurvivalBridge.hpp"
#include "ports/ios/survival/SurvivalConfig.hpp"
unsigned storedXP=0,oldXP=0; bool hasXP=true;
bool KisakApple_HasSurvivalMW3XP(){return hasXP;}
unsigned KisakApple_GetSurvivalMW3XP(){return storedXP;}
unsigned KisakApple_GetSurvivalXP(){return oldXP;}
@interface ClassMenu:NSObject { cod4ios::survival::Status _status; }
@property(strong) NSDictionary *catalog;
- (NSDictionary *)bundledMW3Catalog;
- (unsigned)classRank;
- (BOOL)loadoutWeaponAvailable:(unsigned)value secondary:(BOOL)secondary;
- (BOOL)loadoutRankAvailable:(unsigned)value;
- (BOOL)loadoutPerkAvailable:(unsigned)value;
- (void)active;
@end
@implementation ClassMenu
- (NSDictionary *)bundledMW3Catalog {return self.catalog;}
- (void)active {_status.active=true;_status.rank=13;_status.mp7Available=false;_status.uspAvailable=true;}
'''+methods+r'''
@end
int main(){@autoreleasepool {
 ClassMenu *menu=[ClassMenu new]; NSMutableArray *thresholds=[NSMutableArray new];
 for(unsigned i=0;i<50;++i)[thresholds addObject:@(i*100)];
 menu.catalog=@{@"version":@1,@"weapons":@[@"mw3_usp45",@"mw3_mp7",@"mw3_acr"],@"rankThresholds":thresholds};
 assert([menu loadoutWeaponAvailable:0 secondary:YES]);
 assert([menu loadoutWeaponAvailable:1 secondary:NO]);
 assert(![menu loadoutRankAvailable:1] && ![menu loadoutPerkAvailable:1]);
 storedXP=1200;assert([menu classRank]==13 && [menu loadoutRankAvailable:1] && ![menu loadoutRankAvailable:2]);
 assert([menu loadoutPerkAvailable:1] && [menu loadoutPerkAvailable:2]);
 storedXP=1300;assert([menu loadoutRankAvailable:2]);
 hasXP=false;oldXP=6500;assert([menu classRank]==14);hasXP=true;
 menu.catalog=@{};assert(![menu loadoutWeaponAvailable:0 secondary:YES] && [menu classRank]==1);
 assert([menu loadoutWeaponAvailable:3 secondary:NO]);
 menu.catalog=@{@"version":@1,@"weapons":@[@"mw3_mp7"],@"rankThresholds":thresholds};[menu active];
#ifndef KISAK_MP
 assert(![menu loadoutWeaponAvailable:1 secondary:NO]); // Mounted assets override advertised planning catalog.
 assert([menu loadoutWeaponAvailable:0 secondary:YES]);
#else
 assert([menu loadoutWeaponAvailable:1 secondary:NO]); // MP startup can still plan its next SP class.
#endif
}}
'''
with tempfile.TemporaryDirectory(prefix='survival-class-menu-') as directory:
 for mode in ('KISAK_SP','KISAK_MP'):
  code=Path(directory)/(mode+'.mm');exe=Path(directory)/mode;code.write_text(fixture,encoding='utf-8')
  subprocess.run(['xcrun','clang++','-std=c++17','-fobjc-arc','-framework','Foundation','-D'+mode,'-I',str(root),str(code),'-o',str(exe)],check=True)
  subprocess.run([str(exe)],check=True)
print('Create-a-Class: pregame pack/rank/perk gates work from SP and MP menus; active SP uses mounted assets')
