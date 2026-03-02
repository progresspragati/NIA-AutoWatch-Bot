import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from course_completer import complete_scorm_video, Settings

class TestVideoLogic(unittest.TestCase):
    def setUp(self):
        self.settings = Settings()
        self.settings.max_retries = 2
        self.mock_driver = MagicMock()
        self.mock_driver.window_handles = ["main", "popup"]
        self.mock_driver.current_window_handle = "main"

    @patch("time.sleep", return_value=None)
    def test_complete_scorm_video_success_ff(self, mock_sleep):
        """Test successful video completion with fast-forward enabled."""
        self.settings.fast_forward = True
        
        # Mock wait for enter button
        mock_enter_btn = MagicMock()
        with patch("selenium.webdriver.support.ui.WebDriverWait.until", return_value=mock_enter_btn):
            # Mock the API check to return True (completed) on the first check
            self.mock_driver.execute_script.side_effect = [
                None,  # script_core execution
                True   # api_check returns True
            ]
            
            result = complete_scorm_video(self.mock_driver, self.settings, "http://test.url", "Test Lesson")
            
            self.assertTrue(result)
            self.mock_driver.close.assert_called() # Should close the popup
            self.mock_driver.switch_to.window.assert_any_call("main")

    @patch("time.sleep", return_value=None)
    def test_complete_scorm_video_natural_playback(self, mock_sleep):
        """Test natural playback where it waits for video to end."""
        self.settings.fast_forward = False
        
        mock_enter_btn = MagicMock()
        with patch("selenium.webdriver.support.ui.WebDriverWait.until", return_value=mock_enter_btn):
            # execute_script sequence:
            # 1. script_core (initial)
            # 2. api_check -> returns True (LMS says done)
            # 3. video_state check -> returns 'playing' (Wait)
            # 4. script_core (retry 1)
            # 5. api_check -> returns True
            # 6. video_state check -> returns 'ended' (Done)
            
            self.mock_driver.execute_script.side_effect = [
                None,     # initial script
                True,     # api_check
                'playing',# video status
                None,     # retry 1 script
                True,     # api_check
                'ended'   # video status
            ]
            
            result = complete_scorm_video(self.mock_driver, self.settings, "http://test.url", "Test Lesson")
            
            self.assertTrue(result)
            self.mock_driver.close.assert_called()

    @patch("time.sleep", return_value=None)
    def test_popup_closed_unexpectedly(self, mock_sleep):
        """Test behavior when the vido popup is closed during the monitoring loop."""
        mock_enter_btn = MagicMock()
        with patch("selenium.webdriver.support.ui.WebDriverWait.until", return_value=mock_enter_btn):
            # 1. Initial check passes (2 windows)
            # 2. Inside loop, it checks window_handles again. We make it return only 1 window on second call.
            self.mock_driver.window_handles = ["main", "popup"]
            
            # Use PropertyMock to change handles over time
            type(self.mock_driver).window_handles = unittest.mock.PropertyMock(side_effect=[
                ["main", "popup"], # line 154 (if)
                ["main", "popup"], # line 163 (wait/iframe check handles)
                ["main", "popup"], # line 200 (defensive check)
                ["main"]          # line 205 (closure check) -> BREAKS LOOP
            ])

            result = complete_scorm_video(self.mock_driver, self.settings, "http://test.url", "Test Lesson")
            
            # Should still return True because it gracefully handled the closure and returned to main
            self.assertTrue(result)
            self.mock_driver.switch_to.window.assert_any_call("main")

if __name__ == "__main__":
    unittest.main()
