"""
Avatar Manager for handling Samantha's visual expressions and synchronization with voice tone.
"""
import logging
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw
from pathlib import Path
from typing import Dict, Optional
import asyncio
import random
import time

logger = logging.getLogger(__name__)

class AvatarManager:
    """Manages Samantha's avatar expressions and synchronization with voice tone."""
    
    def __init__(self, root: Optional[tk.Tk] = None):
        self.root = root
        self.avatar_frame = None
        self.avatar_label = None
        self.current_expression = "neutral"
        self.expression_images: Dict[str, ImageTk.PhotoImage] = {}
        self.avatar_states = {
            "calm": {
                "expression": "serene",
                "eye_state": "soft",
                "mouth_curve": 0.2  # slight smile
            },
            "excited": {
                "expression": "energetic",
                "eye_state": "wide",
                "mouth_curve": 0.8  # big smile
            },
            "attentive": {
                "expression": "focused",
                "eye_state": "alert",
                "mouth_curve": 0.3
            },
            "neutral": {
                "expression": "balanced",
                "eye_state": "natural",
                "mouth_curve": 0.0
            }
        }
        self.animation_frame = 0
        self.blink_timer = None
        self.mouth_timer = None
        self.is_speaking = False
        self.animation_frames = {}
        self._setup_avatar_display()
        self._load_expressions()
        self._load_animation_frames()
        self._start_idle_animations()
        
    def _setup_avatar_display(self):
        """Set up the avatar display frame and label."""
        if not self.root:
            return
            
        # Create avatar frame
        self.avatar_frame = ttk.Frame(self.root)
        self.avatar_frame.pack(side=tk.RIGHT, padx=10, pady=10)
        
        # Create avatar label
        self.avatar_label = ttk.Label(self.avatar_frame)
        self.avatar_label.pack()
        
    def _load_expressions(self):
        """Load avatar expression images."""
        try:
            avatar_dir = Path("assets/avatars")
            avatar_dir.mkdir(parents=True, exist_ok=True)
            
            # Load expression images
            for expression in ["calm", "excited", "attentive", "neutral"]:
                image_path = avatar_dir / f"avatar_{expression}.png"
                if image_path.exists():
                    img = Image.open(image_path)
                    # Resize image if needed
                    img = img.resize((200, 200), Image.Resampling.LANCZOS)
                    self.expression_images[expression] = ImageTk.PhotoImage(img)
                else:
                    logger.warning(f"Avatar expression image not found: {image_path}")
                    
        except Exception as e:
            logger.error(f"Failed to load avatar expressions: {e}")
            
    def update_avatar_expression(self, tone: str):
        """
        Update avatar expression based on voice tone.
        
        Args:
            tone: The emotional tone to express
        """
        try:
            # Get expression image
            expression_map = {
                "calm": "avatar_calm.png",
                "excited": "avatar_happy.png",
                "attentive": "avatar_listening.png",
                "neutral": "avatar_neutral.png"
            }
            
            avatar_image = expression_map.get(tone, "avatar_neutral.png")
            self.display_avatar_expression(avatar_image)
            
        except Exception as e:
            logger.error(f"Failed to update avatar expression: {e}")
            
    def display_avatar_expression(self, image_path: str):
        """
        Display the avatar expression image.
        
        Args:
            image_path: Path to the expression image
        """
        try:
            if not self.avatar_label:
                return
                
            # Load and display image
            img = Image.open(image_path)
            img = img.resize((200, 200), Image.Resampling.LANCZOS)
            tk_img = ImageTk.PhotoImage(img)
            self.avatar_label.config(image=tk_img)
            self.avatar_label.image = tk_img
            
        except Exception as e:
            logger.error(f"Failed to display avatar expression: {e}")
            print(f"Avatar expression changed to: {image_path}")  # Fallback console output
            
    async def animate_expression_change(self, from_tone: str, to_tone: str, duration: float = 0.5):
        """
        Smoothly animate between expressions.
        
        Args:
            from_tone: Starting tone
            to_tone: Target tone
            duration: Animation duration in seconds
        """
        try:
            if from_tone == to_tone:
                return
                
            # Get state parameters
            from_state = self.avatar_states[from_tone]
            to_state = self.avatar_states[to_tone]
            
            # Calculate number of frames
            fps = 30
            frames = int(duration * fps)
            
            for frame in range(frames):
                # Calculate interpolation factor
                t = frame / frames
                
                # Interpolate state parameters
                current_state = {
                    "expression": self._interpolate_expression(
                        from_state["expression"],
                        to_state["expression"],
                        t
                    ),
                    "eye_state": self._interpolate_expression(
                        from_state["eye_state"],
                        to_state["eye_state"],
                        t
                    ),
                    "mouth_curve": from_state["mouth_curve"] + (
                        to_state["mouth_curve"] - from_state["mouth_curve"]
                    ) * t
                }
                
                # Update display
                self._update_avatar_state(current_state)
                await asyncio.sleep(1/fps)
                
        except Exception as e:
            logger.error(f"Failed to animate expression change: {e}")
            
    def _interpolate_expression(self, from_expr: str, to_expr: str, t: float) -> str:
        """Helper method to interpolate between expression states."""
        # For now, just return the target expression
        # In a more advanced implementation, this could generate intermediate expressions
        return to_expr if t > 0.5 else from_expr
        
    def _update_avatar_state(self, state: Dict):
        """Update avatar display based on state parameters."""
        try:
            if not self.avatar_label:
                return
                
            # In a more advanced implementation, this would generate/modify
            # the avatar image based on the state parameters
            expression = state["expression"]
            if expression in self.expression_images:
                self.avatar_label.config(image=self.expression_images[expression])
                self.avatar_label.image = self.expression_images[expression]
                
        except Exception as e:
            logger.error(f"Failed to update avatar state: {e}")

    def _load_animation_frames(self):
        """Load animation frames for different expressions."""
        try:
            avatar_dir = Path("assets/avatars")
            avatar_dir.mkdir(parents=True, exist_ok=True)
            
            # Load base expressions
            for expression in ["calm", "excited", "attentive", "neutral"]:
                # Load main expression
                base_path = avatar_dir / f"avatar_{expression}.png"
                if base_path.exists():
                    img = Image.open(base_path)
                    img = img.resize((200, 200), Image.Resampling.LANCZOS)
                    self.expression_images[expression] = ImageTk.PhotoImage(img)
                    
                    # Create blink frames
                    blink_img = self._create_blink_frame(img)
                    self.animation_frames[f"{expression}_blink"] = ImageTk.PhotoImage(blink_img)
                    
                    # Create speaking frames
                    speak_img = self._create_speak_frame(img)
                    self.animation_frames[f"{expression}_speak"] = ImageTk.PhotoImage(speak_img)
                    
        except Exception as e:
            logger.error(f"Failed to load animation frames: {e}")

    def _create_blink_frame(self, base_img: Image) -> Image:
        """Create a blinking frame from base image."""
        try:
            blink_img = base_img.copy()
            draw = ImageDraw.Draw(blink_img)
            
            # Get eye positions from base image
            width, height = base_img.size
            center_x = width // 2
            center_y = height // 2
            
            # Draw closed eyes (simple lines)
            draw.line(
                [(center_x - 30, center_y - 20), (center_x - 10, center_y - 20)],
                fill='black',
                width=2
            )
            draw.line(
                [(center_x + 10, center_y - 20), (center_x + 30, center_y - 20)],
                fill='black',
                width=2
            )
            
            return blink_img
            
        except Exception as e:
            logger.error(f"Failed to create blink frame: {e}")
            return base_img

    def _create_speak_frame(self, base_img: Image) -> Image:
        """Create a speaking frame from base image."""
        try:
            speak_img = base_img.copy()
            draw = ImageDraw.Draw(speak_img)
            
            # Get mouth position
            width, height = base_img.size
            center_x = width // 2
            center_y = height // 2
            
            # Draw slightly open mouth
            draw.ellipse(
                [
                    (center_x - 20, center_y + 10),
                    (center_x + 20, center_y + 25)
                ],
                outline='black',
                width=2
            )
            
            return speak_img
            
        except Exception as e:
            logger.error(f"Failed to create speak frame: {e}")
            return base_img

    def _start_idle_animations(self):
        """Start idle animations (blinking)."""
        if not self.avatar_label:
            return
        
        async def blink_cycle():
            while True:
                await asyncio.sleep(random.uniform(2.0, 5.0))  # Random blink interval
                if not self.is_speaking:
                    # Show blink frame
                    blink_frame = self.animation_frames.get(
                        f"{self.current_expression}_blink",
                        self.expression_images[self.current_expression]
                    )
                    self.avatar_label.config(image=blink_frame)
                    self.avatar_label.image = blink_frame
                    
                    # Hold blink briefly
                    await asyncio.sleep(0.15)
                    
                    # Return to normal
                    normal_frame = self.expression_images[self.current_expression]
                    self.avatar_label.config(image=normal_frame)
                    self.avatar_label.image = normal_frame
        
        # Start blink cycle
        asyncio.create_task(blink_cycle())

    async def animate_speaking(self, duration: float = 0.5):
        """
        Animate speaking motion.
        
        Args:
            duration: How long to animate speaking
        """
        try:
            self.is_speaking = True
            speak_start = time.time()
            
            while time.time() - speak_start < duration:
                # Alternate between normal and speaking frames
                if self.animation_frame % 2 == 0:
                    frame = self.expression_images[self.current_expression]
                else:
                    frame = self.animation_frames.get(
                        f"{self.current_expression}_speak",
                        self.expression_images[self.current_expression]
                    )
                
                self.avatar_label.config(image=frame)
                self.avatar_label.image = frame
                self.animation_frame += 1
                
                await asyncio.sleep(0.1)  # Control animation speed
                
            # Reset to normal frame
            self.avatar_label.config(
                image=self.expression_images[self.current_expression]
            )
            self.avatar_label.image = self.expression_images[self.current_expression]
            self.is_speaking = False
            
        except Exception as e:
            logger.error(f"Failed to animate speaking: {e}")
            self.is_speaking = False 