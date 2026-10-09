#import "survival_ui.h"
#import <GameController/GameController.h>
#include "../engine/controller_input.h"
#include "../platform/apple_engine_mode.h"
#ifndef KISAK_MP
#include "../survival/SurvivalBridge.hpp"
#endif

BOOL KisakInstallSurvivalContent(NSString *documents,NSError **error) {
    NSFileManager *files=NSFileManager.defaultManager;
    // Foundation does not always resolve symlink ancestors when the final file
    // is absent. Reject redirected components explicitly before creating folders.
    NSString *checked=documents.stringByResolvingSymlinksInPath;
    for(NSString *component in @[@"mods", @"specops_survival", @"maps", @"specops_survival.gsc"]) {
        checked=[checked stringByAppendingPathComponent:component];
        NSDictionary *attributes=[files attributesOfItemAtPath:checked error:NULL];
        if([attributes[NSFileType] isEqualToString:NSFileTypeSymbolicLink]) {
            if(error) *error=[NSError errorWithDomain:@"COD4iOSSurvival" code:1 userInfo:@{NSLocalizedDescriptionKey:@"The Survival mod path cannot use redirected folders or files."}];
            return NO;
        }
    }
    NSString *root=[documents stringByAppendingPathComponent:@"mods/specops_survival"];
    NSString *relative=@"maps/specops_survival.gsc";
    NSString *destination=[root stringByAppendingPathComponent:relative];
    // Resolve the existing ancestors too: a user-created symlink must not redirect writes.
    NSString *resolved=destination.stringByResolvingSymlinksInPath;
    NSString *expected=[documents.stringByResolvingSymlinksInPath stringByAppendingPathComponent:@"mods/specops_survival/maps/specops_survival.gsc"];
    if(![resolved isEqualToString:expected]) {
        if(error) *error=[NSError errorWithDomain:@"COD4iOSSurvival" code:1 userInfo:@{NSLocalizedDescriptionKey:@"The Survival mod path must stay in Documents/mods/specops_survival without redirected folders."}];
        return NO;
    }
    NSString *source=[NSBundle.mainBundle.resourcePath stringByAppendingPathComponent:@"SurvivalContent/maps/specops_survival.gsc"];
    if(![files fileExistsAtPath:destination]) {
        if(![files createDirectoryAtPath:destination.stringByDeletingLastPathComponent withIntermediateDirectories:YES attributes:nil error:error]) return NO;
        return [files copyItemAtPath:source toPath:destination error:error];
    }
    BOOL directory=NO;
    if(![files fileExistsAtPath:destination isDirectory:&directory] || directory) {
        if(error) *error=[NSError errorWithDomain:@"COD4iOSSurvival" code:2 userInfo:@{NSLocalizedDescriptionKey:@"The Survival script path must be a file."}];
        return NO;
    }
    return YES;
}

@implementation KISSurvivalUI {
    UILabel *_hud, *_detail;
    UIButton *_shop, *_modes;
    UIView *_shade;
    UIStackView *_panel;
    NSMutableArray<UIButton *> *_choices;
    BOOL _choosingMode, _running, _pendingShop;
    NSUInteger _selected;
    NSTimer *_timer;
    kisak::controller::ButtonState _buttons;
#ifndef KISAK_MP
    cod4ios::survival::Status _status;
    cod4ios::survival::Status _shopRequestStatus;
#endif
}
- (instancetype)initWithFrame:(CGRect)frame {
    if((self=[super initWithFrame:frame])) {
        self.autoresizingMask=UIViewAutoresizingFlexibleWidth|UIViewAutoresizingFlexibleHeight;
        _hud=[UILabel new]; _hud.textColor=UIColor.whiteColor;
        _hud.font=[UIFont monospacedDigitSystemFontOfSize:14 weight:UIFontWeightSemibold];
        _hud.backgroundColor=[UIColor.blackColor colorWithAlphaComponent:.6]; _hud.numberOfLines=3;
        _hud.translatesAutoresizingMaskIntoConstraints=NO; [self addSubview:_hud];
        _shop=[UIButton buttonWithType:UIButtonTypeSystem]; [_shop setTitle:@"Shop" forState:UIControlStateNormal];
        [_shop addTarget:self action:@selector(openShop) forControlEvents:UIControlEventTouchUpInside];
        _modes=[UIButton buttonWithType:UIButtonTypeSystem]; [_modes setTitle:@"Modes" forState:UIControlStateNormal];
        [_modes addTarget:self action:@selector(modesPressed) forControlEvents:UIControlEventTouchUpInside];
        for(UIButton *button in @[_shop,_modes]) {
            button.backgroundColor=[UIColor.blackColor colorWithAlphaComponent:.7];
            [button setTitleColor:UIColor.whiteColor forState:UIControlStateNormal];
            button.translatesAutoresizingMaskIntoConstraints=NO; [self addSubview:button];
        }
        [NSLayoutConstraint activateConstraints:@[
            [_hud.leadingAnchor constraintEqualToAnchor:self.safeAreaLayoutGuide.leadingAnchor constant:12],
            [_hud.topAnchor constraintEqualToAnchor:self.safeAreaLayoutGuide.topAnchor constant:8],
            [_hud.trailingAnchor constraintLessThanOrEqualToAnchor:_shop.leadingAnchor constant:-8],
            [_shop.topAnchor constraintEqualToAnchor:_hud.topAnchor],
            [_shop.trailingAnchor constraintEqualToAnchor:_modes.leadingAnchor constant:-8],
            [_shop.widthAnchor constraintEqualToConstant:76],[_shop.heightAnchor constraintEqualToConstant:44],
            [_modes.topAnchor constraintEqualToAnchor:_hud.topAnchor],
            [_modes.trailingAnchor constraintEqualToAnchor:self.safeAreaLayoutGuide.trailingAnchor constant:-12],
            [_modes.widthAnchor constraintEqualToConstant:76],[_modes.heightAnchor constraintEqualToConstant:44]]];
        _choices=[NSMutableArray new];
        __weak KISSurvivalUI *weakSelf=self;
        _timer=[NSTimer scheduledTimerWithTimeInterval:1.0/30 repeats:YES block:^(NSTimer *timer){
            (void)timer; [weakSelf pollController];
        }];
        _hud.hidden=_shop.hidden=YES;
    }
    return self;
}
- (void)dealloc { [_timer invalidate]; }
- (BOOL)modal { return _shade!=nil; }
- (UIView *)hitTest:(CGPoint)point withEvent:(UIEvent *)event {
    UIView *hit=[super hitTest:point withEvent:event];
    return hit==self ? nil : hit;
}
- (void)clearPanel {
    [_shade removeFromSuperview]; _shade=nil; _panel=nil; _detail=nil;
    [_choices removeAllObjects]; _selected=0; _pendingShop=NO;
}
- (void)panelTitle:(NSString *)title detail:(NSString *)detail choices:(NSArray<NSString *> *)titles {
    [self clearPanel];
    _shade=[[UIView alloc] initWithFrame:self.bounds];
    _shade.autoresizingMask=UIViewAutoresizingFlexibleWidth|UIViewAutoresizingFlexibleHeight;
    _shade.backgroundColor=[UIColor.blackColor colorWithAlphaComponent:.88]; [self addSubview:_shade];
    _panel=[UIStackView new]; _panel.axis=UILayoutConstraintAxisVertical; _panel.spacing=8;
    _panel.translatesAutoresizingMaskIntoConstraints=NO; [_shade addSubview:_panel];
    UILabel *heading=[UILabel new]; heading.text=title; heading.textColor=UIColor.whiteColor;
    heading.font=[UIFont systemFontOfSize:21 weight:UIFontWeightBold]; heading.textAlignment=NSTextAlignmentCenter;
    [_panel addArrangedSubview:heading];
    _detail=[UILabel new]; _detail.text=detail; _detail.textColor=UIColor.lightGrayColor;
    _detail.numberOfLines=0; _detail.font=[UIFont systemFontOfSize:13]; _detail.textAlignment=NSTextAlignmentCenter;
    [_panel addArrangedSubview:_detail];
    for(NSString *titleText in titles) {
        UIButton *button=[UIButton buttonWithType:UIButtonTypeSystem];
        [button setTitle:titleText forState:UIControlStateNormal]; [button setTitleColor:UIColor.whiteColor forState:UIControlStateNormal];
        button.tag=_choices.count; [button addTarget:self action:@selector(choice:) forControlEvents:UIControlEventTouchUpInside];
        [button.heightAnchor constraintEqualToConstant:38].active=YES;
        [_choices addObject:button]; [_panel addArrangedSubview:button];
    }
    NSLayoutConstraint *preferredWidth=[_panel.widthAnchor constraintEqualToAnchor:_shade.safeAreaLayoutGuide.widthAnchor multiplier:.8];
    preferredWidth.priority=UILayoutPriorityDefaultHigh;
    [NSLayoutConstraint activateConstraints:@[
        [_panel.centerXAnchor constraintEqualToAnchor:_shade.centerXAnchor],
        [_panel.centerYAnchor constraintEqualToAnchor:_shade.centerYAnchor],
        [_panel.widthAnchor constraintLessThanOrEqualToConstant:480],
        preferredWidth,
        [_panel.topAnchor constraintGreaterThanOrEqualToAnchor:_shade.safeAreaLayoutGuide.topAnchor constant:6],
        [_panel.bottomAnchor constraintLessThanOrEqualToAnchor:_shade.safeAreaLayoutGuide.bottomAnchor constant:-6]]];
    [self highlight];
}
- (void)highlight {
    for(NSUInteger i=0;i<_choices.count;++i)
        _choices[i].backgroundColor=i==_selected ? [UIColor colorWithRed:.2 green:.35 blue:.18 alpha:1] : [UIColor colorWithWhite:.2 alpha:1];
}
- (void)showModes:(BOOL)running {
#ifndef KISAK_MP
    if(self.modal && !_choosingMode) cod4ios::survival::queueAction(cod4ios::survival::Action::CloseShop,_status.epoch);
#endif
    _running=running; _choosingMode=YES;
    [self panelTitle:@"COD4iOS" detail:running ? @"Changing between Campaign and Survival reloads level state. Multiplayer requires reopening the app." : @"Touch a mode or use D-pad and A. Original game files must be in Documents."
                 choices:running ? @[@"Campaign",@"Special Ops Survival",@"Multiplayer",@"Cancel"] : @[@"Campaign",@"Special Ops Survival",@"Multiplayer"]];
}
- (void)modesPressed { [self showModes:YES]; }
- (void)openShop {
#ifndef KISAK_MP
    using namespace cod4ios::survival;
    _status=readStatus();
    if(!_status.active) return;
    if(_status.match.phase==Phase::GameOver) { queueAction(Action::Retry,_status.epoch); return; }
    if(_status.match.phase!=Phase::Intermission || !queueAction(Action::OpenShop,_status.epoch)) return;
    _choosingMode=NO;
    [self panelTitle:@"Survival Shop" detail:@"D-pad selects • A purchases • B closes"
             choices:@[@"Refill ammo — 250",@"Armor (100 points) — 500",@"AK-47 — 750",@"Close shop"]];
    _pendingShop=YES;
    _shopRequestStatus=_status;
#endif
}
- (void)choice:(UIButton *)button {
    const NSUInteger index=button.tag;
    if(_choosingMode) {
        if(index>=3) { [self clearPanel]; return; }
        const char *mode=index==0 ? "campaign" : index==1 ? "survival" : "multiplayer";
        [self clearPanel]; if(self.modeSelected) self.modeSelected(mode); return;
    }
#ifndef KISAK_MP
    using namespace cod4ios::survival;
    if(index==3) { queueAction(Action::CloseShop,_status.epoch); [self clearPanel]; }
    else queueAction(index==0 ? Action::Ammo : index==1 ? Action::Armor : Action::Rifle,_status.epoch);
#endif
}
- (void)update {
#ifndef KISAK_MP
    using namespace cod4ios::survival;
    _status=readStatus();
    _hud.hidden=!_status.active; _shop.hidden=!_status.active;
    if(!_status.active) { if(self.modal && !_choosingMode) [self clearPanel]; return; }
    const auto &s=_status.match;
    _hud.text=[NSString stringWithFormat:@"Wave %u • Enemies %u • Credits %u\nBest %u • Armor %u%@",s.wave,s.alive+s.spawnRemaining,s.credits,_status.bestWave,_status.armor,
        s.phase==Phase::Intermission ? [NSString stringWithFormat:@" • Next wave %.0fs",ceil(s.secondsRemaining)] : @""];
    [_shop setTitle:s.phase==Phase::GameOver ? @"Retry" : @"Shop" forState:UIControlStateNormal];
    _shop.enabled=s.phase==Phase::Intermission || s.phase==Phase::GameOver;
    if(self.modal && !_choosingMode) {
        if(_status.shopOpen) _pendingShop=NO;
        if(!shopRequestPending(_status,_shopRequestStatus)) _pendingShop=NO;
        if(!_status.shopOpen && !_pendingShop) [self clearPanel];
        else _detail.text=[NSString stringWithFormat:@"Credits %u • D-pad / A / B\n%s",s.credits,_status.message];
    }
    if(s.phase==Phase::GameOver) _hud.text=[_hud.text stringByAppendingFormat:@"\n%s",_status.message];
#endif
}
- (void)pollController {
    using namespace kisak::controller;
    GCExtendedGamepad *pad=GCController.controllers.firstObject.extendedGamepad;
    uint32_t buttons=0;
    if(pad.buttonA.isPressed) buttons|=1u<<South;
    if(pad.buttonB.isPressed) buttons|=1u<<East;
    if(pad.buttonOptions.isPressed) buttons|=1u<<Options;
    if(pad.dpad.up.isPressed) buttons|=1u<<Up;
    if(pad.dpad.down.isPressed) buttons|=1u<<Down;
    buttons|=MenuDirection(pad.leftThumbstick.xAxis.value,pad.leftThumbstick.yAxis.value,.55f);
    const Edges edges=_buttons.Update(buttons,pad!=nil,self.modal);
    if(self.modal) {
        if(edges.pressed&(1u<<Up)) _selected=(_selected+_choices.count-1)%_choices.count;
        if(edges.pressed&(1u<<Down)) _selected=(_selected+1)%_choices.count;
        [self highlight];
        if(edges.pressed&(1u<<South)) [self choice:_choices[_selected]];
        else if(edges.pressed&(1u<<East)) {
            if(_choosingMode && _running) [self clearPanel];
            else if(!_choosingMode) [self choice:_choices.lastObject];
        }
    } else {
        if(edges.pressed&(1u<<Options)) [self showModes:YES];
        else if(edges.pressed&(1u<<Up)) [self openShop];
    }
}
@end
