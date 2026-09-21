from flask import Flask, request, jsonify
import os
import csv
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import threading
import time
from collections import defaultdict
import schedule

app = Flask(__name__)

# =========================
# Email Configuration
# =========================
SENDER_EMAIL = "vksahu160805@gmail.com"
SENDER_PASSWORD = "pnnc iumu spmx tyxc"  # Gmail App Password
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# =========================
# Student Database
# =========================
# Map student names (same as image filenames in known_faces) to their details
student_database = {
    "vinay sahu": {
        "email": "vksahu160805@gmail.com",
        "full_name": "Vinay Kumar Sahu",
        "roll_number": "CS001",
        "phone": "+91-XXXXXXXXXX"
    },
    "chhatrapal dewangan": {
        "email": "nikhildew2004@gmail.com", 
        "full_name": "chhatrapal dewangan",
        "roll_number": "CS002",
        "phone": "+91-XXXXXXXXXX"
    },
    "tushar sahu": {
        "email": "tusharsahujsp@gmail.com",
        "full_name": "tushar sahu",
        "roll_number": "CS003",
        "phone": "+91-XXXXXXXXXX"
    },
    "shikhar sahu": {
        "email": "shikharsahu.90@gmail.com",
        "full_name": "shikhar sahu",
        "roll_number": "CS004",
        "phone": "+91-XXXXXXXXXX"
    },
    "chhatrapal patel": {
        "email": "chhatrapalpatel1711@gmail.com",
        "full_name": "chhatrapal patel",
        "roll_number": "CS005",
        "phone": "+91-XXXXXXXXXX"
    },
    "sanjana bhagat": {
        "email": "sanjana2003b@gmail.com",
        "full_name": "sanjana bhagat",
        "roll_number": "CS006",
        "phone": "+91-XXXXXXXXXX"
    },
    # Add more students here following the same pattern
    # The key should match the filename in known_faces folder (without extension)
}

# Admin/Teacher email configuration
ADMIN_EMAILS = [
    "chhatrapaldewangan2004@gmail.com",  # Primary admin
    # Add more admin emails here
]

# =========================
# Configuration
# =========================
attendance_base_folder = "attendance"
os.makedirs(attendance_base_folder, exist_ok=True)

# Email tracking to avoid spam
email_sent_cache = defaultdict(set)  # subject -> set of student names
last_absence_check = {}  # subject -> datetime

# =========================
# Email Utility Functions
# =========================
def send_email(to_email, subject, html_message, plain_message=None, attachment_path=None):
    """Enhanced email sending with HTML support and attachments"""
    try:
        msg = MIMEMultipart('alternative')
        msg["From"] = SENDER_EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject

        # Add plain text version if provided
        if plain_message:
            msg.attach(MIMEText(plain_message, "plain"))
        
        # Add HTML version
        msg.attach(MIMEText(html_message, "html"))

        # Add attachment if provided
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {os.path.basename(attachment_path)}'
                )
                msg.attach(part)

        # Send email
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        server.quit()

        print(f"📧 Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email to {to_email}: {e}")
        return False

def create_attendance_email_template(student_name, full_name, subject, timestamp, status="PRESENT"):
    """Create professional HTML email template"""
    status_color = "#28a745" if status == "PRESENT" else "#dc3545"
    status_icon = "✅" if status == "PRESENT" else "❌"
    
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Attendance Notification</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f8f9fa;
                margin: 0;
                padding: 20px;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background: white;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #4f96ff 0%, #8b5cf6 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .content {{
                padding: 30px;
            }}
            .status-badge {{
                background-color: {status_color};
                color: white;
                padding: 8px 16px;
                border-radius: 20px;
                font-weight: bold;
                display: inline-block;
                margin: 10px 0;
            }}
            .details-table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            .details-table td {{
                padding: 12px;
                border-bottom: 1px solid #eee;
            }}
            .details-table td:first-child {{
                font-weight: bold;
                color: #555;
                width: 40%;
            }}
            .footer {{
                background-color: #f8f9fa;
                padding: 20px;
                text-align: center;
                color: #666;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎓 Smart Attendance System</h1>
                <p>Automated Attendance Notification</p>
            </div>
            
            <div class="content">
                <h2>Hello {full_name}!</h2>
                
                <p>Your attendance status has been updated:</p>
                
                <div class="status-badge">
                    {status_icon} {status}
                </div>
                
                <table class="details-table">
                    <tr>
                        <td>Student Name:</td>
                        <td>{full_name}</td>
                    </tr>
                    <tr>
                        <td>Subject:</td>
                        <td>{subject}</td>
                    </tr>
                    <tr>
                        <td>Date & Time:</td>
                        <td>{timestamp}</td>
                    </tr>
                    <tr>
                        <td>Status:</td>
                        <td style="color: {status_color}; font-weight: bold;">{status}</td>
                    </tr>
                </table>
                
                {'<p style="color: #28a745;">Great! Your attendance has been successfully recorded.</p>' if status == 'PRESENT' else '<p style="color: #dc3545;">Please contact your instructor regarding your absence.</p>'}
            </div>
            
            <div class="footer">
                <p>This is an automated message from the Smart Attendance System.</p>
                <p>For any queries, please contact the system administrator.</p>
                <p>© 2024 Smart Attendance System. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    plain_template = f"""
    Smart Attendance System - Notification
    
    Hello {full_name},
    
    Your attendance status has been updated:
    
    Student Name: {full_name}
    Subject: {subject}
    Date & Time: {timestamp}
    Status: {status}
    
    {'Great! Your attendance has been successfully recorded.' if status == 'PRESENT' else 'Please contact your instructor regarding your absence.'}
    
    This is an automated message from the Smart Attendance System.
    For any queries, please contact the system administrator.
    
    © 2024 Smart Attendance System. All rights reserved.
    """
    
    return html_template, plain_template

def notify_admin_unknown_face(timestamp, subject, frame_path=None):
    """Notify admin about unknown face detection"""
    html_message = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Unknown Face Detected</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f8f9fa; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; padding: 30px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }}
            .alert {{ background-color: #fff3cd; border: 1px solid #ffeaa7; color: #856404; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>⚠️ Unknown Face Detected</h2>
            <div class="alert">
                <strong>Security Alert!</strong> An unrecognized person was detected in the attendance system.
            </div>
            <p><strong>Subject:</strong> {subject}</p>
            <p><strong>Time:</strong> {timestamp}</p>
            <p><strong>Action Required:</strong> Please review the security footage and update the known faces database if necessary.</p>
        </div>
    </body>
    </html>
    """
    
    for admin_email in ADMIN_EMAILS:
        send_email(
            admin_email,
            f"🚨 Unknown Face Detected - {subject}",
            html_message,
            attachment_path=frame_path
        )

# =========================
# Attendance Management Functions
# =========================
def get_subject_attendance_file(subject_name):
    """Get attendance file path for a specific subject"""
    today_date = datetime.now().strftime("%d%m%y")
    subject_folder = os.path.join(attendance_base_folder, subject_name)
    os.makedirs(subject_folder, exist_ok=True)
    return os.path.join(subject_folder, f"attendance_{subject_name}_{today_date}.csv")

def mark_attendance_with_notification(name, subject, send_email_notification=True):
    """Mark attendance and send email notification - FIXED VERSION"""
    attendance_file = get_subject_attendance_file(subject)
    
    # Check if already marked today - MORE THOROUGH CHECK
    marked_today = False
    if os.path.exists(attendance_file):
        try:
            with open(attendance_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines[1:]:  # Skip header
                    if line.strip():
                        parts = line.split(",")
                        if len(parts) >= 1 and parts[0].strip() == name.strip():
                            marked_today = True
                            break
        except Exception as e:
            print(f"Error reading attendance file: {e}")
    
    if marked_today:
        # IMPORTANT: Return already_marked status properly
        return {
            "status": "already_marked", 
            "message": f"{name} already marked present today",
            "email_sent": False
        }
    
    # Mark attendance
    try:
        file_exists = os.path.exists(attendance_file)
        with open(attendance_file, "a", encoding="utf-8", newline='') as f:
            if not file_exists:
                f.write("Name,Subject,Timestamp\n")
            
            now = datetime.now()
            timestamp = now.strftime("%H:%M:%S")
            f.write(f"{name},{subject},{timestamp}\n")
        
        # Send email notification if enabled
        email_sent = False
        if send_email_notification and name in student_database:
            student_info = student_database[name]
            cache_key = f"{subject}_{datetime.now().strftime('%d%m%y')}"
            
            if name not in email_sent_cache[cache_key]:
                html_msg, plain_msg = create_attendance_email_template(
                    name, student_info["full_name"], subject, 
                    now.strftime("%d/%m/%Y %H:%M:%S"), "PRESENT"
                )
                
                if send_email(student_info["email"], f"Attendance Marked ✅ - {subject}", html_msg, plain_msg):
                    email_sent_cache[cache_key].add(name)
                    email_sent = True
        
        return {
            "status": "success", 
            "message": f"Attendance marked for {name}",
            "email_sent": email_sent
        }
        
    except Exception as e:
        return {"status": "error", "message": f"Failed to mark attendance: {e}"}

def get_attendance_records(subject=None, date=None):
    """Get attendance records for specific subject and/or date"""
    if date is None:
        date = datetime.now().strftime("%d%m%y")
    
    records = []
    
    if subject:
        # Get records for specific subject
        attendance_file = get_subject_attendance_file(subject)
        if os.path.exists(attendance_file):
            try:
                df = pd.read_csv(attendance_file, engine="python", on_bad_lines="skip")
                records = df.to_dict('records')
            except Exception as e:
                print(f"Error reading {attendance_file}: {e}")
    else:
        # Get records for all subjects
        if os.path.exists(attendance_base_folder):
            for subject_folder in os.listdir(attendance_base_folder):
                subject_path = os.path.join(attendance_base_folder, subject_folder)
                if os.path.isdir(subject_path):
                    attendance_file = os.path.join(subject_path, f"attendance_{subject_folder}_{date}.csv")
                    if os.path.exists(attendance_file):
                        try:
                            df = pd.read_csv(attendance_file, engine="python", on_bad_lines="skip")
                            subject_records = df.to_dict('records')
                            records.extend(subject_records)
                        except Exception as e:
                            print(f"Error reading {attendance_file}: {e}")
    
    return records

def check_and_notify_absent_students(subject):
    """Check for absent students and send notifications"""
    try:
        attendance_records = get_attendance_records(subject)
        present_students = {record["Name"] for record in attendance_records}
        
        # Find absent students
        all_registered_students = set(student_database.keys())
        absent_students = all_registered_students - present_students
        
        cache_key = f"{subject}_{datetime.now().strftime('%d%m%y')}_absent"
        
        for student_name in absent_students:
            if student_name not in email_sent_cache[cache_key]:
                student_info = student_database[student_name]
                
                html_msg, plain_msg = create_attendance_email_template(
                    student_name, student_info["full_name"], subject,
                    datetime.now().strftime("%d/%m/%Y"), "ABSENT"
                )
                
                if send_email(
                    student_info["email"], 
                    f"Attendance Alert ❌ - {subject}", 
                    html_msg, plain_msg
                ):
                    email_sent_cache[cache_key].add(student_name)
        
        return len(absent_students)
    except Exception as e:
        print(f"Error checking absent students: {e}")
        return 0

# =========================
# API Routes
# =========================

@app.route("/mark", methods=["POST"])
def mark():
    """API endpoint to mark attendance"""
    try:
        data = request.json
        name = data.get("name")
        subject = data.get("subject", "Default")
        send_email_flag = data.get("send_email", True)
        
        if not name:
            return jsonify({"status": "error", "message": "Name is required"}), 400
        
        result = mark_attendance_with_notification(name, subject, send_email_flag)
        
        if result["status"] == "success":
            return jsonify(result), 200
        elif result["status"] == "already_marked":
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/attendance", methods=["GET"])
def get_attendance():
    """Fetch attendance records"""
    try:
        subject = request.args.get("subject")
        date = request.args.get("date")  # Format: DDMMYY
        
        records = get_attendance_records(subject, date)
        
        return jsonify({
            "status": "success", 
            "records": records,
            "count": len(records),
            "subject": subject,
            "date": date or datetime.now().strftime("%d%m%y")
        }), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/notify-absent", methods=["POST"])
def notify_absent():
    """Manually trigger absent student notifications"""
    try:
        data = request.json
        subject = data.get("subject")
        
        if not subject:
            return jsonify({"status": "error", "message": "Subject is required"}), 400
        
        absent_count = check_and_notify_absent_students(subject)
        
        return jsonify({
            "status": "success",
            "message": f"Absent notifications sent to {absent_count} students",
            "absent_count": absent_count
        }), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/unknown-face", methods=["POST"])
def report_unknown_face():
    """Report unknown face detection"""
    try:
        data = request.json
        subject = data.get("subject", "Unknown")
        timestamp = data.get("timestamp", datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        
        notify_admin_unknown_face(timestamp, subject)
        
        return jsonify({
            "status": "success",
            "message": "Unknown face reported to administrators"
        }), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/students", methods=["GET"])
def get_students():
    """Get list of registered students"""
    try:
        students = []
        for name, info in student_database.items():
            students.append({
                "name": name,
                "full_name": info["full_name"],
                "email": info["email"],
                "roll_number": info.get("roll_number", "N/A")
            })
        
        return jsonify({
            "status": "success",
            "students": students,
            "count": len(students)
        }), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/send-custom-email", methods=["POST"])
def send_custom_email():
    """Send custom email to students"""
    try:
        data = request.json
        student_names = data.get("students", [])  # List of student names
        subject = data.get("subject", "Custom Notification")
        message = data.get("message", "")
        
        if not student_names or not message:
            return jsonify({"status": "error", "message": "Students and message are required"}), 400
        
        sent_count = 0
        for student_name in student_names:
            if student_name in student_database:
                student_info = student_database[student_name]
                html_msg = f"""
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2>Hello {student_info['full_name']}!</h2>
                    <p>{message}</p>
                    <hr>
                    <p><small>This message was sent from the Smart Attendance System.</small></p>
                </body>
                </html>
                """
                
                if send_email(student_info["email"], subject, html_msg, message):
                    sent_count += 1
        
        return jsonify({
            "status": "success",
            "message": f"Email sent to {sent_count} students",
            "sent_count": sent_count
        }), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "registered_students": len(student_database),
        "email_config": "configured" if SENDER_EMAIL and SENDER_PASSWORD else "not_configured"
    }), 200

# =========================
# Background Tasks
# =========================
def cleanup_email_cache():
    """Cleanup old email cache entries"""
    global email_sent_cache
    try:
        current_date = datetime.now().strftime("%d%m%y")
        keys_to_remove = []
        
        for key in email_sent_cache:
            if current_date not in key:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del email_sent_cache[key]
        
        print(f"🧹 Cleaned up {len(keys_to_remove)} old cache entries")
    except Exception as e:
        print(f"Error during cache cleanup: {e}")

# Schedule daily cleanup
schedule.every().day.at("00:01").do(cleanup_email_cache)

def run_scheduler():
    """Run scheduled tasks in background thread"""
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute



# =========================
# Application Startup
# =========================
if __name__ == "__main__":
    # Start background scheduler
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    print("🚀 Flask API Server Starting...")
    print(f"📧 Email configured for: {SENDER_EMAIL}")
    print(f"👥 Registered students: {len(student_database)}")
    print(f"📁 Attendance folder: {attendance_base_folder}")
    print("🌐 Server will be available at http://localhost:5001")
    
    app.run(host="0.0.0.0", port=5000, debug=True)