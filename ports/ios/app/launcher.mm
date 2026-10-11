// One app, two engines.
//
// KISAK_MP is not a feature flag: it changes struct layouts (entityState_s, cpose_t, the critical
// section, MAX_CONFIGSTRINGS), so the singleplayer and multiplayer engines cannot be linked into
// one binary without an ODR violation. Retail solves this with two executables and the menu
// launches the other one; iOS does not let a sandboxed app spawn a second executable.
//
// So each engine is a dylib exporting only KisakEngine_AppMain. iOS two-level namespacing keeps
// each image's symbols and globals private, and only one is ever loaded. The mode is remembered,
// the in-game menu sets it, and the change takes effect the next time the app is opened - an
// engine that has already brought up Metal, audio and its hunk allocator cannot be swapped out
// underneath itself.
#import <Foundation/Foundation.h>
#include <dlfcn.h>
#include <stdio.h>
#include <signal.h>
#include <unistd.h>
#include <fcntl.h>
#include <string.h>

extern "C" int KisakPreview_Main(int argc, char *argv[]);
extern "C" NSString *const KisakEngineModeKey = @"KisakEngineMode";

// Diagnostic files stay in the user-accessible app Documents directory.
// Crash events are best-effort and do not replace Apple's system crash reports.
static int kisakDiagnosticFD = -1;
static NSString *kisakMarkerPath = nil;
static void KisakDiagnosticEvent(NSString *event) {
    if (kisakDiagnosticFD < 0) return;
    NSString *line = [NSString stringWithFormat:@"%@ %@\n", [NSDate date], event];
    NSData *bytes = [line dataUsingEncoding:NSUTF8StringEncoding];
    if (bytes) (void)write(kisakDiagnosticFD, bytes.bytes, bytes.length);
}
static void KisakUncaughtException(NSException *exception) {
    KisakDiagnosticEvent([NSString stringWithFormat:@"UNCAUGHT_EXCEPTION %@ %@ stack=%@",
        exception.name, exception.reason, exception.callStackSymbols]);
}
static void KisakFatalSignal(int signum) {
    const char *message = "FATAL_SIGNAL: check iOS system crash report for stack trace\n";
    if (kisakDiagnosticFD >= 0) (void)write(kisakDiagnosticFD, message, strlen(message));
    signal(signum, SIG_DFL);
    raise(signum);
}
static void KisakStartDiagnostics(NSString *mode) {
    NSString *docs = NSSearchPathForDirectoriesInDomains(NSDocumentDirectory, NSUserDomainMask, YES).firstObject;
    if (!docs) return;
    kisakMarkerPath = [docs stringByAppendingPathComponent:@"cod4ios_session_active.marker"];
    NSString *log = [docs stringByAppendingPathComponent:@"cod4ios_diagnostics.log"];
    kisakDiagnosticFD = open(log.fileSystemRepresentation, O_WRONLY|O_CREAT|O_APPEND, 0600);
    if ([[NSFileManager defaultManager] fileExistsAtPath:kisakMarkerPath])
        KisakDiagnosticEvent(@"PREVIOUS_SESSION_UNCLEAN (possible crash, force quit or termination)");
    [@"active" writeToFile:kisakMarkerPath atomically:YES encoding:NSUTF8StringEncoding error:nil];
    KisakDiagnosticEvent([NSString stringWithFormat:@"SESSION_START mode=%@ app=%@",mode,
        NSBundle.mainBundle.infoDictionary[@"CFBundleShortVersionString"] ?: @"unknown"]);
    NSSetUncaughtExceptionHandler(&KisakUncaughtException);
    signal(SIGABRT, KisakFatalSignal);
    signal(SIGSEGV, KisakFatalSignal);
    signal(SIGBUS, KisakFatalSignal);
}
static void KisakStopDiagnostics(int result) {
    KisakDiagnosticEvent([NSString stringWithFormat:@"ENGINE_EXIT code=%d",result]);
    if (kisakMarkerPath)
        [[NSFileManager defaultManager] removeItemAtPath:kisakMarkerPath error:nil];
    if (kisakDiagnosticFD >= 0) { close(kisakDiagnosticFD); kisakDiagnosticFD=-1; }
}


int main(int argc, char *argv[])
{
    @autoreleasepool {
        NSString *mode = [NSUserDefaults.standardUserDefaults stringForKey:KisakEngineModeKey];
        // First launch with a copied MW3 bundle: open the viewer instead of COD4 MP.
        // An explicitly saved mode always wins.
        if(!mode.length) {
            NSFileManager *fm=[NSFileManager defaultManager];
            for(NSNumber *location in @[@(NSApplicationSupportDirectory),@(NSDocumentDirectory)]) {
                NSURL *base=[fm URLForDirectory:(NSSearchPathDirectory)location.unsignedIntegerValue
                                      inDomain:NSUserDomainMask appropriateForURL:nil create:YES error:nil];
                for(NSURL *folder in @[base,[base URLByAppendingPathComponent:@"ImportedMW3" isDirectory:YES]]) {
                    NSArray<NSURL *> *entries=[fm contentsOfDirectoryAtURL:folder includingPropertiesForKeys:nil options:0 error:nil];
                    for(NSURL *entry in entries) {
                        if([entry.pathExtension.lowercaseString isEqualToString:@"mw3map"]) {
                            mode=@"mw3_preview";break;
                        }
                    }
                    if(mode.length)break;
                }
                if(mode.length)break;
            }
        }
        if ([mode isEqualToString:@"mw3_preview"]) {
            KisakStartDiagnostics(@"mw3_preview");
            KisakDiagnosticEvent(@"MW3_PREVIEW_BEGIN");
            int result=KisakPreview_Main(argc,argv);
            KisakStopDiagnostics(result);
            return result;
        }
        const BOOL multiplayer = ![mode isEqualToString:@"sp"];
        KisakStartDiagnostics(multiplayer ? @"multiplayer" : @"single_player");
        NSString *name = multiplayer ? @"libkisakcod_mp.dylib" : @"libkisakcod_sp.dylib";
        NSString *path = [NSBundle.mainBundle.privateFrameworksPath stringByAppendingPathComponent:name];

        void *image = dlopen(path.fileSystemRepresentation, RTLD_NOW | RTLD_LOCAL);
        if (!image) {
            KisakDiagnosticEvent([NSString stringWithFormat:@"ENGINE_DLOPEN_FAILED name=%@ error=%s",name,dlerror() ?: "unknown"]);
            fprintf(stderr, "KisakCOD: cannot load %s\n", name.UTF8String);
            // Fall back to the other engine rather than leaving the player with a dead icon.
            name = multiplayer ? @"libkisakcod_sp.dylib" : @"libkisakcod_mp.dylib";
            path = [NSBundle.mainBundle.privateFrameworksPath stringByAppendingPathComponent:name];
            image = dlopen(path.fileSystemRepresentation, RTLD_NOW | RTLD_LOCAL);
            if (!image) {
                fprintf(stderr, "KisakCOD: no engine to load: %s\n", dlerror());
                KisakDiagnosticEvent(@"BOTH_ENGINE_LIBRARIES_FAILED");
                KisakStopDiagnostics(1);
                return 1;
            }
        }
        int (*entry)(int, char **) = (int (*)(int, char **))dlsym(image, "KisakEngine_AppMain");
        if (!entry) {
            fprintf(stderr, "KisakCOD: %s has no entry point: %s\n", name.UTF8String, dlerror());
            KisakDiagnosticEvent(@"ENGINE_ENTRY_MISSING");
            KisakStopDiagnostics(1);
            return 1;
        }
        fprintf(stderr, "KisakCOD: running %s\n", name.UTF8String);
        KisakDiagnosticEvent([NSString stringWithFormat:@"ENGINE_BEGIN name=%@",name]);
        int result = entry(argc, argv);
        KisakStopDiagnostics(result);
        return result;
    }
}
