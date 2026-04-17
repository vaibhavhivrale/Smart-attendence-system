<h1 align="center">🎓 Smart Attendance System</h1>
<p align="center">
  <b>Real-Time Face Recognition Attendance with Admin Dashboard</b><br>
  <i>Python • OpenCV • Streamlit • SQLite • bcrypt</i>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue?logo=python" />
  <img src="https://img.shields.io/badge/streamlit-1.20+-red?logo=streamlit" />
  <img src="https://img.shields.io/badge/opencv-4.7+-green?logo=opencv" />
  <img src="https://img.shields.io/badge/license-MIT-yellow" />
</p>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **Face Recognition** | Real-time LBPH-based detection via webcam with confidence scoring |
| **In/Out Tracking** | Automatic check-in and check-out with 60s cooldown |
| **Admin Dashboard** | Attendance metrics, trend charts, department distribution, CSV export |
| **Secure Login** | bcrypt-hashed passwords, rate limiting (5 attempts → 5min lockout) |
| **Public Scanner** | Mark attendance without logging in — for kiosk/station deployment |
| **Sound System** | Configurable login chimes (3 types) generated in pure Python |
| **Analytics** | Plotly-powered attendance trends and department distribution charts |
| **Change Password** | Admin can update credentials from Settings panel |
| **Centralized Config** | All paths, constants, tunables in `config.py` with `.env` override |
| **Structured Logging** | Rotating log files in `logs/` — no more print statements |

---

## 📁 Project Structure

```text
smart-attendance/
├── app.py                  # Streamlit entry point
├── config.py               # Centralized configuration
├── requirements.txt        # Python dependencies
├── run.bat                 # One-click Windows launcher
├── build.bat               # PyInstaller build script
├── .env.example            # Environment variable template
├── .gitignore              # Git exclusions
│
├── src/                    # Application modules
│   ├── auth.py             # Admin auth (bcrypt, rate limiting)
│   ├── db.py               # SQLite schema & CRUD
│   ├── face_system.py      # Camera, capture, LBPH training, recognition
│   ├── analytics.py        # Plotly chart generators
│   ├── sounds.py           # Pure-Python WAV synthesizer
│   ├── ui_components.py    # Login card, CSS, animations
│   ├── utils.py            # CSV logging, attendance processing
│   └── logger.py           # Rotating file + console logger
│
├── data/                   # Captured face images (per user)
├── models/                 # Trained LBPH model + label map
├── attendance_logs/        # Daily CSV attendance exports
├── logs/                   # Application logs
└── attendance.db           # SQLite database (auto-created)
```

---

## 🚀 Quick Start (Windows)

### Prerequisites
- **Python 3.10+** — [Download](https://www.python.org/downloads/)
- **Webcam** — built-in or USB

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/smart-attendance.git
cd smart-attendance

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
streamlit run app.py
```

Or simply **double-click `run.bat`** — it handles venv activation automatically.

### Default Login
| Field | Value |
|-------|-------|
| Username | `admin` |
| Password | `admin` |

> ⚠️ **Change the default password immediately** via Settings → 🔐 Change Admin Password.

---

## 📖 Usage Guide

### 1. Register Users
1. Log in as Admin → **Register User**
2. Enter User ID + Full Name + Department
3. Camera captures 30 face samples automatically
4. LBPH model retrains with the new user

### 2. Mark Attendance
- **Admin**: Sidebar → Mark Attendance → Start Scanner
- **Public**: Login page → "📸 Mark Attendance (Public Access)"
- Face detected → green box → attendance logged automatically
- 60-second cooldown prevents duplicate scans

### 3. Dashboard
- View total registered, present, half-day, absent counts
- Interactive attendance trend chart
- Department distribution pie chart
- Download filtered CSV

### 4. Settings
- Toggle login sound effects (3 sound types)
- Adjust volume
- Change admin password

---

## ⚙️ Configuration

All settings live in [`config.py`](config.py). Override with environment variables or a `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `SAS_DB_PATH` | `attendance.db` | SQLite database file |
| `SAS_DATA_DIR` | `data` | Face training images |
| `SAS_MODELS_DIR` | `models` | Trained LBPH model |
| `SAS_CAMERA_INDICES` | `0,1,2` | Webcam indices to try |
| `SAS_FACE_TOLERANCE` | `75` | LBPH distance threshold |
| `SAS_SCAN_COOLDOWN` | `60` | Seconds between re-scans |
| `SAS_MAX_LOGIN_ATTEMPTS` | `5` | Failed logins before lockout |
| `SAS_LOCKOUT_WINDOW` | `300` | Lockout duration (seconds) |

See [`.env.example`](.env.example) for the full template.

---

## 🔒 Security

| Layer | Implementation |
|-------|----------------|
| Password Storage | bcrypt with 12 salt rounds |
| Login Protection | Rate limiting (5 attempts → 5-min lockout) |
| Error Messages | Generic "Invalid username or password" (no info leaks) |
| SQL Queries | Parameterized queries throughout |
| Input Sanitization | Pattern rejection + length capping |
| Session Management | Streamlit session state with secure logout |

---

## 🏗️ Building an Executable

```bash
# Run the build script
build.bat
```

This uses PyInstaller to create a standalone distribution in `dist/SmartAttendance/`. The output runs on Windows machines **without Python installed**.

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Streamlit + Custom CSS (Glassmorphism) |
| Backend | Python 3.10+ |
| Face Detection | OpenCV Haar Cascades |
| Face Recognition | LBPH (Local Binary Patterns Histograms) |
| Database | SQLite3 |
| Auth | bcrypt |
| Charts | Plotly Express |
| Audio | Pure Python WAV synthesis (wave, math, struct) |
| Logging | Python logging (RotatingFileHandler) |

---

## 📄 License

This project is open source under the [MIT License](LICENSE).

---

<p align="center">
  Built with ❤️ for real-world attendance automation
</p>
