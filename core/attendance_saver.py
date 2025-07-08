import os
from datetime import datetime
from config import ATTENDANCE_DIR

def save_attendance(current_class, student_presence, class_name):
    start, end, subject = current_class
    present = [name for name, status in student_presence.items() if status == "Present"]

    date_folder = datetime.now().strftime("%d-%m-%Y")
    class_folder = os.path.join(ATTENDANCE_DIR, class_name, date_folder)
    os.makedirs(class_folder, exist_ok=True)

    file_path = os.path.join(class_folder, f"{subject}.txt")

    with open(file_path, "w") as f:
        f.write(f"Class: {subject}\nTime: {start} - {end}\n\nPresent Students:\n")
        for student in present:
            f.write(f"- {student}\n")

    print(f"✅ Attendance saved: {file_path}")