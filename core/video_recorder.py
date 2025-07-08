import cv2
import os
import subprocess
import threading
from datetime import datetime
from config import VIDEO_DIR, camera_mapping

video_capture = None
ffmpeg_process = None
recording = False
video_path = None
latest_frame = None
FPS, RES = 20, (640, 480)

def start_recording(subject, class_name):
    global video_capture, ffmpeg_process, recording, video_path

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    date_folder = datetime.now().strftime("%d-%m-%Y")
    folder = os.path.join(VIDEO_DIR, class_name, date_folder)
    os.makedirs(folder, exist_ok=True)

    video_path = os.path.join(folder, f"{subject}_{timestamp}.mp4")

    camera_id = camera_mapping.get(class_name, 0)

    # Start webcam
    video_capture = cv2.VideoCapture(camera_id)
    if not video_capture.isOpened():
        print("❌ Camera error")
        return None

    video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, RES[0])
    video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, RES[1])

    # ffmpeg command to encode in H.264 and streamable mp4
    ffmpeg_command = [
        'ffmpeg',
        '-y',  # overwrite output file if exists
        '-f', 'rawvideo',
        '-vcodec', 'rawvideo',
        '-pix_fmt', 'bgr24',
        '-s', f'{RES[0]}x{RES[1]}',
        '-r', str(FPS),
        '-i', '-',  # input from stdin
        '-an',
        '-vcodec', 'libx264',
        '-preset', 'veryfast',
        '-pix_fmt', 'yuv420p',
        '-movflags', '+faststart',  # important for browser compatibility
        video_path
    ]

    ffmpeg_process = subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE)
    recording = True
    print(f"🎥 Recording started: {video_path}")
    return video_capture

def write_frame(frame):
    if recording and ffmpeg_process:
        try:
            ffmpeg_process.stdin.write(frame.tobytes())
        except BrokenPipeError:
            print("⚠️ FFmpeg pipe broken. Stopping recording.")
            stop_recording()

def stop_recording():
    global video_capture, ffmpeg_process, recording, latest_frame

    recording = False
    latest_frame = None
    if video_capture:
        video_capture.release()
        cv2.destroyAllWindows()
        video_capture = None
    if ffmpeg_process:
        ffmpeg_process.stdin.close()
        ffmpeg_process.wait()
        ffmpeg_process = None

    

    print(f"✅ Recording stopped. Video saved: {video_path}")
