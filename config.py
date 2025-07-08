import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Base Paths
ENCODING_DIR = os.path.join(BASE_DIR, "encodings_faces")
STATIC_DIR = os.path.join(BASE_DIR, "static")
ATTENDANCE_DIR = os.path.join(STATIC_DIR, "attendance")
VIDEO_DIR = os.path.join(STATIC_DIR, "recorded_videos")
TIMETABLE_DIR = os.path.join(STATIC_DIR, "timetables")
SUBJECT_DIR = os.path.join(STATIC_DIR, "teacher_subjects")

# Thresholds
TEACHER_DETECTION_THRESHOLD = 5
STUDENT_PRESENCE_THRESHOLD = 5

USERS = {
    "admin": {"password": "admin123", "role": "Admin"},
    "teacher": {"password": "teach2025", "role": "Teacher"}
}

camera_mapping = {
    "bca": 0,  # USB Camera 0
    "mca": 1,  # USB Camera 1
    "btech": 2  # USB Camera 2
}

# IP Addresses for LIVE streaming
ip_address = {
    "bca": "http://192.168.197.35:8000/stream",
    "mca": "http://192.168.197.35:8001/stream",
    "btech": "http://192.168.197.35:8002/stream"
}