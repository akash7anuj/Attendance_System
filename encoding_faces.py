import os
import face_recognition
import pickle

# Directory locations
STUDENT_DIR = "static/student_images"
TEACHER_DIR = "static/teacher_images"

ENCODING_DIR = "encodings_faces"

# Ensure encodings directory exists
os.makedirs(ENCODING_DIR, exist_ok=True)

def encode_faces(folder_path):
    encodings = []
    names = []
    for filename in os.listdir(folder_path):
        if filename.endswith((".jpg", ".jpeg", ".png")):
            path = os.path.join(folder_path, filename)
            name = os.path.splitext(filename)[0]
            image = face_recognition.load_image_file(path)
            encoding = face_recognition.face_encodings(image)
            if encoding:
                encodings.append(encoding[0])
                names.append(name)
    return encodings, names

# ✅ Encode teachers (only once since common)
print("Encoding teachers...")
teacher_encodings, teacher_names = encode_faces(TEACHER_DIR)
with open(os.path.join(ENCODING_DIR, "teacher_encodings.pkl"), "wb") as f:
    pickle.dump((teacher_encodings, teacher_names), f)

# ✅ Automatically loop through all student classes
for class_name in os.listdir(STUDENT_DIR):
    class_path = os.path.join(STUDENT_DIR, class_name)
    if os.path.isdir(class_path):
        print(f"Encoding students for class: {class_name}")
        student_encodings, student_names = encode_faces(class_path)
        filename = f"student_{class_name}_encodings.pkl"
        with open(os.path.join(ENCODING_DIR, filename), "wb") as f:
            pickle.dump((student_encodings, student_names), f)

print("✅ All encodings generated successfully!")
