import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Add src directory to path so we can import course_completer
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from course_completer import process_user, Settings
from selenium.webdriver.common.by import By

class TestBotSimulation(unittest.TestCase):
    def setUp(self):
        # Create a mock settings object
        self.settings = Settings()
        self.settings.timeout = 1
        self.settings.info_only = True # Don't try to actually play things
        
        # Create a mock driver
        self.mock_driver = MagicMock()
        self.mock_user = {"Login_id": "bot_test", "Password": "password123"}

    @patch("time.sleep", return_value=None)
    def test_login_flow(self, mock_sleep):
        """Verify that the bot correctly attempts to login with user credentials."""
        # Setup mock elements for login page
        mock_username_field = MagicMock()
        mock_password_field = MagicMock()
        mock_submit_button = MagicMock()
        
        # Configure find_element to return our mocks
        self.mock_driver.find_element.side_effect = lambda by, value: {
            "username": mock_username_field,
            "password": mock_password_field,
            "submitform": mock_submit_button
        }.get(value, MagicMock())
        
        # Run the process
        try:
            # We wrap it because it might fail later during course scanning (which is fine for this test)
            process_user(self.mock_driver, self.settings, self.mock_user)
        except Exception:
            pass 

        # Check if the correct URLs were visited
        self.mock_driver.get.assert_any_call("https://onlinetraining.niapune.org.in/index.php")
        
        # Check if credentials were entered
        mock_username_field.send_keys.assert_called_with("bot_test")
        mock_password_field.send_keys.assert_called_with("password123")
        mock_submit_button.click.assert_called()

    @patch("time.sleep", return_value=None)
    def test_course_discovery(self, mock_sleep):
        """Simulate finding a course CID and verify the bot tries to scan it."""
        # 1. Setup mock links
        mock_link = MagicMock()
        mock_link.get_attribute.return_value = "https://example.com/course?cid=555"
        
        # Configure driver to return our link during course discovery
        self.mock_driver.find_elements.return_value = [mock_link]
        
        # 2. Configure driver to return NO scorm items in the scan loop (to end early)
        # We need a side effect for the various find_elements calls
        self.mock_driver.find_elements.side_effect = [
            [mock_link], # Links on Courses page
            [],          # Links on Dashboard (optional fallback)
            []           # Scorm items inside course CID 555
        ]

        # 3. Setup dashboard elements (for identity check)
        self.mock_driver.find_element.return_value.text = "WELCOME TEST USER"

        # Run process
        process_user(self.mock_driver, self.settings, self.mock_user)

        # Verify it navigated to the Course CID 555 URL
        expected_url = "https://onlinetraining.niapune.org.in/nlms/course/view.php?id=555"
        self.mock_driver.get.assert_any_call(expected_url)

if __name__ == "__main__":
    unittest.main()
