# NIA-AutoWatch-Bot 🚀

Automate the completion of SCORM video lessons on the NIA training portal.

## 📋 Quick Setup

1.  **Add Users**: Open `users.csv` and add your login IDs and passwords.
2.  **Configure**: Open `settings.xml` to change options (Mute, FastForward, etc.).

## 🚀 How to Run

Open your terminal in this folder and run:

```bash
python course_completer.py
```

## 🧪 Testing the Bot (Safe Mode)

Before starting a real run, you can run automated tests to make sure the robot is working correctly. These tests do not actually log into the real NIA portal and do not watch any videos.

1.  **Open your terminal.**
2.  **Activate your virtual environment:**
    ```powershell
    .\.venv\Scripts\Activate.ps1
    ```
3.  **Run the tests:**
    ```powershell
    python tests/test_settings.py
    python tests/test_simulation.py
    ```

## ⚙️ Settings (settings.xml)

- **Headless**: Set to `true` to run the browser in the background (hidden).
- **FastForward**: Set to `true` to skip to the end of videos instantly.
- **Mute**: Set to `true` to keep the automation silent.
- **ReplayDone**: Set to `true` to re-watch videos that are already marked "Done".
- **CourseID**: Put a specific number (e.g. `16`) to only process one course.

## 🛠️ Troubleshooting

- **Browser Crashes**: The script will automatically try to relaunch and continue.
- **Stay on one window**: Do not run the script in two terminals at the same time.
- **Pop-ups**: Ensure your browser/system isn't blocking the video pop-up windows.
