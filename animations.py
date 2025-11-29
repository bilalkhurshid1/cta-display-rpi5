"""
Animation effects for CTA Display
"""
import random
import tkinter as tk


class BubbleAnimation:
    """Manages bubble animations on touch/click events."""
    
    def __init__(self, canvas: tk.Canvas, root: tk.Tk):
        self.canvas = canvas
        self.root = root
        self.bubbles = []
        self.is_running = False
    
    def spawn_bubbles(self, x: int, y: int):
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
            bubble_id = self.canvas.create_oval(
                bubble_x - radius, bubble_y - radius,
                bubble_x + radius, bubble_y + radius,
                fill=color, outline="", width=0
            )
            
            # Movement properties
            vx = random.uniform(-1.5, 1.5)  # Horizontal drift
            vy = random.uniform(-3, -5)     # Upward velocity
            max_age = random.randint(60, 90)  # Lifespan in frames (~2-3 seconds at 30fps)
            
            self.bubbles.append({
                "id": bubble_id,
                "x": bubble_x,
                "y": bubble_y,
                "vx": vx,
                "vy": vy,
                "age": 0,
                "max_age": max_age,
            })
        
        # Start animation if not already running
        if not self.is_running:
            self.is_running = True
            self._animate()
    
    def _animate(self):
        """Update all bubbles: move, age, and remove expired ones."""
        to_remove = []
        
        for bubble in self.bubbles:
            bubble["age"] += 1
            
            # Remove if expired
            if bubble["age"] >= bubble["max_age"]:
                self.canvas.delete(bubble["id"])
                to_remove.append(bubble)
                continue
            
            # Update position
            bubble["x"] += bubble["vx"]
            bubble["y"] += bubble["vy"]
            
            # Move on canvas
            self.canvas.coords(
                bubble["id"],
                bubble["x"] - 12, bubble["y"] - 12,
                bubble["x"] + 12, bubble["y"] + 12
            )
        
        # Remove expired bubbles from list
        for bubble in to_remove:
            self.bubbles.remove(bubble)
        
        # Continue animation if bubbles remain
        if self.bubbles:
            self.root.after(33, self._animate)  # ~30fps
        else:
            self.is_running = False


class RippleAnimation:
    """Manages ripple transition effects."""
    
    def __init__(self, canvas: tk.Canvas, root: tk.Tk, screen_w: int, screen_h: int, background_id: int, title_id: int):
        self.canvas = canvas
        self.root = root
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.background_id = background_id
        self.title_id = title_id
        self.ripples = []
        self.is_running = False
    
    def start(self):
        """Start ripple effect from center of screen."""
        center_x = self.screen_w // 2
        center_y = self.screen_h // 2
        
        # Calculate max radius to cover entire screen from center
        max_radius = int((self.screen_w**2 + self.screen_h**2)**0.5 / 2) + 50
        
        # Create 3 ripples with staggered starts
        for i in range(3):
            ripple_id = self.canvas.create_oval(
                center_x, center_y,
                center_x, center_y,
                outline="white",
                width=3,
                fill=""
            )
            # Layer ripples above background but below text
            self.canvas.tag_raise(ripple_id, self.background_id)
            self.canvas.tag_lower(ripple_id, self.title_id)
            
            self.ripples.append({
                "id": ripple_id,
                "center_x": center_x,
                "center_y": center_y,
                "radius": -i * 30,  # Stagger start times
                "max_radius": max_radius,
                "speed": 5,  # Pixels per frame
            })
        
        # Start animation if not already running
        if not self.is_running:
            self.is_running = True
            self._animate()
    
    def _animate(self):
        """Update ripple expansion animation."""
        to_remove = []
        
        for ripple in self.ripples:
            ripple["radius"] += ripple["speed"]
            
            # Remove if fully expanded
            if ripple["radius"] > ripple["max_radius"]:
                self.canvas.delete(ripple["id"])
                to_remove.append(ripple)
                continue
            
            # Only draw if radius is positive
            if ripple["radius"] > 0:
                # Update oval coordinates
                x1 = ripple["center_x"] - ripple["radius"]
                y1 = ripple["center_y"] - ripple["radius"]
                x2 = ripple["center_x"] + ripple["radius"]
                y2 = ripple["center_y"] + ripple["radius"]
                self.canvas.coords(ripple["id"], x1, y1, x2, y2)
        
        # Remove finished ripples
        for ripple in to_remove:
            self.ripples.remove(ripple)
        
        # Continue animation if ripples remain
        if self.ripples:
            self.root.after(33, self._animate)  # ~30fps
        else:
            self.is_running = False