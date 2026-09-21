import cv2
import face_recognition
import numpy as np
import os
import sys
from datetime import datetime
import threading
import signal
import requests
import json

# =========================
# Global Variables & Signal Handler
# =========================
running = True

def signal_handler(signum, frame):
    """Handle termination signals gracefully"""
    global running
    print(f"\n🛑 Received signal {signum}. Shutting down gracefully...")
    running = False

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# =========================
# Flask API Integration
# =========================
FLASK_API_BASE = "http://localhost:5001"

def call_flask_api(endpoint, method="GET", data=None):
    """Call Flask API with error handling"""
    try:
        url = f"{FLASK_API_BASE}/{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=2)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=2)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"⚠️  API Error: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Flask API not available: {e}")
        return None

def mark_attendance_via_api(name, subject):
    """Mark attendance via Flask API"""
    data = {
        "name": name,
        "subject": subject,
        "send_email": True
    }
    result = call_flask_api("mark", "POST", data)
    if result:
        print(f"📧 API Response: {result.get('message', 'Success')}")
        return result.get('status') == 'success'
    return False

def report_unknown_face_to_api(subject):
    """Report unknown face to Flask API"""
    data = {
        "subject": subject,
        "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    }
    call_flask_api("unknown-face", "POST", data)

# =========================
# Subject Handling
# =========================
# Get subject name from command line argument
if len(sys.argv) < 2:
    print("❌ Error: Subject name required!")
    print("Usage: python main.py <subject_name>")
    sys.exit(1)

subject_name = sys.argv[1].strip()
if not subject_name:
    print("❌ Error: Subject name cannot be empty!")
    sys.exit(1)

print(f"🎯 Starting face recognition for subject: {subject_name}")

# =========================
# Paths and Directory Setup
# =========================
known_faces_path = "known_faces"   # folder with images directly inside
attendance_base_folder = "attendance"
os.makedirs(attendance_base_folder, exist_ok=True)

# Create subject-specific folder
subject_folder = os.path.join(attendance_base_folder, subject_name)
os.makedirs(subject_folder, exist_ok=True)

# Attendance file with today's date and subject
today_date = datetime.now().strftime("%d%m%y")
attendance_file = os.path.join(subject_folder, f"attendance_{subject_name}_{today_date}.csv")

# Path for live frame for Streamlit
live_frame_file = "live.jpg"

print(f"📁 Subject folder: {subject_folder}")
print(f"📊 Attendance file: {attendance_file}")
print(f"📸 Known faces path: {known_faces_path}")

# =========================
# Load Known Faces
# =========================
images = []
classNames = []
encodeList = []

print("✅ Loading known faces...")

# Check if known_faces directory exists
if not os.path.exists(known_faces_path):
    print(f"❌ Error: Known faces directory '{known_faces_path}' not found!")
    print(f"Please create the '{known_faces_path}' directory and add face images.")
    sys.exit(1)

# Load face images with better error handling
face_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp')
face_files = [f for f in os.listdir(known_faces_path) if f.lower().endswith(face_extensions)]

if not face_files:
    print(f"❌ Error: No face images found in '{known_faces_path}' directory!")
    print(f"Please add some face images {face_extensions} to the known_faces folder.")
    sys.exit(1)

print(f"🔍 Found {len(face_files)} image files. Loading...")

successful_loads = 0
for file in face_files:
    img_path = os.path.join(known_faces_path, file)
    
    try:
        img = cv2.imread(img_path)
        if img is None:
            print(f"⚠️  Skipping unreadable file: {file}")
            continue

        # Validate image dimensions
        if img.shape[0] < 50 or img.shape[1] < 50:
            print(f"⚠️  Image too small ({img.shape[1]}x{img.shape[0]}): {file}")
            continue

        images.append(img)
        # Use filename without extension as the person's name
        name = os.path.splitext(file)[0]
        classNames.append(name)
        successful_loads += 1
        print(f"📸 Loaded: {name}")
        
    except Exception as e:
        print(f"⚠️  Error loading {file}: {e}")
        continue

if successful_loads == 0:
    print("❌ Error: No valid face images could be loaded!")
    sys.exit(1)

print(f"✅ Successfully loaded {successful_loads} images")

# =========================
# Encode Faces with Progress
# =========================
print("🔄 Encoding faces... This may take a moment...")

valid_classNames = []
valid_encodeList = []
encoding_successful = 0

for i, img in enumerate(images):
    try:
        print(f"🔄 Encoding face {i+1}/{len(images)}: {classNames[i]}")
        
        # Convert to RGB
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_rgb = np.ascontiguousarray(img_rgb, dtype=np.uint8)

        # Find face locations
        boxes = face_recognition.face_locations(img_rgb, model="hog")
        
        if not boxes:
            print(f"⚠️  No face detected in {classNames[i]}'s image. Trying with CNN model...")
            # Try with CNN model for better detection (slower but more accurate)
            boxes = face_recognition.face_locations(img_rgb, model="cnn", number_of_times_to_upsample=1)
            
        if not boxes:
            print(f"❌ Still no face found in {classNames[i]}'s image. Skipping...")
            continue
            
        if len(boxes) > 1:
            print(f"⚠️  Multiple faces detected in {classNames[i]}'s image. Using the first one...")
            
        # Get face encodings
        enc = face_recognition.face_encodings(img_rgb, boxes, num_jitters=1)
        
        if enc:
            valid_classNames.append(classNames[i])
            valid_encodeList.append(enc[0])
            encoding_successful += 1
            print(f"✅ Successfully encoded: {classNames[i]}")
        else:
            print(f"❌ Could not encode face for {classNames[i]}. Skipping...")
            
    except Exception as e:
        print(f"❌ Error processing {classNames[i]}: {e}")
        continue

if not valid_encodeList:
    print("❌ Error: No valid face encodings found!")
    print("Please ensure your images contain clear, detectable faces.")
    print("Tips:")
    print("- Use high-quality, well-lit images")
    print("- Ensure faces are clearly visible and not tilted")
    print("- Use images with single faces")
    sys.exit(1)

# Update lists with successful encodings
classNames = valid_classNames
encodeList = valid_encodeList

print(f"🎉 Successfully encoded {encoding_successful} faces")
print(f"📋 Active faces: {classNames}")

# =========================
# Attendance Management Functions
# =========================
attendance_lock = threading.Lock()
attendance_cache = set()  # To avoid duplicate entries in the same session

def load_existing_attendance():
    """Load existing attendance to avoid duplicates - improved version"""
    global attendance_cache
    attendance_cache.clear()  # Clear cache first
    
    try:
        # First try to get from API if available
        api_result = call_flask_api("attendance", "GET")
        if api_result and api_result.get("status") == "success":
            today_str = datetime.now().strftime("%d/%m/%Y")  # API date format
            records = api_result.get("records", [])
            
            for record in records:
                # Check if record is from today
                if record.get("Date") == today_str:
                    name = record.get("Name")
                    if name:
                        attendance_cache.add(name)
            
            print(f"📊 Loaded {len(attendance_cache)} existing attendance records from API for today")
            return
    
    except Exception as e:
        print(f"⚠️  Error loading attendance from API: {e}")
    
    # Fallback: Load from local file
    try:
        if os.path.exists(attendance_file):
            with open(attendance_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                # Skip header and extract names
                for line in lines[1:]:
                    if line.strip():
                        parts = line.strip().split(",")
                        if parts and parts[0]:
                            attendance_cache.add(parts[0])
            
            print(f"📊 Loaded {len(attendance_cache)} existing attendance records from local file for today")
                            
    except Exception as e:
        print(f"⚠️  Error loading existing attendance from local file: {e}")
        attendance_cache = set()  # Reset to empty set on error

def markAttendance(name, subject):
    """Thread-safe attendance marking with API integration - COMPLETELY FIXED VERSION"""
    global attendance_cache
    
    if name == "Unknown":
        return False
    
    with attendance_lock:
        # Check if already marked in this session
        if name in attendance_cache:
            print(f"⚠️  {name} already in cache - skipping")
            return False
        
        # Try Flask API first
        try:
            api_result = mark_attendance_via_api(name, subject)
            
            if api_result is True:
                # Successfully marked via API
                attendance_cache.add(name)
                print(f"🟢 API: Successfully marked {name} in {subject}")
                return True
            elif api_result == 'already_marked':
                # Already marked in API/database
                attendance_cache.add(name)  # Add to cache to prevent future attempts
                print(f"ℹ️  {name} already marked in database")
                return False
            else:
                # API failed, try local fallback
                print(f"⚠️  API failed for {name}, trying local fallback")
                pass  # Continue to local fallback
                
        except Exception as e:
            print(f"⚠️  API error for {name}: {e}")
            # Continue to local fallback
        
        # Local file fallback (only if API completely failed)
        try:
            today_date = datetime.now().strftime("%d%m%y")
            subject_folder = os.path.join(attendance_base_folder, subject)
            attendance_file = os.path.join(subject_folder, f"attendance_{subject}_{today_date}.csv")
            
            # Check local file for duplicates
            if os.path.exists(attendance_file):
                with open(attendance_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    for line in lines[1:]:  # Skip header
                        if line.strip():
                            parts = line.strip().split(",")
                            if parts and parts[0].strip() == name.strip():
                                attendance_cache.add(name)
                                print(f"ℹ️  {name} already marked locally")
                                return False
            
            # Mark in local file
            os.makedirs(subject_folder, exist_ok=True)
            file_exists = os.path.exists(attendance_file)
            
            with open(attendance_file, "a", encoding="utf-8", newline='') as f:
                if not file_exists:
                    f.write("Name,Subject,Timestamp\n")
                
                now = datetime.now()
                dtString = now.strftime("%H:%M:%S")
                f.write(f"{name},{subject},{dtString}\n")
                
                attendance_cache.add(name)
                print(f"🟢 Local: Marked {name} in {subject} at {dtString}")
                return True
                
        except Exception as e:
            print(f"❌ Error in local marking for {name}: {e}")
            return False
        
        return False
# Load existing attendance
load_existing_attendance()
print(f"📊 Found {len(attendance_cache)} existing attendance records for today")

# =========================
# Camera Setup with Better Error Handling
# =========================
def initialize_camera():
    """Initialize camera with fallback options"""
    print("📷 Initializing camera...")
    
    # Try different camera indices
    for cam_index in [0, 1, 2]:
        try:
            cap = cv2.VideoCapture(cam_index)
            if cap.isOpened():
                # Test if we can read frames
                ret, test_frame = cap.read()
                if ret and test_frame is not None:
                    print(f"✅ Camera {cam_index} initialized successfully")
                    
                    # Set optimal camera properties
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    cap.set(cv2.CAP_PROP_FPS, 30)
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer for real-time processing
                    
                    return cap
                else:
                    cap.release()
            else:
                cap.release()
        except Exception as e:
            print(f"⚠️  Camera {cam_index} failed: {e}")
            continue
    
    print("❌ Could not initialize any camera!")
    return None

video_capture = initialize_camera()
if video_capture is None:
    print("❌ No working camera found. Please check your camera connection.")
    sys.exit(1)

# =========================
# Face Recognition Parameters
# =========================
RECOGNITION_THRESHOLD = 0.5  # Lower = stricter matching
CONFIDENCE_THRESHOLD = 60    # Minimum confidence percentage to display
FRAME_SKIP = 2              # Process every nth frame for better performance
MIN_DETECTION_COUNT = 3     # Minimum detections before marking attendance

# Tracking variables
detection_counts = {}  # Track detection counts for each person
frame_count = 0
last_marked = {}  # Track last marking time for each person
unknown_face_reported = False  # Flag to avoid spam reporting

print(f"📷 Camera initialized successfully for {subject_name}")
print("🔍 Scanning for faces... Press 'q' in the camera window to quit.")
print(f"🎯 Recognition threshold: {RECOGNITION_THRESHOLD}")
print(f"📊 Confidence threshold: {CONFIDENCE_THRESHOLD}%")

# =========================
# Main Recognition Loop
# =========================
try:
    while running:
        ret, frame = video_capture.read()
        if not ret or frame is None:
            print("⚠️  Failed to grab frame from camera")
            continue

        frame_count += 1
        current_time = datetime.now()
        
        # Process face recognition every FRAME_SKIP frames
        process_faces = (frame_count % FRAME_SKIP == 0)
        
        if process_faces:
            # Resize frame for faster processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            rgb_small_frame = np.ascontiguousarray(rgb_small_frame, dtype=np.uint8)

            try:
                # Find faces and encodings
                face_locations = face_recognition.face_locations(rgb_small_frame, model="hog")
                if face_locations:
                    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
                else:
                    face_encodings = []
            except Exception as e:
                print(f"⚠️  Face detection error: {e}")
                face_locations = []
                face_encodings = []

            # Process each detected face
            for face_encoding, face_location in zip(face_encodings, face_locations):
                try:
                    # Compare with known faces
                    face_distances = face_recognition.face_distance(encodeList, face_encoding)

                    name = "Unknown"
                    confidence = 0
                    
                    if len(face_distances) > 0:
                        best_match_index = np.argmin(face_distances)
                        best_distance = face_distances[best_match_index]
                        
                        if best_distance < RECOGNITION_THRESHOLD:
                            name = classNames[best_match_index]
                            confidence = (1 - best_distance) * 100
                            
                            # Only proceed if confidence is above threshold
                            if confidence >= CONFIDENCE_THRESHOLD:
                                # Track detection counts
                                if name not in detection_counts:
                                    detection_counts[name] = 0
                                detection_counts[name] += 1
                                
                                # Mark attendance if enough consistent detections
                                if (detection_counts[name] >= MIN_DETECTION_COUNT and 
                                    name not in attendance_cache):
                                    
                                    success = markAttendance(name, subject_name)
                                    if success:
                                        last_marked[name] = current_time
                        else:
                            # Unknown face detected - report once per session
                            if not unknown_face_reported:
                                report_unknown_face_to_api(subject_name)
                                unknown_face_reported = True
                                print("⚠️  Unknown face reported to administrators")

                    # Scale back face location for original frame
                    top, right, bottom, left = [v * 4 for v in face_location]
                    
                    # Choose colors and labels based on recognition
                    if name != "Unknown" and confidence >= CONFIDENCE_THRESHOLD:
                        if name in attendance_cache:
                            color = (0, 255, 0)  # Green for recognized and marked
                            status = "✓ MARKED"
                        else:
                            color = (0, 255, 255)  # Yellow for recognized but not yet marked
                            status = f"DETECTING ({detection_counts.get(name, 0)}/{MIN_DETECTION_COUNT})"
                        
                        label = f"{name} ({confidence:.1f}%)"
                        status_label = status
                    else:
                        color = (0, 0, 255)  # Red for unknown faces
                        label = "Unknown"
                        status_label = "NOT RECOGNIZED"

                    # Draw rectangle and labels
                    cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                    
                    # Main label background
                    cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
                    cv2.putText(frame, label, (left + 6, bottom - 6), 
                              cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
                    
                    # Status label
                    if name != "Unknown":
                        status_y = top - 10 if top > 40 else bottom + 25
                        text_size = cv2.getTextSize(status_label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
                        cv2.rectangle(frame, (left, status_y - 20), 
                                    (left + text_size[0] + 10, status_y + 5), color, cv2.FILLED)
                        cv2.putText(frame, status_label, (left + 5, status_y - 5), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                        
                except Exception as e:
                    print(f"⚠️  Error processing face: {e}")
                    continue

        # Add informative overlay
        overlay_height = 120
        overlay = np.zeros((overlay_height, frame.shape[1], 3), dtype=np.uint8)
        
        # Background with transparency effect
        cv2.rectangle(overlay, (0, 0), (frame.shape[1], overlay_height), (0, 0, 0), -1)
        frame[0:overlay_height] = cv2.addWeighted(frame[0:overlay_height], 0.7, overlay, 0.3, 0)
        
        # Subject and time info
        subject_text = f"Subject: {subject_name}"
        time_text = f"Time: {current_time.strftime('%H:%M:%S')}"
        status_text = f"Recognized: {len(attendance_cache)} | Active: {len([n for n in detection_counts if detection_counts[n] > 0])}"
        api_text = f"API: {'Online' if call_flask_api('health') else 'Offline'}"
        
        # Draw text with outline for better visibility
        texts = [subject_text, time_text, status_text, api_text]
        y_positions = [25, 45, 65, 85]
        
        for text, y_pos in zip(texts, y_positions):
            # Text outline (black)
            cv2.putText(frame, text, (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 3)
            # Text fill (white)
            cv2.putText(frame, text, (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        # Save frame for Streamlit display (always save for live feed)
        try:
            cv2.imwrite(live_frame_file, frame)
        except Exception as e:
            print(f"⚠️  Error saving frame: {e}")

        # Display frame in OpenCV window (optional - can be disabled for headless mode)
        try:
            cv2.imshow(f"Face Attendance System - {subject_name}", frame)
        except Exception as e:
            # Headless mode - no display available
            pass

        # Check for quit commands and keyboard input
        try:
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                print("🛑 Quit command received via keyboard")
                running = False
                break
            elif key == ord("s"):
                # Save screenshot
                screenshot_name = f"screenshot_{subject_name}_{current_time.strftime('%H%M%S')}.jpg"
                cv2.imwrite(screenshot_name, frame)
                print(f"📸 Screenshot saved: {screenshot_name}")
            elif key == ord("r"):
                # Reset detection counts
                detection_counts.clear()
                print("🔄 Detection counts reset")
        except Exception:
            # No keyboard input available (headless mode)
            pass

        # Check if we should continue running
        if not running:
            break

except KeyboardInterrupt:
    print("\n🛑 Interrupted by user (Ctrl+C)")
    running = False
except Exception as e:
    print(f"❌ Unexpected error in main loop: {e}")
    import traceback
    traceback.print_exc()
finally:
    # Cleanup operations
    print("\n🧹 Cleaning up...")
    
    try:
        if video_capture:
            video_capture.release()
            print("📷 Camera released")
    except Exception as e:
        print(f"⚠️  Error releasing camera: {e}")
    
    try:
        cv2.destroyAllWindows()
        print("🖼️  Windows closed")
    except Exception as e:
        print(f"⚠️  Error closing windows: {e}")
    
    # Remove live frame file
    try:
        if os.path.exists(live_frame_file):
            os.remove(live_frame_file)
            print(f"🗑️  Removed {live_frame_file}")
    except Exception as e:
        print(f"⚠️  Error removing live frame file: {e}")
    
    # Final statistics
    print(f"\n📊 Session Summary for {subject_name}:")
    print(f"   • Total people recognized: {len(attendance_cache)}")
    print(f"   • Attendance file: {attendance_file}")
    print(f"   • Total frames processed: {frame_count}")
    
    if attendance_cache:
        print(f"   • People marked present: {list(attendance_cache)}")
    
    print(f"✅ Face recognition session ended successfully for {subject_name}")

# =========================
# Additional Utility Functions
# =========================
def get_system_info():
    """Get system information for debugging"""
    import platform
    print(f"\n🖥️  System Information:")
    print(f"   • Python version: {platform.python_version()}")
    print(f"   • Platform: {platform.system()} {platform.release()}")
    print(f"   • OpenCV version: {cv2.__version__}")
    
    try:
        import face_recognition
        print(f"   • face_recognition version: Available")
    except ImportError:
        print(f"   • face_recognition: Not available")

# Print system info on startup
if __name__ == "__main__":
    get_system_info()