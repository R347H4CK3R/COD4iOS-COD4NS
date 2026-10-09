#!/usr/bin/env python3
"""Execute production map routing with every setup selection, including bad settings."""
from pathlib import Path
import os, shlex, shutil, subprocess, tempfile
root=Path(__file__).resolve().parents[4]
native=(root/'ports/ios/survival/survival_engine.cpp').read_text()
app=(root/'ports/ios/app/engine_app.mm').read_text()
assert 'KisakApple_RunEngine(KisakSurvival_StartupCommand());' in app
assert 'Cbuf_AddText(0,reloadCommand());' in native
assert 'Cbuf_AddText(0,survival ? reloadCommand(true)' in native

def extract(name):
    start=native.index(name); opening=native.index('{',start); depth=1; end=opening+1
    while depth:
        depth += (native[end]=='{') - (native[end]=='}'); end+=1
    return native[start:end]+'\n'
compiler=['xcrun','clang++'] if shutil.which('xcrun') else shlex.split(os.environ.get('CXX','clang++'))
code=r'''#include <cassert>
#include <cstdio>
#include <string>
#include "ports/ios/survival/SurvivalConfig.hpp"
using namespace cod4ios::survival;
Config config; unsigned selectedMap=0, selectedClass=0;
void KisakApple_GetSurvivalConfig(unsigned* map,unsigned* difficulty,unsigned* playerClass) { *map=selectedMap; *difficulty=1; *playerClass=selectedClass; }
'''+extract('void loadConfig()')+extract('const char *reloadCommand(')+extract('const char *KisakSurvival_StartupCommand()')+r'''
int main() {
 const char* retail[]={"bog_a","bog_b","ambush","blackout","armada"};
 for(unsigned map=0;map<5;++map) for(unsigned playerClass=0;playerClass<3;++playerClass) {
  selectedMap=map; selectedClass=playerClass;
  const std::string startup=KisakSurvival_StartupCommand(), retry=reloadCommand(), change=reloadCommand(true);
  assert(startup.find(std::string("+devmap ")+retail[map])!=std::string::npos);
  assert(retry.find(std::string("devmap ")+retail[map]+"\n")!=std::string::npos);
  assert(change.find("vid_restart\n")==0);
  assert(change.find(std::string("devmap ")+retail[map]+"\n")!=std::string::npos);
  assert(startup.find(std::string("kisak_survival_class ")+std::to_string(playerClass))!=std::string::npos);
 }
 selectedMap=999; selectedClass=999;
 assert(std::string(KisakSurvival_StartupCommand()).find("+devmap bog_a")!=std::string::npos);
 assert(std::string(reloadCommand()).find("kisak_survival_class 0")!=std::string::npos);
}
'''
with tempfile.TemporaryDirectory(prefix='survival-map-test-') as directory:
 folder=Path(directory); source=folder/'test.cpp'; executable=folder/('maps.exe' if os.name=='nt' else 'maps')
 source.write_text(code)
 subprocess.run(compiler+['-std=c++17','-I',str(root),str(source),'-o',str(executable)],check=True)
 subprocess.run([str(executable)],check=True)
print('Production startup/retry/mode-switch commands route all five maps and all classes, invalid settings default to Bog')
