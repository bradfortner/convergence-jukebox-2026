"""
Record Label Service - Handles 45 RPM record label display with animation
"""

import os
import random
from typing import Optional, List, Dict, Any, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageSequence
import config


class RecordLabelService:
    """Service for creating and managing 45 RPM record label animations"""

    def __init__(self):
        """Initialize record label service"""
        self.template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'record_labels')
        self.templates: List[str] = []
        self.load_templates()

        # Label settings
        self.label_width = 500
        self.label_height = 500
        self.animation_frames = 600  # 10 seconds at 60 FPS
        self.rotation_speed = 6  # degrees per frame

    def load_templates(self):
        """Load available record label templates"""
        if os.path.exists(self.template_dir):
            self.templates = [
                f for f in os.listdir(self.template_dir)
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))
            ]

        # If no templates found, we'll generate them
        if not self.templates:
            self._generate_default_templates()

    def _generate_default_templates(self):
        """Generate default record label templates programmatically"""
        # Create a simple default template in memory
        # In production, these would be pre-made image files
        pass

    def get_random_template(self) -> Optional[str]:
        """Get a random template path"""
        if not self.templates:
            return None
        return os.path.join(self.template_dir, random.choice(self.templates))

    def create_label_animation(
        self,
        song: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> Optional[List[Image.Image]]:
        """
        Create a rotating record label animation with song information

        Returns list of PIL Images for animation frames
        """
        try:
            # Create frames for animation
            frames: List[Image.Image] = []

            for frame_num in range(self.animation_frames):
                # Create base label image
                frame = self._create_label_frame(song, frame_num)
                if frame:
                    frames.append(frame)

            # Save as GIF if output path provided
            if output_path and frames:
                self._save_animation_as_gif(frames, output_path)

            return frames if frames else None

        except Exception as e:
            print(f"Error creating label animation: {e}")
            return None

    def _create_label_frame(self, song: Dict[str, Any], frame_num: int) -> Optional[Image.Image]:
        """Create a single animation frame"""
        try:
            # Start with a template or create default
            template_path = self.get_random_template()

            if template_path and os.path.exists(template_path):
                # Load template
                label = Image.open(template_path).copy()
                label = label.resize((self.label_width, self.label_height), Image.Resampling.LANCZOS)
            else:
                # Create default label
                label = self._create_default_label()

            # Add rotation effect
            rotation_angle = (frame_num * self.rotation_speed) % 360
            label = label.rotate(rotation_angle, expand=False, fillcolor=(0, 0, 0))

            # Add text overlay
            self._add_song_text(label, song)

            return label

        except Exception as e:
            print(f"Error creating frame {frame_num}: {e}")
            return None

    def _create_default_label(self) -> Image.Image:
        """Create a default record label template"""
        # Create circular record label
        img = Image.new('RGB', (self.label_width, self.label_height), color=(20, 20, 20))
        draw = ImageDraw.Draw(img)

        # Draw outer circle (vinyl record)
        draw.ellipse(
            [(10, 10), (self.label_width - 10, self.label_height - 10)],
            outline=(100, 100, 100),
            width=3
        )

        # Draw label area (center circle)
        center_size = 200
        center_x = (self.label_width - center_size) // 2
        center_y = (self.label_height - center_size) // 2

        draw.ellipse(
            [(center_x, center_y), (center_x + center_size, center_y + center_size)],
            fill=(200, 20, 20)
        )

        # Draw center spindle hole
        spindle_size = 40
        spindle_x = (self.label_width - spindle_size) // 2
        spindle_y = (self.label_height - spindle_size) // 2

        draw.ellipse(
            [(spindle_x, spindle_y), (spindle_x + spindle_size, spindle_y + spindle_size)],
            fill=(50, 50, 50)
        )

        # Draw grooves (concentric circles)
        for i in range(50, 250, 20):
            draw.ellipse(
                [(self.label_width // 2 - i, self.label_height // 2 - i),
                 (self.label_width // 2 + i, self.label_height // 2 + i)],
                outline=(100, 100, 100),
                width=1
            )

        return img

    def _add_song_text(self, image: Image.Image, song: Dict[str, Any]):
        """Add song information text to label"""
        try:
            draw = ImageDraw.Draw(image)

            # Try to load a font, fall back to default
            try:
                title_font = ImageFont.truetype(config.FONT_PATH, 24)
                artist_font = ImageFont.truetype(config.FONT_PATH, 18)
            except:
                title_font = ImageFont.load_default()
                artist_font = ImageFont.load_default()

            title = song.get('title', 'Unknown')[:30]
            artist = song.get('artist', 'Unknown')[:30]

            # Truncate if too long
            if len(title) > 22:
                title = title[:19] + "..."
            if len(artist) > 22:
                artist = artist[:19] + "..."

            # Draw text in center label area
            center_x = self.label_width // 2
            center_y = self.label_height // 2

            # Title
            title_bbox = draw.textbbox((0, 0), title, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            draw.text(
                (center_x - title_width // 2, center_y - 30),
                title,
                fill=(255, 255, 255),
                font=title_font
            )

            # Artist
            artist_bbox = draw.textbbox((0, 0), artist, font=artist_font)
            artist_width = artist_bbox[2] - artist_bbox[0]
            draw.text(
                (center_x - artist_width // 2, center_y + 10),
                artist,
                fill=(255, 255, 255),
                font=artist_font
            )

        except Exception as e:
            print(f"Error adding text to label: {e}")

    def _save_animation_as_gif(self, frames: List[Image.Image], output_path: str):
        """Save frames as animated GIF"""
        try:
            if frames:
                frames[0].save(
                    output_path,
                    save_all=True,
                    append_images=frames[1:],
                    duration=1000 // 60,  # 60 FPS
                    loop=0
                )
                print(f"Saved animation to {output_path}")
        except Exception as e:
            print(f"Error saving GIF: {e}")

    def load_animation_from_gif(self, gif_path: str) -> Optional[List[Image.Image]]:
        """Load animation frames from a GIF file"""
        try:
            if not os.path.exists(gif_path):
                return None

            frames = []
            gif = Image.open(gif_path)

            for frame_index in range(gif.n_frames):
                gif.seek(frame_index)
                frame = gif.convert('RGB')
                frame = frame.resize((self.label_width, self.label_height), Image.Resampling.LANCZOS)
                frames.append(frame)

            return frames if frames else None

        except Exception as e:
            print(f"Error loading GIF animation: {e}")
            return None

    def get_label_dimensions(self) -> Tuple[int, int]:
        """Get label dimensions"""
        return (self.label_width, self.label_height)

    def set_animation_duration(self, frames: int):
        """Set animation frame count"""
        self.animation_frames = frames

    def set_rotation_speed(self, degrees_per_frame: float):
        """Set rotation speed in degrees per frame"""
        self.rotation_speed = degrees_per_frame
