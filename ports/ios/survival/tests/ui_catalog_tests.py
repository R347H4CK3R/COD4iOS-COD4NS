#!/usr/bin/env python3
"""Exercise production map menu/card routing using a Foundation UI fixture."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parents[4]
s=(root/'ports/ios/app/survival_ui.mm').read_text(encoding='utf-8')
render=s[s.index('- (void)renderMapBrowser {'):s.index('- (NSDictionary *)bundledMW3Catalog')]
route=s[s.index('    if(_screen==8) {'):s.index('    if(_screen==9) {')]
fixture=r'''
#import <Foundation/Foundation.h>
#include <cassert>
#include "ports/ios/survival/SurvivalConfig.hpp"
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
@end
@implementation FixtureLabel
@end
@interface FixtureButton:NSObject
@property(strong) FixtureLabel *titleLabel;
@end
@implementation FixtureButton
@end
@interface MenuFixture:NSObject {
 unsigned _map; NSInteger _screen; BOOL _choosingMode, _installed;
 NSString *_feedback;
 NSMutableArray<FixtureButton *> *_choices;
 NSArray<NSString *> *_titles;
}
- (void)renderMapBrowser;
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
- (void)renderSetup { _screen=1; }
- (void)panelTitle:(NSString *)title detail:(NSString *)detail choices:(NSArray<NSString *> *)choices {
 _titles=choices; _choices=[NSMutableArray new];
 for(NSString *choice in choices) { FixtureButton *b=[FixtureButton new]; b.titleLabel=[FixtureLabel new]; [_choices addObject:b]; }
}
''' + render + '\n- (void)chooseIndex:(NSUInteger)index {\n'+route+'}\n@end\n'+r'''
int main() { @autoreleasepool {
 MenuFixture *menu=[MenuFixture new]; [menu renderMapBrowser];
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
