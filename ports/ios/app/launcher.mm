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
#include "../survival/ModeCatalog.hpp"

extern "C" NSString *const KisakEngineModeKey = @"KisakEngineMode";

int main(int argc, char *argv[])
{
    @autoreleasepool {
        NSString *mode = [NSUserDefaults.standardUserDefaults stringForKey:KisakEngineModeKey];
        const auto selected=cod4ios::modes::fromSavedId(mode.UTF8String ?: "");
        const BOOL multiplayer = cod4ios::modes::engine(selected)==cod4ios::modes::Engine::MultiPlayer;
        NSString *name = multiplayer ? @"libkisakcod_mp.dylib" : @"libkisakcod_sp.dylib";
        NSString *path = [NSBundle.mainBundle.privateFrameworksPath stringByAppendingPathComponent:name];

        void *image = dlopen(path.fileSystemRepresentation, RTLD_NOW | RTLD_LOCAL);
        if (!image) {
            fprintf(stderr, "KisakCOD: cannot load %s: %s\n", name.UTF8String, dlerror());
            // Loading the wrong engine would silently run a different selected mode.
            return 1;
        }
        int (*entry)(int, char **) = (int (*)(int, char **))dlsym(image, "KisakEngine_AppMain");
        if (!entry) {
            fprintf(stderr, "KisakCOD: %s has no entry point: %s\n", name.UTF8String, dlerror());
            return 1;
        }
        fprintf(stderr, "KisakCOD: running %s\n", name.UTF8String);
        return entry(argc, argv);
    }
}
