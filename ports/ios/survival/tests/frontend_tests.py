from pathlib import Path
import os, shlex, subprocess, tempfile
root=Path(__file__).resolve().parents[4]
s=(root/'src/ui/ui_main.cpp').read_text()
fn=s[s.index('int __cdecl UI_SetActiveMenu('):s.index('void __cdecl UI_DrawConnectScreen()')]
leave=s[s.index('    if (!I_stricmp(out, "Leave"))'):s.index('    if (!I_stricmp(out, "closeingame"))')]
stubs=r'''
#include <cassert>
#include <string>
#include <vector>
#ifndef __cdecl
#define __cdecl
#endif
#define __APPLE__ 1
enum uiMenuCommand_t {UIMENU_NONE,UIMENU_MAIN,UIMENU_INGAME,UIMENU_PREGAME,UIMENU_POSTGAME,UIMENU_BRIEFING,UIMENU_VICTORYSCREEN,UIMENU_SAVEERROR,UIMENU_SAVE_LOADING,UIMENU_CONTROLLERREMOVED,UIMENU_SCRIPT_POPUP};
struct { struct {struct {float x,y;} cursor;} uiDC; } uiInfo;
uiMenuCommand_t g_currentMenuType=UIMENU_NONE;
bool selected=false; const char *error=""; int catcher=0,paused=0,clears=0,progress=0;
std::vector<std::string> opened;
bool KisakSurvival_IsSelected(){return selected;}
int Menu_Count(...) {return 1;}
void MyAssertHandler(...) {assert(false);}
void Key_RemoveCatcher(int,int){catcher=0;}
void Key_ClearStates(int){++clears;}
void Dvar_SetIntByName(const char*,int n){paused=n;}
void Menus_CloseAll(...){opened.clear();}
bool CL_SkipRendering(){return false;}
void Key_SetCatcher(int,int n){catcher=n;}
void Menus_OpenByName(void*,const char *name){opened.emplace_back(name);}
const char *Dvar_GetString(const char*){return error;}
void CL_StopControllerRumbles(){}
void SND_FadeAllSounds(double,int){}
bool UI_AutoContinue(){return false;}
void UI_PlayerStart(){++progress;}
bool SaveMemory_IsRecentlyLoaded(){return false;}
bool Menu_GetFocused(...){return false;}
int I_stricmp(const char *a,const char *b){return std::string(a)==b ? 0 : 1;}
int disconnects=0;
void Cbuf_AddText(int,const char*){++disconnects;}
void CL_SetActive(){}
'''
tests=r'''
int main(){
selected=true;
UI_SetActiveMenu(0,UIMENU_MAIN); assert(opened.empty() && catcher==16);
leaveMenu("Leave"); assert(opened.empty() && disconnects==1);
error="load failed"; UI_SetActiveMenu(0,UIMENU_MAIN);
assert(opened.size()==1 && opened[0]=="error_popmenu");
error=""; UI_SetActiveMenu(0,UIMENU_INGAME); assert(opened.back()=="pausedmenu" && paused==1);
UI_SetActiveMenu(0,UIMENU_SAVE_LOADING); assert(opened.back()=="savegameloading");
UI_SetActiveMenu(0,UIMENU_SAVEERROR); assert(opened.back()=="savegame_error");
UI_SetActiveMenu(0,UIMENU_PREGAME); assert(opened.back()=="pregame");
error="load failed"; UI_SetActiveMenu(0,UIMENU_PREGAME); assert(opened.back()=="pregame_loaderror");
UI_SetActiveMenu(0,UIMENU_NONE); assert(opened.empty() && catcher==0 && paused==0 && clears==1);
selected=false; error=""; UI_SetActiveMenu(0,UIMENU_MAIN); assert(opened.size()==1 && opened[0]=="main");
error="failure"; UI_SetActiveMenu(0,UIMENU_MAIN); assert(opened.back()=="error_popmenu");
}
'''
with tempfile.TemporaryDirectory() as directory:
 p=Path(directory); source=p/'menu.cpp'; exe=p/'menu.exe'
 source.write_text(stubs+fn+'void leaveMenu(const char *out, int localClientNum=0){\n'+leave+'}\n'+tests)
 subprocess.run(shlex.split(os.environ.get('CXX','clang++'))+['-std=c++17',str(source),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('Production front end: Survival hides main; Campaign, errors, pause and progress preserved')

