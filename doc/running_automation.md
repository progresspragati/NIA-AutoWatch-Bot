# NIA Automation Scraper & Completer - Execution Guide

This document explains how to set up and run the NIA automation tools. The project now contains two main scripts:

1.  **`comprehensive_scraper.py`**: Extracts detailed course reports and lesson watch times into CSV files.
2.  **`course_completer.py`**: **NEW** - Automatically watches and completes all unfinished video lessons for you to unlock your certificate.

---

## 🛠️ Step 1: Set Up & Activate the Virtual Environment

To prevent conflicts with other Python projects, always run the scripts inside the virtual environment.

1.  **Open Terminal** in the project directory: `d:\personal\Pragati\Automation_watch`
2.  **Activate the Virtual Environment**:
    - **PowerShell**:
      ```powershell
      .\.venv\Scripts\Activate.ps1
      ```
    - **Command Prompt (CMD)**:
      ```cmd
      .venv\Scripts\activate
      ```

---

## 📦 Step 2: Install Dependencies (One-time)

If you are setting this up for the first time on a new PC, run:

```bash
pip install selenium webdriver-manager
```

---

## 🚀 Step 3: Run the Automation

Ensure your `users.csv` file has the correct login credentials (`Login_id`, `Password`).

### **Option A: Generate Reports Only**

To extract the lesson data and watch durations to CSV format without altering any completion statuses:

```bash
python comprehensive_scraper.py
```

_(Reports will be saved individually inside the `course_info` directory)._

### **Option B: Auto-Complete All Videos 🎓**

If you want to quickly finish all pending lessons and unlock the certificate, run the completer. This script bypasses the video playtime requirements via the SCORM API.

```bash
python course_completer.py
```

1.  The script will log in for each user in `users.csv`.
2.  It will detect all enrolled courses.
3.  It will enter every lesson marked as "To do".
4.  It immediately sends the `completed` API signal simulating that the video reached the end.
5.  It moves to the next lesson automatically.

---

## 📂 Project Directory Structure

| File / Folder              | Purpose                                                    |
| :------------------------- | :--------------------------------------------------------- |
| `comprehensive_scraper.py` | Generates final user reports (Read-only automation).       |
| `course_completer.py`      | Auto-completes unfinished SCORM videos (Write automation). |
| `users.csv`                | Input file for user credentials.                           |
| `course_info/`             | **(Output)** Contains CSV files for each user.             |
| `.venv/`                   | Python virtual environment.                                |
| `doc/`                     | Documentation and guides.                                  |

---

## 🔧 Troubleshooting

- **Completer Skipping Lessons**: If a lesson says `[FAIL] Could not auto-complete... Skipping for now`, it generally means the lesson does not support automated SCORM completion (e.g., standard Moodle Quizzes or PDFs). The script will skip it and move to the next item automatically.
- **Headless Mode**: To run either script silently without the browser window popping up, uncomment the following line in the python code:
  ```python
  # chrome_options.add_argument("--headless")
  ```
