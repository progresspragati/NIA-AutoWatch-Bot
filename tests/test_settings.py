import unittest
import os
import xml.etree.ElementTree as ET
import sys

# Add src directory to path so we can import course_completer
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from course_completer import get_settings, Settings

class TestSettings(unittest.TestCase):
    def test_default_settings(self):
        """Verify that default settings are used when no file exists."""
        settings = get_settings("non_existent_file_999.xml")
        # Check some defaults
        self.assertFalse(settings.headless)
        self.assertEqual(settings.timeout, 15)
        self.assertEqual(settings.max_retries, 15)

    def test_xml_loading(self):
        """Verify that settings are correctly loaded from an XML file."""
        xml_path = "tmp_test_settings.xml"
        root = ET.Element("Settings")
        ET.SubElement(root, "HideBrowser").text = "true"
        ET.SubElement(root, "WaitTimeout").text = "45"
        ET.SubElement(root, "MaxCompletionChecks").text = "100"
        ET.SubElement(root, "FastForward").text = "false"
        ET.SubElement(root, "MuteAudio").text = "false"
        
        tree = ET.ElementTree(root)
        tree.write(xml_path)

        try:
            settings = get_settings(xml_path)
            self.assertTrue(settings.headless)
            self.assertEqual(settings.timeout, 45)
            self.assertEqual(settings.max_retries, 100)
            self.assertFalse(settings.fast_forward)
            self.assertFalse(settings.mute)
        finally:
            if os.path.exists(xml_path):
                os.remove(xml_path)

if __name__ == "__main__":
    unittest.main()
