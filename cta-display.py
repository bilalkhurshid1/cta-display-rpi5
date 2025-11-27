#!/usr/bin/env python3
"""
CTA Train ETA Display (Raspberry Pi 5 + 7" touchscreen)

- Fullscreen Tkinter app
- Background image comes from /home/bilal/cta-display-rpi5/background/current.jpg
- Text overlay shows next Brown Line → Loop trains at Paulina
"""
import os
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
