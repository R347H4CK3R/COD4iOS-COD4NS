#import "survival_ui.h"
#import <GameController/GameController.h>
#import <CommonCrypto/CommonDigest.h>
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
    NSMutableArray<NSString *> *content=[NSMutableArray arrayWithArray:@[@"maps/specops_survival.gsc", @"maps/specops_survival_v2.gsc", @"maps/specops_survival_v3.gsc", @"maps/specops_survival_v4.gsc"]];
    NSString *bundleRoot=[NSBundle.mainBundle.resourcePath stringByAppendingPathComponent:@"SurvivalContent"];
    NSString *manifestPath=[bundleRoot stringByAppendingPathComponent:@"MW3Assets.json"];
    // Assets are owned only after a recorded hash match. Journaled staging
    // protects a multi-file upgrade across failures and app termination.
    auto fail=[&](NSString *reason)->BOOL {
        if(error) *error=[NSError errorWithDomain:@"COD4iOSSurvival" code:4 userInfo:@{NSLocalizedDescriptionKey:reason}];
        return NO;
    };
    auto regular=[&](NSString *path)->BOOL {
        NSDictionary *attr=[files attributesOfItemAtPath:path error:NULL];
        return [attr[NSFileType] isEqualToString:NSFileTypeRegular];
    };
    auto hash=[&](NSString *path)->NSString * {
        if(!regular(path)) return nil;
        NSInputStream *stream=[NSInputStream inputStreamWithFileAtPath:path]; [stream open];
        CC_SHA256_CTX context; CC_SHA256_Init(&context); uint8_t chunk[65536]; NSInteger count;
        while((count=[stream read:chunk maxLength:sizeof(chunk)])>0) CC_SHA256_Update(&context,chunk,(CC_LONG)count);
        [stream close]; if(count<0) return nil;
        unsigned char digest[CC_SHA256_DIGEST_LENGTH]; CC_SHA256_Final(digest,&context);
        NSMutableString *value=[NSMutableString new]; for(unsigned char byte:digest) [value appendFormat:@"%02x",byte];
        return value;
    };
    auto assetName=[](id name)->BOOL {
        return [name isKindOfClass:NSString.class] && [name length] && [name isEqualToString:[name lastPathComponent]] &&
            ![name containsString:@"\\"] && [@[@"ff",@"iwd"] containsObject:[name pathExtension]];
    };
    auto hashesValid=[&](id value)->BOOL {
        if(![value isKindOfClass:NSDictionary.class]) return NO;
        for(id name in value) {
            id digest=value[name];
            if(!assetName(name) || ![digest isKindOfClass:NSString.class] || [digest length]!=64 ||
                [digest rangeOfCharacterFromSet:[[NSCharacterSet characterSetWithCharactersInString:@"0123456789abcdef"] invertedSet]].location!=NSNotFound) return NO;
        }
        return YES;
    };
    auto readJSON=[&](NSString *path)->id {
        if(!regular(path)) return nil;
        NSData *data=[NSData dataWithContentsOfFile:path];
        return data ? [NSJSONSerialization JSONObjectWithData:data options:0 error:NULL] : nil;
    };
    auto writeJSON=[&](id record,NSString *path)->BOOL {
        NSData *data=[NSJSONSerialization dataWithJSONObject:record options:0 error:error];
        return data && [data writeToFile:path options:NSDataWritingAtomic error:error];
    };
    NSString *managedPath=[root stringByAppendingPathComponent:@".mw3-managed.json"];
    NSString *journalPath=[root stringByAppendingPathComponent:@".mw3-update.json"];
    for(NSString *path in @[managedPath,journalPath]) {
        NSDictionary *attr=[files attributesOfItemAtPath:path error:NULL];
        if(attr && !regular(path)) return fail(@"MW3 ownership records cannot be redirected or replaced with directories.");
    }
    id managed=readJSON(managedPath);
    if(managed && (![managed isKindOfClass:NSDictionary.class] || ![managed[@"version"] isEqual:@1] || !hashesValid(managed[@"hashes"])))
        return fail(@"The managed MW3 asset record is invalid. Your files were preserved.");
    if([files fileExistsAtPath:managedPath] && !managed) return fail(@"The managed MW3 asset record could not be read.");
    id journal=readJSON(journalPath);
    if([files fileExistsAtPath:journalPath]) {
        if(![journal isKindOfClass:NSDictionary.class] || ![journal[@"version"] isEqual:@1] ||
            !hashesValid(journal[@"oldHashes"]) || !hashesValid(journal[@"newHashes"]) ||
            [journal[@"newHashes"] count]==0 || [journal[@"newHashes"] count]>32 || !journal[@"previousManaged"] ||
            ![journal[@"backup"] isKindOfClass:NSString.class] || ![journal[@"backup"] hasPrefix:@".mw3-backup-"] ||
            ![journal[@"backup"] isEqual:[journal[@"backup"] lastPathComponent]] || [journal[@"backup"] containsString:@"\\"])
            return fail(@"An invalid MW3 upgrade journal was preserved for recovery.");
        for(NSString *name in journal[@"oldHashes"]) if(!journal[@"newHashes"][name]) return fail(@"The MW3 upgrade journal contains an unrelated backup entry.");
        NSString *backup=[root stringByAppendingPathComponent:journal[@"backup"]];
        NSDictionary *backupAttr=[files attributesOfItemAtPath:backup error:NULL];
        if(![backupAttr[NSFileType] isEqualToString:NSFileTypeDirectory]) return fail(@"MW3 upgrade backup is unavailable or redirected.");
        // Validate every recovery target before touching any of them.
        for(NSString *name in journal[@"newHashes"]) {
            NSString *destination=[root stringByAppendingPathComponent:name];
            NSDictionary *attr=[files attributesOfItemAtPath:destination error:NULL];
            NSString *current=hash(destination), *old=journal[@"oldHashes"][name], *next=journal[@"newHashes"][name];
            if(attr && (!current || (![current isEqual:next] && ![current isEqual:old]))) return fail(@"An interrupted MW3 upgrade contains user changes. Files and backups were preserved.");
            if(old) {
                NSString *saved=[backup stringByAppendingPathComponent:name];
                if(![hash(saved) isEqual:old] && ![current isEqual:old]) return fail(@"An interrupted MW3 upgrade cannot be restored safely. Backups were preserved.");
            }
        }
        id previous=journal[@"previousManaged"];
        if(previous && previous!=NSNull.null && (![previous isKindOfClass:NSDictionary.class] || ![previous[@"version"] isEqual:@1] || !hashesValid(previous[@"hashes"]))) return fail(@"The previous MW3 ownership record is invalid.");
        if(managed && ![managed isEqual:previous] && ![managed[@"hashes"] isEqual:journal[@"newHashes"]]) return fail(@"The MW3 ownership record changed during an interrupted update. Records and backups were preserved.");
        for(NSString *name in journal[@"newHashes"]) {
            NSString *destination=[root stringByAppendingPathComponent:name], *old=journal[@"oldHashes"][name];
            if(old && [hash(destination) isEqual:old]) continue;
            NSString *restored=nil;
            if(old) {
                restored=[root stringByAppendingPathComponent:[@".mw3-restore-" stringByAppendingString:NSUUID.UUID.UUIDString]];
                if(![files copyItemAtPath:[backup stringByAppendingPathComponent:name] toPath:restored error:error]) return NO;
                if(![hash(restored) isEqual:old]) return fail(@"MW3 backup copy verification failed. Original files were preserved.");
            }
            if([files fileExistsAtPath:destination] && ![files removeItemAtPath:destination error:error]) return NO;
            if(old && ![files moveItemAtPath:restored toPath:destination error:error]) return NO;
        }
        if(previous && previous!=NSNull.null) { if(!writeJSON(previous,managedPath)) return NO; managed=previous; }
        else { if([files fileExistsAtPath:managedPath] && ![files removeItemAtPath:managedPath error:error]) return NO; managed=nil; }
        if(![files removeItemAtPath:journalPath error:error]) return NO;
    }
    NSDictionary *manifestAttr=[files attributesOfItemAtPath:manifestPath error:NULL];
    if(manifestAttr) {
        if(!regular(manifestPath)) return fail(@"The bundled MW3 asset manifest cannot be redirected.");
        id assetNames=readJSON(manifestPath);
        if(![assetNames isKindOfClass:NSArray.class] || [assetNames count]==0 || [assetNames count]>32) return fail(@"Invalid bundled MW3 asset manifest.");
        NSMutableDictionary *newHashes=[NSMutableDictionary new], *oldHashes=[NSMutableDictionary new];
        BOOL changed=NO;
        for(id name in assetNames) {
            if(!assetName(name) || newHashes[name]) return fail(@"Invalid or duplicate bundled MW3 asset name.");
            NSString *bundled=hash([bundleRoot stringByAppendingPathComponent:name]);
            if(!bundled) return fail(@"A bundled MW3 asset is missing or redirected.");
            newHashes[name]=bundled;
            NSString *destination=[root stringByAppendingPathComponent:name];
            NSDictionary *attr=[files attributesOfItemAtPath:destination error:NULL];
            NSString *current=hash(destination);
            if(attr && !current) return fail(@"An existing MW3 asset cannot be redirected or replaced with a directory.");
            if(current) oldHashes[name]=current;
            BOOL trustedLegacy=([name isEqual:@"mod.ff"] && [current isEqual:@"a1fd9764833341ab6f400bfa5dc4c2e9d3a8113b32a0223f477b987cc8fffc47"]) || ([name isEqual:@"z_mw3_acr.iwd"] && [current isEqual:@"e4624e12d0e0176b130c072ba49588859c70fbb7c2e76d2e2f36e9002d2eb27a"]);
            if(current && ![current isEqual:bundled] && ![current isEqual:managed[@"hashes"][name]] && !trustedLegacy)
                return fail(@"Bundled MW3 assets conflict with a user-edited or unmanaged file. Your files were preserved.");
            if(![current isEqual:bundled]) changed=YES;
        }
        if(![files createDirectoryAtPath:root withIntermediateDirectories:YES attributes:nil error:error]) return NO;
        NSDictionary *newManaged=@{@"version":@1,@"hashes":newHashes};
        if(changed) {
            NSString *token=NSUUID.UUID.UUIDString;
            NSString *stage=[root stringByAppendingPathComponent:[@".mw3-stage-" stringByAppendingString:token]];
            NSString *backupName=[@".mw3-backup-" stringByAppendingString:token];
            NSString *backup=[root stringByAppendingPathComponent:backupName];
            if(![files createDirectoryAtPath:stage withIntermediateDirectories:NO attributes:nil error:error] ||
               ![files createDirectoryAtPath:backup withIntermediateDirectories:NO attributes:nil error:error]) return NO;
            for(NSString *name in assetNames) {
                NSString *staged=[stage stringByAppendingPathComponent:name];
                if(![files copyItemAtPath:[bundleRoot stringByAppendingPathComponent:name] toPath:staged error:error] || ![hash(staged) isEqual:newHashes[name]]) return fail(@"MW3 asset staging failed. Existing files were preserved.");
            }
            NSDictionary *transaction=@{@"version":@1,@"backup":backupName,@"oldHashes":oldHashes,@"newHashes":newHashes,@"previousManaged":managed ?: NSNull.null};
            if(!writeJSON(transaction,journalPath)) return NO;
            for(NSString *name in assetNames) {
                NSString *destination=[root stringByAppendingPathComponent:name];
                // Recheck ownership after staging, before any overwrite.
                if(oldHashes[name] && ![hash(destination) isEqual:oldHashes[name]]) return fail(@"An MW3 asset changed during staging. Upgrade paused; files and backups were preserved.");
                if(oldHashes[name] && ![files moveItemAtPath:destination toPath:[backup stringByAppendingPathComponent:name] error:error]) return NO;
                if(![files moveItemAtPath:[stage stringByAppendingPathComponent:name] toPath:destination error:error]) return NO;
            }
            if(!writeJSON(newManaged,managedPath)) return NO;
            if(![files removeItemAtPath:journalPath error:error]) return NO;
            [files removeItemAtPath:stage error:NULL]; // Empty staging only; backups remain for the user.
        } else if(!writeJSON(newManaged,managedPath)) return NO;
    }
    for(NSString *relative in content) {
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
    unsigned _primary, _secondary, _equipment, _perk;
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
    UIStackView *cardRow=nil;
    const NSUInteger cardColumns=self.bounds.size.width>=700 ? 4 : 2;
    for(NSString *titleText in titles) {
        const NSUInteger index=_choices.count;
        const BOOL mapCard=_screen==8 && index<21;
        if(_screen==8 && (index==0 || index==4 || index==8 || index==12 || index==16)) {
            UILabel *tier=[UILabel new];
            tier.text=index==16 ? @"COD4 / ADDITIONAL OPERATIONS" : @[@"TIER 1   •   EASY",@"TIER 2   •   REGULAR",@"TIER 3   •   HARDENED",@"TIER 4   •   VETERAN"][index/4];
            tier.textColor=[UIColor colorWithRed:.72 green:.82 blue:.42 alpha:1];
            tier.font=[UIFont monospacedSystemFontOfSize:13 weight:UIFontWeightBold];
            [_panel addArrangedSubview:tier]; cardRow=nil;
        }
        if(mapCard && (!cardRow || index%cardColumns==0)) {
            cardRow=[UIStackView new]; cardRow.axis=UILayoutConstraintAxisHorizontal;
            cardRow.distribution=UIStackViewDistributionFillEqually; cardRow.spacing=8;
            [_panel addArrangedSubview:cardRow];
        }
        UIButton *button=[UIButton buttonWithType:UIButtonTypeSystem];
        [button setTitle:titleText forState:UIControlStateNormal]; [button setTitleColor:UIColor.whiteColor forState:UIControlStateNormal];
        button.tag=_choices.count; [button addTarget:self action:@selector(choice:) forControlEvents:UIControlEventTouchUpInside];
        [button.heightAnchor constraintEqualToConstant:mapCard ? 76 : 38].active=YES;
        if(mapCard) {
            button.titleLabel.numberOfLines=3;
            button.titleLabel.font=[UIFont systemFontOfSize:12 weight:UIFontWeightSemibold];
            button.layer.borderWidth=1;
            button.layer.cornerRadius=2;
            button.contentEdgeInsets=UIEdgeInsetsMake(6,6,6,6);
        }
        [_choices addObject:button];
        if(mapCard) [cardRow addArrangedSubview:button]; else [_panel addArrangedSubview:button];
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
    for(NSUInteger i=0;i<_choices.count;++i) {
        _choices[i].backgroundColor=i==_selected ? [UIColor colorWithRed:.24 green:.30 blue:.13 alpha:1] : [UIColor colorWithWhite:.12 alpha:1];
        _choices[i].layer.borderColor=(i==_selected ? [UIColor colorWithRed:.72 green:.82 blue:.42 alpha:1] : [UIColor colorWithWhite:.28 alpha:1]).CGColor;
    }
}

- (void)scrollSelected {
    if(_selected<_choices.count) [_scroll scrollRectToVisible:[_choices[_selected] convertRect:_choices[_selected].bounds toView:_scroll] animated:YES];
}

- (void)showModes:(BOOL)running {
#ifndef KISAK_MP
    if(self.modal && (!_choosingMode || ((_screen==1 || _screen>=8) && _setupInMatch))) cod4ios::survival::queueAction(cod4ios::survival::Action::CloseShop,_status.epoch);
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
    // Materialize migration before a fresh setup writes its first config.
    KisakApple_GetSurvivalLoadout(&_primary,&_secondary,&_equipment,&_perk);
    if(![NSUserDefaults.standardUserDefaults objectForKey:@"KisakSurvivalLoadout"]) KisakApple_SetSurvivalLoadout(_primary,_secondary,_equipment,_perk);
    _map=MIN(_map,4u); _difficulty=MIN(_difficulty,3u); _playerClass=MIN(_playerClass,2u);
    [self renderSetup];
}

- (void)renderSetup {
    [self panelTitle:@"SPECIAL OPS / SURVIVAL" detail:_feedback ?: @"Choose a map and persistent class. Original MW3 maps remain locked until native compatibility is complete. Starting reloads the match."
        choices:@[[NSString stringWithFormat:@"Map: %s%@",cod4ios::survival::mapName(_map),[self mapAvailable:_map] ? @"" : @" (unavailable)"],
        [NSString stringWithFormat:@"Difficulty: %s",cod4ios::survival::difficultyName(_difficulty)],@"CREATE-A-CLASS",@"START SURVIVAL",@"Back"]];
}

- (void)renderMapBrowser {
    _screen=8; _choosingMode=YES;
    NSArray *maps=@[@"TIER 1 / EASY â€” Resistance",@"TIER 1 / EASY â€” Village",@"TIER 1 / EASY â€” Interchange",@"TIER 1 / EASY â€” Underground",
        @"TIER 2 / REGULAR â€” Dome",@"TIER 2 / REGULAR â€” Mission",@"TIER 2 / REGULAR â€” Seatown",@"TIER 2 / REGULAR â€” Bootleg",
        @"TIER 3 / HARDENED â€” Carbon",@"TIER 3 / HARDENED â€” Hardhat",@"TIER 3 / HARDENED â€” Fallen",@"TIER 3 / HARDENED â€” Outpost",
        @"TIER 4 / VETERAN â€” Lockdown",@"TIER 4 / VETERAN â€” Arkaden",@"TIER 4 / VETERAN â€” Downturn",@"TIER 4 / VETERAN â€” Bakaara"];
    NSMutableArray *choices=[NSMutableArray new];
    for(NSString *name in maps) [choices addObject:[name stringByAppendingString:@"\nLOCKED â€” native map compatibility required"]];
    for(unsigned i=0;i<5;++i) [choices addObject:[NSString stringWithFormat:@"COD4 EXTENSION â€” %s%@%@",cod4ios::survival::mapName(i),i==_map ? @" â€¢ SELECTED" : @"",[self mapAvailable:i] ? @"" : @" â€¢ unavailable"]];
    [choices addObject:@"Back"];
    [self panelTitle:@"SURVIVAL / SELECT MAP" detail:_feedback ?: @"Original MW3 roster above. Playable COD4 extensions below use their own maps; they do not replace Dome or another MW3 map." choices:choices];
    for(NSUInteger i=0;i<16;++i) { _choices[i].titleLabel.numberOfLines=2; _choices[i].titleLabel.font=[UIFont systemFontOfSize:12 weight:UIFontWeightSemibold]; }
}

- (NSDictionary *)bundledMW3Catalog {
    NSString *path=[NSBundle.mainBundle.resourcePath stringByAppendingPathComponent:@"SurvivalContent/MW3Catalog.json"];
    NSData *data=[NSData dataWithContentsOfFile:path];
    id catalog=data ? [NSJSONSerialization JSONObjectWithData:data options:0 error:NULL] : nil;
    if(![catalog isKindOfClass:NSDictionary.class] || ![catalog[@"version"] isEqual:@1] || ![catalog[@"weapons"] isKindOfClass:NSArray.class]) return nil;
    return catalog;
}

- (unsigned)classRank {
#ifndef KISAK_MP
    if(_status.active) return _status.rank;
#endif
    if(!KisakApple_HasSurvivalMW3XP()) return cod4ios::survival::rankForXP(KisakApple_GetSurvivalXP());
    id thresholds=[self bundledMW3Catalog][@"rankThresholds"];
    if(![thresholds isKindOfClass:NSArray.class] || [thresholds count]!=50) return 1;
    const unsigned xp=KisakApple_GetSurvivalMW3XP(); unsigned rank=1,previous=0;
    for(NSUInteger i=0;i<[thresholds count];++i) {
        id value=thresholds[i];
        if(![value isKindOfClass:NSNumber.class] || [value doubleValue]<0 || [value doubleValue]>1000000000 || [value doubleValue]!=[value unsignedIntValue] || (i==0 ? [value unsignedIntValue]!=0 : [value unsignedIntValue]<=previous)) return 1;
        previous=[value unsignedIntValue]; if(xp>=previous) rank=(unsigned)i+1;
    }
    return rank;
}

- (BOOL)loadoutWeaponAvailable:(unsigned)value secondary:(BOOL)secondary {
#ifndef KISAK_MP
    if(_status.active) {
        if(secondary) return value==1 || _status.uspAvailable;
        return value==0 || value>=3 || (value==1 ? _status.mp7Available : _status.acrAvailable);
    }
#endif
    NSArray *weapons=[self bundledMW3Catalog][@"weapons"];
    if(secondary) return value==1 || [weapons containsObject:@"mw3_usp45"];
    return value==0 || value>=3 || [weapons containsObject:value==1 ? @"mw3_mp7" : @"mw3_acr"];
}

- (BOOL)loadoutRankAvailable:(unsigned)value {
    return value==1 ? [self classRank]>=13 : value==2 ? [self classRank]>=14 : YES;
}

- (BOOL)loadoutPerkAvailable:(unsigned)value {
    return value==1 ? [self classRank]>=4 : value==2 ? [self classRank]>=6 : YES;
}

- (void)renderClass {
    _screen=9; _choosingMode=YES;
    NSArray *primaries=@[@"None",@"MW3 MP7",@"MW3 ACR",@"COD4 M4",@"COD4 AK-47"];
    NSArray *secondaries=@[@"MW3 USP .45",@"None"];
    NSArray *equipment=@[@"Last Stand",@"Armor",@"Frag + Flash"];
    NSArray *perks=@[@"None",@"Quick Recovery",@"Sleight of Hand"];
    [self panelTitle:@"SURVIVAL / CREATE-A-CLASS" detail:_feedback ?: @"Saved between matches. Applies when you start or retry. MP7 unlocks at rank 13; ACR at rank 14. Converted weapons require their loaded asset pack."
        choices:@[[NSString stringWithFormat:@"Primary: %@%@",primaries[_primary],[self loadoutWeaponAvailable:_primary secondary:NO] ? @"" : @" â€¢ unavailable"],
        [NSString stringWithFormat:@"Secondary: %@%@",secondaries[_secondary],[self loadoutWeaponAvailable:_secondary secondary:YES] ? @"" : @" â€¢ unavailable"],
        [@"Equipment: " stringByAppendingString:equipment[_equipment]],[@"Perk: " stringByAppendingString:perks[_perk]],@"SAVE CLASS",@"Back"]];
}

- (void)renderClassChoices:(NSInteger)screen {
    _screen=screen; _choosingMode=YES;
    NSArray *names=screen==10 ? @[@"None",@"MW3 MP7",@"MW3 ACR",@"COD4 M4",@"COD4 AK-47"] : screen==11 ? @[@"MW3 USP .45",@"None"] : screen==12 ? @[@"Last Stand",@"Armor",@"Frag + Flash"] : @[@"None",@"Quick Recovery",@"Sleight of Hand"];
    NSMutableArray *choices=[NSMutableArray new];
    for(NSUInteger i=0;i<names.count;++i) {
        NSString *lock=screen<=11 && ![self loadoutWeaponAvailable:(unsigned)i secondary:screen==11] ? @" â€¢ LOCKED (pack not loaded)" : screen==10 && ![self loadoutRankAvailable:(unsigned)i] ? (i==1 ? @" â€¢ LOCKED (rank 13)" : @" â€¢ LOCKED (rank 14)") : screen==13 && ![self loadoutPerkAvailable:(unsigned)i] ? (i==1 ? @" â€¢ LOCKED (rank 4)" : @" â€¢ LOCKED (rank 6)") : @"";
        [choices addObject:[names[i] stringByAppendingString:lock]];
    }
    [choices addObject:@"Back"];
    [self panelTitle:screen==10 ? @"CLASS / PRIMARY" : screen==11 ? @"CLASS / SECONDARY" : screen==12 ? @"CLASS / EQUIPMENT" : @"CLASS / PERK" detail:_feedback ?: @"Choose a starting loadout item. Availability and unlocks are checked again when the match starts." choices:choices];
}

- (void)renderShop:(NSInteger)screen {
    const BOOL pending=_pendingShop;
    _screen=screen; _choosingMode=NO;
    if(screen==3) [self panelTitle:@"Survival Bank" detail:@"Transfers use match credits. Bank persists between matches." choices:@[@"Deposit 500",@"Deposit 1000",@"Deposit all",@"Withdraw 500",@"Withdraw 1000",@"Withdraw all",@"Back"]];
    else if(screen==4) [self panelTitle:@"Survival Cheats" detail:@"Cheats apply only to this Survival match." choices:@[@"Toggle invulnerability",@"Toggle infinite ammo",@"Add 10000 credits",@"Skip current wave",@"Back"]];
    else if(screen==5) [self panelTitle:@"Weapon Armory" detail:@"MW3 ACR requires its converted asset pack. Original game files stay intact." choices:@[@"Refill ammo - 250",@"COD4 AK-47 - 750",@"MW3 USP .45 - 250",@"MW3 MP7 - 2000 (rank 13)",@"MW3 ACR - 3000 (rank 14)",@"Pack-a-Punch - 2000 / 4000 / 6000",@"Back"]];
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
    if(index>=_choices.count) return;
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
    if(_screen==8) {
        if(index==21) { _screen=1; _feedback=nil; [self renderSetup]; return; }
        if(index<16) { _feedback=@"This original MW3 map is locked. Its geometry, navigation and native runtime are not compatible yet."; [self renderMapBrowser]; return; }
        const unsigned map=(unsigned)index-16;
        if(![self mapAvailable:map]) { _feedback=@"This COD4 extension's original map files are unavailable."; [self renderMapBrowser]; return; }
        _map=map; _screen=1; _feedback=nil; [self renderSetup]; return;
    }
    if(_screen==9) {
        if(index==5) { _screen=1; _feedback=nil; [self renderSetup]; return; }
        if(index<4) { _feedback=nil; [self renderClassChoices:10+index]; return; }
        if((_primary==0 && _secondary==1) || ![self loadoutWeaponAvailable:_primary secondary:NO] || ![self loadoutWeaponAvailable:_secondary secondary:YES] || ![self loadoutRankAvailable:_primary] || ![self loadoutPerkAvailable:_perk]) {
            _feedback=@"Class cannot be saved: a selected weapon is unavailable or rank locked. Choose an available weapon."; [self renderClass]; return;
        }
        if(!KisakApple_SetSurvivalLoadout(_primary,_secondary,_equipment,_perk)) { _feedback=@"Class rejected. Your previous class is preserved."; [self renderClass]; return; }
        _screen=1; _feedback=@"Class saved. Start Survival to apply it."; [self renderSetup]; return;
    }
    if(_screen>=10 && _screen<=13) {
        const NSInteger screen=_screen;
        if(index==(NSInteger)_choices.count-1) { _feedback=nil; [self renderClass]; return; }
        if((screen<=11 && (![self loadoutWeaponAvailable:(unsigned)index secondary:screen==11] || (screen==10 && ![self loadoutRankAvailable:(unsigned)index]))) || (screen==13 && ![self loadoutPerkAvailable:(unsigned)index])) {
            _feedback=@"This item is unavailable or rank locked."; [self renderClassChoices:screen]; return;
        }
        if(screen==10) _primary=(unsigned)index; else if(screen==11) _secondary=(unsigned)index; else if(screen==12) _equipment=(unsigned)index; else _perk=(unsigned)index;
        _feedback=nil; [self renderClass]; return;
    }
    if(_screen==1) {
        if(index==0) { _feedback=nil; [self renderMapBrowser]; return; }
        else if(index==1) _difficulty=(_difficulty+1)%4;
        else if(index==2) { KisakApple_GetSurvivalLoadout(&_primary,&_secondary,&_equipment,&_perk); _feedback=nil; [self renderClass]; return; }
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
    if((_screen==5 && index==6) || (_screen==6 && index==4) || (_screen==7 && index==2)) { [self renderShop:2]; return; }
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
        const BOOL imported=index>=2 && index<=4;
        const BOOL available=index==2 ? _status.uspAvailable : index==3 ? _status.mp7Available : _status.acrAvailable;
        if(imported && !available) {
            _detail.text=@"This converted MW3 weapon is not loaded.";
            _actionPendingUntil=NSDate.timeIntervalSinceReferenceDate+1; return;
        }
        const unsigned minimum=index==3 ? 13 : index==4 ? 14 : 1;
        if(imported && _status.rank<minimum) {
            _detail.text=[NSString stringWithFormat:@"Weapon unlocks at rank %u.",minimum];
            _actionPendingUntil=NSDate.timeIntervalSinceReferenceDate+1; return;
        }
        action=index==0 ? Action::Ammo : index==1 ? Action::Rifle : index==2 ? Action::USP45 : index==3 ? Action::MP7 : index==4 ? Action::ACR : Action::Pack;
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
    if(!_status.active) { _lastStatusMessage=nil; _hudNotice=nil; _hudNoticeUntil=0; if(self.modal && (!_choosingMode || ((_screen==1 || _screen>=8) && _setupInMatch))) [self clearPanel]; return; }
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
            if(_screen==1 || _screen>=8) [self choice:_choices.lastObject];
            else if(_choosingMode && _running) [self clearPanel];
            else if(!_choosingMode) [self choice:_choices.lastObject];
        }
    } else {
        if(edges.pressed&(1u<<Options)) [self showModes:YES];
        else if(edges.pressed&(1u<<Up)) [self openShop];
    }
}
@end
