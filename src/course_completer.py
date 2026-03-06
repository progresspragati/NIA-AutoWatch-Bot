import time
import os
import csv
import argparse
import concurrent.futures
import xml.etree.ElementTree as ET
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURATION (Structure Support) ---
# This allows the script to be run from root or from within the src/ folder
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR) if os.path.basename(SCRIPT_DIR) == "src" else SCRIPT_DIR

URL_LOGIN = "https://onlinetraining.niapune.org.in/index.php"
URL_COURSES = "https://onlinetraining.niapune.org.in/learner/learnerCourses.php"
URL_DASHBOARD = "https://onlinetraining.niapune.org.in/learner/learnerDashboard.php"

# Path to settings and user data
SETTINGS_FILE = os.path.join(PROJECT_ROOT, "config", "settings.xml")
DEFAULT_USERS_FILE = os.path.join(PROJECT_ROOT, "config", "users.csv")
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")

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
        self.simultaneous_videos = 1
        self.simultaneous_users = 1
        self.info_only = False
        self.users_file = DEFAULT_USERS_FILE

def get_settings(settings_file=SETTINGS_FILE):
    """Combines command line arguments and XML settings."""
    settings = Settings()

    # 1. Parse XML settings if file exists
    if os.path.exists(settings_file):
        try:
            tree = ET.parse(settings_file)
            root = tree.getroot()
            
            # Browser & System
            settings.headless = root.findtext("HideBrowser", "false").lower() == "true"
            settings.timeout = int(root.findtext("WaitTimeout", "15"))
            settings.max_retries = int(root.findtext("MaxCompletionChecks", "500"))
            
            # Automation Logic
            settings.fast_forward = root.findtext("FastForward", "true").lower() == "true"
            settings.replay_done = root.findtext("ProcessCompletedVideos", "false").lower() == "true"
            settings.mute = root.findtext("MuteAudio", "true").lower() == "true"
            
            # Mode
            settings.info_only = root.findtext("ScanOnlyMode", "false").lower() == "true"
            
            # Performance
            settings.simultaneous_videos = max(1, min(10, int(root.findtext("VideosPerUser", "1"))))
            settings.simultaneous_users = max(1, min(10, int(root.findtext("ConcurrentUsers", "1"))))
            
            # Files
            user_file_val = root.findtext("CredentialFile", "users.csv")
            # If the XML only gives a filename (no dir), assume it's in config/
            if not os.path.dirname(user_file_val):
                settings.users_file = os.path.join(PROJECT_ROOT, "config", user_file_val)
            else:
                settings.users_file = os.path.join(PROJECT_ROOT, user_file_val)
            
            print(f"[INFO] Loaded configuration from {settings_file}")
        except Exception as e:
            print(f"[WARN] Error parsing {settings_file}: {e}. Defaults used.")

    # 2. Parse command line arguments (priority overrides)
    parser = argparse.ArgumentParser(description="NIA-AutoWatch-Bot")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--timeout", type=int)
    parser.add_argument("--course-id", type=str)
    parser.add_argument("--max-retries", type=int)
    parser.add_argument("--no-fast-forward", action="store_true")
    parser.add_argument("--replay-done", action="store_true")
    parser.add_argument("--unmute", action="store_true", help="Enable audio even if XML mutes it")
    parser.add_argument("--simultaneous", type=int, help="Number of videos to run simultaneously PER USER (1-10)")
    parser.add_argument("--sim-users", type=int, help="Number of users to process at once (1-5)")
    parser.add_argument("--info-only", action="store_true", help="Only scan and show info, skip videos")
    parser.add_argument("--users-file", type=str)
    
    cli_args, unknown = parser.parse_known_args()

    if cli_args.headless: settings.headless = True
    if cli_args.timeout: settings.timeout = cli_args.timeout
    if cli_args.course_id: settings.course_id = cli_args.course_id
    if cli_args.max_retries: settings.max_retries = cli_args.max_retries
    if cli_args.no_fast_forward: settings.fast_forward = False
    if cli_args.replay_done: settings.replay_done = True
    if cli_args.unmute: settings.mute = False
    if cli_args.simultaneous: settings.simultaneous_videos = max(1, min(10, cli_args.simultaneous))
    if cli_args.sim_users: settings.simultaneous_users = max(1, min(10, cli_args.sim_users))
    if cli_args.info_only: settings.info_only = True
    if cli_args.users_file: settings.users_file = cli_args.users_file

    return settings

def get_driver(settings_obj):
    """Initializes a fresh Chrome WebDriver."""
    chrome_options = Options()
    if settings_obj.headless:
        chrome_options.add_argument("--headless")
    
    if settings_obj.mute:
        chrome_options.add_argument("--mute-audio")
        
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--log-level=3")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def complete_scorm_video(driver, settings_obj, lesson_url, lesson_name, uid="System"):
    """Handles a single video completion task."""
    main_window = driver.current_window_handle
    print(f"[{uid}]       - Processing: {lesson_name}")
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
            
            mode = "Fast-Forward" if settings_obj.fast_forward else "Natural Playback"
            print(f"[{uid}]       - Player Popup Active ({mode})...")
            
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
                for i in range(settings_obj.max_retries):
                    try:
                        # Defensive check
                        try:
                            _ = driver.window_handles
                        except:
                            print(f"[{uid}]       - [CRITICAL] Browser connection lost.")
                            return False

                        if len(driver.window_handles) < 2:
                            print(f"[{uid}]       - [ERROR] Popup window closed unexpectedly.")
                            break

                        driver.execute_script(script_core, settings_obj.fast_forward, settings_obj.mute)
                        
                        # Check API status
                        driver.switch_to.default_content()
                        is_done = driver.execute_script(api_check)
                        
                        if is_done:
                            should_close = True
                            if not settings_obj.fast_forward:
                                try:
                                    driver.switch_to.frame(iframe)
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
                                            print(f"[{uid}]       - Video status: {video_state}. Waiting...")
                                    elif video_state == 'no_video' and i < 10:
                                        should_close = False
                                        if i % 3 == 0: print(f"[{uid}]       - Waiting for video player to load...")
                                    driver.switch_to.default_content()
                                except: pass
                            
                            if should_close:
                                print(f"[{uid}]       - [SUCCESS] Module completed.")
                                driver.close()
                                driver.switch_to.window(main_window)
                                return True
                        
                        driver.switch_to.frame(iframe)
                    except KeyboardInterrupt:
                        print(f"[{uid}]       - [INFO] Interrupted by user. Cleaning up...")
                        raise
                    except Exception as loop_e:
                        pass
                    
                    time.sleep(5)

                # Final Cleanup
                try:
                    if len(driver.window_handles) > 1:
                        driver.switch_to.default_content()
                        driver.execute_script(JS_FIND_API + "var api=findAPI(window); if(api){api.LMSSetValue('cmi.core.lesson_status', 'completed'); api.LMSCommit('');}")
                        print(f"[{uid}]       - [INFO] Closing popup.")
                        driver.close()
                except: pass
            except Exception as player_e:
                print(f"      - [ERROR] Player interaction error: {player_e}")
            
            try:
                driver.switch_to.window(main_window)
            except: pass
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

def process_user(driver, settings_obj, user):
    """Processes all courses for a single user account."""
    uid, pwd = user['Login_id'], user['Password']
    wait = WebDriverWait(driver, settings_obj.timeout)
    
    try:
        # login
        driver.get(URL_LOGIN)
        wait.until(EC.presence_of_element_located((By.ID, "username"))).clear()
        driver.find_element(By.ID, "username").send_keys(uid)
        driver.find_element(By.ID, "password").clear()
        driver.find_element(By.ID, "password").send_keys(pwd)
        driver.find_element(By.ID, "submitform").click()
        time.sleep(3)

        # identity discovery
        user_display = uid
        module_info = "Unknown"
        remaining_hours = "Unknown"
        
        try:
            driver.get(URL_DASHBOARD)
            time.sleep(2)
            try:
                name_el = driver.find_element(By.XPATH, "//body//*[contains(translate(text(), 'WELCOME', 'welcome'), 'welcome')]")
                raw_text = name_el.text
                if "welcome" in raw_text.lower():
                    name_only = raw_text.lower().split("welcome")[-1].split("\n")[0].strip()
                    for p in raw_text.split("\n"):
                        if "welcome" in p.lower():
                            name_only = p.lower().split("welcome")[-1].strip().title()
                    user_display = f"{uid} [{name_only}]"
            except: pass
            
            try:
                rem_el = driver.find_element(By.XPATH, "//span[contains(text(), 'Remaining')]/following::span[@class='info-box-number'][1]")
                remaining_hours = rem_el.text.strip()
            except:
                try:
                    page_text = driver.find_element(By.TAG_NAME, "body").text
                    lines = page_text.split("\n")
                    for i, line in enumerate(lines):
                        if "Remaining (HH:MM)" in line:
                            for j in range(i+1, min(i+4, len(lines))):
                                potential_time = lines[j].strip()
                                if ":" in potential_time and any(char.isdigit() for char in potential_time):
                                    remaining_hours = potential_time
                                    break
                            if remaining_hours != "Unknown": break
                except: pass

            try:
                page_text = driver.find_element(By.TAG_NAME, "body").text
                for line in page_text.split("\n"):
                    if "Module Enrolled" in line:
                        module_info = line.split("Enrolled:")[-1].strip()
                    if "Registration Type" in line:
                        reg_type = line.split("Type:")[-1].strip()
                        if module_info != "Unknown": module_info += f" ({reg_type})"
                        else: module_info = reg_type
            except: pass
        except Exception as identity_e:
            if settings_obj.info_only: print(f"      - [DEBUG] Identity check failed: {identity_e}")

        final_header = f"[USER] {user_display}"
        if remaining_hours != "Unknown":
            final_header += f" [Remaining Hours : {remaining_hours}]"
        final_header += " - Starting Automation..."
        
        print(f"\n{final_header}")
        print(f"      > Module: {module_info}")
        course_list = []
        discovery_urls = [URL_COURSES, URL_DASHBOARD]
        
        for url in discovery_urls:
            driver.get(url)
            time.sleep(3)
            links = driver.find_elements(By.XPATH, "//a[contains(@href, 'cid=')]")
            for l in links:
                href = l.get_attribute("href")
                if "cid=" in href:
                    cid = href.split("cid=")[-1].split("&")[0]
                    if cid and cid.isdigit(): course_list.append(cid)
            if course_list: break

        course_list = list(set(course_list))
        if settings_obj.course_id:
            course_list = [c for c in course_list if c == settings_obj.course_id]

        print(f"[{uid}]   - Verified {len(course_list)} enrolled course(s).")

        for cid in course_list:
            course_url = f"https://onlinetraining.niapune.org.in/nlms/course/view.php?id={cid}"
            print(f"[{uid}]   [COURSE] Scanning Module CID {cid}...")
            seen_in_run = set()
            
            driver.get(course_url)
            time.sleep(4)
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
                if settings_obj.replay_done or is_todo:
                    try:
                        anchor = item.find_element(By.CSS_SELECTOR, "a.aalink")
                        href = anchor.get_attribute("href")
                        # Normalize URL: Keep only id and scoid
                        # Example: mod/scorm/view.php?id=1234&scoid=5678
                        base_url = href.split('?')[0]
                        params = href.split('?')[-1].split('&')
                        essential_params = [p for p in params if p.startswith('id=') or p.startswith('scoid=')]
                        norm_href = base_url + ('?' + '&'.join(essential_params) if essential_params else '')
                        
                        name = (anchor.text or anchor.get_attribute("title") or "Unknown").replace("SCORM package", "").strip()
                        to_process.append((name, href, norm_href))
                    except: pass
            
            if not to_process:
                print(f"[{uid}]     - Module CID {cid}: All videos already completed!")
                continue

            total_items = len(to_process)
            print(f"[{uid}]     - Found {total_items} items to verify/process for CID {cid}")

            if settings_obj.info_only:
                print(f"[{uid}]     - [INFO ONLY] Skipping playback.")
                continue

            batch_size = settings_obj.simultaneous_videos
            # Process strictly in batches once
            for i in range(0, total_items, batch_size):
                tasks = to_process[i : i + batch_size]
                
                if batch_size > 1:
                    print(f"[{uid}]     - [SIMULTANEOUS] Processing batch {i+1}-{min(i+batch_size, total_items)} of {total_items}...")
                    def run_parallel_task(task_info):
                        t_name, t_url, t_norm = task_info
                        item_idx = to_process.index(task_info) + 1
                        try:
                            t_driver = get_driver(settings_obj)
                            t_driver.get(URL_LOGIN)
                            t_driver.find_element(By.ID, "username").send_keys(uid)
                            t_driver.find_element(By.ID, "password").send_keys(pwd)
                            t_driver.find_element(By.ID, "submitform").click()
                            time.sleep(2)
                            complete_scorm_video(t_driver, settings_obj, t_url, f"[{item_idx}/{total_items}] {t_name}", uid)
                            t_driver.quit()
                        except Exception as e:
                            print(f"[{uid}]     - [ERROR] Parallel task failed for {t_name}: {e}")
                            try: t_driver.quit()
                            except: pass

                    with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as executor:
                        executor.map(run_parallel_task, tasks)
                else:
                    target_name, target_url, target_norm = tasks[0]
                    current_num = i + 1
                    try:
                        complete_scorm_video(driver, settings_obj, target_url, f"[{current_num}/{total_items}] {target_name}", uid)
                    except Exception as e:
                        print(f"[{uid}]     - [ERROR] Video interaction failed: {e}")
                        if "connection" in str(e).lower() or "session id" in str(e).lower(): raise e
                
                time.sleep(1)
            
            print(f"[{uid}]     - Module CID {cid}: Pass complete.")
    except KeyboardInterrupt:
        print(f"[{uid}]   - [INTERRUPTED] Stopping session for {uid}...")
        raise
    except Exception as e:
        print(f"[{uid}]   - [ERROR] Session failed: {e}")
        raise
    finally:
        print(f"[{uid}]   - Session for {uid} finished.")
        try: driver.delete_all_cookies()
        except: pass

def run_user_parallel(user_data, settings_obj):
    """Task for a single user thread."""
    driver = None
    try:
        driver = get_driver(settings_obj)
        process_user(driver, settings_obj, user_data)
    except Exception as fatal_user_e:
        print(f"[FATAL ERROR] User {user_data.get('Login_id', 'Unknown')} session aborted: {fatal_user_e}")
    finally:
        if driver:
            try: driver.quit()
            except: pass

def main():
    try:
        settings_obj = get_settings()
        print("="*60)
        print("🚀 NIA-AutoWatch-Bot v2.0 - STARTING")
        print("="*60)
        
        if not os.path.exists(settings_obj.users_file):
            print(f"[ERROR] {settings_obj.users_file} not found. Cannot start.")
            return

        if not os.path.exists(LOG_DIR): os.makedirs(LOG_DIR)

        users = []
        with open(settings_obj.users_file, mode='r', encoding='utf-8') as f:
            users = list(csv.DictReader(f))

        if settings_obj.simultaneous_users > 1:
            print(f"[INFO] Using Simultaneous User Threads: {settings_obj.simultaneous_users}")
            with concurrent.futures.ThreadPoolExecutor(max_workers=settings_obj.simultaneous_users) as executor:
                futures = [executor.submit(run_user_parallel, u, settings_obj) for u in users]
                try:
                    concurrent.futures.wait(futures)
                except KeyboardInterrupt:
                    print("\n[!] Ctrl+C detected. Shutting down threads...")
                    executor.shutdown(wait=False, cancel_futures=True)
                    raise
        else:
            driver = get_driver(settings_obj)
            try:
                for user_data in users:
                    try:
                        driver.title
                    except:
                        print("[INFO] Re-initializing lost browser connection...")
                        driver = get_driver(settings_obj)

                    try:
                        process_user(driver, settings_obj, user_data)
                    except KeyboardInterrupt:
                        raise
                    except Exception as fatal_user_e:
                        print(f"[FATAL ERROR] User {user_data['Login_id']} session aborted: {fatal_user_e}")
                        try: driver.quit()
                        except: pass
                        driver = get_driver(settings_obj)
            finally:
                if driver:
                    try: driver.quit()
                    except: pass

        print("\n" + "="*60)
        print("🎉 AUTOMATION FINISHED - ALL USERS PROCESSED")
        print("="*60)
    except KeyboardInterrupt:
        print("\n\n" + "!"*60)
        print("🛑 TERMINATED BY USER (Ctrl+C)")
        print("Closing all active browser windows...")
        print("!"*60 + "\n")
    except Exception as e:
        print(f"\n[CRITICAL ERROR] {e}")

if __name__ == "__main__":
    main()
