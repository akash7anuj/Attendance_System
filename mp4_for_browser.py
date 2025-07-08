import os
import subprocess

# 🔧 You just change this input file path here
input_path = r"C:\Users\Akash\Desktop\College_Attendance_System\static\recorded_videos\bca\14-06-2025\Programming with Java_20250614_225000.mp4"

# 🔧 Output path (will save alongside input)
name, ext = os.path.splitext(input_path)
output_path = f"{name}_fixed.mp4"

def convert_video(input_path, output_path):
    command = [
        "ffmpeg",
        "-i", input_path,
        "-c:v", "libx264",
        "-crf", "23",
        "-preset", "veryfast",
        "-c:a", "aac",
        "-b:a", "128k",
        output_path
    ]

    print("Running command:")
    print(" ".join(command))

    result = subprocess.run(command)

    if result.returncode == 0:
        print(f"✅ Successfully converted: {output_path}")
    else:
        print("❌ Conversion failed.")

if __name__ == "__main__":
    convert_video(input_path, output_path)
