#import "survival_ui.h"
#import <GameController/GameController.h>
#include "../engine/controller_input.h"
#include "../platform/apple_engine_mode.h"
#include "../survival/SurvivalConfig.hpp"
#ifndef KISAK_MP
#include "../survival/SurvivalBridge.hpp"
#endif

BOOL KisakInstallSurvivalContent(NSString *documents,NSError **error) {
    NSFileManager *files=NSFileManager.defaultManager;
    // Foundation does not always resolve symlink ancestors when the final file
    // is absent. Reject redirected components explicitly before creating folders.
    NSString *checked=documents.stringByResolvingSymlinksInPath;
    for(NSString *component in @[@"mods", @"specops_survival", @"maps"]) {
        checked=[checked stringByAppendingPathComponent:component];
        NSDictionary *attributes=[files attributesOfItemAtPath:checked error:NULL];
        if([attributes[NSFileType] isEqualToString:NSFileTypeSymbolicLink]) {
            if(error) *error=[NSError errorWithDomain:@"COD4iOSSurvival" code:1 userInfo:@{NSLocalizedDescriptionKey:@"The Survival mod path cannot use redirected folders or files."}];
            return NO;
        }
    }
    NSString *root=[documents stringByAppendingPathComponent:@"mods/specops_survival"];
    for(NSString *relative in @[@"maps/specops_survival.gsc", @"maps/specops_survival_v2.gsc", @"maps/specops_survival_v3.gsc"]) {
    NSString *destination=[root stringByAppendingPathComponent:relative];
    NSDictionary *destinationAttributes=[files attributesOfItemAtPath:destination error:NULL];
    if([destinationAttributes[NSFileType] isEqualToString:NSFileTypeSymbolicLink]) {
        if(error) *error=[NSError errorWithDomain:@"COD4iOSSurvival" code:1 userInfo:@{NSLocalizedDescriptionKey:@"The Survival script cannot be redirected."}];
        return NO;
    }
    // Resolve the existing ancestors too: a user-created symlink must not redirect writes.
    NSString *resolved=destination.stringByResolvingSymlinksInPath;
    NSString *expected=[documents.stringByResolvingSymlinksInPath stringByAppendingPathComponent:[@"mods/specops_survival" stringByAppendingPathComponent:relative]];
    if(![resolved isEqualToString:expected]) {
        if(error) *error=[NSError errorWithDomain:@"COD4iOSSurvival" code:1 userInfo:@{NSLocalizedDescriptionKey:@"The Survival mod path must stay in Documents/mods/specops_survival without redirected folders."}];
        return NO;
    }
    NSString *source=[NSBundle.mainBundle.resourcePath stringByAppendingPathComponent:[@"SurvivalContent" stringByAppendingPathComponent:relative]];
    if(![files fileExistsAtPath:destination]) {
        if(![files createDirectoryAtPath:destination.stringByDeletingLastPathComponent withIntermediateDirectories:YES attributes:nil error:error]) return NO;
        if(![files copyItemAtPath:source toPath:destination error:error]) return NO;
        continue;
    }
    BOOL directory=NO;
    if(![files fileExistsAtPath:destination isDirectory:&directory] || directory) {
        if(error) *error=[NSError errorWithDomain:@"COD4iOSSurvival" code:2 userInfo:@{NSLocalizedDescriptionKey:@"The Survival script path must be a file."}];
        return NO;
    }
    }
    return YES;
}

@implementation KISSurvivalUI {
    UILabel *_hud, *_detail;
    UIButton *_shop, *_modes;
    UIView *_shade;
    UIStackView *_panel;
    NSMutableArray<UIButton *> *_choices;
    BOOL _choosingMode, _running, _pendingShop, _setupInMatch, _setupFromShop;
    NSInteger _screen; // 0 modes, 1 setup, 2 shop, 3 bank, 4 cheats, 5 weapons, 6 equipment, 7 extras
    unsigned _map, _difficulty, _playerClass;
    UIScrollView *_scroll;
    NSString *_feedback;
    NSTimeInterval _actionPendingUntil, _shopPendingUntil, _hudNoticeUntil;
    NSString *_lastStatusMessage, *_hudNotice;
    uint64_t _noticeEpoch;
    uint64_t _noticeSerial;
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
        _hud.backgroundColor=[UIColor.blackColor colorWithAlphaComponent:.6]; _hud.numberOfLines=0;
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
            [_hud.bottomAnchor constraintLessThanOrEqualToAnchor:self.safeAreaLayoutGuide.bottomAnchor constant:-8],
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
    [_shade removeFromSuperview]; _shade=nil; _panel=nil; _detail=nil; _scroll=nil;
    [_choices removeAllObjects]; _selected=0; _pendingShop=NO;
}
- (void)panelTitle:(NSString *)title detail:(NSString *)detail choices:(NSArray<NSString *> *)titles {
    [self clearPanel];
    _shade=[[UIView alloc] initWithFrame:self.bounds];
    _shade.autoresizingMask=UIViewAutoresizingFlexibleWidth|UIViewAutoresizingFlexibleHeight;
    _shade.backgroundColor=[UIColor.blackColor colorWithAlphaComponent:.88]; [self addSubview:_shade];
    _panel=[UIStackView new]; _panel.axis=UILayoutConstraintAxisVertical; _panel.spacing=8;
    _panel.translatesAutoresizingMaskIntoConstraints=NO; _scroll=[UIScrollView new]; _scroll.translatesAutoresizingMaskIntoConstraints=NO; [_shade addSubview:_scroll];
    [_scroll addSubview:_panel];
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
    [NSLayoutConstraint activateConstraints:@[
        [_scroll.centerXAnchor constraintEqualToAnchor:_shade.centerXAnchor],
        [_scroll.widthAnchor constraintEqualToAnchor:_shade.safeAreaLayoutGuide.widthAnchor multiplier:.85],
        [_scroll.topAnchor constraintEqualToAnchor:_shade.safeAreaLayoutGuide.topAnchor constant:8],
        [_scroll.bottomAnchor constraintEqualToAnchor:_shade.safeAreaLayoutGuide.bottomAnchor constant:-8],
        [_panel.topAnchor constraintEqualToAnchor:_scroll.contentLayoutGuide.topAnchor],
        [_panel.bottomAnchor constraintEqualToAnchor:_scroll.contentLayoutGuide.bottomAnchor],
        [_panel.leadingAnchor constraintEqualToAnchor:_scroll.contentLayoutGuide.leadingAnchor],
        [_panel.trailingAnchor constraintEqualToAnchor:_scroll.contentLayoutGuide.trailingAnchor],
        [_panel.widthAnchor constraintEqualToAnchor:_scroll.frameLayoutGuide.widthAnchor]]];
    [self highlight];
}
- (void)highlight {
    for(NSUInteger i=0;i<_choices.count;++i)
        _choices[i].backgroundColor=i==_selected ? [UIColor colorWithRed:.2 green:.35 blue:.18 alpha:1] : [UIColor colorWithWhite:.2 alpha:1];
}
- (void)scrollSelected {
    if(_selected<_choices.count) [_scroll scrollRectToVisible:[_choices[_selected] convertRect:_choices[_selected].bounds toView:_scroll] animated:YES];
}
- (void)showModes:(BOOL)running {
#ifndef KISAK_MP
    if(self.modal && (!_choosingMode || (_screen==1 && _setupInMatch))) cod4ios::survival::queueAction(cod4ios::survival::Action::CloseShop,_status.epoch);
#endif
    _running=running; _choosingMode=YES; _screen=0;
    [self panelTitle:@"COD4iOS" detail:running ? @"Changing between Campaign and Survival reloads level state. Multiplayer requires reopening the app." : @"Touch a mode or use D-pad and A. Original game files must be in Documents."
                 choices:running ? @[@"Campaign",@"Special Ops Survival",@"Multiplayer",@"Cancel"] : @[@"Campaign",@"Special Ops Survival",@"Multiplayer"]];
}
- (void)modesPressed { [self showModes:YES]; }
- (BOOL)mapAvailable:(unsigned)index {
    NSString *mapID=[NSString stringWithUTF8String:cod4ios::survival::mapId(index)];
    NSString *documents=NSSearchPathForDirectoriesInDomains(NSDocumentDirectory,NSUserDomainMask,YES).firstObject;
    NSString *zone=[documents stringByAppendingPathComponent:@"zone"];
    NSFileManager *fm=NSFileManager.defaultManager;
    for(NSString *language in [fm contentsOfDirectoryAtPath:zone error:NULL]) {
        NSString *file=[[zone stringByAppendingPathComponent:language] stringByAppendingPathComponent:[mapID stringByAppendingString:@".ff"]];
        BOOL directory=NO; if([fm fileExistsAtPath:file isDirectory:&directory] && !directory) return YES;
    }
    return NO;
}
- (void)showSetup:(BOOL)inMatch {
    _setupFromShop=(_screen==2); _setupInMatch=inMatch; _screen=1; _choosingMode=YES;
    KisakApple_GetSurvivalConfig(&_map,&_difficulty,&_playerClass);
    _map=MIN(_map,4u); _difficulty=MIN(_difficulty,3u); _playerClass=MIN(_playerClass,2u);
    [self renderSetup];
}
- (void)renderSetup {
    NSString *mapName=[NSString stringWithUTF8String:cod4ios::survival::mapName(_map)];
    NSString *difficultyName=[NSString stringWithUTF8String:cod4ios::survival::difficultyName(_difficulty)];
    NSArray *classes=@[@"Assault - M4",@"Raider - AK-47",@"Armored - M4 + 100 armor"];
    [self panelTitle:@"Survival Setup" detail:_feedback ?: @"Select map, difficulty and class. Start loads a new match. Only Bog has device validation."
        choices:@[[NSString stringWithFormat:@"Map: %@%@",mapName,[self mapAvailable:_map] ? @"" : @" (unavailable)"],
        [@"Difficulty: " stringByAppendingString:difficultyName],[@"Class: " stringByAppendingString:classes[_playerClass]],@"Start",@"Back"]];
}
- (void)renderShop:(NSInteger)screen {
    const BOOL pending=_pendingShop;
    _screen=screen; _choosingMode=NO;
    if(screen==3) [self panelTitle:@"Survival Bank" detail:@"Transfers use match credits. Bank persists between matches." choices:@[@"Deposit 500",@"Deposit 1000",@"Deposit all",@"Withdraw 500",@"Withdraw 1000",@"Withdraw all",@"Back"]];
    else if(screen==4) [self panelTitle:@"Survival Cheats" detail:@"Cheats apply only to this Survival match." choices:@[@"Toggle invulnerability",@"Toggle infinite ammo",@"Add 10000 credits",@"Skip current wave",@"Back"]];
    else if(screen==5) [self panelTitle:@"Weapon Armory" detail:@"MW3 ACR requires its converted asset pack. Original game files stay intact." choices:@[@"Refill ammo - 250",@"AK-47 - 750",@"MW3 ACR - converted pack required",@"Pack-a-Punch - 2000 / 4000 / 6000",@"Back"]];
    else if(screen==6) [self panelTitle:@"Equipment Armory" detail:@"Protection for the next fight." choices:@[@"Armor (100 points) - 500",@"Revive protection - 1500 (rank 2)",@"Quick Recovery - 2000 (rank 4)",@"Sleight of Hand - 2500 (rank 6)",@"Back"]];
    else if(screen==7) [self panelTitle:@"Survival Extras" detail:@"Persistent bank and match cheats." choices:@[@"Bank",@"Cheats",@"Back"]];
    else [self panelTitle:@"Survival Armory" detail:@"Opening shop..." choices:@[@"Weapon Armory",@"Equipment Armory",@"Extras",@"Setup (new match)",@"Close shop"]];
    _pendingShop=pending;
}
- (void)openShop {
#ifndef KISAK_MP
    using namespace cod4ios::survival;
    _status=readStatus();
    if(!_status.active) { _hud.text=@"Survival is not active."; return; }
    if(_status.match.phase==Phase::GameOver) { queueAction(Action::Retry,_status.epoch); return; }
    if(_status.match.phase!=Phase::Fighting && _status.match.phase!=Phase::Intermission) { _hud.text=@"Shop is available once the match starts."; return; }
    if(!queueAction(Action::OpenShop,_status.epoch)) { _hud.text=@"Shop request rejected. Try again."; return; }
    [self renderShop:2]; _pendingShop=YES; _shopRequestStatus=_status; _shopPendingUntil=NSDate.timeIntervalSinceReferenceDate+2;
#endif
}
- (void)choice:(UIButton *)button {
    const NSUInteger index=button.tag;
    if(_screen==0) {
        if(index>=3) { [self clearPanel]; return; }
        if(index==1) {
            _feedback=nil;
#ifndef KISAK_MP
            _status=cod4ios::survival::readStatus(); [self showSetup:_status.active];
#else
            [self showSetup:NO];
#endif
            return;
        }
        [self clearPanel]; if(self.modeSelected) self.modeSelected(index==0 ? "campaign" : "multiplayer"); return;
    }
    if(_screen==1) {
        if(index==0) _map=(_map+1)%5;
        else if(index==1) _difficulty=(_difficulty+1)%4;
        else if(index==2) _playerClass=(_playerClass+1)%3;
        else if(index==4) { _feedback=nil; if(_setupFromShop) [self renderShop:2]; else [self showModes:_running]; return; }
        else {
            if(![self mapAvailable:_map]) { _feedback=@"Selected map is unavailable. Add its original zone language file to Documents."; [self renderSetup]; return; }
            if(!KisakApple_SetSurvivalConfig(_map,_difficulty,_playerClass)) { _feedback=@"Configuration rejected."; [self renderSetup]; return; }
#ifndef KISAK_MP
            if(_setupInMatch && !cod4ios::survival::queueAction(cod4ios::survival::Action::Retry,_status.epoch)) {
                _feedback=@"New match request rejected. Try again."; [self renderSetup]; return;
            }
#endif
            [self clearPanel]; if(!_setupInMatch && self.modeSelected) self.modeSelected("survival"); return;
        }
        _feedback=nil; [self renderSetup]; return;
    }
#ifndef KISAK_MP
    using namespace cod4ios::survival;
    if(_screen==2 && index==4) { queueAction(Action::CloseShop,_status.epoch); [self clearPanel]; return; }
    if((_screen==3 && index==6) || (_screen==4 && index==4)) { [self renderShop:7]; return; }
    if((_screen==5 && index==4) || (_screen==6 && index==4) || (_screen==7 && index==2)) { [self renderShop:2]; return; }
    if(_screen==2) {
        if(index==3) {
            if(!_status.shopOpen) { _detail.text=@"Shop opening is pending. Please wait."; _actionPendingUntil=NSDate.timeIntervalSinceReferenceDate+.35; return; }
            _feedback=nil; [self showSetup:YES];
        } else [self renderShop:index==0 ? 5 : index==1 ? 6 : 7];
        return;
    }
    if(_screen==7) { [self renderShop:index==0 ? 3 : 4]; return; }
    if(!_status.shopOpen) { _detail.text=@"Shop opening is pending. Please wait."; _actionPendingUntil=NSDate.timeIntervalSinceReferenceDate+.35; return; }
    Action action=Action::Ammo; unsigned amount=0;
    if(_screen==5) {
        if(index==2 && !_status.acrAvailable) {
            _detail.text=@"The converted MW3 ACR asset pack is not loaded.";
            _actionPendingUntil=NSDate.timeIntervalSinceReferenceDate+1; return;
        }
        if(index==2 && _status.rank<importedAcrRank) {
            _detail.text=@"MW3 ACR unlocks at rank 14.";
            _actionPendingUntil=NSDate.timeIntervalSinceReferenceDate+1; return;
        }
        action=index==0 ? Action::Ammo : index==1 ? Action::Rifle : index==2 ? Action::ACR : Action::Pack;
    }
    else if(_screen==6) {
        if(index==1 && (_status.reviveReady || _status.rank<2)) {
            _detail.text=_status.reviveReady ? @"Revive protection is already ready." : @"Revive protection unlocks at rank 2.";
            _actionPendingUntil=NSDate.timeIntervalSinceReferenceDate+1; return;
        }
        if(index==2 && (_status.quickRecovery || _status.rank<4)) {
            _detail.text=_status.quickRecovery ? @"Quick Recovery is already active." : @"Quick Recovery unlocks at rank 4.";
            _actionPendingUntil=NSDate.timeIntervalSinceReferenceDate+1; return;
        }
        if(index==3 && (_status.fastReload || _status.rank<6)) {
            _detail.text=_status.fastReload ? @"Sleight of Hand is already active." : @"Sleight of Hand unlocks at rank 6.";
            _actionPendingUntil=NSDate.timeIntervalSinceReferenceDate+1; return;
        }
        action=index==0 ? Action::Armor : index==1 ? Action::Revive : index==2 ? Action::Recovery : Action::FastReload;
    }
    else if(_screen==3) { action=index<3 ? Action::Deposit : Action::Withdraw; amount=index%3==0 ? 500 : index%3==1 ? 1000 : index<3 ? _status.match.credits : _status.bank; }
    else action=index==0 ? Action::God : index==1 ? Action::InfiniteAmmo : index==2 ? Action::Money : Action::NextWave;
    const bool accepted=queueAction(action,_status.epoch,amount);
    _detail.text=accepted ? @"Request pending..." : @"Request rejected. Try again.";
    _actionPendingUntil=NSDate.timeIntervalSinceReferenceDate+.35;
#endif
}
- (void)update {
#ifndef KISAK_MP
    using namespace cod4ios::survival;
    _status=readStatus();
    _hud.hidden=!_status.active; _shop.hidden=!_status.active;
    if(!_status.active) { _lastStatusMessage=nil; _hudNotice=nil; _hudNoticeUntil=0; if(self.modal && (!_choosingMode || (_screen==1 && _setupInMatch))) [self clearPanel]; return; }
    const auto &s=_status.match;
    NSString *message=[NSString stringWithUTF8String:_status.message] ?: @"";
    const NSTimeInterval now=NSDate.timeIntervalSinceReferenceDate;
    if(_noticeEpoch!=_status.epoch) {
        _noticeEpoch=_status.epoch; _lastStatusMessage=nil; _hudNotice=nil; _hudNoticeUntil=0;
    }
    if(_noticeSerial!=_status.noticeSerial || ![_lastStatusMessage isEqualToString:message]) {
        _noticeSerial=_status.noticeSerial;
        _lastStatusMessage=[message copy];
        if(message.length && s.phase!=Phase::GameOver) {
            _hudNotice=[[message componentsSeparatedByCharactersInSet:NSCharacterSet.newlineCharacterSet] componentsJoinedByString:@" "];
            _hudNoticeUntil=now+3;
        }
    }
    _hud.text=[NSString stringWithFormat:@"Survival - Wave %u - Enemies %u\nCash %u - Armor %u - Best %u%@\nRank %u (%u XP) - Bank %u - Streak %u",s.wave,s.alive+s.spawnRemaining,s.credits,_status.armor,_status.bestWave,
        s.phase==Phase::Intermission ? [NSString stringWithFormat:@" - Next %.0fs",ceil(s.secondsRemaining)] : @"",_status.rank,_status.xp,_status.bank,_status.killstreak];
    [_shop setTitle:s.phase==Phase::GameOver ? @"Retry" : @"Shop" forState:UIControlStateNormal];
    _shop.enabled=YES;
    if(self.modal && !_choosingMode) {
        if(_status.shopOpen) _pendingShop=NO;
        if(!_status.active || _status.epoch!=_shopRequestStatus.epoch || (s.phase!=Phase::Fighting && s.phase!=Phase::Intermission)) _pendingShop=NO;
        if(_pendingShop && NSDate.timeIntervalSinceReferenceDate>=_shopPendingUntil) {
            _pendingShop=NO; _detail.text=[NSString stringWithFormat:@"Shop did not open. Close and try again.\n%s",_status.message];
        }
        if(!_status.shopOpen && !_pendingShop) {
            if(!_status.active || _status.epoch!=_shopRequestStatus.epoch || (s.phase!=Phase::Fighting && s.phase!=Phase::Intermission)) [self clearPanel];
            else _detail.text=[NSString stringWithFormat:@"Shop is closed. Close this menu and try again.\n%s",_status.message];
        }
        else if(NSDate.timeIntervalSinceReferenceDate>=_actionPendingUntil) {
            NSString *response=_pendingShop ? @"Opening shop..." : [NSString stringWithUTF8String:_status.message];
            if(_screen==3) _detail.text=[NSString stringWithFormat:@"Wallet %u - Bank %u - Rank %u\n%@",s.credits,_status.bank,_status.rank,response];
            else if(_screen==6) _detail.text=[NSString stringWithFormat:@"Cash %u - Rank %u\nRevive protection prevents one lethal hit and restores health.\n%@",s.credits,_status.rank,response];
            else if(_screen==4) _detail.text=[NSString stringWithFormat:@"Wallet %u - God %@ - Infinite ammo %@\n%@",s.credits,_status.godMode ? @"ON" : @"OFF",_status.infiniteAmmo ? @"ON" : @"OFF",response];
            else _detail.text=[NSString stringWithFormat:@"Wallet %u - Bank %u - Rank %u (%u XP)\nHeld weapon Pack tier %u / 3 - Streak %u\nSupply rewards: 5 ammo / 8 armor / 12 cash 1000\n%@",s.credits,_status.bank,_status.rank,_status.xp,_status.packTier,_status.killstreak,response];
        }
        if(_screen==5 && _choices.count>=5) [_choices[2] setTitle:!_status.acrAvailable ? @"MW3 ACR - converted pack required" : _status.rank<importedAcrRank ? @"MW3 ACR - LOCKED (rank 14)" : @"MW3 ACR - 3000" forState:UIControlStateNormal];
        if(_screen==6 && _choices.count>=4) {
            NSString *revive=_status.reviveReady ? @"Revive protection - READY" : _status.rank<2 ? @"Revive protection - LOCKED (rank 2)" : @"Revive protection - 1500";
            NSString *recovery=_status.quickRecovery ? @"Quick Recovery - ACTIVE" : _status.rank<4 ? @"Quick Recovery - LOCKED (rank 4)" : @"Quick Recovery - 2000";
            [_choices[1] setTitle:revive forState:UIControlStateNormal];
            [_choices[2] setTitle:recovery forState:UIControlStateNormal];
            NSString *reload=_status.fastReload ? @"Sleight of Hand - ACTIVE" : _status.rank<6 ? @"Sleight of Hand - LOCKED (rank 6)" : @"Sleight of Hand - 2500";
            [_choices[3] setTitle:reload forState:UIControlStateNormal];
        }
        if(_screen==4 && _choices.count>=2) {
            [_choices[0] setTitle:[NSString stringWithFormat:@"Invulnerability: %@ (toggle)",_status.godMode ? @"ON" : @"OFF"] forState:UIControlStateNormal];
            [_choices[1] setTitle:[NSString stringWithFormat:@"Infinite ammo: %@ (toggle)",_status.infiniteAmmo ? @"ON" : @"OFF"] forState:UIControlStateNormal];
        }
    }
    if(s.phase==Phase::GameOver) _hud.text=[_hud.text stringByAppendingFormat:@"\n%@",[[message componentsSeparatedByCharactersInSet:NSCharacterSet.newlineCharacterSet] componentsJoinedByString:@" "]];
    else if(_hudNotice.length && now<_hudNoticeUntil) _hud.text=[_hud.text stringByAppendingFormat:@"\n%@",_hudNotice];
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
    if(self.modal && _choices.count) {
        if(edges.pressed&(1u<<Up)) _selected=(_selected+_choices.count-1)%_choices.count;
        if(edges.pressed&(1u<<Down)) _selected=(_selected+1)%_choices.count;
        [self highlight];
        if(edges.pressed&((1u<<Up)|(1u<<Down))) [self scrollSelected];
        if(edges.pressed&(1u<<South)) [self choice:_choices[_selected]];
        else if(edges.pressed&(1u<<East)) {
            if(_screen==1) [self choice:_choices.lastObject];
            else if(_choosingMode && _running) [self clearPanel];
            else if(!_choosingMode) [self choice:_choices.lastObject];
        }
    } else {
        if(edges.pressed&(1u<<Options)) [self showModes:YES];
        else if(edges.pressed&(1u<<Up)) [self openShop];
    }
}
@end
