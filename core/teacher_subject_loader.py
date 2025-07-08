import os, json
from config import SUBJECT_DIR

def load_teacher_subjects(class_name):
    path = os.path.join(SUBJECT_DIR, f"{class_name}_subjects.json")
    if not os.path.exists(path): return []
    with open(path) as f:
        return json.load(f)

def get_correct_teacher(subject_mapping, current_subject):
    if not current_subject: return None
    for record in subject_mapping:
        if record['subject'].lower() == current_subject.lower():
            return record['teacher']
    return None