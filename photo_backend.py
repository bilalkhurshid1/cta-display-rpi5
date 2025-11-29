#!/usr/bin/env python3
import os
import shutil
from datetime import datetime
from flask import Flask, request, render_template, abort, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 20MB max upload

# === CONFIG ===

load_dotenv()

# Long, random token – replace this with the output from secrets.token_hex(32)
token = os.environ.get("UPLOAD_TOKEN")
if not token:
    raise RuntimeError("UPLOAD_TOKEN must be set in the environment (.env)")

# Where cta-display.py will read the background from:
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BG_PATH = os.path.join(BASE_DIR, "background", "current.jpg")
DEFAULT_IMAGE_PATH = os.path.join(BASE_DIR, "images", "default.jpg")

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp", "HEIC", "heic"}

# === HELPERS ===

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# === ROUTES ===

@app.route("/upload/<secret>", methods=["GET", "POST"])
def upload(secret: str):
    # Wrong token? Pretend this doesn't exist.
    if secret != token:
        abort(404)

    if request.method == "GET":
        return render_template("upload.html")

    # POST: process upload
    if "photo" not in request.files:
        return render_template("upload.html"), 400

    file = request.files["photo"]
    if file.filename == "":
        return render_template("upload.html"), 400

    if not allowed_file(file.filename):
        return render_template("upload.html"), 400

    os.makedirs(os.path.dirname(BG_PATH), exist_ok=True)

    safe_name = secure_filename(file.filename)
    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    tmp_path = os.path.join(os.path.dirname(BG_PATH), f"tmp-{ts}-{safe_name}")

    file.save(tmp_path)
    os.replace(tmp_path, BG_PATH)  # overwrite any existing background

    return render_template("upload.html")


@app.route("/reset/<secret>", methods=["POST"])
def reset_to_default(secret: str):
    """Reset background to default image"""
    # Wrong token? Pretend this doesn't exist.
    if secret != token:
        abort(404)

    try:
        # Check if default image exists
        if not os.path.exists(DEFAULT_IMAGE_PATH):
            return jsonify({"success": False, "error": "Default image not found"}), 404

        # Create background directory if it doesn't exist
        os.makedirs(os.path.dirname(BG_PATH), exist_ok=True)

        # Copy default image to background
        shutil.copy2(DEFAULT_IMAGE_PATH, BG_PATH)

        return jsonify({"success": True, "message": "Background reset to default"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}, 200

@app.route("/images/<path:filename>")
def serve_image(filename):
    """Serve images from the images directory"""
    images_dir = os.path.join(BASE_DIR, "images")
    return send_from_directory(images_dir, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)