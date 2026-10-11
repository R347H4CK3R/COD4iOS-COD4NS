import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from mw3_gameplay_config import load,resolve
class TestResolver(unittest.TestCase):
 def setUp(self): self.entries=load(Path(__file__).resolve().parents[1]/'config/mw3/gameplay.sample.json')
 def test_override(self):
  self.assertEqual(resolve(self.entries,'multiplayer')['weapon']['assault_rifle_base']['source'],'mw3')
 def test_separation(self):
  self.assertNotIn('uav',resolve(self.entries,'special_ops')['killstreak'])
 def test_inverse_preference(self):
  self.assertEqual(resolve(self.entries,'multiplayer','cod4')['weapon']['assault_rifle_base']['source'],'cod4')
 def test_invalid(self):
  with self.assertRaises(ValueError): resolve(self.entries,'campaign')
 def test_categories(self):
  self.assertEqual(len(resolve(self.entries,'multiplayer')),6)
if __name__=='__main__': unittest.main()
