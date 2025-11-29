"""
Image processing utilities for background and text theming
"""
import os
import tkinter as tk
import numpy as np
from PIL import Image, ImageTk
from typing import Optional, Tuple


def compute_luminance(img: Image.Image) -> float:
    """
    Calculate average luminance of an image.
    
    Args:
        img: PIL Image object
    
    Returns:
        Average luminance in range [0, 1]
    """
    thumb = img.resize((64, 64)).convert("RGB")
    arr = np.asarray(thumb, dtype="float32") / 255.0
    # ITU-R BT.709 luminance formula
    lum = np.mean(
        0.2126 * arr[:, :, 0]
        + 0.7152 * arr[:, :, 1]
        + 0.0722 * arr[:, :, 2]
    )
    return float(lum)


def get_text_color_for_background(img: Image.Image, threshold: float = 0.55) -> str:
    """
    Determine optimal text color (black/white) based on background brightness.
    
    Args:
        img: PIL Image object
        threshold: Luminance threshold for light/dark detection
    
    Returns:
        "black" for light backgrounds, "white" for dark backgrounds
    """
    lum = compute_luminance(img)
    return "black" if lum > threshold else "white"


class BackgroundManager:
    """Manages background image loading and updates."""
    
    def __init__(self, canvas: tk.Canvas, image_path: str, screen_w: int, screen_h: int):
        """
        Initialize background manager.
        
        Args:
            canvas: Tkinter Canvas to draw on
            image_path: Path to background image file
            screen_w: Screen width in pixels
            screen_h: Screen height in pixels
        """
        self.canvas = canvas
        self.image_path = image_path
        self.screen_w = screen_w
        self.screen_h = screen_h
        
        self.background_image: Optional[ImageTk.PhotoImage] = None
        self.background_mtime: float = 0
        self.background_image_id: Optional[int] = None
    
    def update_if_needed(self) -> Tuple[bool, Optional[str]]:
        """
        Load or reload background image if file has changed.
        
        Returns:
            Tuple of (was_updated: bool, text_color: Optional[str])
            text_color is the recommended text color for this background
        """
        if not os.path.exists(self.image_path):
            return False, None
        
        try:
            mtime = os.path.getmtime(self.image_path)
        except OSError:
            return False, None
        
        # No change detected
        if mtime == self.background_mtime:
            return False, None
        
        self.background_mtime = mtime
        
        try:
            img = Image.open(self.image_path).convert("RGB")
        except Exception as e:
            print(f"Error loading background: {e}")
            return False, None
        
        # Determine text color based on brightness
        text_color = get_text_color_for_background(img)
        
        # Resize to screen and convert for Tkinter
        img = img.resize((self.screen_w, self.screen_h), Image.LANCZOS)
        self.background_image = ImageTk.PhotoImage(img)
        
        # First load vs update
        is_first_load = self.background_image_id is None
        
        if is_first_load:
            self.background_image_id = self.canvas.create_image(
                0, 0, anchor="nw", image=self.background_image
            )
        else:
            self.canvas.itemconfig(self.background_image_id, image=self.background_image)
        
        # Keep background behind other elements
        self.canvas.tag_lower(self.background_image_id)
        
        return not is_first_load, text_color
    
    def get_background_id(self) -> Optional[int]:
        """Get the canvas ID of the background image."""
        return self.background_image_id