"""
auth.py — Secure admin authentication with bcrypt hashing,
rate limiting, and input sanitization.
"""
import bcrypt
import sqlite3
import time
import re

from config import DB_PATH, MAX_LOGIN_ATTEMPTS, LOCKOUT_WINDOW
from src.logger import get_logger

log = get_logger("auth")

# ─── Rate limiter state (in-memory per process) ─────────────────────────────
_login_attempts: dict[str, list[tuple[float, bool]]] = {}
ATTEMPT_CLEANUP = 600  # seconds — prune old entries


def _get_connection():
    return sqlite3.connect(DB_PATH)


# ─── Database Bootstrap ─────────────────────────────────────────────────────

def init_admin_table():
    """
    Create the admins table and seed a default admin if none exists.
    Default: username='admin', password='admin' (bcrypt hashed).
    """
    conn = _get_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()

    # Seed default admin only if the table is empty
    c.execute("SELECT COUNT(*) FROM admins")
    count = c.fetchone()[0]
    if count == 0:
        hashed = hash_password("admin")
        c.execute(
            "INSERT INTO admins (username, password_hash) VALUES (?, ?)",
            ("admin", hashed),
        )
        conn.commit()
        log.info("Default admin account created (username: admin).")

    conn.close()


# ─── Password Hashing ───────────────────────────────────────────────────────

def hash_password(plain_password: str) -> str:
    """Hash a password with bcrypt (12 rounds). Returns utf-8 string."""
    return bcrypt.hashpw(
        plain_password.encode("utf-8"),
        bcrypt.gensalt(rounds=12),
    ).decode("utf-8")


def check_password(plain_password: str, hashed: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed.encode("utf-8"),
        )
    except Exception:
        return False


# ─── Input Sanitization ─────────────────────────────────────────────────────

def sanitize_input(value: str) -> str:
    """
    Strip whitespace and reject obviously dangerous inputs.
    Prevents basic injection via the UI layer.
    """
    value = value.strip()
    if re.search(r"[;'\"\-\-]", value):
        return ""
    return value[:128]


# ─── Rate Limiting ──────────────────────────────────────────────────────────

def _cleanup_old_attempts():
    """Remove entries older than ATTEMPT_CLEANUP seconds."""
    cutoff = time.time() - ATTEMPT_CLEANUP
    for key in list(_login_attempts.keys()):
        _login_attempts[key] = [
            (ts, ok) for ts, ok in _login_attempts[key] if ts > cutoff
        ]
        if not _login_attempts[key]:
            del _login_attempts[key]


def is_rate_limited(identifier: str) -> tuple[bool, int]:
    """
    Check if an identifier (username / IP) is currently locked out.
    Returns (is_locked, seconds_remaining).
    """
    _cleanup_old_attempts()
    attempts = _login_attempts.get(identifier, [])

    window_start = time.time() - LOCKOUT_WINDOW
    recent_failures = [ts for ts, ok in attempts if ts > window_start and not ok]

    if len(recent_failures) >= MAX_LOGIN_ATTEMPTS:
        oldest_failure = min(recent_failures)
        remaining = int(LOCKOUT_WINDOW - (time.time() - oldest_failure))
        return True, max(remaining, 1)

    return False, 0


def record_attempt(identifier: str, success: bool):
    """Record a login attempt for rate-limiting purposes."""
    if identifier not in _login_attempts:
        _login_attempts[identifier] = []
    _login_attempts[identifier].append((time.time(), success))


# ─── Core Authentication ────────────────────────────────────────────────────

def verify_admin(username: str, password: str) -> tuple[bool, str]:
    """
    Authenticate an admin user.
    Returns (success, message). Generic error on failure (no info leak).
    """
    username = sanitize_input(username)
    password = password.strip()[:128]

    if not username or not password:
        return False, "Please enter both username and password."

    locked, remaining = is_rate_limited(username)
    if locked:
        log.warning("Rate limit hit for user '%s'. Locked for %ds.", username, remaining)
        return False, f"Too many failed attempts. Try again in {remaining}s."

    conn = _get_connection()
    c = conn.cursor()
    c.execute("SELECT password_hash FROM admins WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()

    if row and check_password(password, row[0]):
        record_attempt(username, True)
        log.info("Admin login successful: %s", username)
        return True, "OK"
    else:
        record_attempt(username, False)
        log.warning("Failed login attempt for: %s", username)
        return False, "Invalid username or password."


# ─── Admin Management ───────────────────────────────────────────────────────

def change_admin_password(username: str, old_password: str, new_password: str) -> tuple[bool, str]:
    """Allow an authenticated admin to change their password."""
    ok, msg = verify_admin(username, old_password)
    if not ok:
        return False, "Current password is incorrect."

    if len(new_password) < 6:
        return False, "New password must be at least 6 characters."

    new_hash = hash_password(new_password)
    conn = _get_connection()
    c = conn.cursor()
    c.execute("UPDATE admins SET password_hash = ? WHERE username = ?", (new_hash, username))
    conn.commit()
    conn.close()
    log.info("Password changed for admin: %s", username)
    return True, "Password updated successfully."
