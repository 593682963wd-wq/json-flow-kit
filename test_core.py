import unittest,tempfile,json
from pathlib import Path
from core import run

class Tests(unittest.TestCase):
 def test_dedupe(self):self.assertEqual(len(run(json.loads(Path('example.json').read_text()))['data']),2)
 def test_empty(self):self.assertEqual(run({})['data'],[])
 def test_disallowed(self):
  with self.assertRaises(ValueError):run({'steps':[{'type':'http'}]})
 def test_filter_path(self):self.assertEqual(run({'data':{'items':[{'key':'a','n':3}]},'steps':[{'type':'select','path':'items[key=a].n'}]})['data'],3)

if __name__=="__main__":unittest.main()
