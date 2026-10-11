from pathlib import Path
p=Path(__file__).resolve().parents[1]/'ports/ios/core/mw3_combat_adapter.cpp'
s=p.read_text()
if 'mw3_gameplay_events.log' not in s:
 s=s.replace('#include <cstdlib>','#include <cstdlib>\n#include <cstdio>\n#include <ctime>')
 needle='bool read_integer(MW3Mode mode,MW3Category category,const char* id,const char* key,int& result){'
 addition='''void gameplay_event(const char* category,const char* weapon,int before,int after) {
#if defined(__APPLE__)
 if(before==after) return;
 const char* home=std::getenv("HOME"); if(!home || !*home) return;
 std::string path=std::string(home)+"/Documents/mw3_gameplay_events.log";
 if(FILE* f=std::fopen(path.c_str(),"a")) {
  std::fprintf(f,"%lld %s %s original=%d override=%d\\n",
    static_cast<long long>(std::time(nullptr)),category,weapon,before,after);
  std::fclose(f);
 }
#else
 (void)category;(void)weapon;(void)before;(void)after;
#endif
}
'''
 s=s.replace(needle,addition+needle,1)
 s=s.replace(' return std::clamp(replacement,1,100000);',' const int result=std::clamp(replacement,1,100000);\n gameplay_event("damage",weapon,original,result);\n return result;')
 s=s.replace(' return std::clamp(replacement,0,120000);',' const int result=std::clamp(replacement,0,120000);\n gameplay_event("reload_ms",weapon,original,result);\n return result;')
 p.write_text(s)
print('gameplay diagnostics added')
