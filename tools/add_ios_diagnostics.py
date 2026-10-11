from pathlib import Path
p=Path(__file__).resolve().parents[1]/'ports/ios/app/launcher.mm'
s=p.read_text(encoding='utf-8')
assert 'int main(int argc, char *argv[])' in s
if 'KisakDiagnosticEvent' not in s:
 s=s.replace('#include <stdio.h>','#include <stdio.h>\n#include <signal.h>\n#include <unistd.h>\n#include <fcntl.h>\n#include <string.h>')
 anchor='extern "C" NSString *const KisakEngineModeKey = @"KisakEngineMode";'
 extra=r'''
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
'''
 s=s.replace(anchor,anchor+'\n'+extra,1)
 s=s.replace('        const BOOL multiplayer = ![mode isEqualToString:@"sp"];','        const BOOL multiplayer = ![mode isEqualToString:@"sp"];\n        KisakStartDiagnostics(multiplayer ? @"multiplayer" : @"single_player");',1)
 s=s.replace('            fprintf(stderr, "KisakCOD: cannot load %s: %s\\n", name.UTF8String, dlerror());',
 '''            KisakDiagnosticEvent([NSString stringWithFormat:@"ENGINE_DLOPEN_FAILED name=%@ error=%s",name,dlerror() ?: "unknown"]);
            fprintf(stderr, "KisakCOD: cannot load %s\\n", name.UTF8String);''',1)
 s=s.replace('                return 1;','                KisakDiagnosticEvent(@"BOTH_ENGINE_LIBRARIES_FAILED");\n                KisakStopDiagnostics(1);\n                return 1;',1)
 s=s.replace('            return 1;\n        }\n        fprintf(stderr,','            KisakDiagnosticEvent(@"ENGINE_ENTRY_MISSING");\n            KisakStopDiagnostics(1);\n            return 1;\n        }\n        fprintf(stderr,',1)
 s=s.replace('        return entry(argc, argv);','        KisakDiagnosticEvent([NSString stringWithFormat:@"ENGINE_BEGIN name=%@",name]);\n        int result = entry(argc, argv);\n        KisakStopDiagnostics(result);\n        return result;',1)
 p.write_text(s,encoding='utf-8')
print('Diagnostic launch instrumentation:',s.count('KisakDiagnosticEvent'))
