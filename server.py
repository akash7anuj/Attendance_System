from flask import Flask, render_template, Response, flash
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user

import os
from flask import send_from_directory
import pandas as pd
from flask import request, jsonify
from flask import redirect, url_for
import json
import re

from config import ip_address, USERS



app = Flask(__name__)

app.secret_key = 'secret_key_here'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Dummy user store
# USERS = {
#     "admin": {"password": "admin123", "role": "Admin"},
#     "teacher": {"password": "teach2025", "role": "Teacher"}
# }

class User(UserMixin):
    def __init__(self, id, role):
        self.id = id
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    if user_id in USERS:
        return User(user_id, USERS[user_id]['role'])
    return None

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = USERS.get(username)
        if user and user["password"] == password:
            login_user(User(username, user["role"]))
            flash("Logged in successfully!", "success")
            return redirect(url_for("attendance_system"))
        else:
            flash("Invalid credentials", "danger")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully", "info")
    return redirect(url_for("login"))

# ======================
# Home Route (You may already have this)
# ======================

@app.route("/attendance_system")
@login_required
def attendance_system():
    return render_template("index.html")

# @app.route('/')
# def index():
#     return render_template('index.html')


# ======================
# Live Streaming Main Page
# ======================

@app.route('/livestream')
def livestream():
    return render_template("livestream2.html",ip_address=ip_address)

@app.route('/view/<classname>')
def view_fullscreen(classname):
    if classname in ip_address:
        return render_template("livestream_view.html", classname=classname, stream_url=ip_address[classname])
    else:
        return "Class not found", 404


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
# VIDEO_DIR = os.path.join(ROOT_DIR, "static", "recorded_videos")

VIDEO_DIR = 'static/recorded_videos'

# Show class list
@app.route('/recordings')
def list_classes():
    classes = os.listdir(VIDEO_DIR)
    return render_template("recordings_classes.html", classes=classes)

# Show dates for selected class
@app.route('/recordings/<classname>')
def list_dates(classname):
    class_path = os.path.join(VIDEO_DIR, classname)
    if not os.path.exists(class_path):
        dates = []
    else:
        dates = os.listdir(class_path)
    return render_template("recordings_dates.html", classname=classname, dates=dates)

# Show videos for selected class and date
@app.route('/recordings/<classname>/<date>')
def list_videos(classname, date):
    video_path = os.path.join(VIDEO_DIR, classname, date)
    if not os.path.exists(video_path):
        videos = []
    else:
        videos = [f for f in os.listdir(video_path) if f.endswith('.mp4')]
    return render_template("recordings_videos.html", classname=classname, date=date, videos=videos)

# Video streaming route
@app.route('/recordings/<classname>/<date>/play/<filename>')
def play_video(classname, date, filename):
    return render_template('recording_view.html', classname=classname, date=date, filename=filename)


@app.route('/video/<classname>/<date>/<filename>')
def stream_video(classname, date, filename):
    video_path = os.path.join(VIDEO_DIR, classname, date, filename)
    if not os.path.exists(video_path):
        return "File not found", 404

    return partial_response(video_path)

# Streaming function
def partial_response(path):
    range_header = request.headers.get('Range', None)
    if not range_header:
        return Response(open(path, 'rb'), mimetype="video/mp4")

    size = os.path.getsize(path)
    byte1, byte2 = 0, None

    m = re.search(r'(\d+)-(\d*)', range_header)
    if m:
        g = m.groups()
        byte1 = int(g[0])
        if g[1]:
            byte2 = int(g[1])

    chunk_size = 1024 * 1024
    byte2 = byte2 if byte2 else size - 1
    length = byte2 - byte1 + 1

    with open(path, 'rb') as f:
        f.seek(byte1)
        data = f.read(length)

    rv = Response(data, 206, mimetype='video/mp4',
                  content_type='video/mp4',
                  direct_passthrough=True)
    rv.headers.add('Content-Range', f'bytes {byte1}-{byte2}/{size}')
    rv.headers.add('Accept-Ranges', 'bytes')
    return rv



BASE_ATTENDANCE_DIR = 'static/attendance'

# Main attendance page route
@app.route('/attendance')
def attendance():
    # Get list of classes
    if not os.path.exists(BASE_ATTENDANCE_DIR):
        os.makedirs(BASE_ATTENDANCE_DIR)

    classes = [d for d in os.listdir(BASE_ATTENDANCE_DIR) if os.path.isdir(os.path.join(BASE_ATTENDANCE_DIR, d))]
    return render_template('attendance.html', classes=sorted(classes))


# Get available dates for selected class
@app.route('/get_dates', methods=['POST'])
def get_dates():
    classname = request.form['classname']
    class_path = os.path.join(BASE_ATTENDANCE_DIR, classname)

    if not os.path.exists(class_path):
        return jsonify([])

    dates = [d for d in os.listdir(class_path) if os.path.isdir(os.path.join(class_path, d))]
    dates.sort(reverse=True)
    return jsonify(dates)


# Get available files for selected class + date
@app.route('/get_files', methods=['POST'])
def get_files():
    classname = request.form['classname']
    date = request.form['date']
    path = os.path.join(BASE_ATTENDANCE_DIR, classname, date)

    if not os.path.exists(path):
        return jsonify([])

    files = [f for f in os.listdir(path) if f.endswith(('.csv', '.txt'))]
    files.sort()
    return jsonify(files)


# Load selected attendance file and return HTML table
@app.route('/get_table', methods=['POST'])
def get_table():
    classname = request.form['classname']
    date = request.form['date']
    filename = request.form['filename']
    filepath = os.path.join(BASE_ATTENDANCE_DIR, classname, date, filename)

    try:
        # Handle CSV and TXT (assuming txt is comma separated)
        if filename.endswith('.csv'):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_csv(filepath, delimiter=',')  # you can change delimiter if needed

        table_html = df.to_html(classes="table table-striped table-bordered", index=False, border=0)
        return jsonify({'table': table_html})

    except Exception as e:
        return jsonify({'table': f"<div class='alert alert-danger'>Error reading file: {e}</div>"})


# Download route (optional)
@app.route('/download')
def download():
    classname = request.args.get('classname')
    date = request.args.get('date')
    filename = request.args.get('filename')

    directory = os.path.join(BASE_ATTENDANCE_DIR, classname, date)
    return send_from_directory(directory, filename, as_attachment=True)



app.config['UPLOAD_FOLDER'] = 'static/student_images'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

# Ensure folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Return allowed extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/students')
def students():
    # This route can be used to show a list of students or a form to add new students
    return render_template('student.html')

@app.route('/upload_students')
def upload_students():
    classes = ['bca', 'mca', 'btech']  # You can load this from DB too
    return render_template('students_upload.html', classes=classes)


@app.route('/upload_student', methods=['POST'])
def upload_student():
    classname = request.form.get('classname')
    name = request.form.get('name')
    rollno = request.form.get('rollno')
    file = request.files.get('file')

    if not all([classname, name, rollno, file]):
        return "Missing data", 400

    # Create class folder if not exists
    class_folder = os.path.join(app.config['UPLOAD_FOLDER'], classname)
    os.makedirs(class_folder, exist_ok=True)

    # Prepare new filename
    first_name = name.strip().split()[0].lower()
    new_filename = f"{first_name}_{rollno}.jpg"

    file_path = os.path.join(class_folder, new_filename)
    file.save(file_path)

    return redirect(url_for('upload_students'))

@app.route('/view_students')
def view_students():
    classes = ['bca', 'mca', 'btech']  # same as before
    return render_template('student_view.html', classes=classes)



@app.route('/get_students/<classname>')
def get_students(classname):
    class_folder = os.path.join(app.config['UPLOAD_FOLDER'], classname)
    if not os.path.exists(class_folder):
        return jsonify([])
    
    files = [f for f in os.listdir(class_folder) if allowed_file(f)]
    data = []
    for f in files:
        parts = f.rsplit('.', 1)[0].split('_')
        if len(parts) == 2:
            data.append({'filename': f, 'name': parts[0].capitalize(), 'rollno': parts[1]})
    return jsonify(data)


@app.route('/delete_student/<classname>/<filename>', methods=['POST'])
def delete_student(classname, filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], classname, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    return jsonify({'success': True})


@app.route('/download_student/<classname>/<filename>')
def download_student(classname, filename):
    folder = os.path.join(app.config['UPLOAD_FOLDER'], classname)
    return send_from_directory(folder, filename, as_attachment=True)


@app.route('/teachers')
def teachers():
    return render_template('teachers.html')

@app.route('/upload_teachers')
def upload_teachers():
    return render_template('teachers_upload.html')

@app.route('/upload_teacher', methods=['POST'])
def upload_teacher():
    teacher_name = request.form['teacher_name'].strip().replace(" ", "_").lower()
    file = request.files['teacher_image']

    if not teacher_name or not file:
        return "Missing data", 400

    # Create folder if not exists
    teacher_folder = os.path.join('static', 'teacher_images')
    os.makedirs(teacher_folder, exist_ok=True)

    # Save as TeacherName.jpg
    filename = f"{teacher_name}.jpg"
    file_path = os.path.join(teacher_folder, filename)
    file.save(file_path)

    return redirect(url_for('upload_teachers'))

@app.route('/view_teachers')
def view_teachers():
    return render_template('teachers_view.html')

# Get all teacher images
@app.route('/get_teachers')
def get_teachers():
    teacher_folder = os.path.join('static', 'teacher_images')
    os.makedirs(teacher_folder, exist_ok=True)

    files = [f for f in os.listdir(teacher_folder) if f.endswith(('.jpg', '.jpeg', '.png'))]
    files.sort()

    teachers = []
    for file in files:
        name = os.path.splitext(file)[0].replace("_", " ").title()
        teachers.append({'filename': file, 'name': name})
    return jsonify(teachers)

# Delete teacher image
@app.route('/delete_teacher/<filename>', methods=['POST'])
def delete_teacher(filename):
    teacher_folder = os.path.join('static', 'teacher_images')
    file_path = os.path.join(teacher_folder, filename)

    if os.path.exists(file_path):
        os.remove(file_path)
        return jsonify({'success': True})
    else:
        return jsonify({'success': False})

# Download teacher image
@app.route('/download_teacher/<filename>')
def download_teacher(filename):
    teacher_folder = os.path.join('static', 'teacher_images')
    return send_from_directory(teacher_folder, filename, as_attachment=True)


TIMETABLE_FOLDER = os.path.join('static', 'timetables')
os.makedirs(TIMETABLE_FOLDER, exist_ok=True)

# Predefined classes
CLASSES = ['bca', 'mca', 'btech']

# --------- Routes ----------

@app.route('/timetable')
def timetable():    
    return render_template('time_json.html', classes=CLASSES)

# View timetable page (main page)
@app.route('/view_timetable')
def view_timetable():
    return render_template('timetable_view.html', classes=CLASSES)

# Edit timetable page
@app.route('/edit_timetable')
def edit_timetable():
    return render_template('timetable_edit.html', classes=CLASSES)

# Load timetable API
@app.route('/load_timetable', methods=['POST'])
def load_timetable():
    data = request.get_json()
    class_name = data['className']

    filepath = os.path.join(TIMETABLE_FOLDER, f"{class_name}_timetable.json")
    if not os.path.exists(filepath):
        return jsonify({})

    with open(filepath, 'r') as f:
        timetable = json.load(f)

    return jsonify(timetable)

# Save timetable API
@app.route('/save_timetable', methods=['POST'])
def save_timetable():
    data = request.get_json()
    class_name = data['className']
    timetable_data = data['timetable']

    filepath = os.path.join(TIMETABLE_FOLDER, f"{class_name}_timetable.json")

    with open(filepath, 'w') as f:
        json.dump(timetable_data, f, indent=4)

    return "Timetable saved successfully!"

@app.route('/teacher_subjects')
def teacher_subjects():
    return render_template('teachers_subjects.html', classes=CLASSES)

@app.route('/save_teacher_subjects', methods=['POST'])
def save_teacher_subjects():
    data = request.get_json()
    class_name = data['className']
    records = data['records']

    folder = os.path.join('static', 'teacher_subjects')
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, f"{class_name}_subjects.json")

    with open(filepath, 'w') as f:
        json.dump(records, f, indent=4)

    return "Subjects saved successfully!"

@app.route('/load_teacher_subjects', methods=['POST'])
def load_teacher_subjects():
    data = request.get_json()
    class_name = data['className']

    folder = os.path.join('static', 'teacher_subjects')
    filepath = os.path.join(folder, f"{class_name}_subjects.json")

    if not os.path.exists(filepath):
        return jsonify([])

    with open(filepath, 'r') as f:
        records = json.load(f)

    return jsonify(records)


# # ======================
# # Run Flask App
# # ======================
# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5005, debug=True)
