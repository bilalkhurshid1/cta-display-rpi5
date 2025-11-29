#!/usr/bin/env python3
"""
CTA Train ETA Display (Raspberry Pi 5 + 7" touchscreen)

- Fullscreen Tkinter app
- Background image comes from /home/bilal/cta-display-rpi5/background/current.jpg
- Text overlay shows next Brown Line → Loop trains at Paulina
"""
import os
import tkinter as tk
from dotenv import load_dotenv

from animations import BubbleAnimation, RippleAnimation
from cta_api import CTAClient
from image_utils import BackgroundManager

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

# === INITIALIZE COMPONENTS ===

# Background manager
background_manager = BackgroundManager(canvas, BACKGROUND_PATH, screen_w, screen_h)

# Animation managers
bubble_anim = BubbleAnimation(canvas, root)
ripple_anim = None  # Will be initialized after first background load

# CTA API client
cta_client = CTAClient(CTA_KEY, PAULINA_LOOP_ROUTE_ID)

# Touch/click handlers
def on_touch(x: int, y: int):
    """Handle touch/click events."""
    bubble_anim.spawn_bubbles(x, y)

canvas.bind("<Button-1>", lambda e: on_touch(e.x, e.y))
canvas.bind("<B1-Motion>", lambda e: on_touch(e.x, e.y))


# === UPDATE LOOP ===

def format_minutes_text(minutes: int) -> str:
    unit = "min" if minutes == 1 else "mins"
    return f"{minutes} {unit} away"


def update():
    global ripple_anim
    
    try:
        trains = cta_client.get_next_trains()
        was_updated, text_color = background_manager.update_if_needed()
        
        # Initialize ripple animation after first background load
        if ripple_anim is None and background_manager.get_background_id() is not None:
            ripple_anim = RippleAnimation(
                canvas, root, screen_w, screen_h,
                background_manager.get_background_id(), title_id
            )
        
        # Update text colors if background changed
        if text_color:
            canvas.itemconfigure(title_id, fill=text_color)
            canvas.itemconfigure(primary_id, fill=text_color)
            canvas.itemconfigure(secondary_id, fill=text_color)
        
        # Trigger ripple effect on background updates (not first load)
        if was_updated and ripple_anim:
            ripple_anim.start()

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

# Initial background load
background_manager.update_if_needed()
update()
root.mainloop()