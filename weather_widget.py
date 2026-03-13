import os
import tkinter as tk
from PIL import Image, ImageTk

# WMO weather code → (day icon, night icon)
# Uses as many of the available icon variants as possible.
_CODE_TO_ICON = {
    0:  ("clear-day.png",                "clear-night.png"),
    1:  ("clear-day.png",                "clear-night.png"),
    2:  ("partly-cloudy-day.png",        "partly-cloudy-night.png"),
    3:  ("overcast-day.png",             "overcast-night.png"),
    45: ("fog-day.png",                  "fog-night.png"),
    48: ("fog-day.png",                  "fog-night.png"),
    51: ("partly-cloudy-day-drizzle.png", "partly-cloudy-night-drizzle.png"),
    53: ("drizzle.png",                  "drizzle.png"),
    55: ("drizzle.png",                  "drizzle.png"),
    56: ("partly-cloudy-day-sleet.png",  "partly-cloudy-night-sleet.png"),
    57: ("sleet.png",                    "sleet.png"),
    61: ("partly-cloudy-day-rain.png",   "partly-cloudy-night-rain.png"),
    63: ("rain.png",                     "rain.png"),
    65: ("rain.png",                     "rain.png"),
    66: ("sleet.png",                    "sleet.png"),
    67: ("sleet.png",                    "sleet.png"),
    71: ("partly-cloudy-day-snow.png",   "partly-cloudy-night-snow.png"),
    73: ("snow.png",                     "snow.png"),
    75: ("snow.png",                     "snow.png"),
    77: ("snow.png",                     "snow.png"),
    80: ("partly-cloudy-day-rain.png",   "partly-cloudy-night-rain.png"),
    81: ("rain.png",                     "rain.png"),
    82: ("rain.png",                     "rain.png"),
    85: ("partly-cloudy-day-snow.png",   "partly-cloudy-night-snow.png"),
    86: ("snow.png",                     "snow.png"),
    95: ("thunderstorms-day.png",        "thunderstorms-night.png"),
    96: ("thunderstorms-day-rain.png",   "thunderstorms-night-rain.png"),
    99: ("thunderstorms-day-rain.png",   "thunderstorms-night-rain.png"),
}

_DEFAULT_ICON = ("overcast-day.png", "overcast-night.png")

ICON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "weather-icons")
ICON_SIZE = 80


class WeatherWidget:
    def __init__(self, canvas: tk.Canvas, screen_w: int):
        self._canvas = canvas
        self._x = screen_w - 20  # right edge with 20px margin
        self._cy = 70             # vertical center, aligned with title
        self._item_ids: list[int] = []
        self._icon_cache: dict[str, ImageTk.PhotoImage] = {}
        self._current_photo: ImageTk.PhotoImage | None = None

    def redraw(self, weather_code: int, temp: int, high: int, low: int,
               color: str, is_day: bool = True):
        for item_id in self._item_ids:
            self._canvas.delete(item_id)
        self._item_ids = []

        photo = self._get_icon(weather_code, is_day)

        # Icon on the left side of the widget, vertically centered on cy
        if photo:
            self._current_photo = photo
            icon_id = self._canvas.create_image(
                self._x - ICON_SIZE, self._cy, image=photo, anchor="e",
            )
            self._item_ids.append(icon_id)

        # Temp to the right of the icon, vertically centered on cy
        temp_x = self._x
        self._item_ids.append(self._canvas.create_text(
            temp_x, self._cy - 10, text=f"{temp}°",
            font=("Helvetica", 32, "bold"), fill=color, anchor="ne",
        ))

        # High/low below temp
        self._item_ids.append(self._canvas.create_text(
            temp_x, self._cy + 20, text=f"{high}°/{low}°",
            font=("Helvetica", 16), fill=color, anchor="ne",
        ))

    def recolor(self, color: str):
        for item_id in self._item_ids:
            if self._canvas.type(item_id) == "text":
                self._canvas.itemconfigure(item_id, fill=color)

    def _get_icon(self, weather_code: int, is_day: bool) -> ImageTk.PhotoImage | None:
        day_icon, night_icon = _CODE_TO_ICON.get(weather_code, _DEFAULT_ICON)
        filename = day_icon if is_day else night_icon

        if filename in self._icon_cache:
            return self._icon_cache[filename]

        path = os.path.join(ICON_DIR, filename)
        if not os.path.exists(path):
            print(f"Weather icon not found: {path}")
            return None

        img = Image.open(path).convert("RGBA")
        img = img.resize((ICON_SIZE, ICON_SIZE), Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        self._icon_cache[filename] = photo
        return photo
