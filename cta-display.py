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
from weather_api import WeatherClient
from weather_widget import WeatherWidget

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

leave_now_id = canvas.create_text(
    screen_w // 2,
    screen_h // 2 + 70,
    text="",
    font=("Helvetica", 32, "bold"),
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

# Weather client
weather_client = WeatherClient()
weather_counter = 1  # start at 1 so update() doesn't re-fetch on first cycle
current_text_color = "white"

# Weather widget
weather_widget = WeatherWidget(canvas, screen_w)

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


def update_weather():
    """Fetch and display current weather."""
    weather = weather_client.get_weather()
    if weather:
        weather_widget.redraw(
            weather["weather_code"], weather["temp"],
            weather["high"], weather["low"],
            current_text_color, weather["is_day"],
        )


def update():
    global ripple_anim, weather_counter, current_text_color

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
            canvas.itemconfigure(leave_now_id, fill=text_color)
            current_text_color = text_color
            weather_widget.recolor(text_color)

        # Trigger ripple effect on background updates (not first load)
        if was_updated and ripple_anim:
            ripple_anim.start()

        # Weather refresh every ~10 min (counter mod 40 at 15s intervals)
        if weather_counter % 40 == 0:
            update_weather()
        weather_counter += 1

        # Default: hide "Leave now!"
        show_leave_now = False

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
                if 1 <= first["minutes"] <= 4:
                    show_leave_now = True

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

        canvas.itemconfigure(leave_now_id, text="Leave now" if show_leave_now else "")

    except Exception as e:
        print(f"Unexpected error in update(): {e}")
        canvas.itemconfigure(primary_id, text="--")
        canvas.itemconfigure(secondary_id, text="Error")
        canvas.itemconfigure(leave_now_id, text="")

    root.after(REFRESH_MS, update)


# === MAIN ===

# Initial background load
background_manager.update_if_needed()
root.after(0, update_weather)  # fetch weather immediately on first frame
update()
root.mainloop()