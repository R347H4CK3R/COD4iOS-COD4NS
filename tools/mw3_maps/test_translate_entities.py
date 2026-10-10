import unittest,tempfile
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
from translate_entities import translate,load_dictionary,COMMIT,DICTIONARY,TranslationError,UnsupportedTokens

class TranslationTests(unittest.TestCase):
    def test_values_and_layout_preserved(self):
        original=b'{\r\n1668 "worldspawn"\r\n2810 "0.7"\r\n}\r\n'
        self.assertEqual(translate(original,{1668:'classname',2810:'sunradiosity'}),
                         b'{\r\n"classname" "worldspawn"\r\n"sunradiosity" "0.7"\r\n}\r\n')
    def test_unknown_fatal_and_all_collected(self):
        with self.assertRaises(UnsupportedTokens) as context:
            translate(b'{ 999 "x" 1629 "y" }',{})
        self.assertEqual(context.exception.tokens,[999,1629])
    def test_1629_cannot_be_guessed(self):
        with self.assertRaises(UnsupportedTokens):translate(b'{ 1629 "x" }',{1629:'guessed'})
    def test_quoted_value_escapes_preserved(self):
        original=b'{ 1668 "a\\\"b\\\\c" }'
        self.assertEqual(translate(original,{1668:'classname'}),b'{ "classname" "a\\\"b\\\\c" }')
    def test_syntax_rejected(self):
        for text in (b'{ 1668 "x"',b'{ { 1668 "x" } }',b'1668 "x"',b'{ 1668 x }',
                     b'{ 1668 "x" }junk',b'{ 1668 "unterminated }',b'{ 1668 "x\0" }',b'{ -1 "x" }'):
            with self.subTest(text=text),self.assertRaises(TranslationError):translate(text,{1668:'classname'})
    def test_repeated_entities_and_duplicate_keys(self):
        self.assertEqual(translate(b'{ 1 "a" 1 "b" }\n{ 1 "c" }',{1:'key'}),
                         b'{ "key" "a" "key" "b" }\n{ "key" "c" }')
    def test_unsafe_dictionary_name(self):
        with self.assertRaises(TranslationError):translate(b'{ 1 "x" }',{1:'key"injection'})
    def test_budget(self):
        with self.assertRaises(TranslationError):translate(b' '*(4*1024*1024+1),{})
    def test_dictionary_commit_and_content_verified(self):
        with patch('translate_entities.subprocess.run',return_value=SimpleNamespace(stdout='wrong\n')):
            with self.assertRaises(TranslationError):load_dictionary(Path('unused'))
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder);dictionary=source/DICTIONARY;dictionary.parent.mkdir(parents=True);dictionary.write_text('modified source')
            with patch('translate_entities.subprocess.run',return_value=SimpleNamespace(stdout=COMMIT+'\n')):
                with self.assertRaises(TranslationError):load_dictionary(source)
if __name__=='__main__':unittest.main()
