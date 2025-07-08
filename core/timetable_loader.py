import os, json
from datetime import datetime
from config import TIMETABLE_DIR

def load_timetable(class_name):
    path = os.path.join(TIMETABLE_DIR, f"{class_name}_timetable.json")
    if not os.path.exists(path): return {}
    with open(path) as f:
        return json.load(f)

def get_current_class(class_name):
    timetable = load_timetable(class_name)
    now = datetime.now()
    day = now.strftime("%A")
    time_now = now.strftime("%H:%M")

    if day not in timetable: return None

    for slot in timetable[day]:
        start, end, subject = slot
        if start <= time_now < end:
            return (start, end, subject)
    return None

def is_within_schedule(current_class):
    if not current_class: return False
    start, end, _ = current_class
    now = datetime.now().strftime("%H:%M")
    return start <= now < end