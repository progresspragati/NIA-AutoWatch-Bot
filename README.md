# NIA-AutoWatch-Bot 🚀

**A professional automation tool to complete SCORM video lessons on the NIA training portal.**  
Built with Python and Selenium, designed for reliability, speed, and ease of use.

---

## 🌟 Features for Developers

- 📂 **Structured Architecture**: Clean separation of source code, configuration, and data.
- ⚡ **Turbo Mode**: Fast-forward videos to 99% completion instantly.
- 👯 **Parallel Processing**: Multi-threaded support for processing multiple accounts or videos at once.
- 🧪 **Test Suite**: Comprehensive unit and integration tests (10+ tests) to verify logic safely.
- 🛡️ **Self-Healing**: Automatically detects browser crashes or connection losses and resumes.

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

### Advanced CLI Overrides

You can override any XML setting directly from the command line:

```powershell
# Run in background (hidden) with 3 simultaneous users
.\.venv\Scripts\python.exe src\course_completer.py --headless --sim-users 3
```

---

## 🧪 Testing & Quality Assurance

We take code quality seriously. Before contributing or running on a live account, run the test suite:

```powershell
# Run all logic and integration tests
.\.venv\Scripts\python.exe tests\test_settings.py
.\.venv\Scripts\python.exe tests\test_simulation.py
.\.venv\Scripts\python.exe tests\test_video_logic.py
.\.venv\Scripts\python.exe tests\test_cli.py
.\.venv\Scripts\python.exe tests\test_parallel.py
```

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

---

_Maintained with ❤️ for the NIA community._
