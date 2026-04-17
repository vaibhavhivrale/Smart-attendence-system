import streamlit as st
import base64
import os

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────────────────────────────────────────
def inject_custom_css():
    """Injects premium global CSS for the entire app."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Poppins:wght@400;500;600;700&display=swap');

        * { font-family: 'Inter', sans-serif !important; }

        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
        }

        header { visibility: hidden; }

        /* ── Metric Cards ── */
        [data-testid="stMetricValue"] {
            font-size: 2.2rem !important;
            color: #2e66ff !important;
            font-weight: 700;
        }
        [data-testid="stMetricLabel"] {
            font-size: 1.1rem !important;
            font-weight: 500;
            color: #555555;
        }
        [data-testid="metric-container"] {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 12px;
            padding: 1.2rem;
            box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.05);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        [data-testid="metric-container"]:hover {
            transform: translateY(-4px);
            box-shadow: 0px 8px 20px rgba(46, 102, 255, 0.12);
        }

        /* ── Buttons ── */
        .stButton > button {
            border-radius: 10px !important;
            font-weight: 600 !important;
            padding: 0.55rem 1.6rem !important;
            border: none !important;
            transition: all 0.25s ease;
        }
        .stButton > button:hover {
            transform: scale(1.02);
            box-shadow: 0 4px 14px rgba(46, 102, 255, 0.35);
        }

        /* ── Scanner Container ── */
        .scanner-container {
            border: 3px solid #2e66ff;
            border-radius: 14px;
            padding: 10px;
            box-shadow: 0 0 24px rgba(46, 102, 255, 0.22);
            background: #fff;
        }

        /* ── Dark Mode Overrides ── */
        @media (prefers-color-scheme: dark) {
            [data-testid="metric-container"] {
                background-color: #1a1f35;
                border: 1px solid #2e3556;
                box-shadow: 0px 4px 12px rgba(0,0,0,0.3);
            }
            [data-testid="stMetricLabel"] { color: #a0aec0; }
            [data-testid="stMetricValue"] { color: #5aa1ff !important; }
            .scanner-container { background: #1a1f35; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# SOUND PLAYER  (injects <audio autoplay> with base64 WAV)
# ─────────────────────────────────────────────────────────────────────────────
def render_sound_player(sound_type: str = "Default Chime", volume_pct: int = 60):
    """Inject an auto-playing audio element. Called ONLY on successful login."""
    try:
        from src.sounds import get_sound_b64
        data_uri = get_sound_b64(sound_type, volume_pct)
        st.markdown(
            f"""
            <audio autoplay style="display:none">
                <source src="{data_uri}" type="audio/wav">
            </audio>
            """,
            unsafe_allow_html=True,
        )
    except Exception:
        pass  # Never crash the app over a sound


# ─────────────────────────────────────────────────────────────────────────────
# SUCCESS CHECKMARK ANIMATION
# ─────────────────────────────────────────────────────────────────────────────
def render_success_animation(message: str = "Login Successful"):
    """Animated SVG checkmark with fade-in message."""
    st.markdown(
        f"""
        <style>
        @keyframes fadeScaleIn {{
            from {{ opacity: 0; transform: scale(0.6); }}
            to   {{ opacity: 1; transform: scale(1); }}
        }}
        @keyframes strokeDraw {{
            from {{ stroke-dashoffset: 200; }}
            to   {{ stroke-dashoffset: 0; }}
        }}
        @keyframes circleDraw {{
            from {{ stroke-dashoffset: 314; opacity: 0; }}
            to   {{ stroke-dashoffset: 0;  opacity: 1; }}
        }}
        .success-wrap {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 1rem;
            animation: fadeScaleIn 0.5s ease forwards;
            padding: 2rem 0;
        }}
        .success-svg circle {{
            stroke-dasharray: 314;
            stroke-dashoffset: 314;
            animation: circleDraw 0.6s ease 0.1s forwards;
        }}
        .success-svg polyline {{
            stroke-dasharray: 200;
            stroke-dashoffset: 200;
            animation: strokeDraw 0.5s ease 0.6s forwards;
        }}
        .success-msg {{
            font-family: 'Poppins', sans-serif;
            font-size: 1.4rem;
            font-weight: 600;
            color: #10b981;
            letter-spacing: 0.02em;
            animation: fadeScaleIn 0.5s ease 0.8s both;
        }}
        </style>
        <div class="success-wrap">
            <svg class="success-svg" width="90" height="90" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="45"
                    fill="none" stroke="#10b981" stroke-width="5"
                    stroke-linecap="round"/>
                <polyline points="28,52 44,68 72,34"
                    fill="none" stroke="#10b981" stroke-width="6"
                    stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <p class="success-msg">{message}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# CENTERED LOGIN CARD
# ─────────────────────────────────────────────────────────────────────────────
def render_login_screen():
    """
    Renders a fully-centered admin-only login card.
    Includes: loading spinner, SVG checkmark, chime, public attendance bypass.
    """
    # ── Init session state keys ──────────────────────────────────────────────
    for key, default in [
        ("logged_in", False),
        ("role", None),
        ("login_loading", False),
        ("login_success", False),
        ("login_error", ""),
        ("public_mode", False),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    # ── Full-viewport centering CSS ──────────────────────────────────────────
    st.markdown(
        """
        <style>
        /* Hide Streamlit chrome */
        header, footer, #MainMenu { visibility: hidden !important; }

        /* ── DARK BACKGROUND ── force override Streamlit's theme */
        body,
        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stAppViewContainer"] > .main,
        section.main,
        .main > div {
            background: linear-gradient(135deg, #0d1b2e 0%, #1a3556 45%, #0d1b2e 100%) !important;
            min-height: 100vh;
        }

        /* Remove padding so the content can vertically center */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 1rem !important;
            max-width: 1000px !important;
        }

        /* ── Floating orb decorations ── */
        .stApp::before {
            content: '';
            position: fixed;
            top: -120px; left: -100px;
            width: 500px; height: 500px;
            background: radial-gradient(circle, rgba(59,130,246,0.2) 0%, transparent 65%);
            border-radius: 50%;
            pointer-events: none;
            z-index: 0;
            animation: floatOrb1 9s ease-in-out infinite alternate;
        }
        .stApp::after {
            content: '';
            position: fixed;
            bottom: -150px; right: -100px;
            width: 600px; height: 600px;
            background: radial-gradient(circle, rgba(139,92,246,0.18) 0%, transparent 65%);
            border-radius: 50%;
            pointer-events: none;
            z-index: 0;
            animation: floatOrb2 11s ease-in-out infinite alternate-reverse;
        }
        @keyframes floatOrb1 {
            from { transform: translate(0,0) scale(1); }
            to   { transform: translate(40px,30px) scale(1.12); }
        }
        @keyframes floatOrb2 {
            from { transform: translate(0,0) scale(1); }
            to   { transform: translate(-30px,-40px) scale(1.08); }
        }

        /* ── Center column styling = the glass card ── */
        /* Target the middle column (index 1) inside horizontal block */
        div[data-testid="stHorizontalBlock"] > div:nth-child(2) {
            background: rgba(255,255,255,0.07) !important;
            backdrop-filter: blur(24px) !important;
            -webkit-backdrop-filter: blur(24px) !important;
            border: 1px solid rgba(255,255,255,0.14) !important;
            border-radius: 24px !important;
            padding: 2.5rem !important;
            box-shadow: 0 12px 40px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.06) inset !important;
            z-index: 10;
            position: relative;
        }

        /* ── Labels & text on dark bg ── */
        .stTextInput label,
        [data-testid="stTextInput"] label,
        p, span, label {
            color: #cbd5e1 !important;
        }

        /* ── Input fields ── */
        [data-testid="stTextInput"] input {
            background: rgba(255,255,255,0.09) !important;
            border: 1.5px solid rgba(255,255,255,0.18) !important;
            border-radius: 10px !important;
            color: #f1f5f9 !important;
            font-size: 1rem !important;
            padding: 0.6rem 0.9rem !important;
        }
        [data-testid="stTextInput"] input::placeholder {
            color: #64748b !important;
        }
        [data-testid="stTextInput"] input:focus {
            border-color: #3b82f6 !important;
            box-shadow: 0 0 0 3px rgba(59,130,246,0.3) !important;
            outline: none !important;
        }

        /* ── Login button ── */
        div[data-testid="stButton"] > button {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
            color: #fff !important;
            font-size: 1rem !important;
            font-weight: 600 !important;
            padding: 0.7rem 1.5rem !important;
            border-radius: 12px !important;
            border: none !important;
            transition: all 0.25s ease !important;
            letter-spacing: 0.02em;
            box-shadow: 0 4px 15px rgba(59,130,246,0.35) !important;
        }
        div[data-testid="stButton"] > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 24px rgba(59,130,246,0.5) !important;
        }

        /* ── Error banner ── */
        .login-error {
            background: rgba(239,68,68,0.18);
            border: 1px solid rgba(239,68,68,0.5);
            border-radius: 10px;
            padding: 0.75rem 1rem;
            color: #fca5a5;
            font-size: 0.9rem;
            margin-bottom: 1rem;
            text-align: left;
        }

        /* ── Divider ── */
        .login-divider {
            border: none;
            border-top: 1px solid rgba(255,255,255,0.1);
            margin: 1.25rem 0;
        }

        /* ── Spinner ── */
        .stSpinner > div { border-top-color: #3b82f6 !important; }

        /* Alert box dark mode fix */
        [data-testid="stAlert"] {
            background: rgba(59,130,246,0.12) !important;
            border: 1px solid rgba(59,130,246,0.3) !important;
            color: #bfdbfe !important;
            border-radius: 10px !important;
        }

        /* Responsive */
        @media (max-width: 640px) {
            div[data-testid="stHorizontalBlock"] > div:nth-child(2) {
                padding: 1.5rem !important;
                border-radius: 16px !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )



    # ── Center column trick ───────────────────────────────────────────────────
    _, center_col, _ = st.columns([1, 2, 1])

    with center_col:
        # Card header — rendered inside the glass column
        st.markdown(
            """
            <div style="text-align:center; margin-bottom:1.5rem; padding-top:0.5rem;">
                <span style="font-size:3.2rem; display:block; margin-bottom:0.6rem;">🎓</span>
                <h2 style="font-family:'Poppins',sans-serif; font-size:1.6rem; font-weight:700;
                            color:#f1f5f9; margin:0 0 0.3rem 0; line-height:1.3;">
                    Admin Login
                </h2>
                <p style="font-size:0.88rem; color:#94a3b8; margin:0;">
                    Smart Attendance System — Restricted Access
                </p>
            </div>
            <hr style="border:none; border-top:1px solid rgba(255,255,255,0.1); margin:0 0 1.2rem 0;">
            """,
            unsafe_allow_html=True,
        )

        # ── SUCCESS STATE ────────────────────────────────────────────────────
        if st.session_state.login_success:
            render_success_animation("Login Successful")
            # Play sound
            from src.db import get_setting
            if get_setting("sound_enabled", "true") == "true":
                sound_type = get_setting("sound_type", "Default Chime")
                vol = int(get_setting("sound_volume", "60"))
                render_sound_player(sound_type, vol)
            st.info("Redirecting to Dashboard…")
            time_placeholder = st.empty()
            import time
            time.sleep(1.5)
            st.session_state.login_success = False
            st.rerun()
            return

        # ── LOADING STATE ────────────────────────────────────────────────────
        if st.session_state.login_loading:
            import time
            with st.spinner("Verifying credentials…"):
                time.sleep(0.9)  # Brief UX delay for spinner to show
            # Transition to success state
            st.session_state.login_loading = False
            st.session_state.login_success = True
            st.session_state.logged_in = True
            st.session_state.role = "Admin"
            st.rerun()
            return

        # ── ERROR BANNER ─────────────────────────────────────────────────────
        if st.session_state.login_error:
            st.markdown(
                f'<div class="login-error">⚠️ {st.session_state.login_error}</div>',
                unsafe_allow_html=True,
            )

        # ── INPUT FIELDS ─────────────────────────────────────────────────────
        username = st.text_input(
            "Username",
            placeholder="Enter admin username",
            key="login_username",
        )
        password = st.text_input(
            "Password",
            placeholder="Enter password",
            type="password",
            key="login_password",
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # ── LOGIN BUTTON ─────────────────────────────────────────────────────
        if st.button("Log In", use_container_width=True, type="primary", key="login_btn"):
            if not username or not password:
                st.session_state.login_error = "Please enter both username and password."
                st.rerun()
            else:
                from src.auth import verify_admin
                success, message = verify_admin(username, password)
                if success:
                    # Step 1: trigger loading spinner on next rerun
                    st.session_state.login_error = ""
                    st.session_state.login_loading = True
                    st.session_state.admin_username = username
                    st.rerun()
                else:
                    st.session_state.login_error = message
                    st.rerun()

        # ── DIVIDER + PUBLIC BYPASS ───────────────────────────────────────────
        st.markdown("<hr class='login-divider'>", unsafe_allow_html=True)
        st.markdown(
            "<p style='text-align:center; color:#94a3b8; font-size:0.82rem; margin-bottom:0.5rem;'>No login required for attendance marking</p>",
            unsafe_allow_html=True,
        )
        if st.button(
            "📸  Mark Attendance (Public Access)",
            use_container_width=True,
            key="public_attendance_btn",
        ):
            st.session_state.public_mode = True
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# SOUND SETTINGS PANEL  (Admin → Settings)
# ─────────────────────────────────────────────────────────────────────────────
def render_sound_settings():
    """Renders the full Sound Settings UI inside the Admin Settings page."""
    from src.db import get_setting, set_setting

    st.markdown(
        """
        <style>
        .settings-card {
            background: #f8faff;
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 1.5rem;
        }
        .settings-title {
            font-size: 1.15rem;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 0.25rem;
        }
        .settings-desc {
            font-size: 0.88rem;
            color: #64748b;
            margin-bottom: 1.5rem;
        }
        @media (prefers-color-scheme: dark) {
            .settings-card {
                background: #1a1f35;
                border-color: #2e3556;
            }
            .settings-title { color: #e2e8f0; }
            .settings-desc  { color: #94a3b8; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="settings-card">
            <p class="settings-title">🔊 Sound Settings</p>
            <p class="settings-desc">Customize login success notification sounds for the admin panel.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Enable / Disable ──────────────────────────────────────────────────────
    enabled_val = get_setting("sound_enabled", "true") == "true"
    sound_enabled = st.toggle("Enable Login Sound", value=enabled_val, key="snd_enabled")
    if sound_enabled != enabled_val:
        set_setting("sound_enabled", "true" if sound_enabled else "false")
        st.toast("Sound preference saved ✓", icon="🔊")

    st.markdown("---")

    # ── Controls (only if enabled) ────────────────────────────────────────────
    if sound_enabled:
        col_vol, col_type = st.columns(2)

        with col_vol:
            st.markdown("**🎚️ Volume**")
            volume = st.slider(
                "Volume level",
                min_value=0,
                max_value=100,
                value=int(get_setting("sound_volume", "60")),
                key="snd_volume",
                label_visibility="collapsed",
            )
            if st.button("Save Volume", key="save_vol_btn"):
                set_setting("sound_volume", str(volume))
                st.toast(f"Volume set to {volume}% ✓", icon="✅")

        with col_type:
            st.markdown("**🎵 Sound Type**")
            sound_options = ["Default Chime", "Soft Bell", "Digital Beep"]
            current_type = get_setting("sound_type", "Default Chime")
            sound_type = st.selectbox(
                "Sound selection",
                sound_options,
                index=sound_options.index(current_type) if current_type in sound_options else 0,
                key="snd_type",
                label_visibility="collapsed",
            )
            if st.button("Save Sound", key="save_sound_btn"):
                set_setting("sound_type", sound_type)
                st.toast(f"Sound set to '{sound_type}' ✓", icon="✅")

        st.markdown("---")
        st.markdown("**🧪 Test Sound**")
        test_col, _ = st.columns([1, 3])
        with test_col:
            if st.button("▶ Play Test Sound", key="test_sound_btn", type="primary"):
                render_sound_player(sound_type, volume)
                st.success(f"Playing: **{sound_type}** at {volume}% volume")
    else:
        st.info("Sound is currently disabled. Enable it above to configure options.")


# ─────────────────────────────────────────────────────────────────────────────
# CAMERA UI WRAPPER
# ─────────────────────────────────────────────────────────────────────────────
def render_camera_ui_wrapper():
    """Wrapper to make the camera stream look like a modern scanning window."""
    st.markdown(
        """
        <style>
        .scanner-container {
            border: 3px solid #2e66ff;
            border-radius: 14px;
            padding: 10px;
            box-shadow: 0 0 24px rgba(46, 102, 255, 0.25);
            background: #fff;
        }
        @media (prefers-color-scheme: dark) {
            .scanner-container { background: #1a1f35; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
