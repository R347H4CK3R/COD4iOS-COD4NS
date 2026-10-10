import tempfile
import unittest
from pathlib import Path
from analyze import analyze, parse_script, builtin_registry, single_player_source

class CompatibilityTests(unittest.TestCase):
    def test_comments_strings_nested_calls_and_references(self):
        script = parse_script('''// fake_call()
main(a) { x = real(nested(1)); self method(); maps\\helpers::run(x); ptr = maps\\helpers::callback; localptr=::local; thread ::local(); text="pretend()"; /* omitted() */ if (x) { local(); } }
local() { return 1; }''')
        self.assertEqual(script['definitions'], ['local', 'main'])
        self.assertEqual(script['calls'], ['local', 'method', 'nested', 'real'])
        self.assertEqual(script['references'], [('maps/helpers', 'callback'), ('maps/helpers', 'run')])

    def test_sp_filter_cast_handlers_and_hud_addresses(self):
        source = """#ifdef KISAK_MP
mp_only
#else
sp_only
#endif
#ifdef UNKNOWN
possible_a
#else
possible_b
#endif"""
        filtered=single_player_source(source)
        self.assertNotIn('mp_only',filtered)
        self.assertIn('sp_only',filtered)
        self.assertIn('possible_a',filtered)
        self.assertIn('possible_b',filtered)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'registry.cpp').write_text('BuiltinFunctionDef funcs[1] = {\n { "model", (void(*)())Precache, 0 }\n};\nBuiltinMethodDef meth[1] = {\n { "shader", &SetShader, 0 }\n};')
            registry=builtin_registry(root)
            self.assertIn('model',registry['functions'])
            self.assertIn('shader',registry['methods'])

    def test_registry_names_are_distinct_from_unresolved_helpers(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); scripts=root/'scripts'; engine=root/'engine'; scripts.mkdir(); engine.mkdir()
            (engine/'registry.cpp').write_text('''BuiltinFunctionDef functions[2] = {
 { "tablelookup", Lookup, 0 },
 { "print", Print, 0 }
};
static const BuiltinMethodDef methods[1] = {
 { "givemoney", Money, 0 }
};''')
            (scripts/'numeric.gsc').write_text('main() { tablelookup("sp/waves.csv",0,"1",2); self givemoney(3); helper(); missing(); maps\\other::run(); }\nhelper() {}')
            (scripts/'candidate.gsc').write_text('run() {}')
            report=analyze([scripts], engine, {'maps/core':'numeric.gsc'}, ['maps/core'])
            self.assertEqual(report['scripts']['0:numeric.gsc']['registered_calls'], ['givemoney','tablelookup'])
            self.assertEqual(report['scripts']['0:numeric.gsc']['unclassified_calls'], ['missing'])
            self.assertEqual(report['scripts']['0:numeric.gsc']['tables'], ['sp/waves.csv'])
            self.assertIn('maps/other',report['unresolved_namespaces'])
            self.assertEqual(report['entry_closures']['maps/core']['unresolved_dependencies'], ['maps/other'])
            self.assertEqual(report['unresolved_namespaces']['maps/other']['unverified_candidates'][0]['file'],'0:candidate.gsc')
            resolved=analyze([scripts],engine,{'maps/other':'numeric.gsc'})
            self.assertEqual(resolved['missing_exports'][0]['function'],'run')
            with self.assertRaises(ValueError): analyze([scripts,scripts],engine,{'maps/core':'numeric.gsc'})

if __name__=='__main__': unittest.main()
