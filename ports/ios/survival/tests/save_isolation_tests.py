#!/usr/bin/env python3
"""Exercise production checkpoint paths and the Campaign Continue selection."""
from pathlib import Path
import os, shlex, shutil, subprocess, tempfile
root=Path(__file__).resolve().parents[4]
native=(root/'ports/ios/survival/survival_engine.cpp').read_text().splitlines()
selection='\n'.join(next(line for line in native if line.startswith(prefix)) for prefix in ['bool selected()', 'const char *KisakSurvival_SaveGameDirectory()'])
selection+='\n'+next(line for line in native if line.startswith('bool KisakSurvival_IsSelected()'))+'\n'
source=(root/'src/game/savedevice_pc.cpp').read_text()
destination=next(line for line in source.splitlines() if 'FS_BuildOSPath(' in line and 'saveHeader->filename, destination' in line)
open_device=source[source.index('\nint __cdecl OpenDevice(')+1:source.index('\nvoid __cdecl CloseDevice(')+1]
exists=source[source.index('static bool SaveExistsValidated('):source.index('bool __cdecl SaveExists(')]
open_file=source[source.index('static unsigned int OpenSaveFile('):source.index('\nint __cdecl OpenDevice(')+1] if 'static unsigned int OpenSaveFile(' in source else ''
server=(root/'src/server/sv_main.cpp').read_text()
last_save=server[server.index('void __cdecl SV_SetLastSaveName('):server.index('void __cdecl SV_AddServerCommand(')]
compiler=['xcrun','clang++'] if shutil.which('xcrun') else shlex.split(os.environ.get('CXX','clang++'))
stubs=r'''
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cstdint>
#include <string>
#define __APPLE__ 1
#ifndef __cdecl
#define __cdecl
#endif
#define __int8 char
struct { struct { const char *string; } current; } home{{"/documents"}};
auto *fs_homepath=&home;
struct SaveHeader { const char *filename; int saveVersion; };
void FS_BuildOSPath(const char *home,const char *directory,const char *file,char *out) { std::snprintf(out,260,"%s/%s/%s",home,directory,file); }
void setMode(const char *value) {
#ifdef _WIN32
    _putenv_s("KISAK_SURVIVAL_MODE",value ? value : "");
#else
    if(value) setenv("KISAK_SURVIVAL_MODE",value,1); else unsetenv("KISAK_SURVIVAL_MODE");
#endif
}
int retailReads=0, scopedReads=0, lastWrites=0;
bool scopedExists=true;
std::string lastPath, continueName="profiles/test/save/campaign.svg";
unsigned int FS_FOpenFileRead(const char *name,int *handle) { ++retailReads; lastPath=name; *handle=11; return 64; }
int FS_SV_FOpenFileRead(const char *name,int *handle) { ++scopedReads; lastPath=name; *handle=scopedExists ? 22 : 0; return scopedExists ? 128 : 0; }
int FS_Read(unsigned char *buffer,unsigned int length,int) { reinterpret_cast<SaveHeader *>(buffer)->saveVersion=287; return length; }
void FS_FCloseFile(int) {}
int lastVariable=0; auto *sv_lastSaveGame=&lastVariable;
int SV_IsInternalSave(const char *name) { return std::strstr(name,"internal-")!=nullptr; }
void Dvar_SetString(int *,const char *name) { ++lastWrites; continueName=name; }
void MyAssertHandler(const char *,int,int,const char *,const char *) { std::abort(); }
'''
tests=r'''
int main() {
    SaveHeader header{"profiles/test/save/checkpoint.svg",287}; char output[260]; void *handle=nullptr;
    setMode("1"); build(&header,output);
    assert(!std::strcmp(output,"/documents/mods/specops_survival/players/profiles/test/save/checkpoint.svg"));
    assert(OpenDevice(header.filename,&handle)==128 && handle==(void *)(intptr_t)22 && retailReads==0);
    assert(lastPath=="mods/specops_survival/players/profiles/test/save/checkpoint.svg");
    assert(SaveExistsValidated(header.filename) && retailReads==0);
    scopedExists=false;
    assert(OpenDevice(header.filename,&handle)==-1 && handle==nullptr && retailReads==0);
    assert(!SaveExistsValidated(header.filename) && retailReads==0);
    assert(OpenDevice("../campaign.svg",&handle)==-1 && handle==nullptr);
    SV_SetLastSaveName(header.filename);
    assert(lastWrites==0 && continueName=="profiles/test/save/campaign.svg");
    setMode(nullptr); build(&header,output);
    assert(!std::strcmp(output,"/documents/players/profiles/test/save/checkpoint.svg"));
    assert(OpenDevice(header.filename,&handle)==64 && retailReads==1 && lastPath==header.filename);
    SV_SetLastSaveName(header.filename);
    assert(lastWrites==1 && continueName==header.filename);
    SV_SetLastSaveName("internal-checkpoint.svg"); assert(lastWrites==1);
}
'''
with tempfile.TemporaryDirectory(prefix='survival-save-test-') as directory:
    folder=Path(directory); code=folder/'test.cpp'
    executable=folder/('save-tests.exe' if os.name=='nt' else 'save-tests')
    code.write_text(stubs+selection+open_file+open_device+exists+last_save+'\nvoid build(const SaveHeader *saveHeader,char *destination) {\n'+destination+'\n}\n'+tests)
    subprocess.run(compiler+['-std=c++17',str(code),'-o',str(executable)],check=True)
    subprocess.run([str(executable)],check=True)
print('Checkpoints: Survival writes/reads isolated saves without Campaign fallback or Continue changes')
