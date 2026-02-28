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
