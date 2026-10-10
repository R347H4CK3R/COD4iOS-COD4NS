#!/usr/bin/env python3
"""Exercise production map menu/card routing using a Foundation UI fixture."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parents[4]
s=(root/'ports/ios/app/survival_ui.mm').read_text(encoding='utf-8')
render=s[s.index('- (void)renderMapBrowser {'):s.index('- (NSDictionary *)bundledMW3Catalog')]
landing=s[s.index('- (void)showModes:(BOOL)running {'):s.index('- (void)modesPressed')]
setup=s[s.index('- (void)renderSetup {'):s.index('- (void)renderMapBrowser {')]
assert 'self.modeSelected("campaign")' not in s and 'self.modeSelected("multiplayer")' not in s
route=s[s.index('    if(_screen==8) {'):s.index('    if(_screen==9) {')]
fixture=r'''
#import <Foundation/Foundation.h>
#include <cassert>
#include "ports/ios/survival/SurvivalConfig.hpp"
#include "ports/ios/survival/SurvivalBridge.hpp"
namespace cod4ios::survival {
Status liveStatus; unsigned openRequests=0;
Status readStatus() {return liveStatus;}
bool queueAction(Action action,std::uint64_t,unsigned) {assert(action==Action::OpenShop); ++openRequests; return true;}
}
unsigned KisakApple_GetSurvivalBank() {return 5000;}
#define UIFontWeightSemibold 0
@interface UIFont:NSObject
+ (id)systemFontOfSize:(double)size weight:(double)weight;
@end
@implementation UIFont
+ (id)systemFontOfSize:(double)size weight:(double)weight { return nil; }
@end
@interface FixtureLabel:NSObject
@property unsigned numberOfLines;
@property(strong) id font;
@property(copy) NSString *text;
@end
@implementation FixtureLabel
@end
@interface FixtureButton:NSObject
@property(strong) FixtureLabel *titleLabel;
@end
@implementation FixtureButton
@end
@interface MenuFixture:NSObject {
 unsigned _map,_difficulty; NSInteger _screen; BOOL _choosingMode, _installed, _running, _setupInMatch, _setupFromShop;
 NSUInteger _selected; cod4ios::survival::Status _status, _shopRequestStatus;
 BOOL _pendingShop; NSTimeInterval _shopPendingUntil; FixtureLabel *_hud;
 NSString *_feedback;
 NSMutableArray<FixtureButton *> *_choices;
 NSArray<NSString *> *_titles;
}
- (void)renderMapBrowser;
- (void)showModes:(BOOL)running;
- (void)renderSetup;
- (BOOL)inMatch;
- (BOOL)fromShop;
- (void)chooseIndex:(NSUInteger)index;
- (void)installed:(BOOL)value;
- (unsigned)map;
- (NSArray *)titles;
- (NSString *)feedback;
@end
@implementation MenuFixture
- (void)installed:(BOOL)value { _installed=value; }
- (unsigned)map { return _map; }
- (NSArray *)titles { return _titles; }
- (NSString *)feedback { return _feedback; }
- (BOOL)mapAvailable:(unsigned)index { return _installed && index<5; }
- (void)showSetup:(BOOL)value {_setupFromShop=(_screen==2); _setupInMatch=value; _screen=1; [self renderSetup];}
- (BOOL)inMatch {return _setupInMatch;}
- (BOOL)fromShop {return _setupFromShop;}
- (unsigned)classRank {return 13;}
- (void)highlight {}
- (void)panelTitle:(NSString *)title detail:(NSString *)detail choices:(NSArray<NSString *> *)choices {
 _titles=choices; _choices=[NSMutableArray new];
 for(NSString *choice in choices) { FixtureButton *b=[FixtureButton new]; b.titleLabel=[FixtureLabel new]; [_choices addObject:b]; }
}
''' + landing + setup + render + '\n- (void)chooseIndex:(NSUInteger)index {\n'+route+'}\n@end\n'+r'''
int main() { @autoreleasepool {
 MenuFixture *menu=[MenuFixture new];
 [menu showModes:NO]; assert(!menu.inMatch && !menu.fromShop && menu.titles.count==5);
 assert([menu.titles[2] isEqualToString:@"CREATE-A-CLASS"] && [menu.titles[3] isEqualToString:@"START SURVIVAL"]);
 for(NSString *title in menu.titles) assert(![title containsString:@"Campaign"] && ![title containsString:@"Multiplayer"]);
 cod4ios::survival::liveStatus.active=true; [menu showModes:YES];
 assert(menu.inMatch && menu.fromShop && cod4ios::survival::openRequests==1);
 assert([menu.titles.lastObject isEqualToString:@"BACK TO ARMORY"]);
 cod4ios::survival::liveStatus.match.phase=cod4ios::survival::Phase::GameOver; [menu showModes:YES];
 assert(menu.inMatch && !menu.fromShop && cod4ios::survival::openRequests==1);
 cod4ios::survival::liveStatus.active=false; [menu showModes:YES]; assert(!menu.inMatch && !menu.fromShop);
 [menu renderMapBrowser];
 assert(menu.titles.count==22);
 for(unsigned i=0;i<16;++i) {
  assert([menu.titles[i] containsString:@"LOCKED"]);
  [menu chooseIndex:i]; assert(menu.map==0 && [menu.feedback containsString:@"locked"]);
 }
 assert([menu.titles[4] containsString:@"Dome"]);
 for(unsigned i=16;i<21;++i) assert([menu.titles[i] containsString:@"COD4 EXTENSION"]);
 [menu chooseIndex:17]; assert(menu.map==0 && [menu.feedback containsString:@"unavailable"]);
 [menu installed:YES]; [menu renderMapBrowser]; [menu chooseIndex:17]; assert(menu.map==1);
 [menu renderMapBrowser]; [menu chooseIndex:21]; assert(menu.map==1);
} }
'''
with tempfile.TemporaryDirectory(prefix='survival-ui-catalog-') as directory:
 code=Path(directory)/'test.mm'; exe=Path(directory)/'ui-catalog-tests'
 code.write_text(fixture,encoding='utf-8')
 subprocess.run(['xcrun','clang++','-std=c++17','-fobjc-arc','-framework','Foundation','-I',str(root),str(code),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('Map browser: 16 original cards stay locked; available COD4 extensions route independently')
