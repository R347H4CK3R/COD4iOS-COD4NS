// FPS Compact appearance and positions adapted from the user's MC360-Recomp
// XeniOS/ReXGlue overlay. Copyright 2026 Ben Vanik and MC360-Recomp contributors.
// BSD-3-Clause; see TouchControls.LICENSE.
#import "touch_controls.h"
#import <QuartzCore/QuartzCore.h>
#include "../input/TouchControls.h"

extern void KisakApple_ModCommand(const char *command);
extern "C" void KisakApple_RequestNativeTestBot();
extern "C" void KisakApple_RequestNativeBotRemoval(int count);
extern "C" void KisakApple_SetNativeBotSkill(int skill);

@implementation KISTouchControls {
    kisak::touch::State _input;
    NSMutableArray<UIView *> *_shells;
    UIView *_knob;
    BOOL _available;
    int _context;
    UIButton *_privateCheatsButton;
    BOOL _privateCheats;
    UIButton *_botMinusButton;
    UIButton *_botCountButton;
    UIButton *_botPlusButton;
    UIButton *_botDifficultyButton;
    int _botDifficulty;
    int _botCount;
}
- (instancetype)initWithFrame:(CGRect)frame {
    if (!(self=[super initWithFrame:frame])) return nil;
    self.multipleTouchEnabled=YES;
    self.backgroundColor=UIColor.clearColor;
    self.autoresizingMask=UIViewAutoresizingFlexibleWidth|UIViewAutoresizingFlexibleHeight;
    _shells=[NSMutableArray array];
    for (const auto &control:kisak::touch::controls) {
        UIView *shell=[UIView new];
        shell.userInteractionEnabled=NO;
        shell.layer.borderWidth=1.5;
        shell.layer.borderColor=[UIColor colorWithWhite:1 alpha:control.button<0?.38:.32].CGColor;
        shell.backgroundColor=[UIColor colorWithWhite:1 alpha:control.button<0?.10:.08];
        UILabel *label=[UILabel new];
        label.text=[NSString stringWithUTF8String:control.label];
        label.font=[UIFont systemFontOfSize:12 weight:UIFontWeightSemibold];
        label.textColor=[UIColor colorWithWhite:1 alpha:.92];
        label.textAlignment=NSTextAlignmentCenter;
        label.adjustsFontSizeToFitWidth=YES;
        label.minimumScaleFactor=.6;
        label.tag=100;
        [shell addSubview:label];
        if (control.button<0) {
            NSArray *symbols=@[@"chevron.up",@"chevron.down",@"chevron.left",@"chevron.right"];
            for (NSUInteger n=0;n<4;++n) {
                UIImageView *arrow=[[UIImageView alloc] initWithImage:[UIImage systemImageNamed:symbols[n]]];
                arrow.tintColor=UIColor.whiteColor;arrow.alpha=.85;arrow.tag=101+n;
                arrow.contentMode=UIViewContentModeCenter;[shell addSubview:arrow];
            }
        }
        [_shells addObject:shell];[self addSubview:shell];
    }
    _privateCheatsButton=[UIButton buttonWithType:UIButtonTypeSystem];
    _privateCheatsButton.backgroundColor=[UIColor colorWithWhite:0.08 alpha:0.84];
    _privateCheatsButton.layer.cornerRadius=9;
    _privateCheatsButton.layer.borderColor=[UIColor colorWithWhite:1 alpha:0.42].CGColor;
    _privateCheatsButton.layer.borderWidth=1;
    _privateCheatsButton.titleLabel.font=[UIFont boldSystemFontOfSize:13];
    [_privateCheatsButton setTitle:@"Private Cheats: OFF" forState:UIControlStateNormal];
    [_privateCheatsButton setTitleColor:UIColor.whiteColor forState:UIControlStateNormal];
    [_privateCheatsButton addTarget:self action:@selector(togglePrivateCheats:) forControlEvents:UIControlEventTouchUpInside];
    [self addSubview:_privateCheatsButton];
    _botCount=0;
    _botDifficulty=3;
    KisakApple_SetNativeBotSkill(_botDifficulty);
    _botMinusButton=[UIButton buttonWithType:UIButtonTypeSystem];
    _botCountButton=[UIButton buttonWithType:UIButtonTypeSystem];
    _botPlusButton=[UIButton buttonWithType:UIButtonTypeSystem];
    NSArray<UIButton *> *botButtons=@[_botMinusButton,_botCountButton,_botPlusButton];
    NSArray<NSString *> *botLabels=@[@"Bots −",@"Bots: 0",@"Bots +"];
    for (NSUInteger i=0;i<botButtons.count;i++) {
        UIButton *button=botButtons[i];
        button.backgroundColor=[UIColor colorWithWhite:0.08 alpha:0.84];
        button.layer.cornerRadius=8;
        button.layer.borderColor=[UIColor colorWithWhite:1 alpha:0.42].CGColor;
        button.layer.borderWidth=1;
        button.titleLabel.font=[UIFont boldSystemFontOfSize:12];
        [button setTitle:botLabels[i] forState:UIControlStateNormal];
        [button setTitleColor:UIColor.whiteColor forState:UIControlStateNormal];
        [self addSubview:button];
    }
    [_botMinusButton addTarget:self action:@selector(decreaseBotCount:) forControlEvents:UIControlEventTouchUpInside];
    [_botPlusButton addTarget:self action:@selector(increaseBotCount:) forControlEvents:UIControlEventTouchUpInside];
    [_botCountButton addTarget:self action:@selector(resetBotCount:) forControlEvents:UIControlEventTouchUpInside];
    _botDifficultyButton=[UIButton buttonWithType:UIButtonTypeSystem];
    _botDifficultyButton.backgroundColor=[UIColor colorWithWhite:0.08 alpha:0.84];
    _botDifficultyButton.layer.cornerRadius=8;
    _botDifficultyButton.titleLabel.font=[UIFont boldSystemFontOfSize:12];
    [_botDifficultyButton setTitle:@"Difficulty: Normal" forState:UIControlStateNormal];
    [_botDifficultyButton setTitleColor:UIColor.whiteColor forState:UIControlStateNormal];
    [_botDifficultyButton addTarget:self action:@selector(cycleBotDifficulty:) forControlEvents:UIControlEventTouchUpInside];
    [self addSubview:_botDifficultyButton];
    _knob=[UIView new];_knob.userInteractionEnabled=NO;
    _knob.backgroundColor=[UIColor colorWithWhite:1 alpha:.18];
    _knob.layer.borderWidth=1.5;
    _knob.layer.borderColor=[UIColor colorWithWhite:1 alpha:.72].CGColor;
    [self addSubview:_knob];self.hidden=YES;
    return self;
}
- (void)layoutSubviews {
    [super layoutSubviews];
    const UIEdgeInsets insets=self.safeAreaInsets;
    CGRect safe=UIEdgeInsetsInsetRect(self.bounds,insets);
    safe=CGRectInset(safe,4,4);
    _input.SetBounds({float(safe.origin.x),float(safe.origin.y),float(safe.size.width),float(safe.size.height)});
    for (size_t i=0;i<kisak::touch::count;++i) {
        const auto frame=_input.Frame(i);UIView *shell=_shells[i];
        shell.frame=CGRectMake(frame.x,frame.y,frame.w,frame.h);
        shell.layer.cornerRadius=frame.w*.5f;
        [shell viewWithTag:100].frame=CGRectInset(shell.bounds,5,5);
        if (i==0) {
            const CGFloat c=frame.w*.5f,r=frame.w*.41f,size=MAX(frame.w*.15f,18);
            const CGPoint centers[]={{c,c-r},{c,c+r},{c-r,c},{c+r,c}};
            for (NSUInteger n=0;n<4;++n)
                [shell viewWithTag:101+n].frame=CGRectMake(centers[n].x-size/2,centers[n].y-size/2,size,size);
        }
    }
    _privateCheatsButton.frame=CGRectMake(CGRectGetMaxX(safe)-188, CGRectGetMinY(safe)+4, 184, 37);
    const CGFloat botY=CGRectGetMinY(safe)+45;
    const CGFloat right=CGRectGetMaxX(safe)-4;
    _botMinusButton.frame=CGRectMake(right-184,botY,56,36);
    _botCountButton.frame=CGRectMake(right-124,botY,64,36);
    _botPlusButton.frame=CGRectMake(right-56,botY,56,36);
    _botDifficultyButton.frame=CGRectMake(right-184,botY+40,184,34);
    [self refreshVisuals];
    if(self.inputChanged)self.inputChanged();
}
- (void)setAvailable:(BOOL)available context:(int)context {
    if(_available==available && _context==context)return;
    _available=available;_context=context;
    _input.SetContext(available && context!=2,context==1);
    self.hidden=!available || context==2;
    _privateCheatsButton.hidden=!available || context!=0;
    _botMinusButton.hidden=!available || context!=0;
    _botCountButton.hidden=!available || context!=0;
    _botPlusButton.hidden=!available || (context!=0 && context!=1);
    _botDifficultyButton.hidden=!available || context!=0;
    [self refreshVisuals];
}
- (void)togglePrivateCheats:(id)sender {
    (void)sender;
    // This UI preference is only consulted by UI_StartServer for a local
    // listen server; joining a remote host never applies it.
    _privateCheats=!_privateCheats;
    KisakApple_ModCommand(_privateCheats ? "set ui_privateCheats 1" : "set ui_privateCheats 0");
    [_privateCheatsButton setTitle:(_privateCheats ? @"Private Cheats: ON" : @"Private Cheats: OFF")
                        forState:UIControlStateNormal];
}
- (void)cycleBotDifficulty:(id)sender {
    (void)sender;
    _botDifficulty = _botDifficulty % 5 + 1;
    KisakApple_SetNativeBotSkill(_botDifficulty);
    NSArray<NSString *> *labels=@[@"", @"Recruit", @"Easy", @"Normal", @"Hard", @"Veteran"];
    [_botDifficultyButton setTitle:[NSString stringWithFormat:@"Difficulty: %@",labels[_botDifficulty]]
                         forState:UIControlStateNormal];
}
- (void)applyBotCount {
    // Keep zero as the default. The server-side PeZBOT scripts read these
    // dvars when available; this UI does not itself create bot entities.
    char command[64];
    snprintf(command,sizeof(command),"set svr_pezbots %d",_botCount);
    KisakApple_ModCommand(command);
    KisakApple_ModCommand("set svr_pezbots_allies 0");
    KisakApple_ModCommand("set svr_pezbots_axis 0");
    [_botCountButton setTitle:[NSString stringWithFormat:@"Bots: %d",_botCount] forState:UIControlStateNormal];
}
- (void)decreaseBotCount:(id)sender {
    (void)sender;
    if (_botCount > 0) KisakApple_RequestNativeBotRemoval(1);
    _botCount=MAX(0,_botCount-1);
    [self applyBotCount];
}
- (void)increaseBotCount:(id)sender {
    (void)sender;
    // Context is not a reliable indicator of an active listen server on all
    // iOS menu/scoreboard overlays. Try the guarded native server command
    // whenever + is tapped; its handler rejects calls before map startup.
    KisakApple_RequestNativeTestBot();
    _botCount=MIN(18,_botCount+1);
    [self applyBotCount];
}
- (void)resetBotCount:(id)sender {
    (void)sender;
    KisakApple_RequestNativeBotRemoval(64);
    _botCount=0;
    [self applyBotCount];
}
- (void)refreshVisuals {
    const double now=CACurrentMediaTime();
    for(size_t i=0;i<kisak::touch::count;++i) {
        UIView *shell=_shells[i];const auto &control=kisak::touch::controls[i];
        shell.hidden=_context!=1 && !kisak::touch::MenuControl(i);
        const BOOL pressed=control.button>=0 && _input.Pressed(control.button,now);
        shell.backgroundColor=[UIColor colorWithWhite:1 alpha:pressed?.23:(i==0?.10:.08)];
        shell.layer.borderColor=[UIColor colorWithWhite:1 alpha:pressed?.78:(i==0?.38:.32)].CGColor;
    }
    const auto frame=_input.Frame(0);const auto center=frame.Center();const auto move=_input.MoveKnob();
    const CGFloat side=frame.w*.30f;
    _knob.frame=CGRectMake(center.x+move.x-side*.5f,center.y+move.y-side*.5f,side,side);
    _knob.layer.cornerRadius=side*.5f;
}
- (kisak::controller::Snapshot)sample {
    [self refreshVisuals];
    return _input.Sample(CACurrentMediaTime());
}
- (BOOL)pointInside:(CGPoint)point withEvent:(UIEvent *)event {
    (void)event;
    if (self.hidden) return NO;
    if (!_botPlusButton.hidden && CGRectContainsPoint(_botPlusButton.frame,point)) return YES;
    if (!_botMinusButton.hidden && CGRectContainsPoint(_botMinusButton.frame,point)) return YES;
    if (!_botCountButton.hidden && CGRectContainsPoint(_botCountButton.frame,point)) return YES;
    if (!_privateCheatsButton.hidden && CGRectContainsPoint(_privateCheatsButton.frame,point)) return YES;
    return _input.Hit({float(point.x),float(point.y)})!=-2;
}
- (void)touchesBegan:(NSSet<UITouch *> *)touches withEvent:(UIEvent *)event {
    (void)event;
    for(UITouch *touch in touches) {
        const CGPoint p=[touch locationInView:self];
        _input.Down(reinterpret_cast<uintptr_t>((__bridge void*)touch),{float(p.x),float(p.y)},CACurrentMediaTime());
    }
    [self refreshVisuals];if(self.inputChanged)self.inputChanged();
}
- (void)touchesMoved:(NSSet<UITouch *> *)touches withEvent:(UIEvent *)event {
    (void)event;
    for(UITouch *touch in touches) {
        const CGPoint p=[touch locationInView:self];
        _input.Move(reinterpret_cast<uintptr_t>((__bridge void*)touch),{float(p.x),float(p.y)});
    }
    if(self.inputChanged)self.inputChanged();
}
- (void)touchesEnded:(NSSet<UITouch *> *)touches withEvent:(UIEvent *)event {
    (void)event;
    for(UITouch *touch in touches)_input.Up(reinterpret_cast<uintptr_t>((__bridge void*)touch));
    [self refreshVisuals];if(self.inputChanged)self.inputChanged();
}
- (void)touchesCancelled:(NSSet<UITouch *> *)touches withEvent:(UIEvent *)event {
    (void)event;
    for(UITouch *touch in touches)
        _input.CancelTouch(reinterpret_cast<uintptr_t>((__bridge void*)touch));
    [self refreshVisuals];if(self.inputChanged)self.inputChanged();
}
- (void)cancelInputs { _input.Cancel();[self refreshVisuals]; }
@end
