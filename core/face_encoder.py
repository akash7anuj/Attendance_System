import os, face_recognition, pickle
from config import ENCODING_DIR

def load_student_encodings(class_name):
    path = os.path.join(ENCODING_DIR, f"student_{class_name}_encodings.pkl")
    with open(path, "rb") as f:
        return pickle.load(f)

def load_teacher_encodings():
    path = os.path.join(ENCODING_DIR, "teacher_encodings.pkl")
    with open(path, "rb") as f:
        return pickle.load(f)