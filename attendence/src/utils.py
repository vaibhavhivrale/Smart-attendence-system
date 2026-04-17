import os
import pandas as pd
from datetime import datetime

from config import DATA_DIR, MODELS_DIR, LOGS_DIR

# Re-export for backward compat
DATASET_DIR = DATA_DIR
ENCODINGS_DIR = MODELS_DIR
ENCODINGS_FILE = os.path.join(MODELS_DIR, 'encodings.pkl')

def ensure_dirs():
    for d in [DATA_DIR, MODELS_DIR, LOGS_DIR, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')]:
        os.makedirs(d, exist_ok=True)

def update_csv_log(name, student_id, date_str, time_str, action):
    """
    Updates the daily CSV spreadsheet with in_time and out_time.
    """
    csv_file = os.path.join(LOGS_DIR, f"Attendance_{date_str}.csv")
    
    # Define columns with Total Time added
    cols = ['Date', 'Student ID', 'Name', 'In-Time', 'Out-Time', 'Total Time', 'Status']
    
    if os.path.exists(csv_file):
        df = pd.read_csv(csv_file)
    else:
        df = pd.DataFrame(columns=cols)
        
    # Check if student already in today's log
    idx = df[df['Student ID'] == str(student_id)].index
    
    if len(idx) == 0:
        # Not in log, create new row for IN
        new_row = pd.DataFrame([{
            'Date': date_str,
            'Student ID': str(student_id),
            'Name': name,
            'In-Time': time_str,
            'Out-Time': '',
            'Total Time': 'In Progress',
            'Status': 'Present (In Progress)'
        }])
        df = pd.concat([df, new_row], ignore_index=True)
    else:
        # Already logged IN, update OUT time if action is OUT
        if action == "OUT":
            df.loc[idx, 'Out-Time'] = time_str
            # Calculate Total Time safely here for CSV log directly
            in_t = df.loc[idx, 'In-Time'].values[0]
            try:
                t1 = datetime.strptime(str(in_t).strip(), "%H:%M:%S")
                t2 = datetime.strptime(str(time_str).strip(), "%H:%M:%S")
                diff = t2 - t1
                hours_diff = diff.total_seconds() / 3600.0
                h = int(diff.total_seconds() // 3600)
                m = int((diff.total_seconds() % 3600) // 60)
                df.loc[idx, 'Total Time'] = f"{h:02d}:{m:02d}"
                df.loc[idx, 'Status'] = "Present" if hours_diff >= 4.0 else "Half Day"
            except Exception:
                df.loc[idx, 'Total Time'] = "--"
            
    df.to_csv(csv_file, index=False)

def process_attendance_with_status(df_attendance, df_users, target_date_str):
    """
    Computes 'Total Time' and automatic 'Status' for all registered users on a target_date_str.
    Merges df_attendance and df_users. Evaluates Absent vs Half Day vs Present.
    """
    # 1. Filter attendance for that date
    today_att = df_attendance[df_attendance['Date'] == target_date_str].copy()
    
    # 2. Merge all users against today's attendance to catch Absents
    merged = pd.merge(df_users, today_att, on="Student ID", how="left")
    merged['Date'] = target_date_str
    
    def compute_row(row):
        in_t = row.get('In-Time')
        out_t = row.get('Out-Time')
        
        # Absent case
        if pd.isna(in_t) or str(in_t).strip() == '':
            return pd.Series([None, None, "--", "Absent"])
            
        # In Progress case
        if pd.isna(out_t) or str(out_t).strip() == '':
            return pd.Series([in_t, None, "In Progress", "Present (In Progress)"])
            
        # Time calc
        try:
            fmt = "%H:%M:%S"
            t1 = datetime.strptime(str(in_t).strip(), fmt)
            t2 = datetime.strptime(str(out_t).strip(), fmt)
            diff = t2 - t1
            hours_diff = diff.total_seconds() / 3600.0
            
            h = int(diff.total_seconds() // 3600)
            m = int((diff.total_seconds() % 3600) // 60)
            total_time_str = f"{h:02d}:{m:02d}"
            
            # Note: Negative diffs logic
            if hours_diff < 0:
                return pd.Series([in_t, out_t, "--", "Error: Out < In"])

            if hours_diff >= 4.0:
                status = "Present"
            else:
                status = "Half Day"
                
            return pd.Series([in_t, out_t, total_time_str, status])
            
        except Exception:
            return pd.Series([in_t, out_t, "--", "Error Parsing Time"])

    # Safety checks
    if len(merged) == 0:
        return pd.DataFrame(columns=["Name", "Student ID", "Date", "In-Time", "Out-Time", "Total Time", "Status"])

    res = merged.apply(compute_row, axis=1)
    res.columns = ['In-Time_new', 'Out-Time_new', 'Total Time', 'Status_new']
    
    merged['In-Time'] = res['In-Time_new']
    merged['Out-Time'] = res['Out-Time_new']
    merged['Total Time'] = res['Total Time']
    merged['Status'] = res['Status_new']
    
    final_cols = ["Name", "Student ID", "Date", "In-Time", "Out-Time", "Total Time", "Status"]
    
    for col in final_cols:
        if col not in merged.columns:
            merged[col] = ''
            
    return merged[final_cols].fillna('')
