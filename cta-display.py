#!/usr/bin/env python3
"""
CTA Train ETA Display (Raspberry Pi 5 + 7" touchscreen)

- Fullscreen Tkinter app
- Background image comes from /home/bilal/cta-display-rpi5/background/current.jpg
- Text overlay shows next Brown Line → Loop trains at Paulina
"""
import os
import random
from datetime import datetime
import tkinter as tk
import requests
import numpy as np
from dateutil import parser as dateparser
from dotenv import load_dotenv
from requests.exceptions import RequestException
from PIL import Image, ImageTk

# === CONFIG ===
load_dotenv()

CTA_KEY = os.environ.get("CTA_KEY")
if not CTA_KEY:
    raise RuntimeError("CTA_KEY must be set in the environment (.env)")
PAULINA_LOOP_ROUTE_ID = "30254"      # stop ID for Paulina → Loop
REFRESH_MS = 15000                   # 15 seconds
BACKGROUND_PATH = "/home/bilal/cta-display-rpi5/background/current.jpg"

# === TK SETUP ===

root = tk.Tk()
root.title("CTA Display")
root.overrideredirect(True)  # Remove window decorations (title bar)
root.attributes("-fullscreen", True)
root.attributes("-topmost", True)
root.attributes("-zoomed", True)
root.configure(bg="black")
root.bind("<Escape>", lambda e: root.destroy())  # handy for debugging

screen_w = root.winfo_screenwidth()
screen_h = root.winfo_screenheight()

canvas = tk.Canvas(
    root,
    width=screen_w,
    height=screen_h,
    highlightthickness=0,
    bd=0,
    bg="black",
)
canvas.pack(fill="both", expand=True)

# Bind touch/click handlers
canvas.bind("<Button-1>", lambda e: on_touch(e.x, e.y))
canvas.bind("<B1-Motion>", lambda e: on_touch(e.x, e.y))

# Background image state
background_image = None
background_mtime = 0
background_image_id = None

# === TEXT ITEMS (on the canvas) ===

title_id = canvas.create_text(
    screen_w // 2,
    70,
    text="Paulina → Loop",
    font=("Helvetica", 36),
    fill="white",
)

primary_id = canvas.create_text(
    screen_w // 2,
    screen_h // 2,
    text="--",
    font=("Helvetica", 80, "bold"),
    fill="white",
)

secondary_id = canvas.create_text(
    screen_w // 2,
    screen_h - 80,
    text="Loading…",
    font=("Helvetica", 28),
    fill="white",
)

# === BUBBLE TOUCH ANIMATION ===

bubbles = []  # List of bubble dicts: {id, x, y, vx, vy, age, max_age}
bubble_anim_running = False


def spawn_bubbles(x, y):
    """Spawn 3-5 bubbles around the touch point."""
    count = random.randint(3, 5)
    for _ in range(count):
        # Random offset from touch point
        offset_x = random.randint(-20, 20)
        offset_y = random.randint(-20, 20)
        bubble_x = x + offset_x
        bubble_y = y + offset_y
        
        # Bubble properties
        radius = random.randint(8, 16)
        color = random.choice(["#4A90E2", "#50C878", "#FFD700", "#FF6B9D", "#9B59B6"])
        
        # Create oval on canvas
        bubble_id = canvas.create_oval(
            bubble_x - radius, bubble_y - radius,
            bubble_x + radius, bubble_y + radius,
            fill=color, outline="", width=0
        )
        
        # Movement properties
        vx = random.uniform(-1.5, 1.5)  # Horizontal drift
        vy = random.uniform(-3, -5)     # Upward velocity
        max_age = random.randint(60, 90)  # Lifespan in frames (~2-3 seconds at 30fps)
        
        bubbles.append({
            "id": bubble_id,
            "x": bubble_x,
            "y": bubble_y,
            "vx": vx,
            "vy": vy,
            "age": 0,
            "max_age": max_age,
        })
    
    # Start animation if not already running
    global bubble_anim_running
    if not bubble_anim_running:
        bubble_anim_running = True
        animate_bubbles()


def animate_bubbles():
    """Update all bubbles: move, age, and remove expired ones."""
    global bubble_anim_running
    
    to_remove = []
    
    for bubble in bubbles:
        bubble["age"] += 1
        
        # Remove if expired
        if bubble["age"] >= bubble["max_age"]:
            canvas.delete(bubble["id"])
            to_remove.append(bubble)
            continue
        
        # Update position
        bubble["x"] += bubble["vx"]
        bubble["y"] += bubble["vy"]
        
        # Move on canvas
        canvas.coords(
            bubble["id"],
            bubble["x"] - 12, bubble["y"] - 12,
            bubble["x"] + 12, bubble["y"] + 12
        )
        
        # Fade out effect (optional - adjust opacity via color alpha)
        # For simplicity, we just delete at max_age
    
    # Remove expired bubbles from list
    for bubble in to_remove:
        bubbles.remove(bubble)
    
    # Continue animation if bubbles remain
    if bubbles:
        root.after(33, animate_bubbles)  # ~30fps
    else:
        bubble_anim_running = False


def on_touch(x, y):
    """Handle touch/click events."""
    spawn_bubbles(x, y)


# === LUMINANCE / TEXT THEME HELPERS ===

def compute_luminance(img: Image.Image) -> float:
    """Return average luminance of the image in [0, 1]."""
    thumb = img.resize((64, 64)).convert("RGB")
    arr = np.asarray(thumb, dtype="float32") / 255.0
    # ITU-R BT.709 luminance
    lum = np.mean(
        0.2126 * arr[:, :, 0]
        + 0.7152 * arr[:, :, 1]
        + 0.0722 * arr[:, :, 2]
    )
    return float(lum)


def apply_text_theme_from_image(img: Image.Image) -> None:
    """Choose black/white text based on background brightness."""
    lum = compute_luminance(img)
    is_light_bg = lum > 0.55  # tweak threshold to taste

    if is_light_bg:
        fg = "black"
    else:
        fg = "white"

    canvas.itemconfigure(title_id, fill=fg)
    canvas.itemconfigure(primary_id, fill=fg)
    canvas.itemconfigure(secondary_id, fill=fg)


# === BACKGROUND IMAGE ===

def update_background_if_needed():
    """Load / resize the background image if the file has changed."""
    global background_image, background_mtime, background_image_id

    if not os.path.exists(BACKGROUND_PATH):
        # No image yet
        return

    try:
        mtime = os.path.getmtime(BACKGROUND_PATH)
    except OSError:
        return

    if mtime == background_mtime:
        return  # no change

    background_mtime = mtime

    try:
        img = Image.open(BACKGROUND_PATH).convert("RGB")
    except Exception as e:
        print("Error loading background:", e)
        return

    # Decide text color based on brightness of this new image
    apply_text_theme_from_image(img)

    # Resize to screen and push into Tk
    img = img.resize((screen_w, screen_h), Image.LANCZOS)
    background_image = ImageTk.PhotoImage(img)

    if background_image_id is None:
        background_image_id = canvas.create_image(
            0, 0, anchor="nw", image=background_image
        )
    else:
        canvas.itemconfig(background_image_id, image=background_image)

    canvas.tag_lower(background_image_id)  # send background behind text


# === CTA API ===

def get_next_trains():
    """
    Return up to two upcoming Loop-bound Brown Line trains
    as a list of dicts: {minutes, is_scheduled, is_delayed}
    """
    url = "http://lapi.transitchicago.com/api/1.0/ttarrivals.aspx"
    params = {
        "key": CTA_KEY,
        "stpid": PAULINA_LOOP_ROUTE_ID,
        "max": 2,
        "outputType": "JSON",
    }

    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
    except RequestException as e:
        print(f"Error talking to CTA API: {e}")
        return None

    try:
        data = r.json()
        etas = data["ctatt"]["eta"]
    except Exception as e:
        print(f"Error parsing CTA API response: {e}")
        return None

    now = datetime.now()
    trains = []

    for eta in etas:
        if eta.get("rt") != "Brn":
            continue

        dest = eta.get("destNm", "").lower()
        if "loop" not in dest:
            continue

        try:
            arr = dateparser.parse(eta["arrT"])
        except Exception:
            continue

        diff = int((arr - now).total_seconds() // 60)
        if diff < 0:
            continue

        trains.append(
            {
                "minutes": diff,
                "is_scheduled": str(eta.get("isSch", "0")) == "1",
                "is_delayed": str(eta.get("isDly", "0")) == "1",
            }
        )

    trains.sort(key=lambda t: t["minutes"])
    return trains[:2]


# === UPDATE LOOP ===

def format_minutes_text(minutes: int) -> str:
    unit = "min" if minutes == 1 else "mins"
    return f"{minutes} {unit} away"


def update():
    try:
        trains = get_next_trains()
        update_background_if_needed()

        if trains is None:
            canvas.itemconfigure(primary_id, text="--")
            canvas.itemconfigure(secondary_id, text="No Data")
        elif not trains:
            canvas.itemconfigure(primary_id, text="No trains")
            canvas.itemconfigure(secondary_id, text="No service to Loop")
        else:
            first = trains[0]

            if first["is_scheduled"] or first["is_delayed"]:
                canvas.itemconfigure(primary_id, text="No trains")
                canvas.itemconfigure(
                    secondary_id, text="Check service alerts"
                )
            else:
                canvas.itemconfigure(
                    primary_id,
                    text=format_minutes_text(first["minutes"]),
                )

            if len(trains) > 1:
                second = trains[1]
                if second["is_scheduled"]:
                    canvas.itemconfigure(
                        secondary_id, text="No other train inbound"
                    )
                else:
                    canvas.itemconfigure(
                        secondary_id,
                        text=f"Next: {format_minutes_text(second['minutes'])}",
                    )
            else:
                canvas.itemconfigure(
                    secondary_id, text="No additional trains"
                )

    except Exception as e:
        print(f"Unexpected error in update(): {e}")
        canvas.itemconfigure(primary_id, text="--")
        canvas.itemconfigure(secondary_id, text="Error")

    root.after(REFRESH_MS, update)


# === MAIN ===

update_background_if_needed()
update()
root.mainloop()