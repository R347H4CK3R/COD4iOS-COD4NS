// iPhone launcher for the single-player engine.
//
// The game data comes from the user's own copy of Call of Duty 4: the contents
// of the game folder (main/, zone/, localization.txt) are copied into this
// app's Documents folder through Finder or the Files app. The engine runs on
// its own thread with a large stack, draws into the Metal-backed view once the
// renderer backend exists, and writes its console to Documents/kisakcod.log.

#import <UIKit/UIKit.h>
#import <AVFoundation/AVFoundation.h>
#import <QuartzCore/CAMetalLayer.h>
#import <QuartzCore/CADisplayLink.h>
#import <GameController/GameController.h>
#import <UniformTypeIdentifiers/UniformTypeIdentifiers.h>
#include "../engine/controller_input.h"
#import "touch_controls.h"
#import "client_patch.h"

// Com_Printf, so controller diagnostics land in the console log (stderr is not captured here).
void Com_Printf(int channel, const char *format, ...); // C++ linkage, as declared in qcommon.h
#define KISAK_CON_CHANNEL_SYSTEM 0

#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <mach/mach.h>

int KisakApple_RunEngine(const char *commandLine);
void KisakApple_SetRenderWindow(void *view, int width, int height);
void KisakApple_SetDisplaySafeArea(float horizontal, float vertical);
void KisakApple_TouchEvent(int phase, float x, float y);
void KisakApple_TextInput(const char *utf8);
void KisakApple_TextBackspace();
void KisakApple_TextReturn();
void KisakApple_ModCommand(const char *command);
int KisakApple_TextInputActive();

@interface KISControllerInput : NSObject
- (void)start;
- (void)publish;
@property(nonatomic,strong) KISTouchControls *touchControls;
@end

@implementation KISControllerInput {
    GCController *_controller;
    BOOL _active;
    NSTimer *_pollTimer;
}
- (void)publish
{
    using namespace kisak::controller;
    Snapshot sample;
    [self.touchControls setAvailable:_active && !_controller && !KisakApple_TextInputActive()
                            context:KisakApple_ControllerTouchContext()];
    if (_active && !_controller) sample=[self.touchControls sample];
    GCExtendedGamepad *pad = _controller.extendedGamepad;
    if (_active && pad) {
        sample.connected = true;
        sample.leftX = pad.leftThumbstick.xAxis.value;
        sample.leftY = pad.leftThumbstick.yAxis.value;
        sample.rightX = pad.rightThumbstick.xAxis.value;
        sample.rightY = pad.rightThumbstick.yAxis.value;
        sample.leftTrigger = pad.leftTrigger.value;
        sample.rightTrigger = pad.rightTrigger.value;
        GCControllerButtonInput *buttons[Count] = {
            pad.buttonA, pad.buttonB, pad.buttonX, pad.buttonY,
            pad.leftShoulder, pad.rightShoulder, pad.leftTrigger, pad.rightTrigger,
            pad.leftThumbstickButton, pad.rightThumbstickButton, pad.buttonMenu, pad.buttonOptions,
            pad.dpad.up, pad.dpad.down, pad.dpad.left, pad.dpad.right
        };
        GCControllerButtonInput *share = _controller.physicalInputProfile.buttons[GCInputButtonShare];
        if (share.isPressed) sample.buttons |= 1u << Options;
        if (!buttons[Options]) buttons[Options] = share;
        static BOOL loggedElements = NO;
        if (!loggedElements) {
            loggedElements = YES;
            // Not every pad reports stick clicks; melee sits on the right stick in the stock
            // Xbox 360 layout, so record what this controller actually exposes. This goes to the
            // console log rather than stderr - stderr is not captured on the simulator, so the one
            // fact needed to tell "pad cannot report R3" from "our mapping is wrong" was invisible.
            Com_Printf(KISAK_CON_CHANNEL_SYSTEM,
                       "GameController: %s exposes A=%s B=%s X=%s Y=%s LB=%s RB=%s LT=%s RT=%s L3=%s R3=%s Start=%s Back=%s\n",
                       _controller.vendorName.UTF8String ?: "pad",
                       pad.buttonA ? "y" : "n", pad.buttonB ? "y" : "n",
                       pad.buttonX ? "y" : "n", pad.buttonY ? "y" : "n",
                       pad.leftShoulder ? "y" : "n", pad.rightShoulder ? "y" : "n",
                       pad.leftTrigger ? "y" : "n", pad.rightTrigger ? "y" : "n",
                       pad.leftThumbstickButton ? "y" : "n", pad.rightThumbstickButton ? "y" : "n",
                       pad.buttonMenu ? "y" : "n", pad.buttonOptions ? "y" : "n");
        }
        {
            // Raw stick-click state, straight from the element: tells a pad that never reports the
            // click apart from a mapping problem on our side.
            static BOOL lastL3 = NO, lastR3 = NO;
            const BOOL l3 = pad.leftThumbstickButton.isPressed, r3 = pad.rightThumbstickButton.isPressed;
            if (l3 != lastL3 || r3 != lastR3) {
                lastL3 = l3; lastR3 = r3;
                Com_Printf(KISAK_CON_CHANNEL_SYSTEM, "GameController: raw stick click L3=%d R3=%d\n", (int)l3, (int)r3);
            }
        }
        for (int b = 0; b < Count; ++b) {
            if (buttons[b].isPressed) sample.buttons |= 1u << b;
            // localizedName follows the controller's physical layout AND any
            // remapping configured by the player in iOS Settings.
            NSString *name = buttons[b].localizedName;
            NSString *symbol = buttons[b].sfSymbolsName;
            NSDictionary<NSString *, NSString *> *shortNames = @{
                @"a.circle": @"A", @"b.circle": @"B", @"x.circle": @"X", @"y.circle": @"Y",
                @"xmark.circle": @"Cross", @"square.circle": @"Square",
                @"circle.circle": @"Circle", @"triangle.circle": @"Triangle"
            };
            if (symbol && shortNames[symbol]) name = shortNames[symbol];
            // The original font/localization renderer expects Windows-1252.
            NSData *encoded = [name dataUsingEncoding:NSWindowsCP1252StringEncoding allowLossyConversion:YES];
            if (encoded.length) {
                const size_t count = MIN(encoded.length, sizeof(sample.labels[b]) - 1);
                memcpy(sample.labels[b], encoded.bytes, count);
                for (size_t i = 0; i < count; ++i)
                    if (static_cast<unsigned char>(sample.labels[b][i]) < 32 || sample.labels[b][i] == '^') sample.labels[b][i] = ' ';
            }
        }
    }
    KisakApple_ControllerSubmit(sample);
}
- (void)refresh:(NSNotification *)notification
{
    (void)notification;
    GCController *selected = nil;
    // Keep the active controller when a second one connects.
    if (_controller && [GCController.controllers containsObject:_controller]) selected = _controller;
    if (!selected)
        for (GCController *candidate in GCController.controllers)
            if (candidate.extendedGamepad) { selected = candidate; break; }
#if TARGET_OS_SIMULATOR
    // Explicit test fixture, never enabled in a device build.
    if (!selected && getenv("KISAK_CONTROLLER_TEST")) {
        selected = _controller.isSnapshot ? _controller : [GCController controllerWithExtendedGamepad];
        selected.extendedGamepad.buttonX.localizedName = @"X";
        selected.extendedGamepad.buttonA.localizedName = @"A";
    }
#endif
    static NSUInteger lastCount = NSUIntegerMax;
    if (GCController.controllers.count != lastCount) {
        lastCount = GCController.controllers.count;
        fprintf(stderr, "GameController: %lu controller(s) visible\n", static_cast<unsigned long>(lastCount));
        for (GCController *candidate in GCController.controllers)
            fprintf(stderr, "GameController:   %s (%s)\n", candidate.vendorName.UTF8String ?: "unnamed",
                    candidate.extendedGamepad ? "extended gamepad" : "no extended gamepad profile");
    }
    if (selected != _controller) {
        _controller.extendedGamepad.valueChangedHandler = nil;
        [self.touchControls cancelInputs];
        KisakApple_ControllerSubmit({});
        _controller = selected;
        _controller.handlerQueue = dispatch_get_main_queue();
        // Xbox Series Share is reserved for screenshots by default. In game,
        // use it for the same scoreboard action as Xbox 360 Back / Select.
        _controller.physicalInputProfile.buttons[GCInputButtonShare].preferredSystemGestureState = GCSystemGestureStateDisabled;
        __weak KISControllerInput *weakSelf = self;
        _controller.extendedGamepad.valueChangedHandler = ^(GCExtendedGamepad *pad, GCControllerElement *element) {
            (void)pad; (void)element;
            [weakSelf publish];
        };
        fprintf(stderr, "GameController: %s\n", _controller ? (_controller.vendorName.UTF8String ?: "extended gamepad") : "none connected");
    }
    [self publish];
}
- (void)resign:(NSNotification *)notification
{
    (void)notification;
    _active = NO;
    [self.touchControls setAvailable:NO context:0];
    KisakApple_ControllerSubmit({});
}
- (void)activate:(NSNotification *)notification
{
    _active = YES;
    [self refresh:notification];
}
- (void)start
{
    _active = UIApplication.sharedApplication.applicationState == UIApplicationStateActive;
    // Poll as well as listen: some controllers never fire valueChangedHandler for the thumbstick
    // buttons (melee sits on the right stick), so a handler-only snapshot would miss those presses.
    _pollTimer = [NSTimer scheduledTimerWithTimeInterval:1.0 / 60.0 repeats:YES block:^(NSTimer *timer) {
        (void)timer;
        [self publish];
    }];
    [NSRunLoop.mainRunLoop addTimer:_pollTimer forMode:NSRunLoopCommonModes];
    _pollTimer.tolerance = 1.0 / 240.0;
    NSNotificationCenter *center = NSNotificationCenter.defaultCenter;
    [center addObserver:self selector:@selector(refresh:) name:GCControllerDidConnectNotification object:nil];
    [center addObserver:self selector:@selector(refresh:) name:GCControllerDidDisconnectNotification object:nil];
    [center addObserver:self selector:@selector(refresh:) name:GCControllerDidBecomeCurrentNotification object:nil];
    [center addObserver:self selector:@selector(resign:) name:UIApplicationWillResignActiveNotification object:nil];
    [center addObserver:self selector:@selector(activate:) name:UIApplicationDidBecomeActiveNotification object:nil];
    [self refresh:nil];
}
- (void)dealloc
{
    [_pollTimer invalidate];
    [NSNotificationCenter.defaultCenter removeObserver:self];
    _controller.extendedGamepad.valueChangedHandler = nil;
    KisakApple_ControllerSubmit({});
}
@end

@interface KISEngineView : UIView <UIKeyInput>
// YES while the on-screen keyboard should be visible. The view stays first
// responder either way so a hardware keyboard always reaches the game; an
// empty input view hides the on-screen keyboard when no text field is active.
@property(nonatomic) BOOL wantsKeyboard;
@end

@implementation KISEngineView
+ (Class)layerClass { return CAMetalLayer.class; }

// One finger drives the menu cursor: the engine sees touches as mouse moves in
// render-target pixels, and touch down/up as the left mouse button.
- (void)forwardTouches:(NSSet<UITouch *> *)touches phase:(int)phase
{
    UITouch *touch = touches.anyObject;
    if (!touch)
        return;
    const CGPoint point = [touch locationInView:self];
    if (phase != 1)
        fprintf(stderr, "Touch: phase=%d point=%.1f,%.1f\n", phase, point.x, point.y);
    const CGSize pixels = ((CAMetalLayer *)self.layer).drawableSize;
    const CGSize bounds = self.bounds.size;
    if (bounds.width <= 0 || bounds.height <= 0)
        return;
    KisakApple_TouchEvent(phase, static_cast<float>(point.x * pixels.width / bounds.width),
                         static_cast<float>(point.y * pixels.height / bounds.height));
}

- (void)touchesBegan:(NSSet<UITouch *> *)touches withEvent:(UIEvent *)event { (void)event; [self forwardTouches:touches phase:0]; }
- (void)touchesMoved:(NSSet<UITouch *> *)touches withEvent:(UIEvent *)event { (void)event; [self forwardTouches:touches phase:1]; }
- (void)touchesEnded:(NSSet<UITouch *> *)touches withEvent:(UIEvent *)event { (void)event; [self forwardTouches:touches phase:2]; }
- (void)touchesCancelled:(NSSet<UITouch *> *)touches withEvent:(UIEvent *)event { (void)event; [self forwardTouches:touches phase:2]; }

// On-screen keyboard: the view becomes first responder while a game text field
// (profile name, save name, ...) is being edited; see -syncKeyboard.
- (BOOL)canBecomeFirstResponder { return YES; }

- (UIView *)inputView
{
    static UIView *hidden = nil;
    if (!hidden)
        hidden = [[UIView alloc] initWithFrame:CGRectMake(0, 0, 0, 0)];
    return self.wantsKeyboard ? nil : hidden;
}

- (void)setWantsKeyboard:(BOOL)wantsKeyboard
{
    if (_wantsKeyboard == wantsKeyboard)
        return;
    _wantsKeyboard = wantsKeyboard;
    if (!self.isFirstResponder)
        [self becomeFirstResponder];
    [self reloadInputViews];
}
- (BOOL)hasText { return YES; }
- (void)insertText:(NSString *)text
{
    if ([text isEqualToString:@"\n"])
        KisakApple_TextReturn();
    else
        KisakApple_TextInput(text.UTF8String);
}
- (void)deleteBackward { KisakApple_TextBackspace(); }
- (UITextAutocorrectionType)autocorrectionType { return UITextAutocorrectionTypeNo; }
- (UITextAutocapitalizationType)autocapitalizationType { return UITextAutocapitalizationTypeNone; }
- (UITextSpellCheckingType)spellCheckingType { return UITextSpellCheckingTypeNo; }
- (UIKeyboardType)keyboardType { return UIKeyboardTypeASCIICapable; }
- (UIReturnKeyType)returnKeyType { return UIReturnKeyDone; }
@end

static void *KISEngineThreadMain(void *argument)
{
    (void)argument;
    // Development aid: engine startup commands (for example "+devmap killhouse")
    // come from KISAK_COMMANDLINE, which simctl forwards as SIMCTL_CHILD_KISAK_COMMANDLINE.
    const char *commandLine = getenv("KISAK_COMMANDLINE");
    NSString *mod=[NSUserDefaults.standardUserDefaults stringForKey:@"COD4SelectedMod"];
    NSString *args=commandLine?[NSString stringWithUTF8String:commandLine]:@"";
    NSCharacterSet *bad=[[NSCharacterSet characterSetWithCharactersInString:@"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"] invertedSet];
    if(mod.length && [mod rangeOfCharacterFromSet:bad].location==NSNotFound)
        args=[NSString stringWithFormat:@"+set fs_game mods/%@ %@",mod,args];
    KisakApple_RunEngine(args.UTF8String);
    return nullptr;
}

@interface KISEngineViewController : UIViewController <UIGestureRecognizerDelegate, UIDocumentPickerDelegate>
@end

@implementation KISEngineViewController {
    KISEngineView *_engineView;
    UILabel *_status;
    BOOL _started;
    BOOL _preparingPatch, _patchReady;
    BOOL _engineEditing;
    KISControllerInput *_controllerInput;
    KISTouchControls *_touchControls;
    CADisplayLink *_displayLink;
    UIView *_modPanel;
    UIButton *_modToggle;
    BOOL _modLatched;
}

- (void)loadView
{
    _engineView = [KISEngineView new];
    _engineView.backgroundColor = UIColor.blackColor;
    self.view = _engineView;
}

- (void)viewDidLoad
{
    [super viewDidLoad];
    _status = [UILabel new];
    _status.textColor = UIColor.whiteColor;
    _status.numberOfLines = 0;
    _status.font = [UIFont systemFontOfSize:15 weight:UIFontWeightMedium];
    _status.translatesAutoresizingMaskIntoConstraints = NO;
    [self.view addSubview:_status];
    UIButton *toggle=[UIButton buttonWithType:UIButtonTypeSystem];
    [toggle setTitle:@"MOD" forState:UIControlStateNormal];
    toggle.frame=CGRectMake(10,48,62,38);
    toggle.backgroundColor=UIColor.darkGrayColor;toggle.tintColor=UIColor.cyanColor;
    [toggle addTarget:self action:@selector(toggleMod) forControlEvents:UIControlEventTouchUpInside];
    [self.view addSubview:toggle];
    _modToggle=toggle;
    _modPanel=[[UIView alloc] initWithFrame:CGRectMake(86,20,300,410)];
    _modPanel.backgroundColor=[UIColor colorWithRed:0.05 green:0.07 blue:0.12 alpha:0.97];
    _modPanel.layer.borderWidth=1;_modPanel.layer.borderColor=UIColor.cyanColor.CGColor;
    _modPanel.layer.cornerRadius=9;_modPanel.hidden=YES;
    [self.view addSubview:_modPanel];
    [self modCategory:@"COD4 // MOD MENU" entries:@[@"Player",@"Weapons",@"Game",@"Visuals",@"Mods",@"Close"]];
    [NSTimer scheduledTimerWithTimeInterval:0.12 target:self selector:@selector(checkModCombo) userInfo:nil repeats:YES];
    UILayoutGuide *safe = self.view.safeAreaLayoutGuide;
    [NSLayoutConstraint activateConstraints:@[
        [_status.leadingAnchor constraintEqualToAnchor:safe.leadingAnchor constant:24],
        [_status.trailingAnchor constraintEqualToAnchor:safe.trailingAnchor constant:-24],
        [_status.centerYAnchor constraintEqualToAnchor:safe.centerYAnchor],
    ]];
}

- (void)modCategory:(NSString *)name entries:(NSArray<NSString *> *)entries {
    for(UIView *v in _modPanel.subviews)[v removeFromSuperview];
    UILabel *h=[[UILabel alloc] initWithFrame:CGRectMake(14,8,276,34)];
    h.text=name;h.textColor=UIColor.cyanColor;h.font=[UIFont monospacedSystemFontOfSize:16 weight:UIFontWeightBold];
    [_modPanel addSubview:h];
    for(NSUInteger i=0;i<entries.count;i++) {
        UIButton *b=[UIButton buttonWithType:UIButtonTypeSystem];
        [b setTitle:[@"  > " stringByAppendingString:entries[i]] forState:UIControlStateNormal];
        b.contentHorizontalAlignment=UIControlContentHorizontalAlignmentLeft;
        b.tintColor=UIColor.whiteColor;b.backgroundColor=[UIColor colorWithWhite:0.17 alpha:0.95];
        b.frame=CGRectMake(12,42+31*i,276,28);b.tag=i;
        [b addTarget:self action:@selector(modSelect:) forControlEvents:UIControlEventTouchUpInside];
        [_modPanel addSubview:b];
    }
}
- (void)toggleMod {
    _modPanel.hidden=!_modPanel.hidden;
    [self.view bringSubviewToFront:_modPanel];
    [self.view bringSubviewToFront:_modToggle];
}
- (void)modMessage:(NSString *)message {
    UIAlertController *a=[UIAlertController alertControllerWithTitle:@"COD4 MOD MENU" message:message preferredStyle:UIAlertControllerStyleAlert];
    [a addAction:[UIAlertAction actionWithTitle:@"OK" style:UIAlertActionStyleDefault handler:nil]];
    [self presentViewController:a animated:YES completion:nil];
}
- (void)modSelect:(UIButton *)sender {
    NSArray *names=@[@"Player",@"Weapons",@"Perks",@"Lethals",@"Tacticals",@"Killstreaks",@"Game",@"Visuals",@"Mods",@"Close"];
    NSString *choice=[sender currentTitle];
    if([choice hasPrefix:@"  > "])choice=[choice substringFromIndex:4];
    if([choice containsString:@"Back"]){[self modCategory:@"COD4 // MOD MENU" entries:names];return;}
    if([choice containsString:@"Close"]){[self toggleMod];return;}
    if([choice containsString:@"Player"]){
       [self modCategory:@"PLAYER // PRIVATE CHEATS" entries:@[@"God Mode",@"Demigod",@"Noclip",@"UFO",@"No Target",@"Back"]];return;
    }
    if([choice containsString:@"Weapons"]){
       [self modCategory:@"WEAPONS" entries:@[@"Assault Rifles",@"SMGs",@"Snipers",@"Shotguns",@"Pistols",@"Refill Ammo",@"Back"]];return;
    }
    NSDictionary<NSString *,NSArray<NSString *> *> *categories=@{
      @"Assault Rifles":@[@"M4 Carbine",@"AK-47",@"M16A4",@"G36C",@"G3"],
      @"SMGs":@[@"MP5",@"AK-74u",@"P90",@"Skorpion",@"Mini-Uzi"],
      @"Snipers":@[@"M40A3",@"Barrett .50cal",@"Dragunov",@"R700"],
      @"Shotguns":@[@"W1200",@"M1014"],@"Pistols":@[@"M9",@"USP .45",@"Desert Eagle"],
      @"Perks":@[@"Stopping Power",@"Juggernaut",@"Sleight of Hand",@"Double Tap",@"Steady Aim"],
      @"Lethals":@[@"Frag Grenade",@"Claymore",@"C4"],
      @"Tacticals":@[@"Flashbang",@"Stun Grenade",@"Smoke Grenade"],
      @"Killstreaks":@[@"3 Kills: UAV",@"5 Kills: Airstrike",@"7 Kills: Attack Helicopter"]
    };
    if(categories[choice]){
       NSMutableArray *rows=[categories[choice] mutableCopy];[rows addObject:@"Back"];
       [self modCategory:choice entries:rows];return;
    }
    NSDictionary<NSString *,NSString *> *weaponNames=@{
      @"M4 Carbine":@"m4_mp",@"AK-47":@"ak47_mp",@"M16A4":@"m16_mp",@"G36C":@"g36c_mp",@"G3":@"g3_mp",
      @"MP5":@"mp5_mp",@"AK-74u":@"ak74u_mp",@"P90":@"p90_mp",@"Skorpion":@"skorpion_mp",@"Mini-Uzi":@"uzi_mp",
      @"M40A3":@"m40a3_mp",@"Barrett .50cal":@"barrett_mp",@"Dragunov":@"dragunov_mp",@"R700":@"remington700_mp",
      @"W1200":@"winchester1200_mp",@"M1014":@"m1014_mp",@"M9":@"beretta_mp",@"USP .45":@"usp_mp",@"Desert Eagle":@"deserteagle_mp",
      @"Frag Grenade":@"frag_grenade_mp",@"Claymore":@"claymore_mp",@"C4":@"c4_mp",
      @"Flashbang":@"flash_grenade_mp",@"Stun Grenade":@"concussion_grenade_mp",@"Smoke Grenade":@"smoke_grenade_mp"
    };
    for(NSString *name in weaponNames)if([choice containsString:name]) {
        NSString *item=weaponNames[name];KisakApple_ModCommand([[@"give " stringByAppendingString:item] UTF8String]);
        [self modMessage:@"Item request sent to local COD4 server (sv_cheats 1 required)."];
        return;
    }
    NSArray *perks=categories[@"Perks"], *streaks=categories[@"Killstreaks"];
    for(NSString *name in [perks arrayByAddingObjectsFromArray:streaks])if([choice containsString:name]) {
        [NSUserDefaults.standardUserDefaults setObject:name forKey:
            [perks containsObject:name]?@"COD4MenuSelectedPerk":@"COD4MenuSelectedStreak"];
        [self modMessage:@"Selection saved as a preset; COD4 class/killstreak granting is not yet linked to this menu."];
        return;
    }
    NSDictionary<NSString *,NSString *> *commands=@{
       @"God Mode":@"god", @"Demigod":@"demigod", @"Noclip":@"noclip",
       @"UFO":@"ufo", @"No Target":@"notarget",
       @"Refill Ammo":@"give ammo", @"Give All Weapons":@"give all"
    };
    for(NSString *name in commands)if([choice containsString:name]) {
        KisakApple_ModCommand(commands[name].UTF8String);
        [self modMessage:@"Command queued. Available only when local server cheats are enabled (sv_cheats 1)."];
        return;
    }
    if([choice containsString:@"Game"]){[self modCategory:@"GAME" entries:@[@"Mods",@"Back"]];return;}
    if([choice containsString:@"Visuals"]){[self modCategory:@"VISUALS" entries:@[@"Toggle touch controls",@"Back"]];return;}
    if([choice containsString:@"Toggle touch controls"]){_touchControls.hidden=!_touchControls.hidden;return;}
    if([choice containsString:@"Import Mod Folder"]){[self importModFolder];return;}
    if([choice containsString:@"Mods"]){[self modList];return;}
    if([choice containsString:@"No mod"]){[NSUserDefaults.standardUserDefaults removeObjectForKey:@"COD4SelectedMod"];[self modMessage:@"Close and reopen the app to return to base COD4."];return;}
    if([choice containsString:@"Load: "]) {
       NSString *mod=[choice componentsSeparatedByString:@"Load: "].lastObject;
       [NSUserDefaults.standardUserDefaults setObject:mod forKey:@"COD4SelectedMod"];
       [self modMessage:@"Close and reopen COD4iOS to activate this mod."];return;
    }
    [self modMessage:@"This offline player or weapon feature is not yet implemented."];
}
- (void)modList {
    NSString *path=[[self documentsPath] stringByAppendingPathComponent:@"mods"];
    NSArray *files=[[NSFileManager defaultManager] contentsOfDirectoryAtPath:path error:nil]?:@[];
    NSMutableArray *entries=[NSMutableArray arrayWithObjects:@"Import Mod Folder",@"No mod",nil];
    NSCharacterSet *bad=[[NSCharacterSet characterSetWithCharactersInString:@"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"] invertedSet];
    for(NSString *name in [files sortedArrayUsingSelector:@selector(compare:)]) {
      BOOL dir=NO;
      if(name.length>32 || [name rangeOfCharacterFromSet:bad].location!=NSNotFound)continue;
      if([[NSFileManager defaultManager] fileExistsAtPath:[path stringByAppendingPathComponent:name] isDirectory:&dir] && dir)
         [entries addObject:[@"Load: " stringByAppendingString:name]];
      if(entries.count>=5)break;
    }
    [entries addObject:@"Back"];[self modCategory:@"MODS // Documents/mods" entries:entries];
}
- (void)importModFolder {
    UIDocumentPickerViewController *picker=[[UIDocumentPickerViewController alloc]
        initForOpeningContentTypes:@[UTTypeFolder] asCopy:NO];
    picker.delegate=self;
    picker.allowsMultipleSelection=NO;
    [self presentViewController:picker animated:YES completion:nil];
}
- (void)documentPicker:(UIDocumentPickerViewController *)controller
 didPickDocumentsAtURLs:(NSArray<NSURL *> *)urls {
    NSURL *source=urls.firstObject;
    if(!source)return;
    BOOL secured=[source startAccessingSecurityScopedResource];
    NSFileManager *fm=NSFileManager.defaultManager;
    NSString *base=[[self documentsPath] stringByAppendingPathComponent:@"mods"];
    NSError *err=nil;
    [fm createDirectoryAtPath:base withIntermediateDirectories:YES attributes:nil error:&err];
    NSString *name=source.lastPathComponent;
    // Only single, safe path components are accepted.
    NSCharacterSet *bad=[[NSCharacterSet characterSetWithCharactersInString:
        @"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"] invertedSet];
    if(!name.length || name.length>40 || [name rangeOfCharacterFromSet:bad].location!=NSNotFound) {
        err=[NSError errorWithDomain:@"COD4Mods" code:1
            userInfo:@{NSLocalizedDescriptionKey:@"Rename the mod folder with letters, numbers, _ or - and import again."}];
    }
    if(!err){
        NSString *dest=[base stringByAppendingPathComponent:name];
        if([fm fileExistsAtPath:dest]) {
            err=[NSError errorWithDomain:@"COD4Mods" code:2
                userInfo:@{NSLocalizedDescriptionKey:@"That mod folder already exists. Remove or rename it before importing."}];
        } else {
            [fm copyItemAtURL:source toURL:[NSURL fileURLWithPath:dest isDirectory:YES] error:&err];
        }
    }
    if(secured)[source stopAccessingSecurityScopedResource];
    [self modList];
    [self modMessage:err?err.localizedDescription:
         @"Imported to COD4iOS Documents/mods. Reopen the built-in Mods menu to refresh."];
}
- (void)documentPickerWasCancelled:(UIDocumentPickerViewController *)controller {
    (void)controller;
}
- (void)checkModCombo {
    BOOL down=NO;
    for(GCController *c in GCController.controllers) {
        GCExtendedGamepad *g=c.extendedGamepad;
        if(g && g.leftShoulder.pressed && g.rightShoulder.pressed && g.dpad.up.pressed)down=YES;
    }
    if(down && !_modLatched)[self toggleMod];
    _modLatched=down;
}
- (NSString *)documentsPath
{
    return NSSearchPathForDirectoriesInDomains(NSDocumentDirectory, NSUserDomainMask, YES).firstObject;
}

- (BOOL)hasGameData:(NSString *)root
{
    NSFileManager *files = NSFileManager.defaultManager;
    BOOL isDirectory = NO;
    return [files fileExistsAtPath:[root stringByAppendingPathComponent:@"localization.txt"]]
        && [files fileExistsAtPath:[root stringByAppendingPathComponent:@"main"] isDirectory:&isDirectory] && isDirectory
        && [files fileExistsAtPath:[root stringByAppendingPathComponent:@"zone"] isDirectory:&isDirectory] && isDirectory;
}

- (void)viewDidAppear:(BOOL)animated
{
    [super viewDidAppear:animated];
    [self startIfReady];
}

- (BOOL)installBundledGameDataIfNeeded:(NSString *)root error:(NSError **)error
{
    if ([self hasGameData:root])
        return YES;
    NSString *bundleRoot = [NSBundle.mainBundle.resourcePath stringByAppendingPathComponent:@"PrivateGameData"];
    if (![self hasGameData:bundleRoot])
        return NO;
    NSFileManager *fm = NSFileManager.defaultManager;
    for (NSString *name in @[@"main", @"zone", @"localization.txt"])
    {
        NSString *destination = [root stringByAppendingPathComponent:name];
        if ([fm fileExistsAtPath:destination])
            continue; // Never replace existing user data.
        NSString *source = [bundleRoot stringByAppendingPathComponent:name];
        if (![fm copyItemAtPath:source toPath:destination error:error])
            return NO;
    }
    return [self hasGameData:root];
}

- (void)startIfReady
{
    if (_started)
        return;

    NSString *root = [self documentsPath];
    NSError *bundleError = nil;
    if (![self hasGameData:root])
        [self installBundledGameDataIfNeeded:root error:&bundleError];
    if (bundleError)
    {
        _status.text = [NSString stringWithFormat:@"Bundled game data installation failed: %@", bundleError.localizedDescription];
        return;
    }
    if (![self hasGameData:root])
    {
        _status.text = @"Game files not found.\n\nConnect the iPhone to your Mac, open it in Finder, choose Files → COD4iOS, "
                       @"and copy in the contents of your Call of Duty 4 folder: localization.txt, main and zone. "
                       @"Then reopen the app.";
        return;
    }

#ifdef KISAK_MP
    if(!_patchReady) {
        if(_preparingPatch)return;
        _preparingPatch=YES;
        _status.text=@"Preparing CoD4x multiplayer…";
        __weak KISEngineViewController *weakSelf=self;
        KisakPrepareCoD4xPatch(root,^(NSError *error){
            KISEngineViewController *strongSelf=weakSelf;if(!strongSelf)return;
            strongSelf->_preparingPatch=NO;
            if(error){strongSelf->_status.text=[NSString stringWithFormat:@"%@\n\nCheck your connection and reopen COD4iOS to retry.",error.localizedDescription];return;}
            strongSelf->_patchReady=YES;[strongSelf startIfReady];
        });
        return;
    }
#endif
    _started = YES;
    CGFloat scale = self.view.window.screen.nativeScale;
#if TARGET_OS_SIMULATOR
    // Optional test setting: reduce render targets on memory-constrained Macs
    // without changing the device build or shrinking menu hit targets.
    if (const char *limit = getenv("KISAK_RENDER_MAX_DIMENSION"))
    {
        const int maximum = atoi(limit);
        const CGFloat longest = MAX(self.view.bounds.size.width, self.view.bounds.size.height);
        if (maximum >= 640 && longest > 0)
            scale = MIN(scale, maximum / longest);
    }
#endif
    const int width = static_cast<int>(self.view.bounds.size.width * scale);
    const int height = static_cast<int>(self.view.bounds.size.height * scale);
    ((CAMetalLayer *)_engineView.layer).drawableSize = CGSizeMake(width, height);
    KisakApple_SetRenderWindow((__bridge void *)_engineView, width, height);
    const UIEdgeInsets insets = self.view.safeAreaInsets;
    // Symmetric margins also protect the HUD after rotating to the other
    // landscape orientation, without changing the world/render viewport.
    KisakApple_SetDisplaySafeArea(MAX(insets.left, insets.right) * scale,
                                 MAX(insets.top, insets.bottom) * scale);

    NSString *logPath = [root stringByAppendingPathComponent:@"kisakcod.log"];
    // Retain the prior session, including failures, when the app is reopened.
    NSString *previousLogPath = [root stringByAppendingPathComponent:@"kisakcod.previous.log"];
    if ([[NSFileManager defaultManager] fileExistsAtPath:logPath]) {
        [[NSFileManager defaultManager] removeItemAtPath:previousLogPath error:nil];
        [[NSFileManager defaultManager] moveItemAtPath:logPath toPath:previousLogPath error:nil];
    }
    freopen(logPath.fileSystemRepresentation, "w", stdout);
    setvbuf(stdout, NULL, _IONBF, 0);
    // Share stdout's file description so both streams append in order instead of
    // overwriting each other through separate file offsets.
    dup2(fileno(stdout), fileno(stderr));
    setvbuf(stderr, NULL, _IONBF, 0);
    setvbuf(stdout, nullptr, _IOLBF, 0);
    setenv("KISAK_INSTALL_PATH", root.fileSystemRepresentation, 1);
    chdir(root.fileSystemRepresentation);

    _status.text = @"Starting engine… console output: Documents/kisakcod.log";

    pthread_attr_t attributes;
    pthread_attr_init(&attributes);
    // The decompiled engine keeps large buffers on its main thread's stack.
    pthread_attr_setstacksize(&attributes, 16 * 1024 * 1024);
    pthread_t thread;
    if (pthread_create(&thread, &attributes, KISEngineThreadMain, nullptr) == 0)
    {
        pthread_detach(thread);
        _displayLink = [CADisplayLink displayLinkWithTarget:self selector:@selector(displayTick:)];
        // Request the panel's maximum refresh rate (including ProMotion).
        // This link enables high-refresh presentation; it does not gate the engine.
        const float maximumFPS = self.view.window.screen.maximumFramesPerSecond;
        _displayLink.preferredFrameRateRange = CAFrameRateRangeMake(30.0f, maximumFPS, maximumFPS);
        [_displayLink addToRunLoop:NSRunLoop.mainRunLoop forMode:NSRunLoopCommonModes];
        _controllerInput = [KISControllerInput new];
        _touchControls=[[KISTouchControls alloc] initWithFrame:self.view.bounds];
        [self.view addSubview:_touchControls];
        [self.view bringSubviewToFront:_modPanel];
        [self.view bringSubviewToFront:_modToggle];
        _controllerInput.touchControls=_touchControls;
        __weak KISControllerInput *input=_controllerInput;
        _touchControls.inputChanged=^{ [input publish]; };
        [_controllerInput start];
        // The engine draws into this view now; the label would cover the menu.
        _status.hidden = YES;
        [_engineView becomeFirstResponder];
        UITapGestureRecognizer *twoFingerTap = [[UITapGestureRecognizer alloc] initWithTarget:self action:@selector(toggleKeyboard)];
        twoFingerTap.numberOfTouchesRequired = 2;
        twoFingerTap.delegate = self;
        twoFingerTap.cancelsTouchesInView = NO;
        [_engineView addGestureRecognizer:twoFingerTap];
        [NSTimer scheduledTimerWithTimeInterval:0.2 target:self selector:@selector(syncKeyboard) userInfo:nil repeats:YES];
    }
    else
        _status.text = @"Could not start the engine thread.";
    pthread_attr_destroy(&attributes);
}

- (void)displayTick:(CADisplayLink *)link
{
    (void)link; // Engine frames are uncapped and paced only by available Metal drawables.
}

- (void)syncKeyboard
{
#if TARGET_OS_SIMULATOR
    static unsigned ticks = 0;
    if (++ticks % 25 == 0)
    {
        task_vm_info_data_t info = {};
        mach_msg_type_number_t count = TASK_VM_INFO_COUNT;
        if (task_info(mach_task_self(), TASK_VM_INFO, reinterpret_cast<task_info_t>(&info), &count) == KERN_SUCCESS)
            fprintf(stderr, "Simulator memory: %llu MiB footprint, %llu MiB resident, %llu MiB compressed\n",
                    static_cast<unsigned long long>(info.phys_footprint / (1024 * 1024)),
                    static_cast<unsigned long long>(info.resident_size / (1024 * 1024)),
                    static_cast<unsigned long long>(info.compressed / (1024 * 1024)));
    }
#endif
    const BOOL editing = KisakApple_TextInputActive() != 0;
    if (editing != _engineEditing)
    {
        _engineEditing = editing;
        fprintf(stderr, "Keyboard: game text field editing %s\n", editing ? "started" : "ended");
        // Follow the game: show the keyboard when a field starts editing, hide it after.
        _engineView.wantsKeyboard = editing;
    }
    if (!_engineView.isFirstResponder)
        [_engineView becomeFirstResponder];
}

- (BOOL)gestureRecognizerShouldBegin:(UIGestureRecognizer *)gestureRecognizer
{
    (void)gestureRecognizer;
    return KisakApple_ControllerTouchContext()==0;
}

- (void)toggleKeyboard
{
    _engineView.wantsKeyboard = !_engineView.wantsKeyboard;
    fprintf(stderr, "Keyboard: toggled %s by two-finger tap\n", _engineView.wantsKeyboard ? "on" : "off");
}

- (BOOL)prefersStatusBarHidden { return YES; }
- (BOOL)prefersHomeIndicatorAutoHidden { return YES; }
- (UIInterfaceOrientationMask)supportedInterfaceOrientations { return UIInterfaceOrientationMaskLandscape; }
@end

// iOS 26 and later trap at launch any app that has not adopted the UIScene lifecycle
// (___UIApplicationEvaluateRuntimeIssueForNoSceneLifecycleAdoption). The window is therefore
// built when the scene connects rather than in didFinishLaunchingWithOptions; Info.plist.in
// names this class in its UIApplicationSceneManifest.
@interface KISEngineSceneDelegate : UIResponder <UIWindowSceneDelegate>
@property(nonatomic, strong) UIWindow *window;
@end

@implementation KISEngineSceneDelegate
- (void)scene:(UIScene *)scene willConnectToSession:(UISceneSession *)session options:(UISceneConnectionOptions *)options
{
    (void)session; (void)options;
    if (![scene isKindOfClass:UIWindowScene.class])
        return;
    UIWindowScene *windowScene = (UIWindowScene *)scene;
    self.window = [[UIWindow alloc] initWithWindowScene:windowScene];
    self.window.rootViewController = [KISEngineViewController new];
    [self.window makeKeyAndVisible];
}
@end

@interface KISEngineAppDelegate : UIResponder <UIApplicationDelegate>
@end

@implementation KISEngineAppDelegate
- (BOOL)application:(UIApplication *)application didFinishLaunchingWithOptions:(NSDictionary *)options
{
    (void)application; (void)options;
    AVAudioSession *session = AVAudioSession.sharedInstance;
    NSError *error = nil;
    // Game audio uses media volume and stays audible with the Ring/Silent switch on.
    if (![session setCategory:AVAudioSessionCategoryPlayback mode:AVAudioSessionModeDefault options:0 error:&error])
        NSLog(@"COD4iOS: audio session category failed: %@", error);
    [self activateGameAudio:nil];
    NSNotificationCenter *center = NSNotificationCenter.defaultCenter;
    [center addObserver:self selector:@selector(activateGameAudio:) name:UIApplicationDidBecomeActiveNotification object:nil];
    [center addObserver:self selector:@selector(audioInterrupted:) name:AVAudioSessionInterruptionNotification object:session];
    return YES;
}

- (void)activateGameAudio:(NSNotification *)notification
{
    (void)notification;
    NSError *error = nil;
    if (![AVAudioSession.sharedInstance setActive:YES error:&error])
        NSLog(@"COD4iOS: audio session activation failed: %@", error);
}

- (void)audioInterrupted:(NSNotification *)notification
{
    if ([notification.userInfo[AVAudioSessionInterruptionTypeKey] unsignedIntegerValue] == AVAudioSessionInterruptionTypeEnded &&
        ([notification.userInfo[AVAudioSessionInterruptionOptionKey] unsignedIntegerValue] & AVAudioSessionInterruptionOptionShouldResume))
        [self activateGameAudio:nil];
}

- (UISceneConfiguration *)application:(UIApplication *)application
    configurationForConnectingSceneSession:(UISceneSession *)session
    options:(UISceneConnectionOptions *)options
{
    (void)application; (void)options;
    UISceneConfiguration *configuration =
        [[UISceneConfiguration alloc] initWithName:@"Default" sessionRole:session.role];
    configuration.delegateClass = KISEngineSceneDelegate.class;
    return configuration;
}
@end

// The app ships both engines as dylibs and loads one. KISAK_MP is a build-wide ABI switch (it
// changes struct layouts), so singleplayer and multiplayer cannot share a binary; two-level
// namespacing keeps each dylib's symbols and globals to itself. The launcher picks a mode and
// calls this, which is the only symbol either dylib exports.
extern "C" __attribute__((visibility("default"))) int KisakEngine_AppMain(int argc, char *argv[])
{
    @autoreleasepool {
        return UIApplicationMain(argc, argv, nil, NSStringFromClass(KISEngineAppDelegate.class));
    }
}

#ifndef KISAK_ENGINE_AS_DYLIB
int main(int argc, char *argv[])
{
    return KisakEngine_AppMain(argc, argv);
}
#endif
