import streamlit as st
import pandas as pd
import os
import subprocess
import time
import csv
import requests
import json
from datetime import datetime, timedelta
import threading
import signal

# Flask API Configuration
FLASK_API_BASE = "http://localhost:5001"

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="FaceTrack Pro - Smart Attendance System", 
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="🔍"
)

# ---------------- Enhanced Professional CSS ----------------
st.markdown("""
<style>
    /* Import Professional Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Playfair+Display:wght@400;500;600;700&display=swap');
    
    /* Reset and Base Styles */
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    html, body {
        scroll-behavior: smooth;
    }
    
    /* Main Background with Better Contrast */
    .main {
        background: linear-gradient(135deg, #0f1419 0%, #1a1f2e 25%, #2d1b69 50%, #1a1f2e 75%, #0f1419 100%);
        background-size: 400% 400%;
        animation: gradient-shift 15s ease infinite;
        font-family: 'Inter', sans-serif;
        position: relative;
        min-height: 100vh;
        color: #ffffff;
    }
    
    @keyframes gradient-shift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Particle Background Effect */
    .main::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
            radial-gradient(circle at 20% 80%, rgba(120, 119, 198, 0.3) 0%, transparent 50%),
            radial-gradient(circle at 80% 20%, rgba(255, 119, 198, 0.15) 0%, transparent 50%),
            radial-gradient(circle at 40% 40%, rgba(120, 200, 255, 0.2) 0%, transparent 50%);
        animation: particles-float 20s ease-in-out infinite;
        pointer-events: none;
        z-index: 0;
    }
    
    @keyframes particles-float {
        0%, 100% { 
            transform: translateX(0px) translateY(0px) rotate(0deg);
            opacity: 0.7;
        }
        33% { 
            transform: translateX(30px) translateY(-30px) rotate(120deg);
            opacity: 1;
        }
        66% { 
            transform: translateX(-20px) translateY(20px) rotate(240deg);
            opacity: 0.8;
        }
    }
    
    /* Website Header */
    .website-header {
        background: rgba(15, 20, 25, 0.95);
        backdrop-filter: blur(20px);
        border-bottom: 2px solid rgba(120, 119, 198, 0.2);
        padding: 1rem 0;
        position: sticky;
        top: 0;
        z-index: 100;
        animation: header-slide-down 1s ease-out;
    }
    
    @keyframes header-slide-down {
        from {
            opacity: 0;
            transform: translateY(-100%);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .header-content {
        max-width: 1200px;
        margin: 0 auto;
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0 2rem;
    }
    
    .logo-section {
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    
    .logo {
        font-size: 2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #4f96ff 0%, #8b5cf6 50%, #ff6b9d 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: 'Playfair Display', serif;
    }
    
    .nav-menu {
        display: flex;
        gap: 2rem;
        list-style: none;
    }
    
    .nav-item {
        color: rgba(255, 255, 255, 0.8);
        text-decoration: none;
        font-weight: 500;
        padding: 0.5rem 1rem;
        border-radius: 25px;
        transition: all 0.3s ease;
        position: relative;
    }
    
    .nav-item:hover {
        color: #ffffff;
        background: rgba(120, 119, 198, 0.2);
        transform: translateY(-2px);
    }
    
    .nav-item.active {
        background: linear-gradient(135deg, rgba(79, 150, 255, 0.3), rgba(139, 92, 246, 0.3));
        color: #ffffff;
    }
    
    /* Enhanced Container */
    .block-container {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 3rem;
        margin: 2rem;
        box-shadow: 
            0 20px 60px rgba(0, 0, 0, 0.3),
            0 8px 32px rgba(120, 119, 198, 0.1),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(20px);
        animation: container-materialize 1.5s ease-out;
        position: relative;
        z-index: 10;
    }
    
    @keyframes container-materialize {
        from {
            opacity: 0;
            transform: translateY(50px) scale(0.95);
        }
        to {
            opacity: 1;
            transform: translateY(0) scale(1);
        }
    }
    
    /* Hero Section */
    .hero-section {
        text-align: center;
        padding: 4rem 0;
        background: linear-gradient(135deg, rgba(15, 20, 25, 0.8), rgba(26, 31, 46, 0.6));
        border-radius: 20px;
        margin: 2rem 0;
        border: 1px solid rgba(120, 119, 198, 0.2);
        position: relative;
        overflow: hidden;
    }
    
    .hero-section::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: conic-gradient(from 0deg, transparent, rgba(79, 150, 255, 0.1), transparent);
        animation: hero-rotate 20s linear infinite;
    }
    
    @keyframes hero-rotate {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .main-title {
        font-size: 4rem;
        font-weight: 800;
        background: linear-gradient(135deg, #4f96ff 0%, #8b5cf6 50%, #ff6b9d 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1.5rem;
        font-family: 'Playfair Display', serif;
        position: relative;
        z-index: 1;
    }
    
    .subtitle {
        font-size: 1.3rem;
        color: rgba(255, 255, 255, 0.8);
        max-width: 800px;
        margin: 0 auto;
        line-height: 1.6;
        position: relative;
        z-index: 1;
    }
    
    /* Section Headers */
    .section-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #ffffff;
        margin: 3rem 0 2rem 0;
        text-align: center;
        background: linear-gradient(135deg, #4f96ff, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Cards */
    .subject-card, .control-card, .status-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(120, 119, 198, 0.3);
        border-radius: 15px;
        padding: 2rem;
        margin: 1.5rem 0;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    
    .subject-card:hover, .control-card:hover, .status-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 40px rgba(120, 119, 198, 0.2);
        border-color: rgba(120, 119, 198, 0.5);
    }
    
    .api-status {
        background: rgba(255, 193, 7, 0.1);
        border: 2px solid rgba(255, 193, 7, 0.3);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        color: #ffc107;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #4f96ff 0%, #8b5cf6 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 30px rgba(79, 150, 255, 0.4);
        background: linear-gradient(135deg, #5a9fff 0%, #9d6cf8 100%);
    }
    
    /* Live Feed */
    .live-feed-container {
        background: rgba(0, 0, 0, 0.3);
        border: 2px solid rgba(120, 119, 198, 0.3);
        border-radius: 15px;
        padding: 1rem;
        text-align: center;
    }
    
    /* Tables */
    .dataframe {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        border: 1px solid rgba(120, 119, 198, 0.2);
    }
    
    /* Custom Metrics */
    .metric-card {
        background: linear-gradient(135deg, rgba(79, 150, 255, 0.1), rgba(139, 92, 246, 0.1));
        border: 1px solid rgba(120, 119, 198, 0.3);
        border-radius: 15px;
        padding: 1.5rem;
        text-align: center;
        margin: 1rem 0;
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 800;
        color: #4f96ff;
        margin-bottom: 0.5rem;
    }
    
    .metric-label {
        font-size: 1rem;
        color: rgba(255, 255, 255, 0.7);
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Status Indicators */
    .status-running {
        color: #28a745;
        font-weight: bold;
    }
    
    .status-stopped {
        color: #dc3545;
        font-weight: bold;
    }
    
    .status-warning {
        color: #ffc107;
        font-weight: bold;
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .header-content {
            flex-direction: column;
            gap: 1rem;
        }
        
        .nav-menu {
            flex-wrap: wrap;
            gap: 1rem;
        }
        
        .main-title {
            font-size: 2.5rem;
        }
        
        .subtitle {
            font-size: 1.1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# ---------------- Utility Functions ----------------
def call_flask_api(endpoint, method="GET", data=None):
    """Call Flask API with error handling"""
    try:
        url = f"{FLASK_API_BASE}/{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        return None

def check_flask_api():
    """Check if Flask API is running"""
    result = call_flask_api("health")
    return result is not None

def get_registered_students():
    """Get list of registered students from Flask API"""
    return call_flask_api("students", "GET")

def get_attendance_records(subject=None, date=None):
    """Get attendance records from Flask API"""
    params = {}
    if subject:
        params['subject'] = subject
    if date:
        params['date'] = date
    
    endpoint = "attendance"
    if params:
        param_str = "&".join([f"{k}={v}" for k, v in params.items()])
        endpoint += f"?{param_str}"
    
    return call_flask_api(endpoint, "GET")

def mark_attendance_api(name, subject):
    """Mark attendance via Flask API"""
    data = {
        "name": name,
        "subject": subject,
        "send_email": st.session_state.email_notifications_enabled
    }
    return call_flask_api("mark", "POST", data)

def send_absent_notifications(subject):
    """Send absent student notifications"""
    data = {"subject": subject}
    return call_flask_api("notify-absent", "POST", data)

# ---------------- Website Header ----------------
st.markdown("""
<div class="website-header">
    <div class="header-content">
        <div class="logo-section">
            <div class="logo">AutoAttendance</div>
        </div>
        <nav class="nav-menu">
            <a href="#" class="nav-item active">Dashboard</a>
            <a href="#" class="nav-item">Analytics</a>
            <a href="#" class="nav-item">Reports</a>
            <a href="#" class="nav-item">Email System</a>
            <a href="#" class="nav-item">Settings</a>
            <a href="#" class="nav-item">Support</a>
        </nav>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------- Hero Section ----------------
st.markdown("""
<div class="hero-section">
    <h1 class="main-title">Smart Attendance System</h1>
    <p class="subtitle">Advanced AI-powered face recognition technology with automated email notifications for seamless, secure, and intelligent attendance management across enterprise environments</p>
</div>
""", unsafe_allow_html=True)

# ---------------- API Status Check ----------------
api_status = check_flask_api()
if not api_status:
    st.markdown("""
    <div class="api-status">
        <h4>⚠️ Flask API Status: Offline</h4>
        <p>Email notifications are disabled. Please start the Flask API server to enable email features.</p>
        <p><code>python flask_app.py</code></p>
    </div>
    """, unsafe_allow_html=True)

# ---------------- Paths and Configuration ----------------
main_python = "python"  # Use system Python
main_script = "main.py"
attendance_base_folder = "attendance"
os.makedirs(attendance_base_folder, exist_ok=True)
frame_file = "live.jpg"

# ---------------- Session State Management ----------------
if "process" not in st.session_state:
    st.session_state.process = None
if "selected_subject" not in st.session_state:
    st.session_state.selected_subject = ""
if "current_subject" not in st.session_state:
    st.session_state.current_subject = ""
if "email_notifications_enabled" not in st.session_state:
    st.session_state.email_notifications_enabled = api_status

# Check if process is still running
if st.session_state.process is not None:
    if st.session_state.process.poll() is not None:
        st.session_state.process = None

# ---------------- Subject Selection Section ----------------
st.markdown('<h2 class="section-header">📚 Subject Selection</h2>', unsafe_allow_html=True)

st.markdown("""
<div class="subject-card">
    <h3>Select or Enter Subject for Attendance</h3>
    <p>Choose from existing subjects or enter any custom subject name. Each subject will have its own attendance records and automated email notifications.</p>
</div>
""", unsafe_allow_html=True)

# Subject selection with custom input capability
col1, col2 = st.columns([1, 1])

with col1:
    suggested_subjects = [
        "Mathematics", "Physics", "Chemistry", "Biology", "Computer Science", 
        "English", "History", "Geography", "Economics", "Psychology",
        "Engineering", "Data Science", "Machine Learning", "Web Development", "Database Management"
    ]
    
    selected_from_list = st.selectbox(
        "Choose from suggested subjects (optional):",
        options=["Select from list..."] + suggested_subjects,
        index=0,
        key="subject_selector"
    )

with col2:
    custom_subject = st.text_input(
        "Enter Subject Name:",
        placeholder="Type any subject name (e.g., Advanced AI, Quantum Physics, etc.)",
        key="custom_subject_input"
    )

# Subject selection logic
final_selected_subject = ""
if custom_subject and custom_subject.strip():
    final_selected_subject = custom_subject.strip()
elif selected_from_list and selected_from_list != "Select from list...":
    final_selected_subject = selected_from_list

if final_selected_subject:
    st.session_state.selected_subject = final_selected_subject

# Display current selection
if st.session_state.selected_subject:
    st.markdown(f"""
    <div class="status-card">
        <h4>📝 Current Selection: <span style="color: #4f96ff;">{st.session_state.selected_subject}</span></h4>
        <p>Ready to start face recognition for this subject.</p>
    </div>
    """, unsafe_allow_html=True)

# ---------------- Control Panel Section ----------------
st.markdown('<h2 class="section-header">🎮 Control Panel</h2>', unsafe_allow_html=True)

# Email notification toggle
if api_status:
    email_enabled = st.checkbox(
        "Enable Email Notifications", 
        value=st.session_state.email_notifications_enabled,
        help="Send automatic email notifications when attendance is marked"
    )
    st.session_state.email_notifications_enabled = email_enabled

# Control buttons
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    if st.button("🚀 Start Face Recognition", type="primary", use_container_width=True):
        if st.session_state.selected_subject:
            if st.session_state.process is None:
                try:
                    # Start the face recognition process
                    st.session_state.process = subprocess.Popen(
                        [main_python, main_script, st.session_state.selected_subject],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    st.session_state.current_subject = st.session_state.selected_subject
                    st.success(f"✅ Face recognition started for {st.session_state.selected_subject}")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed to start face recognition: {str(e)}")
            else:
                st.warning("⚠️ Face recognition is already running!")
        else:
            st.error("❌ Please select a subject first!")

with col2:
    if st.button("🛑 Stop Recognition", use_container_width=True):
        if st.session_state.process is not None:
            try:
                # Terminate the process gracefully
                st.session_state.process.terminate()
                time.sleep(2)  # Give it time to terminate gracefully
                
                if st.session_state.process.poll() is None:
                    # If still running, force kill
                    st.session_state.process.kill()
                
                st.session_state.process = None
                st.session_state.current_subject = ""
                st.success("✅ Face recognition stopped")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error stopping process: {str(e)}")
        else:
            st.warning("⚠️ No active face recognition process!")

with col3:
    if st.button("🔄 Refresh Status", use_container_width=True):
        st.rerun()

# ---------------- Status Display ----------------
st.markdown('<h2 class="section-header">📊 System Status</h2>', unsafe_allow_html=True)

# Create status display
col1, col2, col3, col4 = st.columns(4)

with col1:
    api_status_text = "🟢 Online" if api_status else "🔴 Offline"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{api_status_text}</div>
        <div class="metric-label">Flask API</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    process_status = "🟢 Running" if st.session_state.process is not None else "🔴 Stopped"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{process_status}</div>
        <div class="metric-label">Face Recognition</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    email_status = "🟢 Enabled" if st.session_state.email_notifications_enabled else "🔴 Disabled"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{email_status}</div>
        <div class="metric-label">Email Notifications</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    current_subject_display = st.session_state.current_subject or "None"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="font-size: 1.5rem;">{current_subject_display}</div>
        <div class="metric-label">Active Subject</div>
    </div>
    """, unsafe_allow_html=True)

# ---------------- Live Feed Section ----------------
if st.session_state.process is not None:
    st.markdown('<h2 class="section-header">📹 Live Feed</h2>', unsafe_allow_html=True)
    
    live_feed_placeholder = st.empty()
    
    if os.path.exists(frame_file):
        try:
            with live_feed_placeholder.container():
                st.markdown("""
                <div class="live-feed-container">
                    <h4>🎥 Real-time Face Recognition Feed</h4>
                </div>
                """, unsafe_allow_html=True)
                st.image(frame_file, caption=f"Live Feed - {st.session_state.current_subject}", use_column_width=True)
        except Exception as e:
            st.error(f"Error displaying live feed: {str(e)}")
    else:
        st.info("📷 Waiting for live feed to initialize...")

# ---------------- Attendance Records Section ----------------
st.markdown('<h2 class="section-header">📋 Attendance Records</h2>', unsafe_allow_html=True)

# Date selection for records
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    view_subject = st.selectbox(
        "Select Subject to View:",
        options=["All Subjects"] + ([st.session_state.current_subject] if st.session_state.current_subject else []) + suggested_subjects,
        key="view_subject_selector"
    )

with col2:
    view_date = st.date_input(
        "Select Date:",
        value=datetime.now().date(),
        key="view_date_selector"
    )

with col3:
    if st.button("📊 Load Records", use_container_width=True):
        st.rerun()

# Load and display attendance records
if api_status:
    # Get records from Flask API
    subject_filter = None if view_subject == "All Subjects" else view_subject
    date_filter = view_date.strftime("%d%m%y") if view_date else None
    
    records_data = get_attendance_records(subject_filter, date_filter)
    
    if records_data and records_data.get("status") == "success":
        records = records_data.get("records", [])
        
        if records:
            df = pd.DataFrame(records)
            
            # Display summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Records", len(records))
            with col2:
                unique_subjects = df["Subject"].nunique() if "Subject" in df.columns else 0
                st.metric("Subjects", unique_subjects)
            with col3:
                unique_students = df["Name"].nunique() if "Name" in df.columns else 0
                st.metric("Students Present", unique_students)
            
            # Display records table
            st.dataframe(df, use_container_width=True)
            
            # Download button
            csv = df.to_csv(index=False)
            st.download_button(
                "📥 Download Records (CSV)",
                csv,
                f"attendance_{view_subject}_{view_date.strftime('%d%m%y')}.csv",
                "text/csv",
                use_container_width=True
            )
        else:
            st.info("📝 No attendance records found for the selected criteria.")
    else:
        st.warning("⚠️ Unable to fetch records. Please check if the Flask API is running.")
else:
    # Fallback: Read from local files
    st.info("📁 Reading from local attendance files (API offline)")
    
    try:
        records = []
        subject_folder = view_subject if view_subject != "All Subjects" else None
        date_str = view_date.strftime("%d%m%y")
        
        if subject_folder:
            # Read specific subject
            file_path = os.path.join(attendance_base_folder, subject_folder, f"attendance_{subject_folder}_{date_str}.csv")
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("📝 No attendance records found for the selected subject and date.")
        else:
            # Read all subjects
            all_records = []
            if os.path.exists(attendance_base_folder):
                for subject_dir in os.listdir(attendance_base_folder):
                    subject_path = os.path.join(attendance_base_folder, subject_dir)
                    if os.path.isdir(subject_path):
                        file_path = os.path.join(subject_path, f"attendance_{subject_dir}_{date_str}.csv")
                        if os.path.exists(file_path):
                            df = pd.read_csv(file_path)
                            all_records.append(df)
                
                if all_records:
                    combined_df = pd.concat(all_records, ignore_index=True)
                    st.dataframe(combined_df, use_container_width=True)
                else:
                    st.info("📝 No attendance records found for the selected date.")
    except Exception as e:
        st.error(f"Error reading attendance records: {str(e)}")

# ---------------- Email Management Section ----------------
if api_status:
    st.markdown('<h2 class="section-header">📧 Email Management</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="control-card">
            <h4>📨 Send Absent Notifications</h4>
            <p>Send email notifications to students who are absent from the selected subject.</p>
        </div>
        """, unsafe_allow_html=True)
        
        absent_subject = st.selectbox(
            "Select Subject for Absent Notifications:",
            options=[st.session_state.current_subject] if st.session_state.current_subject else suggested_subjects,
            key="absent_subject_selector"
        )
        
        if st.button("📤 Send Absent Notifications", use_container_width=True):
            if absent_subject:
                result = send_absent_notifications(absent_subject)
                if result and result.get("status") == "success":
                    st.success(f"✅ {result.get('message', 'Notifications sent successfully')}")
                else:
                    st.error("❌ Failed to send notifications")
            else:
                st.error("❌ Please select a subject")
    
    with col2:
        st.markdown("""
        <div class="control-card">
            <h4>👥 Registered Students</h4>
            <p>View and manage registered students in the system.</p>
        </div>
        """, unsafe_allow_html=True)
        
        students_data = get_registered_students()
        if students_data and students_data.get("status") == "success":
            students = students_data.get("students", [])
            st.metric("Total Students", len(students))
            
            if students:
                students_df = pd.DataFrame(students)
                with st.expander("View All Students"):
                    st.dataframe(students_df, use_container_width=True)
        else:
            st.warning("Unable to fetch student data")

# ---------------- Analytics Section ----------------
st.markdown('<h2 class="section-header">📈 Analytics Dashboard</h2>', unsafe_allow_html=True)

if api_status:
    # Get attendance data for analytics
    today_records = get_attendance_records(date=datetime.now().strftime("%d%m%y"))
    
    if today_records and today_records.get("status") == "success":
        records = today_records.get("records", [])
        
        if records:
            df = pd.DataFrame(records)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Attendance by subject today
                if "Subject" in df.columns:
                    subject_counts = df["Subject"].value_counts()
                    st.subheader("Today's Attendance by Subject")
                    st.bar_chart(subject_counts)
            
            with col2:
                # Attendance timeline
                if "Timestamp" in df.columns:
                    st.subheader("Attendance Timeline (Today)")
                    df["Hour"] = pd.to_datetime(df["Timestamp"], format="%H:%M:%S").dt.hour
                    hourly_counts = df["Hour"].value_counts().sort_index()
                    st.line_chart(hourly_counts)
        else:
            st.info("No attendance data available for analytics")
    else:
        st.warning("Unable to fetch analytics data")

# ---------------- Manual Attendance Section ----------------
st.markdown('<h2 class="section-header">✋ Manual Attendance</h2>', unsafe_allow_html=True)

st.markdown("""
<div class="control-card">
    <h4>📝 Mark Attendance Manually</h4>
    <p>Manually mark attendance for students who might not be detected by the camera or for offline attendance.</p>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    manual_student = st.text_input(
        "Student Name:",
        placeholder="Enter student name",
        key="manual_student_name"
    )

with col2:
    manual_subject = st.text_input(
        "Subject:",
        value=st.session_state.current_subject or "",
        placeholder="Enter subject name",
        key="manual_subject_name"
    )

with col3:
    if st.button("✅ Mark Present", use_container_width=True):
        if manual_student and manual_subject:
            if api_status:
                result = mark_attendance_api(manual_student, manual_subject)
                if result and result.get("status") == "success":
                    st.success(f"✅ Marked {manual_student} present in {manual_subject}")
                elif result and result.get("status") == "already_marked":
                    st.warning(f"⚠️ {manual_student} already marked present today")
                else:
                    st.error("❌ Failed to mark attendance")
            else:
                # Fallback to local file
                try:
                    subject_folder = os.path.join(attendance_base_folder, manual_subject)
                    os.makedirs(subject_folder, exist_ok=True)
                    
                    today_date = datetime.now().strftime("%d%m%y")
                    attendance_file = os.path.join(subject_folder, f"attendance_{manual_subject}_{today_date}.csv")
                    
                    # Check if already marked
                    already_marked = False
                    if os.path.exists(attendance_file):
                        with open(attendance_file, "r", encoding="utf-8") as f:
                            content = f.read()
                            if manual_student in content:
                                already_marked = True
                    
                    if not already_marked:
                        file_exists = os.path.exists(attendance_file)
                        with open(attendance_file, "a", encoding="utf-8", newline='') as f:
                            if not file_exists:
                                f.write("Name,Subject,Timestamp\n")
                            
                            timestamp = datetime.now().strftime("%H:%M:%S")
                            f.write(f"{manual_student},{manual_subject},{timestamp}\n")
                        
                        st.success(f"✅ Marked {manual_student} present in {manual_subject}")
                    else:
                        st.warning(f"⚠️ {manual_student} already marked present today")
                        
                except Exception as e:
                    st.error(f"❌ Error marking attendance: {str(e)}")
        else:
            st.error("❌ Please enter both student name and subject")

# ---------------- System Information ----------------
with st.expander("🔧 System Information"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Configuration")
        st.write(f"**Flask API URL:** {FLASK_API_BASE}")
        st.write(f"**Main Script:** {main_script}")
        st.write(f"**Python Path:** {main_python}")
        st.write(f"**Attendance Folder:** {attendance_base_folder}")
        st.write(f"**Live Frame File:** {frame_file}")
    
    with col2:
        st.subheader("File System Status")
        st.write(f"**Main Script Exists:** {'✅' if os.path.exists(main_script) else '❌'}")
        st.write(f"**Attendance Folder Exists:** {'✅' if os.path.exists(attendance_base_folder) else '❌'}")
        st.write(f"**Known Faces Folder:** {'✅' if os.path.exists('known_faces') else '❌'}")
        st.write(f"**Live Feed Active:** {'✅' if os.path.exists(frame_file) else '❌'}")

# ---------------- Auto-refresh for live feed ----------------
if st.session_state.process is not None:
    time.sleep(2)
    st.rerun()

# ---------------- Footer ----------------
st.markdown("""
<div style="text-align: center; margin-top: 4rem; padding: 2rem; border-top: 1px solid rgba(255,255,255,0.1);">
    <p style="color: rgba(255,255,255,0.6);">
        ©️ 2024 Smart Attendance System | Powered by AI & Computer Vision
    </p>
</div>
""", unsafe_allow_html=True)