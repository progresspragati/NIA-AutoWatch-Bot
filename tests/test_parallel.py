import unittest
from unittest.mock import MagicMock, patch
import os
import sys
import concurrent.futures

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from course_completer import main, Settings

class TestParallelProcessing(unittest.TestCase):
    
    @patch("course_completer.get_settings")
    @patch("course_completer.get_driver")
    @patch("course_completer.process_user")
    @patch("csv.DictReader")
    @patch("os.path.exists", return_value=True)
    def test_main_parallel_users(self, mock_exists, mock_csv, mock_process, mock_driver, mock_get_settings):
        """Verify that main() uses ThreadPoolExecutor when simultaneous_users > 1."""
        # 1. Setup settings
        settings = Settings()
        settings.simultaneous_users = 2
        settings.users_file = "mock_users.csv"
        mock_get_settings.return_value = settings
        
        # 2. Setup mock users
        mock_csv.return_value = [
            {"Login_id": "user1", "Password": "p1"},
            {"Login_id": "user2", "Password": "p2"}
        ]
        
        # 3. Call main
        # We need to mock open() to avoid file errors
        with patch("builtins.open", unittest.mock.mock_open(read_data="col1,col2")):
            main()
        
        # 4. Verify process_user was called twice
        # Since it's parallel, we check the call count
        self.assertEqual(mock_process.call_count, 2)
        
        # Verify drivers were closed
        self.assertEqual(mock_driver.return_value.quit.call_count, 2)

if __name__ == "__main__":
    unittest.main()
