#!/usr/bin/env python3
"""Exercise the production SP respawn path without retail files or an Apple SDK."""
from pathlib import Path
import os, shlex, shutil, subprocess, tempfile
root=Path(__file__).resolve().parents[4]
source=(root/'src/game/g_client.cpp').read_text()
respawn=source[source.index('void __cdecl respawn('):source.index('char *__cdecl ClientConnect(')]
native=(root/'ports/ios/survival/survival_engine.cpp').read_text().splitlines()
selection='\n'.join(next(line for line in native if line.startswith(prefix)) for prefix in ['bool selected()', 'bool KisakSurvival_UsesManualRetry()'])
compiler=['xcrun','clang++'] if shutil.which('xcrun') else shlex.split(os.environ.get('CXX','clang++'))
stubs=r'''
#include <cassert>
#include <cstdio>
#include <cstdarg>
#include <cstdlib>
#include <cstring>
#define __APPLE__ 1
#ifndef __cdecl
#define __cdecl
#endif
struct dvar_s { struct { int integer; const char *string; } current; };
dvar_s reload{{0,nullptr}}, delay{{3000,nullptr}};
const dvar_s *g_reloading=&reload, *g_deathDelay=&delay;
struct { int absoluteReloadDelayTime=0; } level;
struct gentity_s { void *client; };
int commands=0;
void setMode(const char *value) {
#ifdef _WIN32
    _putenv_s("KISAK_SURVIVAL_MODE",value ? value : "");
#else
    if(value) setenv("KISAK_SURVIVAL_MODE",value,1); else unsetenv("KISAK_SURVIVAL_MODE");
#endif
}
int Dvar_GetInt(const char *) { return 0; }
void Dvar_SetInt(const dvar_s *d,int n) { const_cast<dvar_s *>(d)->current.integer=n; }
int Sys_Milliseconds() { return 5000; }
void MyAssertHandler(const char *,int,int,const char *,const char *) { std::abort(); }
const char *va(const char *format,...) { static char value[256]; va_list args; va_start(args,format); std::vsnprintf(value,sizeof(value),format,args); va_end(args); return value; }
void SV_GameSendServerCommand(int,const char *) { ++commands; }
const dvar_s *Dvar_FindVar(const char *) { return nullptr; }
'''
tests=r'''
int main() {
    gentity_s player{&player};
    setMode("1"); respawn(&player);
    assert(reload.current.integer==0 && level.absoluteReloadDelayTime==0 && commands==0);
    setMode(nullptr); respawn(&player);
    assert(reload.current.integer==1 && level.absoluteReloadDelayTime==8000 && commands==4);
    respawn(&player);
    assert(level.absoluteReloadDelayTime==8000 && commands==4);
}
'''
with tempfile.TemporaryDirectory(prefix='survival-retry-test-') as directory:
    folder=Path(directory); code=folder/'test.cpp'
    executable=folder/('retry-tests.exe' if os.name=='nt' else 'retry-tests')
    code.write_text(stubs+selection+"\n"+respawn+tests)
    subprocess.run(compiler+['-std=c++17',str(code),'-o',str(executable)],check=True)
    subprocess.run([str(executable)],check=True)
print('Manual retry: Survival skips checkpoint reload; Campaign keeps its delay and death effects')
