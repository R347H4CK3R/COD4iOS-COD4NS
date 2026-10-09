// Which engine the launcher loads next time. Singleplayer and multiplayer are separate dylibs
// (see ports/ios/app/launcher.mm), so switching is a restart, not a hand-off: the running engine
// already owns Metal, the audio device and its hunk, and cannot be torn down from inside itself.
#import <Foundation/Foundation.h>
#import <UIKit/UIKit.h>
#include <algorithm>
#include <cmath>
#include <climits>
#include "apple_engine_mode.h"
#include "../survival/ModeCatalog.hpp"

static NSString *const kModeKey = @"KisakEngineMode";

void KisakApple_SetEngineMode(const char *mode)
{
    if(!mode) return;
    if(!strcmp(mode,"sp")) KisakApple_SetGameMode("campaign");
    else if(!strcmp(mode,"mp")) KisakApple_SetGameMode("multiplayer");
}

const char *KisakApple_GetEngineMode()
{
    @autoreleasepool {
        return !strcmp(KisakApple_GetGameMode(),"multiplayer") ? "mp" : "sp";
    }
}

bool KisakApple_SetGameMode(const char *mode) {
    if(!mode || cod4ios::modes::fromId(mode)==cod4ios::modes::Mode::Invalid) return false;
    @autoreleasepool {
        [NSUserDefaults.standardUserDefaults setObject:[NSString stringWithUTF8String:mode] forKey:kModeKey];
        return true;
    }
}
const char *KisakApple_GetGameMode() {
    @autoreleasepool {
        NSString *value=[NSUserDefaults.standardUserDefaults stringForKey:kModeKey];
        return cod4ios::modes::id(cod4ios::modes::fromSavedId(value.UTF8String ?: ""));
    }
}
unsigned KisakApple_GetSurvivalBestWave() {
    const NSInteger value=[NSUserDefaults.standardUserDefaults integerForKey:@"KisakSurvivalBestWave"];
    return value>0 ? static_cast<unsigned>(MIN(value,NSInteger(1000000))) : 0;
}
void KisakApple_RecordSurvivalBestWave(unsigned wave) {
    if(wave>KisakApple_GetSurvivalBestWave())
        [NSUserDefaults.standardUserDefaults setInteger:MIN(wave,1000000u) forKey:@"KisakSurvivalBestWave"];
}

// Profile and setup each use a single record, so partial preference writes cannot
// produce mixed balances or mixed configuration selections.
static NSDictionary *SurvivalRecord(NSString *key) {
    id record=[NSUserDefaults.standardUserDefaults objectForKey:key];
    if(![record isKindOfClass:NSDictionary.class]) return nil;
    id version=record[@"version"];
    if(![version isKindOfClass:NSNumber.class] || [version doubleValue]!=1.0) return nil;
    return record;
}
static unsigned SurvivalNumber(id value, unsigned fallback, unsigned maximum) {
    if(![value isKindOfClass:NSNumber.class]) return fallback;
    double number=[value doubleValue];
    if(!std::isfinite(number) || number<0 || std::floor(number)!=number) return fallback;
    return static_cast<unsigned>(std::min(number,static_cast<double>(maximum)));
}
unsigned KisakApple_GetSurvivalBank() {
    @autoreleasepool { return SurvivalNumber(SurvivalRecord(@"KisakSurvivalProgress")[@"bank"],0,1000000000u); }
}
unsigned KisakApple_GetSurvivalXP() {
    @autoreleasepool { return SurvivalNumber(SurvivalRecord(@"KisakSurvivalProgress")[@"xp"],0,1000000000u); }
}
void KisakApple_StoreSurvivalProgress(unsigned bank, unsigned xp) {
    @autoreleasepool {
        [NSUserDefaults.standardUserDefaults setObject:@{@"version":@1,@"bank":@(std::min(bank,1000000000u)),@"xp":@(std::min(xp,1000000000u))} forKey:@"KisakSurvivalProgress"];
    }
}
void KisakApple_GetSurvivalConfig(unsigned *map, unsigned *difficulty, unsigned *playerClass) {
    @autoreleasepool {
        NSDictionary *record=SurvivalRecord(@"KisakSurvivalConfig");
        unsigned m=SurvivalNumber(record[@"map"],0,UINT_MAX);
        unsigned d=SurvivalNumber(record[@"difficulty"],1,UINT_MAX);
        unsigned c=SurvivalNumber(record[@"playerClass"],0,UINT_MAX);
        if(map) *map=m<5?m:0;
        if(difficulty) *difficulty=d<4?d:1;
        if(playerClass) *playerClass=c<3?c:0;
    }
}
bool KisakApple_SetSurvivalConfig(unsigned map, unsigned difficulty, unsigned playerClass) {
    if(map>=5 || difficulty>=4 || playerClass>=3) return false;
    @autoreleasepool {
        [NSUserDefaults.standardUserDefaults setObject:@{@"version":@1,@"map":@(map),@"difficulty":@(difficulty),@"playerClass":@(playerClass)} forKey:@"KisakSurvivalConfig"];
        return true;
    }
}
void KisakApple_PromptEngineRestart(const char *mode)
{
    @autoreleasepool {
        NSString *target = [NSString stringWithUTF8String:mode ? mode : "mp"];
        NSString *name = [target isEqualToString:@"sp"] || [target isEqualToString:@"campaign"] ? @"Campaign" :
                         [target isEqualToString:@"survival"] ? @"Survival" : @"Multiplayer";
        dispatch_async(dispatch_get_main_queue(), ^{
            UIWindow *window = nil;
            for (UIScene *scene in UIApplication.sharedApplication.connectedScenes) {
                if ([scene isKindOfClass:UIWindowScene.class]) {
                    for (UIWindow *candidate in ((UIWindowScene *)scene).windows) {
                        if (candidate.isKeyWindow) { window = candidate; break; }
                    }
                    if (!window) window = ((UIWindowScene *)scene).windows.firstObject;
                }
                if (window) break;
            }
            if (!window.rootViewController)
                return;
            UIAlertController *alert = [UIAlertController
                alertControllerWithTitle:[NSString stringWithFormat:@"Switching to %@", name]
                                 message:@"Close the app and open it again to finish switching."
                          preferredStyle:UIAlertControllerStyleAlert];
            [alert addAction:[UIAlertAction actionWithTitle:@"OK" style:UIAlertActionStyleDefault handler:nil]];
            [window.rootViewController presentViewController:alert animated:YES completion:nil];
        });
    }
}
