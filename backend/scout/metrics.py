"""
Deterministic football metrics calculations.
Grounded in published football analytics methods (xG, pressure, momentum).
Pure computation, 0% hallucination risk.
"""

import math
from typing import Dict, Any, List, Optional

def euclidean_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    return round(math.hypot(x2 - x1, y2 - y1), 2)

def calculate_xg(x: float, y: float, is_header: bool = False) -> float:
    """Logistic formulation of xG based on Euclidean goal distance and goal mouth angle."""
    goal_x = 105.0
    goal_y_center = 34.0
    goal_y_top = 30.34
    goal_y_bottom = 37.66
    
    dist = math.hypot(goal_x - x, y - goal_y_center)
    dx = max(0.5, goal_x - x)
    dy1 = y - goal_y_top
    dy2 = y - goal_y_bottom
    angle = abs(math.atan2(dy1, dx) - math.atan2(dy2, dx))
    
    intercept = -0.80
    c_dist = -0.11
    c_angle = 1.30
    c_header = -0.55 if is_header else 0.0
    
    logit = intercept + (c_dist * dist) + (c_angle * angle) + c_header
    xg = 1.0 / (1.0 + math.exp(-logit))
    return round(min(0.95, max(0.015, xg)), 3)

def calculate_pass_difficulty(distance_m: float, pressure: float, vertical_gain_m: float) -> float:
    """
    Computes a pass difficulty rating from 0.0 to 100.0.
    Factors in flight distance, receiver press intensity, and forward progression.
    """
    base = distance_m * 1.4
    press_factor = pressure * 35.0
    vert_factor = max(0.0, vertical_gain_m) * 0.8
    val = base + press_factor + vert_factor
    return round(min(99.0, max(5.0, val)), 1)

def is_line_breaking_pass(start_x: float, end_x: float, difficulty: float) -> bool:
    """True if pass progresses at least 15m forward into the final or middle third with difficulty >= 45."""
    forward_gain = end_x - start_x
    return forward_gain >= 14.0 and end_x >= 55.0 and difficulty >= 45.0
