import unittest
import os
import sys
import shutil
import time
from unittest.mock import patch, MagicMock

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from course_completer import process_user, Settings, get_driver

class TestPortalIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create mock HTML files in the current directory
        cls.mock_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mock_portal")
        if os.path.exists(cls.mock_dir):
            shutil.rmtree(cls.mock_dir)
        os.makedirs(cls.mock_dir)
            
        # 1. Login Page: Includes form and credentials fields
        with open(os.path.join(cls.mock_dir, "login.html"), "w", encoding="utf-8") as f:
            f.write("""
            <html>
                <body>
                    <form id="submitform">
                        <label for="username">Username</label>
                        <input id="username" type="text" name="username">
                        <label for="password">Password</label>
                        <input id="password" type="password" name="password">
                        <button type="submit" id="submitform">Login</button>
                    </form>
                </body>
            </html>
            """)
            
        # 2. Dashboard Page: Includes welcome, hours, and courses
        with open(os.path.join(cls.mock_dir, "dashboard.html"), "w", encoding="utf-8") as f:
            f.write("""
            <html>
                <body>
                    <span>WELCOME TEST USER</span>
                    <div class="info-box-content">
                        <span class="info-box-text">Remaining</span>
                        <span class="info-box-number">42 : 55</span>
                    </div>
                    <div id="module_info">Module Enrolled: Test Module</div>
                    <div id="reg_type">Registration Type: Fresher</div>
                    <a href="course.html?cid=999">View Course 1</a>
                </body>
            </html>
            """)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.mock_dir):
            shutil.rmtree(cls.mock_dir)

    def setUp(self):
        self.settings = Settings()
        self.settings.headless = True
        self.settings.timeout = 5
        self.settings.info_only = True
        self.user = {"Login_id": "test_user", "Password": "test_password"}
        # We need a headless driver for this integration test
        self.driver = get_driver(self.settings)

    def tearDown(self):
        if self.driver:
            self.driver.quit()

    @patch("time.sleep", return_value=None)
    def test_full_portal_flow(self, mock_sleep):
        """
        Integration test: Verifies the bot can:
        1. Navigate a real (headless) browser between local HTML pages.
        2. Successfully extract "Remaining Hours" from the DOM.
        3. Correct identify module names and course links.
        """
        # Convert local file paths to file:// URLs
        # On Windows, we need to handle absolute paths carefully with file:///
        mock_dir_path = os.path.abspath(self.mock_dir).replace("\\", "/")
        if not mock_dir_path.startswith('/'):
            mock_dir_path = '/' + mock_dir_path
            
        login_url = "file://" + mock_dir_path + "/login.html"
        dashboard_url = "file://" + mock_dir_path + "/dashboard.html"
        
        # Divert stdout to check results
        from io import StringIO
        import sys as main_sys
        captured_output = StringIO()
        original_stdout = main_sys.stdout
        main_sys.stdout = captured_output
        
        try:
            # Patch the global URL constants in the course_completer module
            with patch("course_completer.URL_LOGIN", login_url), \
                 patch("course_completer.URL_DASHBOARD", dashboard_url), \
                 patch("course_completer.URL_COURSES", dashboard_url):
                
                process_user(self.driver, self.settings, self.user)
                
                result_output = captured_output.getvalue()
                
                # Check results
                try:
                    self.assertIn("Remaining Hours : 42 : 55", result_output)
                    self.assertIn("Test Module", result_output)
                    self.assertIn("Verified 1 enrolled course(s)", result_output)
                except AssertionError as e:
                    # Print output for debugging on failure
                    original_stdout.write(f"\nCaptured Output:\n{result_output}\n")
                    raise e
            
        finally:
            main_sys.stdout = original_stdout

if __name__ == "__main__":
    unittest.main()
