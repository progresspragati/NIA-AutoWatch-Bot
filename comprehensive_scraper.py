import csv
import time
import os
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURATION ---
URL_LOGIN = "https://onlinetraining.niapune.org.in/index.php"
URL_SUMMARY = "https://onlinetraining.niapune.org.in/learner/learnerSummaryReport.php"
URL_COURSES = "https://onlinetraining.niapune.org.in/learner/learnerCourses.php"

USERS_FILE = "users.csv"
OUTPUT_DIR = "course_info"

def get_driver():
    """Builds and returns a Chrome WebDriver instance."""
    chrome_options = Options()
    # chrome_options.add_argument("--headless") # Uncomment for headless mode
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--log-level=3") # Suppress logs
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def read_users():
    """Reads credentials from users.csv."""
    users = []
    if not os.path.exists(USERS_FILE):
        print(f"[ERROR] Required file {USERS_FILE} not found.")
        return []
        
    try:
        with open(USERS_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                users.append(row)
    except Exception as e:
        print(f"[ERROR] Could not read {USERS_FILE}: {e}")
    return users

def scrape_user_data(driver, user):
    """Processes a single user: login, duration scraping, and course hierarchy."""
    uid = user['Login_id']
    pwd = user['Password']
    wait = WebDriverWait(driver, 20)
    user_data = []
    duration_map = {}

    try:
        # 1. Login
        print(f"\n[USER] {uid} - Logging in...")
        driver.get(URL_LOGIN)
        wait.until(EC.presence_of_element_located((By.ID, "username"))).clear()
        driver.find_element(By.ID, "username").send_keys(uid)
        driver.find_element(By.ID, "password").clear()
        driver.find_element(By.ID, "password").send_keys(pwd)
        driver.find_element(By.ID, "submitform").click()

        # Check if login success
        time.sleep(2)
        if "login" in driver.current_url.lower():
            print(f"  - [ERROR] Login failed for {uid}. Verify credentials.")
            return []

        # 2. Extract Duration Summary
        # This page shows how long each lesson was watched.
        print(f"  - Scraping duration summary...")
        driver.get(URL_SUMMARY)
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))
            time.sleep(2) # Stabilize table
            rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 3:
                    lesson_name = cells[1].text.strip().lower()
                    duration = cells[2].text.strip()
                    duration_map[lesson_name] = duration
        except:
            print("  - [INFO] No duration data found on summary page.")

        # 3. Detect Enrolled Module from Header
        enrolled_module = "Unknown Module"
        try:
            # Header typically shows "Module Enrolled: Direct Life Insurance"
            enrolled_module = driver.find_element(By.CSS_SELECTOR, ".small-font b:nth-of-type(2)").text.strip()
            print(f"  - Enrolled Module: {enrolled_module}")
        except:
            print("  - [WARN] Module name not found in header.")

        # 4. Detect All Enrolled Course IDs (CIDs)
        print(f"  - Detecting course IDs...")
        driver.get(URL_COURSES)
        time.sleep(3)
        
        launch_links = driver.find_elements(By.XPATH, "//a[contains(@href, 'cid=')]")
        course_ids = []
        for link in launch_links:
            href = link.get_attribute("href")
            cid = href.split("cid=")[-1]
            if cid.isdigit() and cid not in course_ids:
                course_ids.append(cid)
        
        print(f"  - Found {len(course_ids)} course(s): {course_ids}")

        # 5. Scrape Structure for Each CID
        for cid in course_ids:
            print(f"  - Collecting CID {cid} hierarchy & links...")
            driver.get(f"https://onlinetraining.niapune.org.in/nlms/course/view.php?id={cid}")
            time.sleep(4)

            try:
                # Expand any collapsed sections
                expands = driver.find_elements(By.XPATH, "//a[contains(text(), 'Expand all')]")
                for exp in expands: exp.click()
            except: pass

            # Attempt to update module title from the section page header
            course_title_actual = enrolled_module
            try:
                header_els = driver.find_elements(By.CSS_SELECTOR, "h1, .page-header-headings")
                if header_els: course_title_actual = header_els[0].text.strip()
            except: pass

            seen_activities = set()
            sections = driver.find_elements(By.CSS_SELECTOR, "li.section, .course-section")
            for section in sections:
                try:
                    section_name = section.find_element(By.CSS_SELECTOR, "h3, .sectionname").text.strip()
                except:
                    section_name = "General"

                # Use precise selector to avoid double-scraping nested elements
                activities = section.find_elements(By.CSS_SELECTOR, ".activity:not(.activity-item)")
                if not activities: activities = section.find_elements(By.CSS_SELECTOR, ".activity-item")

                for act in activities:
                    try:
                        anchor = act.find_element(By.CSS_SELECTOR, "a.stretched-link, a.aalink, a")
                        raw_name = anchor.text.strip()
                        lesson_name = raw_name.replace("SCORM package", "").replace("SCORM PACKAGE", "").strip()
                        if not lesson_name: continue
                        
                        link = anchor.get_attribute("href")
                        
                        # Deduplication to ensure one entry per activity
                        dedup_key = (course_title_actual, section_name, lesson_name, link)
                        if dedup_key in seen_activities: continue
                        seen_activities.add(dedup_key)
                        
                        # Status extraction
                        badges = act.find_elements(By.CSS_SELECTOR, ".badge, .completion-info, .availabilityinfo")
                        status_text = " | ".join([b.text.strip() for b in badges if b.text.strip()]) or "To do"

                        # Correlate duration
                        watch_time = "00 : 00"
                        lname_lower = lesson_name.lower()
                        for key, val in duration_map.items():
                            if lname_lower in key or key in lname_lower:
                                watch_time = val
                                break

                        user_data.append({
                            "User_ID": uid,
                            "Module": course_title_actual,
                            "Subject": section_name,
                            "Topic": section_name,
                            "Lesson_Name": lesson_name,
                            "Status": status_text,
                            "Watch_Time": watch_time,
                            "Lesson_Link": link
                        })
                    except: continue

        print(f"  - [SUCCESS] Finalized {len(user_data)} unique records.")
        driver.delete_all_cookies()

    except Exception as e:
        print(f"  - [ERROR] Processing error: {e}")
    
    return user_data

def main():
    """Main execution entry point."""
    users = read_users()
    if not users: return

    driver = get_driver()
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"[INFO] Created results directory: {OUTPUT_DIR}")

    try:
        for user in users:
            uid = user['Login_id']
            results = scrape_user_data(driver, user)
            
            if results:
                user_file = os.path.join(OUTPUT_DIR, f"{uid}_course_info.csv")
                print(f"[INFO] Saving results to {user_file}")
                keys = results[0].keys()
                with open(user_file, 'w', newline='', encoding='utf-8') as f:
                    dict_writer = csv.DictWriter(f, fieldnames=keys)
                    dict_writer.writeheader()
                    dict_writer.writerows(results)
    finally:
        driver.quit()
        print("\n" + "="*40)
        print("SCRAPING COMPLETED: Check the 'course_info' folder.")
        print("="*40)

if __name__ == "__main__":
    main()
