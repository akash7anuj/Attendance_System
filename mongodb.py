import os
from pymongo import MongoClient
import gridfs

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["attendance_system"]
fs = gridfs.GridFS(db)

def upload_static_to_mongodb(static_root="static"):
    for root, _, files in os.walk(static_root):
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, static_root)  # e.g., attendance/bca/14-06-2025/file.txt

            # Skip if already exists
            if fs.exists({"filename": rel_path}):
                print(f"⚠️ Already exists in DB: {rel_path}")
                continue

            with open(full_path, "rb") as f:
                fs.put(f, filename=rel_path, path=root, content_type=get_content_type(file))
                print(f"✅ Uploaded: {rel_path}")

def get_content_type(filename):
    if filename.endswith(".mp4"):
        return "video/mp4"
    elif filename.endswith(".txt"):
        return "text/plain"
    elif filename.endswith(".json"):
        return "application/json"
    elif filename.endswith((".jpg", ".jpeg", ".png")):
        return "image/jpeg"
    else:
        return "application/octet-stream"
    
def download_file_from_mongodb(filename, output_path):
    file = fs.find_one({"filename": filename})
    if file:
        with open(output_path, "wb") as f:
            f.write(file.read())
        print("✅ Downloaded:", output_path)
    else:
        print("❌ Not found:", filename)


if __name__ == "__main__":
    upload_static_to_mongodb("static")