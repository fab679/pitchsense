"""
Synthetic Match Video Frame Renderer.
Generates 2D overhead broadcast frames with moving player dots and ball trails.
Provides both coordinate-level frame data and SVG/PNG rendered feeds for VideoScout.
"""

from typing import Dict, Any, List, Tuple
import math

WIDTH = 525
HEIGHT = 340

def scale_pos(x: float, y: float) -> Tuple[int, int]:
    """Scales 105 x 68 meter pitch coordinates to frame pixels (525 x 340)."""
    px = int(max(0.0, min(105.0, x)) * (WIDTH / 105.0))
    py = int(max(0.0, min(68.0, y)) * (HEIGHT / 68.0))
    return px, py

class FrameRenderer:
    def __init__(self):
        self.width = WIDTH
        self.height = HEIGHT

    def render_frame_svg(
        self,
        ball_pos: Dict[str, float],
        home_players: List[Dict[str, Any]],
        away_players: List[Dict[str, Any]],
        trail: List[Tuple[int, int]] = None
    ) -> str:
        """Renders an overhead broadcast frame in clean, lightweight SVG vector format."""
        bx, by = scale_pos(ball_pos["x"], ball_pos["y"])
        
        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.width} {self.height}" width="{self.width}" height="{self.height}">',
            f'<rect width="{self.width}" height="{self.height}" fill="#15803D" />',  # Pitch green
            f'<rect x="15" y="15" width="{self.width-30}" height="{self.height-30}" fill="none" stroke="#FFFFFF" stroke-width="2" opacity="0.8" />',
            f'<line x1="{self.width/2}" y1="15" x2="{self.width/2}" y2="{self.height-15}" stroke="#FFFFFF" stroke-width="2" opacity="0.8" />',
            f'<circle cx="{self.width/2}" cy="{self.height/2}" r="45" fill="none" stroke="#FFFFFF" stroke-width="2" opacity="0.8" />',
            f'<circle cx="{self.width/2}" cy="{self.height/2}" r="3" fill="#FFFFFF" opacity="0.8" />'
        ]

        # Draw ball trail
        if trail and len(trail) > 1:
            points_str = " ".join(f"{x},{y}" for x, y in trail[-8:])
            svg_parts.append(f'<polyline points="{points_str}" fill="none" stroke="#FEF08A" stroke-width="2" stroke-dasharray="3,3" opacity="0.7"/>')

        # Draw Home players (Teal dots)
        for p in home_players:
            px, py = scale_pos(p["x"], p["y"])
            svg_parts.append(f'<circle cx="{px}" cy="{py}" r="6" fill="#0F766E" stroke="#FFFFFF" stroke-width="1.5"/>')
            svg_parts.append(f'<text x="{px}" y="{py+3}" font-size="7" font-family="sans-serif" fill="#FFFFFF" text-anchor="middle">{p.get("number", "")}</text>')

        # Draw Away players (Vermilion dots)
        for p in away_players:
            px, py = scale_pos(p["x"], p["y"])
            svg_parts.append(f'<circle cx="{px}" cy="{py}" r="6" fill="#E11D48" stroke="#FFFFFF" stroke-width="1.5"/>')
            svg_parts.append(f'<text x="{px}" y="{py+3}" font-size="7" font-family="sans-serif" fill="#FFFFFF" text-anchor="middle">{p.get("number", "")}</text>')

        # Draw Ball (Yellow glow + white core)
        svg_parts.append(f'<circle cx="{bx}" cy="{by}" r="5" fill="#FACC15" />')
        svg_parts.append(f'<circle cx="{bx}" cy="{by}" r="3" fill="#FFFFFF" />')
        svg_parts.append('</svg>')

        return "".join(svg_parts)
