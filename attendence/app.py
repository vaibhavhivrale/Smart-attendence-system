import streamlit as st
from streamlit_option_menu import option_menu
import cv2
import pandas as pd
from datetime import datetime
import time

from config import APP_TITLE, APP_ICON, SCAN_COOLDOWN
from src.logger import get_logger
from src.db import init_db, add_user, get_users, mark_attendance, get_attendance_by_date, get_connection
from src.utils import ensure_dirs, update_csv_log, LOGS_DIR, process_attendance_with_status
from src.face_system import capture_training_images, generate_encodings, load_encodings, recognize_faces, get_camera
from src.ui_components import inject_custom_css, render_login_screen, render_camera_ui_wrapper, render_sound_settings
from src.analytics import render_attendance_trends, render_department_distribution

log = get_logger("app")

st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="wide")
log.info("%s starting up...", APP_TITLE)

# ── Global Premium CSS ───────────────────────────────────────────────────────
inject_custom_css()

# ── System Initialisation ────────────────────────────────────────────────────
ensure_dirs()
init_db()

# ── Session State Defaults ───────────────────────────────────────────────────
for key, default in [
    ("logged_in", False),
    ("role", None),
    ("admin_username", ""),
    ("login_loading", False),
    ("login_success", False),
    ("login_error", ""),
    ("public_mode", False),
    ("last_scanned", {}),
]:
    if key not in st.session_state:
        st.session_state[key] = default


def logout():
    for key in ["logged_in", "role", "admin_username", "login_loading", "login_success", "login_error", "public_mode"]:
        st.session_state.pop(key, None)
    st.rerun()


# ════════════════════════════════════════════════════════════════════════════
#  PUBLIC MODE  — Mark Attendance without login
# ════════════════════════════════════════════════════════════════════════════
if st.session_state.public_mode and not st.session_state.logged_in:
    # Minimal top bar
    col_logo, col_back = st.columns([5, 1])
    with col_logo:
        st.markdown(
            "<h3 style='margin:0; padding-top:0.5rem;'>🎓 Smart Attendance — Public Scanner</h3>",
            unsafe_allow_html=True,
        )
    with col_back:
        if st.button("← Back to Login", key="back_to_login"):
            st.session_state.public_mode = False
            st.rerun()

    st.markdown("---")

    # ── Attendance Scanner (same as admin version) ───────────────────────────
    st.title("Live Attendance Scanner")
    st.markdown("Ensure your face is clearly visible. Updates log automatically every 60-second cooldown.")

    col_cam, col_info = st.columns([2, 1])

    with col_info:
        st.info(
            """
            **Instructions**:
            1. Click **Start Scanner**.
            2. Look into the camera.
            3. Wait for your bounding box to turn green.
            """
        )
        run_camera = st.checkbox("Start Scanner", key="public_scanner_cb")
        status_msg = st.empty()

    if run_camera:
        recognizer, label_map = load_encodings()
        if recognizer is None:
            status_msg.error("No model encodings found. Please ask Admin to register users first.")
        else:
            users = get_users()
            id_to_name = {u[1]: u[2] for u in users}

            cap = get_camera()
            if cap is None:
                status_msg.error("Cannot access webcam. Please check permissions.")
                st.stop()

            render_camera_ui_wrapper()

            with col_cam:
                st.markdown('<div class="scanner-container">', unsafe_allow_html=True)
                camera_placeholder = st.empty()

                try:
                    while run_camera:
                        ret, frame = cap.read()
                        if not ret:
                            status_msg.error("Camera feed disconnected.")
                            break

                        frame, detected = recognize_faces(frame, recognizer, label_map)

                        current_time = datetime.now()
                        date_str = current_time.strftime("%Y-%m-%d")
                        time_str = current_time.strftime("%H:%M:%S")

                        for std_id in detected:
                            name = id_to_name.get(std_id, "Unknown")
                            last_time = st.session_state.last_scanned.get(std_id)

                            if std_id != "Unknown" and (
                                last_time is None
                                or (current_time - last_time).total_seconds() > SCAN_COOLDOWN
                            ):
                                st.session_state.last_scanned[std_id] = current_time
                                action = mark_attendance(std_id, date_str, time_str)
                                update_csv_log(name, std_id, date_str, time_str, action)
                                status_msg.success(
                                    f"✅ **{action}** marked for **{name}** at {time_str}"
                                )

                        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        camera_placeholder.image(img_rgb, channels="RGB", use_container_width=True)

                finally:
                    cap.release()
                    st.markdown("</div>", unsafe_allow_html=True)

    st.stop()  # Don't render anything else for public mode


# ════════════════════════════════════════════════════════════════════════════
#  LOGIN GATE  — Admin only
# ════════════════════════════════════════════════════════════════════════════
# Show login screen if not logged in OR if we're in the success animation state
if not st.session_state.logged_in or st.session_state.get("login_success", False):
    render_login_screen()
    st.stop()


# ════════════════════════════════════════════════════════════════════════════
#  ADMIN APP  — Full navigation
# ════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(
        f"<h3 style='text-align: center;'>👋 Welcome, {st.session_state.role}</h3>",
        unsafe_allow_html=True,
    )

    choice = option_menu(
        menu_title=None,
        options=["Dashboard", "Register User", "Mark Attendance", "Settings", "Log Out"],
        icons=["house", "person-plus", "camera-video", "gear", "box-arrow-right"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#2e66ff", "font-size": "18px"},
            "nav-link": {
                "font-size": "15px",
                "text-align": "left",
                "margin": "5px",
                "--hover-color": "#eef2ff",
            },
            "nav-link-selected": {
                "background-color": "#2e66ff",
                "color": "white",
                "font-weight": "bold",
            },
        },
    )


# ── LOG OUT ──────────────────────────────────────────────────────────────────
if choice == "Log Out":
    logout()


# ── DASHBOARD ────────────────────────────────────────────────────────────────
elif choice == "Dashboard":
    st.title("Admin Dashboard")
    st.markdown("Overview and system analytics.")

    conn = get_connection()
    df_users = pd.read_sql_query(
        "SELECT id, student_id as `Student ID`, name as Name, department as Department FROM users",
        conn,
    )
    df_all_attendance = pd.read_sql_query(
        "SELECT student_id as `Student ID`, date as Date, in_time as `In-Time`, out_time as `Out-Time`, status as Status FROM attendance",
        conn,
    )
    conn.close()

    st.write("### Filter Dashboard")
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        date_to_view = st.date_input("Select Date for Dashboard Logs", datetime.now().date())
        date_str = date_to_view.strftime("%Y-%m-%d")
    with filter_col2:
        unique_students = ["All"] + df_users["Student ID"].dropna().unique().tolist()
        selected_student = st.selectbox("Filter by Student ID", unique_students)

    processed_df = process_attendance_with_status(df_all_attendance, df_users, date_str)

    display_df = processed_df.copy()
    if selected_student != "All":
        display_df = display_df[display_df["Student ID"] == selected_student]

    total_registered = len(df_users)
    present_count = len(
        processed_df[processed_df["Status"].astype(str).str.contains("Present", na=False)]
    )
    half_day_count = len(processed_df[processed_df["Status"] == "Half Day"])
    absent_count = len(processed_df[processed_df["Status"] == "Absent"])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Users Registered", total_registered)
    col2.metric("Present Today", present_count)
    col3.metric("Half-Day Today", half_day_count)
    col4.metric("Absent Today", absent_count)

    st.write("---")

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.plotly_chart(render_attendance_trends(df_all_attendance), use_container_width=True)
    with chart_col2:
        st.plotly_chart(
            render_department_distribution(
                df_users, processed_df[processed_df["Status"] != "Absent"]
            ),
            use_container_width=True,
        )

    st.write("---")
    st.subheader("Daily Logs & Export")

    if not display_df.empty:
        def color_status(val):
            if "Absent" in str(val):
                return "color: red"
            elif "Present" in str(val):
                return "color: green"
            elif "Half" in str(val):
                return "color: orange"
            return "color: black"

        styled_df = display_df.style.map(color_status, subset=["Status"])
        st.dataframe(styled_df, use_container_width=True)

        csv = display_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Selected CSV", csv, f"Attendance_{date_str}.csv", "text/csv"
        )
    else:
        st.info("No attendance records found for the selected criteria.")


# ── REGISTER USER ─────────────────────────────────────────────────────────────
elif choice == "Register User":
    st.title("Register New User")
    st.markdown("Enroll a new student or staff member into the facial recognition database.")

    with st.form("register_form"):
        col1, col2 = st.columns(2)
        with col1:
            student_id = st.text_input("User ID (Roll No / Emp ID)")
        with col2:
            name = st.text_input("Full Name")

        department = st.selectbox(
            "Department",
            ["Computer Science", "Electrical", "Mechanical", "Civil", "HR", "Other"],
        )
        submit_btn = st.form_submit_button("Register & Capture Face", type="primary")

    if submit_btn:
        if student_id and name:
            if add_user(student_id, name, department):
                st.success(f"User **{name}** added. Initializing camera stream…")

                progress_bar = st.progress(0)
                status_text = st.empty()

                render_camera_ui_wrapper()
                placeholder = st.empty()

                frames_captured = 0
                with st.container():
                    st.markdown('<div class="scanner-container">', unsafe_allow_html=True)
                    for output in capture_training_images(student_id, name):
                        if isinstance(output, str):
                            status_text.info(output)
                            frames_captured += 1
                            progress = min(frames_captured / 30, 1.0)
                            progress_bar.progress(progress)
                        else:
                            img_rgb = cv2.cvtColor(output, cv2.COLOR_BGR2RGB)
                            placeholder.image(img_rgb, channels="RGB", use_container_width=True)
                    st.markdown("</div>", unsafe_allow_html=True)

                placeholder.empty()
                progress_bar.empty()

                with st.spinner("Compiling facial encodings… This may take a moment."):
                    success, msg = generate_encodings()
                    if success:
                        st.success(f"🎉 Training Complete! {msg}")
                    else:
                        st.error(msg)
            else:
                st.error("User ID already exists! Please use a unique ID.")
        else:
            st.warning("Please fill out all required fields.")


# ── MARK ATTENDANCE (Admin) ───────────────────────────────────────────────────
elif choice == "Mark Attendance":
    st.title("Live Attendance Scanner")
    st.markdown(
        "Ensure your face is clearly visible to the camera. The system prevents duplicate rapid check-ins."
    )

    col_cam, col_info = st.columns([2, 1])

    with col_info:
        st.info(
            """
            **Instructions**:
            1. Click **Start Scanner**.
            2. Look into the camera.
            3. Wait for your bounding box to turn green.
            """
        )
        run_camera = st.checkbox("Start Scanner", key="start_scanner_cb")
        status_msg = st.empty()

    if run_camera:
        recognizer, label_map = load_encodings()
        if recognizer is None:
            status_msg.error("No model encodings found. Please register at least one user first.")
        else:
            users = get_users()
            id_to_name = {u[1]: u[2] for u in users}

            cap = get_camera()
            if cap is None:
                status_msg.error("Cannot access webcam. Please check permissions.")
                st.stop()

            render_camera_ui_wrapper()

            with col_cam:
                st.markdown('<div class="scanner-container">', unsafe_allow_html=True)
                camera_placeholder = st.empty()

                try:
                    while run_camera:
                        ret, frame = cap.read()
                        if not ret:
                            status_msg.error("Camera feed disconnected.")
                            break

                        frame, detected = recognize_faces(frame, recognizer, label_map)

                        current_time = datetime.now()
                        date_str = current_time.strftime("%Y-%m-%d")
                        time_str = current_time.strftime("%H:%M:%S")

                        for std_id in detected:
                            name = id_to_name.get(std_id, "Unknown")
                            last_time = st.session_state.last_scanned.get(std_id)

                            if std_id != "Unknown" and (
                                last_time is None
                                or (current_time - last_time).total_seconds() > 60
                            ):
                                st.session_state.last_scanned[std_id] = current_time
                                action = mark_attendance(std_id, date_str, time_str)
                                update_csv_log(name, std_id, date_str, time_str, action)
                                status_msg.success(
                                    f"✅ **{action}** automatically marked for **{name}** at {time_str}"
                                )

                        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        camera_placeholder.image(img_rgb, channels="RGB", use_container_width=True)

                finally:
                    cap.release()
                    st.markdown("</div>", unsafe_allow_html=True)


# ── SETTINGS ──────────────────────────────────────────────────────────────────
elif choice == "Settings":
    st.title("⚙️ Settings")
    st.markdown("Manage admin preferences and system configuration.")
    st.markdown("---")
    render_sound_settings()

    # ── Change Password Section ───────────────────────────────────────────
    st.markdown("---")
    st.subheader("🔐 Change Admin Password")
    st.markdown("Update your login credentials securely.")

    with st.form("change_password_form"):
        current_pw = st.text_input("Current Password", type="password", key="current_pw")
        new_pw = st.text_input("New Password (min 6 chars)", type="password", key="new_pw")
        confirm_pw = st.text_input("Confirm New Password", type="password", key="confirm_pw")
        change_btn = st.form_submit_button("Update Password", type="primary")

    if change_btn:
        if not current_pw or not new_pw or not confirm_pw:
            st.error("Please fill in all password fields.")
        elif new_pw != confirm_pw:
            st.error("New passwords do not match.")
        elif len(new_pw) < 6:
            st.error("New password must be at least 6 characters.")
        else:
            from src.auth import change_admin_password
            admin_user = st.session_state.get("admin_username", "admin")
            ok, msg = change_admin_password(admin_user, current_pw, new_pw)
            if ok:
                st.success(f"✅ {msg}")
            else:
                st.error(f"❌ {msg}")
