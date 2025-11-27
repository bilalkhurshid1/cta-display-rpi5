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
		<meta charset="UTF-8" />
		<title>CTA Background Upload</title>
		<meta name="viewport" content="width=device-width, initial-scale=1" />
		<style>
			body {
				margin: 0;
				padding: 0;
				font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
					sans-serif;
				background-image: url(/images/henderson.png);
				background-size: 100% 100%;
				background-position: center center;
				background-repeat: no-repeat;
				min-height: 100svh;
			}

			/* Center the upload control */
			.container {
				min-height: 100svh;
				display: flex;
				align-items: center;
				justify-content: center;
				text-align: center;
			}

			/* Image button resets */
			#image-upload-btn {
				background: transparent;
				border: none;
				padding: 0;
				margin: 0;
				line-height: 0;
				cursor: pointer;
				-webkit-tap-highlight-color: transparent;
				transform: translateY(-75px);
			}

			#image-upload-btn:disabled {
				opacity: 0.6;
				cursor: default;
			}

			/* Float wrapper carries the hover animation */
			.float-wrap {
				display: inline-block;
				animation: float 3s ease-in-out infinite;
				will-change: transform;
			}

			/* Responsive red button image */
			#red-button-img {
				display: block;
				width: min(60vw, 320px);
				height: auto;
				filter: blur(0.3px) drop-shadow(0 0 8px rgba(255, 0, 0, 0.5))
					drop-shadow(0 0 16px rgba(255, 0, 0, 0.35));
				will-change: transform, filter;
			}

			@media (max-width: 360px) {
				#red-button-img {
					width: 70vw;
				}
			}

			/* Hover/active states: slightly stronger glow and lift */
			#image-upload-btn:hover #red-button-img,
			#image-upload-btn:focus-visible #red-button-img {
				filter: blur(0.3px) drop-shadow(0 0 10px rgba(255, 0, 0, 0.7))
					drop-shadow(0 0 20px rgba(255, 0, 0, 0.5));
				transform: translateY(-3px);
			}

			#image-upload-btn:active #red-button-img {
				transform: translateY(4px);
				filter: blur(0.3px) drop-shadow(0 0 12px rgba(255, 0, 0, 0.8))
					drop-shadow(0 0 24px rgba(255, 0, 0, 0.6));
			}

			/* Gentle float animation */
			@keyframes float {
				0% {
					transform: translateY(0);
				}
				50% {
					transform: translateY(-6px);
				}
				100% {
					transform: translateY(0);
				}
			}

			/* Respect reduced motion */
			@media (prefers-reduced-motion: reduce) {
				.float-wrap {
					animation: none;
				}
			}
		</style>
	</head>
	<body>
		<div class="container" style="text-align: center">
			<button
				id="image-upload-btn"
				type="button"
				aria-label="Upload background"
				style="background-color: transparent; border: none"
			>
				<span class="float-wrap">
					<img id="red-button-img" src="/images/redbutton.png" alt="Upload" />
				</span>
			</button>

			<form
				method="POST"
				action=""
				enctype="multipart/form-data"
				id="upload-form"
			>
				<input
					type="file"
					id="photo"
					name="photo"
					accept="image/*"
					required
					style="display: none"
				/>
			</form>
		</div>

		<script>
			const form = document.getElementById("upload-form");
			const fileInput = document.getElementById("photo");
			const imageButton = document.getElementById("image-upload-btn");

			imageButton.addEventListener("click", () => {
				fileInput.click();
			});

			fileInput.addEventListener("change", (e) => {
				if (fileInput.files && fileInput.files.length > 0) {
					const file = fileInput.files[0];
					const reader = new FileReader();
					const containerWidth = 320;
					const containerHeight = 240;
					const imageWidth = 280;
					const imageHeight = 200;

					reader.onload = function (e) {
						imageButton.innerHTML = `
							<div style="position: relative; width: ${containerWidth}px; height: ${containerHeight}px; display: flex; align-items: center; justify-content: center; padding: 20px; box-sizing: border-box;">
								<div style="color: #fff; font-size: 1.2rem; font-weight: 600; text-align: center;">Thank you!</div>
							</div>
						`;

						const formData = new FormData(form);

						fetch(form.action || window.location.href, {
							method: "POST",
							body: formData,
						})
							.then((response) => response.text())
							.then(() => {
								imageButton.innerHTML = `
								<div style="position: relative; width: ${containerWidth}px; height: ${containerHeight}px; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 20px; box-sizing: border-box; gap: 10px;">
									<div style="color: #fff; font-size: 1.2rem; font-weight: 600; text-align: center;">Background updated!</div>
									<img src="${e.target.result}" alt="Preview" style="width: 60px; height: 60px; object-fit: contain;">
								</div>
							`;

								// Start flying images animation
								startFlyingImages();
							})
							.catch((error) => {
								console.error("Upload failed:", error);
								imageButton.innerHTML = `
								<div style="position: relative; width: ${containerWidth}px; height: ${containerHeight}px; display: flex; align-items: center; justify-content: center; padding: 20px; box-sizing: border-box;">
									<div style="color: #ff6b6b; font-size: 1.2rem; font-weight: 600; text-align: center;">Upload failed</div>
								</div>
							`;
							});
					};

					reader.readAsDataURL(file);
				}
			});

			// Flying images animation function
			function startFlyingImages() {
				const images = [
					"/images/joey.png",
					"/images/bilal.png",
					"/images/clark.png",
					"/images/harry.png",
				];

				let counter = 0;
				for (let i = 0; i < 10; i++) {
					images.forEach((src) => {
						setTimeout(() => {
							createFlyingImage(src);
						}, counter * 150);
						counter++;
					});
				}
			}

			function createFlyingImage(src) {
				const img = document.createElement("img");
				img.src = src;
				img.style.cssText = `
					position: fixed;
					top: ${Math.random() * 90}%;
					width: 150px;
					height: 150px;
					object-fit: contain;
					z-index: 1000;
					pointer-events: none;
				`;

				// Random direction: right to left or left to right
				const direction = Math.random() > 0.5 ? "rtl" : "ltr";
				if (direction === "rtl") {
					img.style.right = "-200px";
					img.style.animation = "flyRightToLeft 3s linear forwards";
				} else {
					img.style.left = "-200px";
					img.style.animation = "flyLeftToRight 3s linear forwards";
				}

				document.body.appendChild(img);

				// Remove image after animation completes
				setTimeout(() => {
					img.remove();
				}, 3000);
			}

			// Add CSS animations
			const style = document.createElement("style");
			style.textContent = `
				@keyframes flyRightToLeft {
					from {
						transform: translateX(0) rotate(0deg);
					}
					to {
						transform: translateX(-120vw) rotate(720deg);
					}
				}
				
				@keyframes flyLeftToRight {
					from {
						transform: translateX(0) rotate(0deg);
					}
					to {
						transform: translateX(120vw) rotate(720deg);
					}
				}
			`;
			document.head.appendChild(style);
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
