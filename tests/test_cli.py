import unittest
from unittest.mock import patch
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from course_completer import get_settings

class TestCLIArguments(unittest.TestCase):
    
    def test_cli_overrides_xml(self):
        """Verify that CLI arguments take priority over XML/defaults."""
        # Mock sys.argv to simulate command line input
        test_args = [
            "course_completer.py",
            "--headless",
            "--timeout", "99",
            "--sim-users", "3",
            "--no-fast-forward"
        ]
        
        with patch.object(sys, 'argv', test_args):
            # We pass a non-existent XML file to ensure we are testing defaults + CLI
            settings = get_settings("non_existent.xml")
            
            self.assertTrue(settings.headless)
            self.assertEqual(settings.timeout, 99)
            self.assertEqual(settings.simultaneous_users, 3)
            self.assertFalse(settings.fast_forward)

    def test_cli_mute_overrides(self):
        """Test the --unmute flag specifically."""
        test_args = ["course_completer.py", "--unmute"]
        with patch.object(sys, 'argv', test_args):
            settings = get_settings("non_existent.xml")
            self.assertFalse(settings.mute)

if __name__ == "__main__":
    unittest.main()
