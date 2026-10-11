#import <UIKit/UIKit.h>

@interface KISMapViewController : UIViewController
@end

@interface KISPreviewSceneDelegate : UIResponder <UIWindowSceneDelegate>
@property(nonatomic,strong) UIWindow *window;
@end
@implementation KISPreviewSceneDelegate
- (void)scene:(UIScene *)scene willConnectToSession:(UISceneSession *)session options:(UISceneConnectionOptions *)options {
    (void)session; (void)options;
    if(![scene isKindOfClass:UIWindowScene.class])return;
    self.window=[[UIWindow alloc] initWithWindowScene:(UIWindowScene *)scene];
    self.window.rootViewController=[KISMapViewController new];
    self.window.backgroundColor=UIColor.blackColor;
    [self.window makeKeyAndVisible];
}
@end

@interface KISAppDelegate : UIResponder <UIApplicationDelegate>
@end
@implementation KISAppDelegate
- (BOOL)application:(UIApplication *)application didFinishLaunchingWithOptions:(NSDictionary *)options {
    (void)application; (void)options;
    return YES;
}
- (UISceneConfiguration *)application:(UIApplication *)application
 configurationForConnectingSceneSession:(UISceneSession *)session
                              options:(UISceneConnectionOptions *)options {
    (void)application;(void)options;
    UISceneConfiguration *config=[[UISceneConfiguration alloc] initWithName:@"MW3 Preview" sessionRole:session.role];
    config.delegateClass=KISPreviewSceneDelegate.class;
    return config;
}
@end

#if defined(KISAK_PREVIEW_EMBEDDED)
extern "C" int KisakPreview_Main(int argc,char *argv[]) {
    @autoreleasepool { return UIApplicationMain(argc,argv,nil,NSStringFromClass(KISAppDelegate.class)); }
}
#else
int main(int argc,char *argv[]) {
    @autoreleasepool { return UIApplicationMain(argc,argv,nil,NSStringFromClass(KISAppDelegate.class)); }
}
#endif
