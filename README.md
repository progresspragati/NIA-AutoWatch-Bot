# NIA-AutoWatch-Bot 🚀

Automate the completion of SCORM video lessons on the NIA training portal.

## 📋 Quick Setup

1.  **Add Users**: Open `config/users.csv` and add your login IDs and passwords.
2.  **Configure**: Open `config/settings.xml` to change options (Mute, FastForward, etc.).
3.  **Install dependencies**: `pip install -r requirements.txt`

## 🚀 How to Run

Open your terminal in this folder and run:

```bash
python src/course_completer.py
```

## ⚙️ Settings (config/settings.xml)

- **Headless**: Set to `true` to run the browser in the background (hidden).
- **FastForward**: Set to `true` to skip to the end of videos instantly.
- **Mute**: Set to `true` to keep the automation silent.
- **ReplayDone**: Set to `true` to re-watch videos that are already marked "Done".
- **CourseID**: Put a specific number (e.g. `16`) to only process one course.

## 🛠️ Troubleshooting

- **Browser Crashes**: The script will automatically try to relaunch and continue.
- **Stay on one window**: Do not run the script in two terminals at the same time.
- **Pop-ups**: Ensure your browser/system isn't blocking the video pop-up windows.
