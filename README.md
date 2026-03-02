# NIA-AutoWatch-Bot 🚀

Automate the completion of SCORM video lessons on the NIA training portal with support for parallel processing and fast-forwarding.

## 📁 Project Architecture

The project follows a clean Source-Config-Data architecture:

- **`src/`**: Main automation scripts.
- **`config/`**: Configuration files (`settings.xml`, `users.csv`).
- **`data/`**: Scraped course information and session data.
- **`doc/`**: Detailed documentation and user guides.
- **`logs/`**: Runtime logs for debugging.
- **`tests/`**: Simulation and unit tests.

---

## 📋 Quick Setup

1.  **Add Users**: Open `config/users.csv` and add your login IDs and passwords.
2.  **Configure**: Open `config/settings.xml` to change options (Mute, FastForward, etc.).
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## 🚀 How to Run

Open your terminal in the root folder and run:

```powershell
.\.venv\Scripts\python.exe src\course_completer.py
```

---

## ⚙️ Settings (`config/settings.xml`)

| Setting                | Description                                          | Recommended               |
| :--------------------- | :--------------------------------------------------- | :------------------------ |
| **Headless**           | Set to `true` to run browser in background (hidden). | `false` (for visibility)  |
| **FastForward**        | Instantly skip to the end of videos.                 | `true`                    |
| **Mute**               | Keeps the automation silent.                         | `true`                    |
| **ReplayDone**         | Re-watch videos already marked "Done".               | `false`                   |
| **SimultaneousUsers**  | Process multiple user accounts at once (1-5).        | `1` (increases RAM usage) |
| **SimultaneousVideos** | Play multiple videos PER USER at once (1-10).        | `1`                       |
| **InfoOnly**           | Only scan and show info, skip video playback.        | `false`                   |

---

## 🧪 Testing the Bot (Safe Mode)

Verify the bot logic without logging into the real portal:

1.  **Activate Virtual Environment**:
    ```powershell
    .\.venv\Scripts\Activate.ps1
    ```
2.  **Run Simulation Tests**:
    ```powershell
    python tests/test_simulation.py
    ```

---

## 🛠️ Troubleshooting

- **Browser Crashes**: The script automatically relaunch and continues.
- **Duplicate Instances**: Do not run the script in two terminals for the same user.
- **Pop-ups**: Ensure your browser/system isn't blocking the video pop-up windows.
- **Connection Closed**: If you see `WinError 10054`, it's usually a temporary portal instability; the bot will retry.

---

_Developed for professional NIA training automation._
