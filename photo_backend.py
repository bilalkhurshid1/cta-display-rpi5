#!/usr/bin/env python3
import os
from datetime import datetime
from flask import Flask, request, render_template_string, abort
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

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp", "HEIC", "heic"}


# === HTML TEMPLATE ===

UPLOAD_FORM_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>CTA Background Upload</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body {
      margin: 0;
      padding: 0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #050510;
      color: #f5f5f5;
    }
    .container {
      max-width: 420px;
      margin: 24px auto;
      padding: 24px 18px;
      border-radius: 16px;
      background: linear-gradient(145deg, #11111f, #050510);
      box-shadow: 0 10px 30px rgba(0,0,0,0.6);
    }
    h1 {
      margin: 0 0 4px;
      font-size: 1.6rem;
    }
    p.subtitle {
      margin: 0 0 16px;
      font-size: 0.9rem;
      color: #aaa;
    }
    label {
      display: block;
      margin-top: 12px;
      margin-bottom: 4px;
      font-size: 0.85rem;
      color: #ccc;
    }
    input[type="file"] {
      width: 100%;
      font-size: 1rem;
      padding: 8px;
      border-radius: 10px;
      border: 1px solid #333;
      background: #181824;
      color: #f5f5f5;
      box-sizing: border-box;
    }
    button {
      margin-top: 16px;
      width: 100%;
      padding: 10px 12px;
      font-size: 1rem;
      font-weight: 600;
      border-radius: 999px;
      border: none;
      cursor: pointer;
      background: #4b8bff;
      color: #fff;
      box-shadow: 0 6px 20px rgba(75,139,255,0.5);
    }
    button:disabled {
      opacity: 0.6;
      cursor: default;
      box-shadow: none;
    }
    .banner {
      margin-bottom: 8px;
      padding: 8px 10px;
      border-radius: 8px;
      font-size: 0.9rem;
    }
    .success {
      background: rgba(60, 179, 113, 0.15);
      border: 1px solid rgba(60, 179, 113, 0.6);
    }
    .error {
      background: rgba(255, 69, 58, 0.15);
      border: 1px solid rgba(255, 69, 58, 0.6);
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>CTA Screen Background</h1>
    <p class="subtitle">Send a photo to use as the CTA display background.</p>

    {% if success %}
      <div class="banner success">✅ Background updated.</div>
    {% elif error %}
      <div class="banner error">{{ error }}</div>
    {% endif %}

    <form method="POST" action="" enctype="multipart/form-data" id="upload-form">
      <label for="photo">Choose a photo</label>
      <input type="file" id="photo" name="photo" accept="image/*" required>
      <button type="submit" id="submit-btn">Upload</button>
    </form>
  </div>

  <script>
    const form = document.getElementById('upload-form');
    const btn = document.getElementById('submit-btn');

    form.addEventListener('submit', () => {
      btn.disabled = true;
      btn.textContent = 'Uploading...';
    });
  </script>
</body>
</html>
"""


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
        return render_template_string(UPLOAD_FORM_HTML, success=False, error=None)

    # POST: process upload
    if "photo" not in request.files:
        return render_template_string(UPLOAD_FORM_HTML, success=False, error="No file provided"), 400

    file = request.files["photo"]
    if file.filename == "":
        return render_template_string(UPLOAD_FORM_HTML, success=False, error="No file selected"), 400

    if not allowed_file(file.filename):
        return render_template_string(UPLOAD_FORM_HTML, success=False, error="Unsupported file type"), 400

    os.makedirs(os.path.dirname(BG_PATH), exist_ok=True)

    safe_name = secure_filename(file.filename)
    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    tmp_path = os.path.join(os.path.dirname(BG_PATH), f"tmp-{ts}-{safe_name}")

    file.save(tmp_path)
    os.replace(tmp_path, BG_PATH)  # overwrite any existing background

    return render_template_string(UPLOAD_FORM_HTML, success=True, error=None)


@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
