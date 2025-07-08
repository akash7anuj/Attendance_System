import cv2, numpy as np
from datetime import datetime
from config import TEACHER_DETECTION_THRESHOLD, STUDENT_PRESENCE_THRESHOLD
import face_recognition


teacher_seen_time = None
attendance_started = False
student_presence = {}

def detect_faces(frame, student_encodings, student_names, teacher_encodings, teacher_names, correct_teacher):
    global teacher_seen_time, attendance_started, student_presence

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb)
    face_encodings = face_recognition.face_encodings(rgb, face_locations)

    all_encodings = teacher_encodings + student_encodings
    all_names = teacher_names + student_names

    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        name, color = "Unknown", (0, 0, 255)
        matches = face_recognition.compare_faces(all_encodings, face_encoding)
        face_distances = face_recognition.face_distance(all_encodings, face_encoding)

        if any(matches):
            best_match = np.argmin(face_distances)
            if matches[best_match]:
                name = all_names[best_match]

                if name == correct_teacher:
                    color = (255, 255, 255)

                    if teacher_seen_time is None:
                        teacher_seen_time = datetime.now()
                    elif (datetime.now() - teacher_seen_time).seconds >= TEACHER_DETECTION_THRESHOLD:
                        if not attendance_started:
                            attendance_started = True
                            print(f"👨‍🏫 Teacher {name} verified — Attendance started.")
                elif name in teacher_names:
                    color = (255, 0, 0)

                elif name in student_names:
                    color = (0, 255, 0)
                    
                    if attendance_started:
                        if name not in student_presence:
                            student_presence[name] = datetime.now()
                        elif isinstance(student_presence[name], datetime):
                            if (datetime.now() - student_presence[name]).seconds >= STUDENT_PRESENCE_THRESHOLD:
                                student_presence[name] = "Present"

        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.putText(frame, name, (left, top-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

    return frame