// Which engine the launcher loads next time. Singleplayer and multiplayer are separate dylibs
// (see ports/ios/app/launcher.mm), so switching is a restart, not a hand-off: the running engine
// already owns Metal, the audio device and its hunk, and cannot be torn down from inside itself.
#import <Foundation/Foundation.h>
#import <UIKit/UIKit.h>
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
