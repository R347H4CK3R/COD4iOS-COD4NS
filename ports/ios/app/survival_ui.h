#pragma once
#import <UIKit/UIKit.h>
@interface KISSurvivalUI : UIView
@property(nonatomic,copy) void (^modeSelected)(const char *mode);
@property(nonatomic,readonly) BOOL modal;
- (void)showModes:(BOOL)running;
- (void)update;
@end
// Copy only missing loose overlay files. Never replace retail files or user edits.
BOOL KisakInstallSurvivalContent(NSString *documents, NSError **error);
