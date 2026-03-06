# NIA-AutoWatch-Bot 🚀

**A professional automation tool to complete SCORM video lessons on the NIA training portal.**  
Built with Python and Selenium, designed for reliability, speed, and ease of use.

---

## 🌟 Features for Developers

- 📂 **Structured Architecture**: Clean separation of source code, configuration, and data.
- ⚡ **Turbo Mode**: Fast-forward videos to 99% completion instantly.
- 👯 **Parallel Processing**: Multi-threaded support for processing multiple accounts or videos at once.
- 🧪 **Test Suite**: Comprehensive unit and integration tests (11 tests) to verify logic safely.
- 🛡️ **Self-Healing**: Automatically detects browser crashes or connection losses and resumes.
- 🛑 **Graceful Shutdown**: Hit `Ctrl+C` to safely terminate the script and close all browser windows instantly.
- 📊 **Smart Dashboard Scanning**: Extracts "Remaining Hours" directly from the dashboard for real-time progress tracking.
- 🔍 **E2E Integration**: Includes a simulated portal environment to test the full login & navigation flow.

---

## 🛠️ Step-by-Step Setup (For Beginners)

### 1. Prerequisites

Ensure you have **Python 3.8 or higher** installed on your Windows machine. You can check by running `python --version` in your terminal.

### 2. Environment Setup

Create and activate a virtual environment to keep dependencies isolated:

```powershell
# Create the virtual environment
python -m venv .venv

# Activate it
.\.venv\Scripts\Activate.ps1

# Install required packages
pip install -r requirements.txt
```

### 3. Configuration

- **Users**: Open `config/users.csv` and add your account details.
- **Settings**: Open `config/settings.xml` to customize the behavior (Hide browser, Audio, Speed).

---

## 🚀 Usage

### Simple Run

Execute the bot using the dedicated environment python:

```powershell
.\.venv\Scripts\python.exe src\course_completer.py
```

### Graceful Exit

If you need to stop the automation early, simply press **Ctrl+C**. The script will:

1.  Detect the interrupt.
2.  Stop all active video threads.
3.  Automatically close all open browser windows for you.

### Advanced CLI Overrides

You can override any XML setting directly from the command line:

```powershell
# Run in background (hidden) with 3 simultaneous users
.\.venv\Scripts\python.exe src\course_completer.py --headless --sim-users 3
```

---

## 🧪 Testing & Quality Assurance

We take code quality seriously. To run the full test suite (including the new browser-based integration tests):

```powershell
# Run all tests automatically
.\.venv\Scripts\python.exe -m unittest discover tests
```

Individual test files:

- `tests/test_integration_portal.py`: Verifies full login and dashboard extraction.
- `tests/test_simulation.py`: Core logic and identity discovery.
- `tests/test_video_logic.py`: SCORM player and API interaction.
- `tests/test_settings.py`: Configuration and XML merging.
- `tests/test_parallel.py`: Multi-threaded user handling.

---

## 📂 Project Structure

```text
Automation_watch/
├── src/           # Core Python source code
├── config/        # Global settings and credentials
├── tests/         # Unit and integration tests
├── doc/           # Detailed user & training guides
├── data/          # Scraped course metadata
└── logs/          # Runtime debug logs
```

---

## ⚙️ Key Settings (`config/settings.xml`)

| Tag               | Action                                                     |
| :---------------- | :--------------------------------------------------------- |
| `ScanOnlyMode`    | Set `true` to just check progress without watching videos. |
| `FastForward`     | Skips to the end of videos instantly.                      |
| `HideBrowser`     | Set to `true` to hide the Chrome window.                   |
| `ConcurrentUsers` | Number of accounts to process at once.                     |

---

## 🛠️ Troubleshooting

- **Missing Module**: Ensure you are running with `.\.venv\Scripts\python.exe`.
- **Browser Error**: Update your Google Chrome to the latest version.
- **Login Failed**: Verify your credentials in `config/users.csv`.
