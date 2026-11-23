import sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import build
class Sources(unittest.TestCase):
 def test_unapproved_source_hosts_are_rejected(self):
  for value in ['http://mast.stsci.edu/a','https://mast.stsci.edu.evil.test/a','javascript:alert(1)']:self.assertEqual(build.source_url(value),'')
  self.assertEqual(build.source_url('https://mast.stsci.edu/a'),'https://mast.stsci.edu/a')
 def test_incomplete_refresh_is_not_a_complete_snapshot(self):
  with patch.object(build,'mast_rows',return_value=[]):
   with self.assertRaises(ValueError):build.build_snapshot()
