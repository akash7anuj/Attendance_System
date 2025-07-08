import time
import cv2
from core.timetable_loader import get_current_class, is_within_schedule
from core.teacher_subject_loader import load_teacher_subjects, get_correct_teacher
from core.face_encoder import load_student_encodings, load_teacher_encodings
from core.face_detector import detect_faces, student_presence, teacher_seen_time, attendance_started
from core.video_recorder import start_recording, write_frame, stop_recording
from core.attendance_saver import save_attendance

# latest frame will be shared globally for streaming
import threading

latest_frame = None
frame_lock = threading.Lock()


def main(class_name):
    global latest_frame, student_presence, teacher_seen_time, attendance_started

    student_encodings, student_names = load_student_encodings(class_name)
    teacher_encodings, teacher_names = load_teacher_encodings()
    subject_mappings = load_teacher_subjects(class_name)
    
    while True:
        current_class = get_current_class(class_name)

        if current_class:
            start, end, subject = current_class
            correct_teacher = get_correct_teacher(subject_mappings, subject)
            print(f"📅 Scheduled Class Found: {subject} | Waiting for teacher verification...")

            video_cap = start_recording(subject, class_name)
            if not video_cap:
                continue

            while is_within_schedule(current_class):
                ret, frame = video_cap.read()
                if not ret:
                    continue

                frame = detect_faces(frame, student_encodings, student_names, teacher_encodings, teacher_names, correct_teacher)
                
                with frame_lock:
                    latest_frame = frame.copy()


                write_frame(frame)

                cv2.putText(frame, f"Recording: {subject}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.imshow(f"Attendance - {class_name.upper()}", frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    stop_recording()
                    video_cap = None

            stop_recording()
            save_attendance(current_class, student_presence, class_name)
            video_cap = None
            teacher_seen_time, attendance_started = None, False
            student_presence.clear()

        else:
            time.sleep(1)



import time
import cv2
from flask import Flask, Response, render_template_string
from core.main import latest_frame  # importing the global frame from main
import threading

frame_lock = threading.Lock()

app = Flask(__name__)

def generate_frames():
    global latest_frame
    while True:
        with frame_lock:
            frame = latest_frame

        if frame is None:
            time.sleep(0.05)
            continue

        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue

        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
@app.route('/')
def index():
    return render_template_string('''
        <html>
            <head><title>Live Video</title></head>
            <body>
                <h1>Live Camera Feed</h1>
                <img src="{{ url_for('stream') }}" width="640" height="480">
            </body>
        </html>
    ''')

@app.route('/stream')
def stream():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
