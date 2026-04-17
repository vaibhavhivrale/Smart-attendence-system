"""
config.py — Centralized configuration for Smart Attendance System.

All paths, constants, and tunables in one place.
Override any value via environment variables (or a .env file).
"""
import os

# ─── Base Directory ──────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ─── Paths ───────────────────────────────────────────────────────────────────
DB_PATH        = os.environ.get("SAS_DB_PATH",        os.path.join(BASE_DIR, "attendance.db"))
DATA_DIR       = os.environ.get("SAS_DATA_DIR",       os.path.join(BASE_DIR, "data"))
MODELS_DIR     = os.environ.get("SAS_MODELS_DIR",     os.path.join(BASE_DIR, "models"))
LOGS_DIR       = os.environ.get("SAS_LOGS_DIR",       os.path.join(BASE_DIR, "attendance_logs"))
LOG_FILE       = os.environ.get("SAS_LOG_FILE",       os.path.join(BASE_DIR, "logs", "smart_attendance.log"))

# ─── Camera ──────────────────────────────────────────────────────────────────
CAMERA_INDICES = [int(i) for i in os.environ.get("SAS_CAMERA_INDICES", "0,1,2").split(",")]

# ─── Face Recognition ───────────────────────────────────────────────────────
FACE_TOLERANCE    = int(os.environ.get("SAS_FACE_TOLERANCE", "75"))
TRAINING_SAMPLES  = int(os.environ.get("SAS_TRAINING_SAMPLES", "30"))

# ─── Attendance ──────────────────────────────────────────────────────────────
SCAN_COOLDOWN     = int(os.environ.get("SAS_SCAN_COOLDOWN", "60"))  # seconds

# ─── Security ────────────────────────────────────────────────────────────────
MAX_LOGIN_ATTEMPTS = int(os.environ.get("SAS_MAX_LOGIN_ATTEMPTS", "5"))
LOCKOUT_WINDOW     = int(os.environ.get("SAS_LOCKOUT_WINDOW", "300"))  # seconds

# ─── App ─────────────────────────────────────────────────────────────────────
APP_TITLE = "Smart Attendance System"
APP_ICON  = "🎓"
APP_PORT  = int(os.environ.get("SAS_PORT", "8502"))
