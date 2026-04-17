import sqlite3

from config import DB_PATH
from src.logger import get_logger

log = get_logger("db")


def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    log.info("Initializing database at %s", DB_PATH)
    conn = get_connection()
    c = conn.cursor()
    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            department TEXT,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Attendance table
    c.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            date TEXT NOT NULL,
            in_time TEXT,
            out_time TEXT,
            status TEXT,
            FOREIGN KEY(student_id) REFERENCES users(student_id)
        )
    ''')

    # Settings table for persistent app preferences
    c.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY NOT NULL,
            value TEXT NOT NULL
        )
    ''')
    # Insert defaults only if they don't already exist
    c.executemany(
        "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
        [("sound_enabled", "true"), ("sound_volume", "60"), ("sound_type", "Default Chime")]
    )
    conn.commit()
    conn.close()

    # Bootstrap admin credentials table (bcrypt-hashed)
    from src.auth import init_admin_table
    init_admin_table()
    log.info("Database initialization complete.")

def add_user(student_id, name, department):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (student_id, name, department) VALUES (?, ?, ?)", 
                  (student_id, name, department))
        conn.commit()
        log.info("Registered user: %s (%s)", name, student_id)
        return True
    except sqlite3.IntegrityError:
        log.warning("Duplicate user ID rejected: %s", student_id)
        return False
    finally:
        conn.close()

def get_users():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    conn.close()
    return users

def mark_attendance(student_id, date_str, time_str):
    """
    Mark attendance for a given student ID.
    If no entry for the date exists, create one with `in_time`.
    If an entry exists, update the `out_time`.
    """
    conn = get_connection()
    c = conn.cursor()
    
    c.execute("SELECT * FROM attendance WHERE student_id = ? AND date = ?", (student_id, date_str))
    record = c.fetchone()
    
    if not record:
        # No entry, mark in_time
        c.execute("INSERT INTO attendance (student_id, date, in_time, status) VALUES (?, ?, ?, ?)",
                  (student_id, date_str, time_str, 'Present'))
        action = "IN"
    else:
        # Entry exists, update out_time
        c.execute("UPDATE attendance SET out_time = ? WHERE student_id = ? AND date = ?",
                  (time_str, student_id, date_str))
        action = "OUT"
        
    conn.commit()
    conn.close()
    log.info("Attendance %s: student=%s date=%s time=%s", action, student_id, date_str, time_str)
    return action

def get_attendance_by_date(date_str):
    conn = get_connection()
    c = conn.cursor()
    query = '''
    SELECT users.name, users.student_id, attendance.date, attendance.in_time, attendance.out_time, attendance.status
    FROM attendance
    JOIN users ON users.student_id = attendance.student_id
    '''
    if date_str:
        query += " WHERE attendance.date = ?"
        c.execute(query, (date_str,))
    else:
        c.execute(query)
    
    records = c.fetchall()
    conn.close()
    return records

def get_setting(key: str, default: str = "") -> str:
    """Retrieve a setting value by key."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else default

def set_setting(key: str, value: str):
    """Update or insert a setting value."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()
