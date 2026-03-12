import math
import tkinter as tk

# Condition string → icon key mapping
_CONDITION_MAP = {
    "clear": "clear",
    "mostly clear": "clear",
    "partly cloudy": "partly",
    "cloudy": "cloudy",
    "foggy": "foggy",
    "drizzle": "rain",
    "rain": "rain",
    "showers": "rain",
    "heavy rain": "rain",
    "freezing rain": "rain",
    "freezing drizzle": "rain",
    "heavy showers": "rain",
    "snow": "snow",
    "heavy snow": "snow",
    "snow grains": "snow",
    "snow showers": "snow",
    "thunderstorm": "thunder",
}


def _condition_to_icon(condition: str) -> str:
    return _CONDITION_MAP.get(condition.lower(), "cloudy")


class WeatherWidget:
    def __init__(self, canvas: tk.Canvas, screen_w: int):
        self._canvas = canvas
        self._cx = screen_w - 10 - 65   # horizontal center of 130px widget box
        self._cy = 10 + 42              # vertical center of cloud shape
        self._item_ids: list[int] = []

    def redraw(self, condition: str, temp: int, high: int, low: int, color: str):
        """Delete existing items and draw fresh icon + labels."""
        for item_id in self._item_ids:
            self._canvas.delete(item_id)
        self._item_ids = []

        icon_key = _condition_to_icon(condition)

        if icon_key == "clear":
            self._draw_clear(temp, high, low, color)
        elif icon_key == "partly":
            self._draw_partly(temp, high, low, color)
        elif icon_key == "cloudy":
            self._draw_cloud_with_labels(temp, high, low, color, precip=False)
        elif icon_key == "foggy":
            self._draw_foggy(temp, high, low, color)
        elif icon_key == "rain":
            self._draw_rain(temp, high, low, color)
        elif icon_key == "snow":
            self._draw_snow(temp, high, low, color)
        elif icon_key == "thunder":
            self._draw_thunder(temp, high, low, color)
        else:
            self._draw_cloud_with_labels(temp, high, low, color, precip=False)

    def recolor(self, color: str):
        """Update fill/outline color of all tracked canvas items."""
        for item_id in self._item_ids:
            item_type = self._canvas.type(item_id)
            if item_type == "text":
                self._canvas.itemconfigure(item_id, fill=color)
            else:
                self._canvas.itemconfigure(item_id, outline=color, fill="")

    # ------------------------------------------------------------------ #
    # Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _ids(self, *ids):
        self._item_ids.extend(ids)

    def _draw_sun_rays(self, sun_cx: int, sun_cy: int, r_inner: int, r_outer: int, color: str):
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            cos_a, sin_a = math.cos(rad), math.sin(rad)
            x1 = sun_cx + r_inner * cos_a
            y1 = sun_cy + r_inner * sin_a
            x2 = sun_cx + r_outer * cos_a
            y2 = sun_cy + r_outer * sin_a
            self._ids(self._canvas.create_line(x1, y1, x2, y2, fill=color, width=2))

    def _draw_cloud_ovals(self, color: str):
        cx, cy = self._cx, self._cy
        self._ids(
            self._canvas.create_oval(cx - 35, cy - 16, cx + 35, cy + 16,
                                     outline=color, fill=""),
            self._canvas.create_oval(cx - 42, cy - 34, cx - 2, cy + 6,
                                     outline=color, fill=""),
            self._canvas.create_oval(cx, cy - 28, cx + 32, cy + 4,
                                     outline=color, fill=""),
        )

    def _draw_clear(self, temp: int, high: int, low: int, color: str):
        cx, cy = self._cx, self._cy
        # Sun circle
        self._ids(self._canvas.create_oval(cx - 18, cy - 18, cx + 18, cy + 18,
                                           outline=color, fill=""))
        # Sun rays
        self._draw_sun_rays(cx, cy, 22, 32, color)
        # Temp text centered in sun area
        self._ids(self._canvas.create_text(cx, cy + 20, text=f"{temp}°",
                                           font=("Helvetica", 22, "bold"), fill=color))
        # H/L below
        self._ids(self._canvas.create_text(cx, cy + 38,
                                           text=f"{high}°/{low}°",
                                           font=("Helvetica", 13), fill=color))

    def _draw_partly(self, temp: int, high: int, low: int, color: str):
        cx, cy = self._cx, self._cy
        sun_cx, sun_cy = cx - 18, cy - 22
        # Small sun (drawn first so cloud overlaps it)
        self._ids(self._canvas.create_oval(sun_cx - 14, sun_cy - 14,
                                           sun_cx + 14, sun_cy + 14,
                                           outline=color, fill=""))
        self._draw_sun_rays(sun_cx, sun_cy, 18, 26, color)
        # Full cloud on top
        self._draw_cloud_ovals(color)
        # Temp inside cloud
        self._ids(self._canvas.create_text(cx, cy, text=f"{temp}°",
                                           font=("Helvetica", 22, "bold"), fill=color))
        # H/L below cloud
        self._ids(self._canvas.create_text(cx, cy + 28,
                                           text=f"{high}°/{low}°",
                                           font=("Helvetica", 13), fill=color))

    def _draw_cloud_with_labels(self, temp: int, high: int, low: int,
                                color: str, precip: bool):
        cx, cy = self._cx, self._cy
        self._draw_cloud_ovals(color)
        self._ids(self._canvas.create_text(cx, cy, text=f"{temp}°",
                                           font=("Helvetica", 22, "bold"), fill=color))
        hl_y = cy + 52 if precip else cy + 28
        self._ids(self._canvas.create_text(cx, hl_y,
                                           text=f"{high}°/{low}°",
                                           font=("Helvetica", 13), fill=color))

    def _draw_foggy(self, temp: int, high: int, low: int, color: str):
        cx, cy = self._cx, self._cy
        self._draw_cloud_ovals(color)
        self._ids(self._canvas.create_text(cx, cy, text=f"{temp}°",
                                           font=("Helvetica", 22, "bold"), fill=color))
        # Fog lines
        for y_offset in [cy + 22, cy + 30, cy + 38]:
            self._ids(self._canvas.create_line(cx - 25, y_offset, cx + 25, y_offset,
                                               fill=color, width=2))
        self._ids(self._canvas.create_text(cx, cy + 52,
                                           text=f"{high}°/{low}°",
                                           font=("Helvetica", 13), fill=color))

    def _draw_rain(self, temp: int, high: int, low: int, color: str):
        cx, cy = self._cx, self._cy
        self._draw_cloud_ovals(color)
        self._ids(self._canvas.create_text(cx, cy, text=f"{temp}°",
                                           font=("Helvetica", 22, "bold"), fill=color))
        # Rain drops
        offsets = [(-20, 0), (0, 0), (20, 0), (-10, 14), (10, 14)]
        for dx, dy in offsets:
            self._ids(self._canvas.create_line(
                cx + dx - 1, cy + 20 + dy,
                cx + dx + 1, cy + 28 + dy,
                fill=color, width=2))
        self._ids(self._canvas.create_text(cx, cy + 52,
                                           text=f"{high}°/{low}°",
                                           font=("Helvetica", 13), fill=color))

    def _draw_snow(self, temp: int, high: int, low: int, color: str):
        cx, cy = self._cx, self._cy
        self._draw_cloud_ovals(color)
        self._ids(self._canvas.create_text(cx, cy, text=f"{temp}°",
                                           font=("Helvetica", 22, "bold"), fill=color))
        # Snow asterisks (3 crossing lines per flake)
        offsets = [(-20, 0), (0, 0), (20, 0), (-10, 14), (10, 14)]
        for dx, dy in offsets:
            ax, ay = cx + dx, cy + 24 + dy
            r = 4
            self._ids(
                self._canvas.create_line(ax - r, ay, ax + r, ay, fill=color, width=1),
                self._canvas.create_line(ax, ay - r, ax, ay + r, fill=color, width=1),
                self._canvas.create_line(ax - r, ay - r, ax + r, ay + r, fill=color, width=1),
            )
        self._ids(self._canvas.create_text(cx, cy + 52,
                                           text=f"{high}°/{low}°",
                                           font=("Helvetica", 13), fill=color))

    def _draw_thunder(self, temp: int, high: int, low: int, color: str):
        cx, cy = self._cx, self._cy
        self._draw_cloud_ovals(color)
        self._ids(self._canvas.create_text(cx, cy, text=f"{temp}°",
                                           font=("Helvetica", 22, "bold"), fill=color))
        # Lightning bolt polygon
        points = [
            cx - 5, cy + 20,
            cx + 4, cy + 20,
            cx + 0, cy + 32,
            cx + 6, cy + 32,
            cx - 5, cy + 48,
            cx + 2, cy + 38,
            cx - 2, cy + 38,
        ]
        self._ids(self._canvas.create_polygon(*points, outline=color, fill="", width=2))
        self._ids(self._canvas.create_text(cx, cy + 52,
                                           text=f"{high}°/{low}°",
                                           font=("Helvetica", 13), fill=color))
