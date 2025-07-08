import cv2
import face_recognition
import numpy as np
import os
import time
from datetime import datetime, timedelta
from flask import Flask
import logging
from flask import Response, render_template_string, url_for
import threading
import json

app= Flask(__name__)

print("Welcome to the Face Recognition Attendance System!\n")

if os.path.exists(r"C:\Users\Akash\Desktop\New folder\attendence\teachers.json"):
    with open(r"C:\Users\Akash\Desktop\New folder\attendence\teachers.json", "r") as f:
        teachers = json.load(f)
else:
    print("teacher.json not found.")
    teachers = []

if os.path.exists(r'C:\Users\Akash\Desktop\New folder\attendence\timetable.json'):
    with open(r'C:\Users\Akash\Desktop\New folder\attendence\timetable.json', 'r') as f:
        TIMETABLE = json.load(f)

else:
    print("timetable.json not found.")
    TIMETABLE = {}


VIDEO_DIR = "saved_videos"
os.makedirs(VIDEO_DIR, exist_ok=True)

ATTENDANCE_DIR = "attendence_list" 
os.makedirs(ATTENDANCE_DIR, exist_ok=True)

# Define directories
STUDENT_FACES_DIR = r"C:\Users\Akash\Desktop\face detection\a_student_faces"  
TEACHER_FACES_DIR = r"C:\Users\Akash\Desktop\face detection\a_teacher_faces"  

# Initialize lists
face_encodings = []
face_names = []

# Function to load faces from a directory
def load_faces(directory):
    encodings = []
    names = []
    for filename in os.listdir(directory):
        if filename.endswith((".jpg", ".png")):
            image_path = os.path.join(directory, filename)
            name = os.path.splitext(filename)[0]  
            
            image = face_recognition.load_image_file(image_path)
            encodings_list = face_recognition.face_encodings(image)
            
            if encodings_list:
                encodings.append(encodings_list[0])
                names.append(name)
    return encodings, names

# Load student and teacher faces
student_encodings, student_names = load_faces(STUDENT_FACES_DIR)
teacher_encodings, teacher_names = load_faces(TEACHER_FACES_DIR)

# Combine both lists
face_encodings.extend(student_encodings + teacher_encodings)
face_names.extend(student_names + teacher_names)

# Print final result
print(f"✅ Loaded {len(student_encodings)} Students faces and {len(teacher_encodings)} Teachers faces.")

student_presence = {}
STUDENT_PRESENCE_THRESHOLD = 10  # Time in seconds required for attendance
TEACHER_DETECTION_THRESHOLD = 5  # Time in seconds required to start attendance

attendance_started = False  # Flag to start attendance after teacher detection
teacher_seen_time = None  

recording = False
video_writer = None
video_capture = None # Camera will be opened dynamically
video_path = None 
current_class = None
latest_frame = None  # Shared frame for Flask stream


def get_current_class():
    """Check if the current time matches a class period."""
    current_day = datetime.today().strftime('%A')
    current_time = datetime.now().strftime('%H:%M')

    if current_day in TIMETABLE:
        for start_time, end_time, subject in TIMETABLE[current_day]:
            if start_time <= current_time < end_time:
                return start_time, end_time, subject
    return None

def get_teacher():
    """Get the current teacher and the list of all teachers."""
    current_class = get_current_class()
    
    if not current_class:
        return None, list(set(teacher["Teacher"] for teacher in teachers))  # Return teacher list even if no class

    start_time, end_time, subject = current_class
    teacher_list = list(set(teacher["Teacher"] for teacher in teachers))
    
    current_teacher = None
    for teacher in teachers:
        if teacher["Subject"] == subject:
            current_teacher = teacher["Teacher"]
            break  # Stop searching once the teacher is found
    
    return current_teacher, teacher_list


def is_within_schedule():
    """Check if the current time falls within any scheduled period."""
    now = datetime.now()
    current_day = now.strftime("%A")
    current_time = now.strftime("%H:%M")
    
    if current_day in TIMETABLE:
        for start, stop, subject in TIMETABLE[current_day]:
            if start <= current_time < stop:
                return True
    return False

def start_recording(subject):
    """Start recording when a class starts."""
    global video_writer, video_path, recording
    FPS = 20

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    

    url = 'http://192.168.165.54:8080/video'

    # video_capture = cv2.VideoCapture(url)

    video_capture = cv2.VideoCapture(0)

    if not video_capture.isOpened():
        print("❌ Error: Could not open webcam.")
        return None
    
    # Set video resolution
    video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
    video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 640)

    # Get video width and height
    width = int(video_capture.get(4))
    height = int(video_capture.get(3))

    # Ensure FPS is correctly set
    # actual_fps = video_capture.get(cv2.CAP_PROP_FPS) or FPS
    actual_fps = FPS  # Use a fixed FPS for simplicity
    # slow_fps = actual_fps   # Slow down the video to 1/4 of the original speed

    # video_capture.set(cv2.CAP_PROP_FPS, slow_fps)

    # fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fourcc = cv2.VideoWriter_fourcc(*'XVID')

    # video_path = os.path.join(VIDEO_DIR, f"{subject}_{timestamp}.mp4")
    video_path = os.path.join(VIDEO_DIR, f"{subject}_{timestamp}.avi")

    video_writer = cv2.VideoWriter(video_path, fourcc, actual_fps, (width, height))
    recording = True

    print(f"🎥 Started recording: {subject} ({video_path})")
    return video_capture


def stop_recording(video_capture):
    """Stop recording when the class ends."""
    global video_writer, recording, latest_frame

    if video_writer:
        video_writer.release()
        video_writer = None

    if video_capture and video_capture.isOpened():
        video_capture.release()
        cv2.destroyAllWindows()
        video_capture = None

    recording = False
    latest_frame = None
    print(f"✅ Stopped recording: ({video_path})\n")

def save_attendance(current_class, student_presence):
    """Save attendance for each class in a separate file."""
    start_time, end_time, subject = current_class
    present_students = [name for name, status in student_presence.items() if status == "Present"] 
    
    # Create a filename based on the subject and start time
    timestamp = datetime.now().strftime("%Y%m%d")
    filename = f"{subject.replace(' ', '_')}_{timestamp}_{start_time.replace(':','-')}.txt"
    attendance_path = os.path.join(ATTENDANCE_DIR, filename)
    
    # Write attendance to the file
    with open(attendance_path, "w") as file:
        file.write(f"Class: {subject}\n")
        file.write(f"Time: {start_time} - {end_time}\n\n")
        file.write("Present Students:\n")
        for student in present_students:
            file.write(f"- {student}\n")
    
    print(f"📋 Attendance saved in '{attendance_path}'.")
    # print("📋 List of Present Students:")
    # for student in present_students:
    #     print(f"- {student}")
    print("✅ Attendance recorded successfully!\n")
    

def detect_faces(frame):
    global teacher_seen_time, attendance_started

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame)
    current_face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    corrent_teacher, teacher_list = get_teacher()

    for (top, right, bottom, left), face_encoding in zip(face_locations, current_face_encodings):
        name = "Unknown"
        box_color = (0, 0, 255)  # Default: Red for unknown

        # Compare faces
        face_matches = face_recognition.compare_faces(face_encodings, face_encoding)
        face_distances = face_recognition.face_distance(face_encodings, face_encoding)

        if any(face_matches):
            best_match_index = np.argmin(face_distances)
            if face_matches[best_match_index]:
                name = face_names[best_match_index]

                # ✅ If the correct subject teacher is detected
                if name == corrent_teacher:
                    box_color = (255, 255, 255)  # White for subject teacher

                    if teacher_seen_time is None:
                        teacher_seen_time = datetime.now()
                    elif (datetime.now() - teacher_seen_time).seconds >= TEACHER_DETECTION_THRESHOLD:
                        if not attendance_started:
                            print(f"👨‍🏫 Correct teacher {name} detected! Attendance started.")
                            attendance_started = True


                # If it's a different teacher
                elif name in teacher_list:
                    box_color = (255, 0, 0)  # Blue for other teachers
                    # logging.info(f"Other teacher detected: {name}")

                # ✅ If a student is detected *after* attendance has started
                elif name in student_names:
                    box_color = (0, 255, 0)  # Green for students

                    if attendance_started:
                        if name not in student_presence:
                            student_presence[name] = datetime.now()
                            logging.info(f"Student {name} detected at {student_presence[name]}")
                        elif isinstance(student_presence[name], datetime):
                            if (datetime.now() - student_presence[name]).seconds >= STUDENT_PRESENCE_THRESHOLD:
                                student_presence[name] = "Present"
                                logging.info(f"Student {name} marked as 'Present'.")

        # Draw box and label on frame
        cv2.rectangle(frame, (left, top), (right, bottom), box_color, 2)
        cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, box_color, 2)

    return frame

# Main execution loop
def main():

    global teacher_seen_time, attendance_started, latest_frame, recording, video_writer, video_capture, current_class, student_presence

    print("⏳ System is waiting for a scheduled class...\n")

    # print("⏳ Waiting for 10 sec before starting recording...")
    # time.sleep(10)
    # print("✅ Started checking timetable for recording.")

    while True:

        class_info = get_current_class()

        if class_info:
            start_time, end_time, subject = class_info
            current_class = (start_time, end_time, subject)
            
            video_capture = start_recording(subject)
            if video_capture is None:
                continue  # Skip to the next iteration if webcam couldn't be opened
            
            if video_capture and video_capture.isOpened():
                while is_within_schedule():
                    ret, frame = video_capture.read()
                    if ret:
                        # video_writer.write(frame)
                        # continue  # Skip to the next iteration if frame couldn't be read

                        detect_faces(frame)

                    # latest_frame = frame.copy()

                    # frame_w = detect_faces(frame)
                    latest_frame = frame.copy()
 
                    if recording: 
                        video_writer.write(frame)
                    
                    # Show the recording on screen
                    cv2.putText(frame, f"Recording: {subject}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                    cv2.imshow("Face Recognition & Attendance", frame)

                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        stop_recording(video_capture)
                        video_capture = None

        else:
            if recording:
                stop_recording(video_capture)
                save_attendance(current_class, student_presence)
                video_capture = None
                
                teacher_seen_time = None  # Reset confirmation timer
                attendance_started = False  # Stop attendance if wrong teacher appears
                student_presence.clear()

                print("⏳ Waiting for the next class...\n")

        time.sleep(1)  # Sleep for a short duration to avoid high CPU usage


def generate_frames():
    global latest_frame
    while True:
        if latest_frame is None:
            continue
        ret, buffer = cv2.imencode('.jpg', latest_frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        

@app.route('/')
def index():
    return render_template_string('''
        <html>
            <head><title>Live Video</title></head>
            <body>
                <h1>Live Camera Feed</h1>
                <img src="{{ url_for('video_feed') }}" width="640" height="480">
            </body>
        </html>
    ''')

 
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

            

def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)

if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    try:
        main()  # Run your original attendance system
    except KeyboardInterrupt:
        if video_capture:
            stop_recording(video_capture)
        cv2.destroyAllWindows()
        print("❌ System interrupted. Exiting...")