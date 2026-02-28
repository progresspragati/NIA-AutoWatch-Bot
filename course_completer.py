import time
import os
import csv
import argparse
import xml.etree.ElementTree as ET
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURATION ---
URL_LOGIN = "https://onlinetraining.niapune.org.in/index.php"
URL_COURSES = "https://onlinetraining.niapune.org.in/learner/learnerCourses.php"
SETTINGS_FILE = "settings.xml"

# JS snippet to find the SCORM API across frames
JS_FIND_API = """
function findAPI(win) {
    var findAttempts = 0;
    while ((win.API == null) && (win.parent != null) && (win.parent != win)) {
        findAttempts++;
        if (findAttempts > 10) return null;
        win = win.parent;
    }
    return win.API;
}
"""

class Settings:
    def __init__(self):
        self.headless = False
        self.timeout = 15
        self.course_id = None
        self.max_retries = 15
        self.fast_forward = True
        self.replay_done = False
        self.mute = True
        self.users_file = "users.csv"

def get_settings():
    """Combines command line arguments and XML settings."""
    settings = Settings()

    # 1. Parse XML settings if file exists
    if os.path.exists(SETTINGS_FILE):
        try:
            tree = ET.parse(SETTINGS_FILE)
            root = tree.getroot()
            
            headless_val = root.findtext("Headless", "false").lower()
            settings.headless = headless_val == "true"
            
            timeout_val = root.findtext("Timeout", "15")
            settings.timeout = int(timeout_val)
            
            retries_val = root.findtext("MaxRetries", "15")
            settings.max_retries = int(retries_val)
            
            ff_val = root.findtext("FastForward", "true").lower()
            settings.fast_forward = ff_val == "true"
            
            rd_val = root.findtext("ReplayDone", "false").lower()
            settings.replay_done = rd_val == "true"
            
            mute_val = root.findtext("Mute", "true").lower()
            settings.mute = mute_val == "true"
            
            settings.users_file = root.findtext("UsersFile", "users.csv")
            
            print(f"[INFO] Loaded configuration from {SETTINGS_FILE}")
        except Exception as e:
            print(f"[WARN] Error parsing {SETTINGS_FILE}: {e}. Defaults used.")

    # 2. Parse command line arguments (priority overrides)
    parser = argparse.ArgumentParser(description="NIA-AutoWatch-Bot")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--timeout", type=int)
    parser.add_argument("--course-id", type=str)
    parser.add_argument("--max-retries", type=int)
    parser.add_argument("--no-fast-forward", action="store_true")
    parser.add_argument("--replay-done", action="store_true")
    parser.add_argument("--unmute", action="store_true", help="Enable audio even if XML mutes it")
    parser.add_argument("--users-file", type=str)
    
    cli_args, unknown = parser.parse_known_args()

    if cli_args.headless: settings.headless = True
    if cli_args.timeout: settings.timeout = cli_args.timeout
    if cli_args.course_id: settings.course_id = cli_args.course_id
    if cli_args.max_retries: settings.max_retries = cli_args.max_retries
    if cli_args.no_fast_forward: settings.fast_forward = False
    if cli_args.replay_done: settings.replay_done = True
    if cli_args.unmute: settings.mute = False
    if cli_args.users_file: settings.users_file = cli_args.users_file

    return settings

# Global settings instance
settings = get_settings()

def get_driver():
    """Initializes a fresh Chrome WebDriver."""
    chrome_options = Options()
    if settings.headless:
        chrome_options.add_argument("--headless")
    
    if settings.mute:
        chrome_options.add_argument("--mute-audio")
        
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--log-level=3")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def complete_scorm_video(driver, lesson_url, lesson_name):
    """Handles a single video completion task."""
    main_window = driver.current_window_handle
    print(f"      - Processing: {lesson_name}")
    driver.get(lesson_url)
    
    try:
        wait = WebDriverWait(driver, 10)
        enter_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit'][value='Enter'], button.btn-primary")))
        enter_btn.click()
        
        # Robustly wait for and switch to the newest window
        time.sleep(4)
        if len(driver.window_handles) > 1:
            popup_window = driver.window_handles[-1]
            driver.switch_to.window(popup_window)
            
            mode = "Fast-Forward" if settings.fast_forward else "Natural Playback"
            print(f"      - Player Popup Active ({mode})...")
            
            try:
                # Find the iframe containing the Articulate player
                iframe = wait.until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
                driver.switch_to.frame(iframe)
                
                # Logic to run inside the iframe
                script_core = """
                if (arguments[0] === true) {
                    var vids = document.getElementsByTagName('video');
                    for (var i = 0; i < vids.length; i++) {
                        if (arguments[1] === true) { vids[i].muted = true; }
                        if (vids[i].duration) {
                            vids[i].currentTime = vids[i].duration - 0.5;
                            vids[i].play();
                        }
                    }
                } else if (arguments[1] === true) {
                    var vids = document.getElementsByTagName('video');
                    for (var i = 0; i < vids.length; i++) { vids[i].muted = true; }
                }
                var next = document.querySelector('#next, .next-button, [aria-label="Next"]');
                if (next) { next.click(); }
                """
                
                # Composite API check script (includes findAPI helper)
                api_check = JS_FIND_API + """
                var api = findAPI(window.parent || window);
                if (api) {
                    var status = api.LMSGetValue('cmi.core.lesson_status');
                    if (status === 'completed' || status === 'passed') return true;
                }
                return false;
                """

                # Main loop waiting for completion
                for i in range(settings.max_retries):
                    try:
                        # 0. Defensive check: Is the driver/browser still alive?
                        try:
                            _ = driver.window_handles
                        except:
                            print("      - [CRITICAL] Browser connection lost.")
                            return False

                        if len(driver.window_handles) < 2:
                            print("      - [ERROR] Popup window closed unexpectedly.")
                            break

                        driver.execute_script(script_core, settings.fast_forward, settings.mute)
                        
                        # Check API status
                        driver.switch_to.default_content()
                        is_done = driver.execute_script(api_check)
                        
                        if is_done:
                            # If we are NOT fast-forwarding, we must ensure the video has actually finished.
                            if not settings.fast_forward:
                                try:
                                    driver.switch_to.frame(iframe)
                                    # This script checks:
                                    # 1. Is there a video element?
                                    # 2. Is it currently playing/not ended?
                                    video_state = driver.execute_script("""
                                        var v = document.querySelector('video');
                                        if (!v) return 'no_video'; 
                                        if (v.ended) return 'ended';
                                        if (v.duration > 0) return 'playing';
                                        return 'loading';
                                    """)
                                    
                                    if video_state == 'playing' or video_state == 'loading':
                                        should_close = False
                                        if i % 3 == 0: 
                                            print(f"      - Video status: {video_state}. Waiting...")
                                    elif video_state == 'no_video' and i < 10:
                                        # Give it a few retries to actually find the video element
                                        should_close = False
                                        if i % 3 == 0: print("      - Waiting for video player to load...")
                                    
                                    driver.switch_to.default_content()
                                except: pass
                            
                            if should_close:
                                print(f"      - [SUCCESS] Module completed.")
                                driver.close()
                                driver.switch_to.window(main_window)
                                return True
                        
                        driver.switch_to.frame(iframe)
                    except Exception as loop_e:
                        pass # Small glitches ignored in loop
                    
                    time.sleep(5)

                # Final Cleanup attempt if loop finished or broke
                try:
                    if len(driver.window_handles) > 1:
                        # Attempt one last force push only if window is still open
                        driver.switch_to.default_content()
                        driver.execute_script(JS_FIND_API + "var api=findAPI(window); if(api){api.LMSSetValue('cmi.core.lesson_status', 'completed'); api.LMSCommit('');}")
                        print("      - [INFO] Closing popup.")
                        driver.close()
                except: pass
            except Exception as player_e:
                print(f"      - [ERROR] Player interaction error: {player_e}")
            
            # SAFE RETURN to main window
            try:
                driver.switch_to.window(main_window)
            except:
                # If main window is somehow lost, relaunch in main logic
                pass
            return True
        return False
    except Exception as launch_e:
        print(f"      - [ERROR] Failed to launch lesson: {launch_e}")
        try:
            if len(driver.window_handles) > 1:
                driver.close()
            driver.switch_to.window(main_window)
        except: pass
        return False

def process_user(driver, user):
    """Processes all courses for a single user account."""
    uid, pwd = user['Login_id'], user['Password']
    wait = WebDriverWait(driver, settings.timeout)
    print(f"\n[USER] {uid} - Starting Course Automation...")
    
    # login
    driver.get(URL_LOGIN)
    wait.until(EC.presence_of_element_located((By.ID, "username"))).clear()
    driver.find_element(By.ID, "username").send_keys(uid)
    driver.find_element(By.ID, "password").clear()
    driver.find_element(By.ID, "password").send_keys(pwd)
    driver.find_element(By.ID, "submitform").click()
    time.sleep(3)

    # course discovery
    driver.get(URL_COURSES)
    links = driver.find_elements(By.XPATH, "//a[contains(@href, 'cid=')]")
    course_list = list(set([l.get_attribute("href").split("cid=")[-1] for l in links if "cid=" in l.get_attribute("href")]))
    
    if settings.course_id:
        course_list = [c for c in course_list if c == settings.course_id]

    print(f"  - Verified {len(course_list)} enrolled course(s).")

    for cid in course_list:
        course_url = f"https://onlinetraining.niapune.org.in/nlms/course/view.php?id={cid}"
        print(f"  [COURSE] Scanning Module CID {cid}...")
        
        seen_in_run = set()
        while True:
            driver.get(course_url)
            time.sleep(4)
            
            # Handle expand all if present
            try:
                driver.find_element(By.XPATH, "//a[contains(text(), 'Expand all')]").click()
                time.sleep(1)
            except: pass

            scorm_items = driver.find_elements(By.CSS_SELECTOR, "li.scorm")
            to_process = []
            for item in scorm_items:
                content = item.text
                is_done = "Done" in content
                is_todo = "To do" in content or not is_done
                
                if settings.replay_done or is_todo:
                    try:
                        anchor = item.find_element(By.CSS_SELECTOR, "a.aalink")
                        href = anchor.get_attribute("href")
                        name = (anchor.text or anchor.get_attribute("title") or "Unknown").replace("SCORM package", "").strip()
                        if href not in seen_in_run:
                            to_process.append((name, href))
                    except: pass
            
            if not to_process:
                print(f"    - Module CID {cid}: No pending videos.")
                break
            
            # Process strictly one per page refresh to maintain state sync
            target_name, target_url = to_process[0]
            try:
                complete_scorm_video(driver, target_url, target_name)
            except Exception as e:
                print(f"    - [ERROR] Video interaction failed: {e}")
                # If it's a connection error, bubble it up to main() to relaunch
                if "connection" in str(e).lower() or "session id" in str(e).lower():
                    raise e
            
            seen_in_run.add(target_url)
            time.sleep(2)

    print(f"  - Session for {uid} finished.")
    driver.delete_all_cookies()

def main():
    print("="*60)
    print("🚀 NIA-AutoWatch-Bot v2.0 - STARTING")
    print("="*60)
    
    if not os.path.exists(settings.users_file):
        print(f"[ERROR] {settings.users_file} not found. cannot start.")
        return

    users = []
    with open(settings.users_file, mode='r', encoding='utf-8') as f:
        users = list(csv.DictReader(f))

    driver = get_driver()
    try:
        for user_data in users:
            # Self-healing: verify driver connection
            try:
                driver.title
            except:
                print("[INFO] Re-initializing lost browser connection...")
                driver = get_driver()

            try:
                process_user(driver, user_data)
            except Exception as fatal_user_e:
                print(f"[FATAL ERROR] User {user_data['Login_id']} session aborted: {fatal_user_e}")
                # Relaunch driver to ensure clean state for next user
                try: driver.quit()
                except: pass
                driver = get_driver()

    finally:
        try: driver.quit()
        except: pass
        print("\n" + "="*60)
        print("🎉 AUTOMATION FINISHED - ALL USERS PROCESSED")
        print("="*60)

if __name__ == "__main__":
    main()
