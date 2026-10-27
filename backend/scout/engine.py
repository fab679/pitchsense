"""
Scout Metric Engine: Real-time deterministic analysis of match event streams.
Maintains state, computes rolling indicators (momentum, control, chaos),
and triggers FactSheets for the agent desk.
"""

from collections import deque
from typing import Dict, Any, List, Optional, Tuple
from backend.scout.metrics import (
    euclidean_distance,
    calculate_xg,
    calculate_pass_difficulty,
    is_line_breaking_pass
)

class ScoutEngine:
    def __init__(self, match_id: str = "seed-21", home_team: str = "SAL", away_team: str = "BRA"):
        self.match_id = match_id
        self.home_team = home_team
        self.away_team = away_team
        
        # State
        self.score = {home_team: 0, away_team: 0}
        self.xg_accumulated = {home_team: 0.0, away_team: 0.0}
        self.pass_counts = {home_team: {"attempted": 0, "completed": 0}, away_team: {"attempted": 0, "completed": 0}}
        self.shot_counts = {home_team: 0, away_team: 0}
        self.tackle_counts = {home_team: 0, away_team: 0}
        
        # Player-level stats
        self.player_stats: Dict[str, Dict[str, Any]] = {}
        
        # Rolling event windows (last 5 minutes = ~300 sec)
        self.recent_events = deque()
        self.current_minute = 0.0
        self.last_t_code = "00:00.0"
        
        # Rolling metrics
        self.momentum_diff = 0.0  # +1.0 (Home dominance) to -1.0 (Away dominance)
        self.control_index = {home_team: 0.5, away_team: 0.5}
        self.chaos_index = 0.25
        
        self.active_possession_chain: List[Dict[str, Any]] = []
        self.moment_seq = 0

    def _init_player(self, code: str, name: str, team: str):
        if code not in self.player_stats:
            self.player_stats[code] = {
                "code": code,
                "name": name,
                "team": team,
                "passes_attempted": 0,
                "passes_completed": 0,
                "shots": 0,
                "goals": 0,
                "tackles": 0,
                "total_pass_distance_m": 0.0,
                "distance_covered_km": 0.0,
                "top_speed_kmh": 0.0,
                "high_pressure_touches": 0,
                "consecutive_press_escapes": 0,
                "milestones": []
            }

    def process_event(self, event: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
        """
        Process a single match event in stream order.
        Returns (augmented_event, optional_fact_sheet).
        """
        seq = event["seq"]
        ev_type = event["type"]
        team = event["team"]
        self.last_t_code = event.get("t_code", "00:00.0")
        self.current_minute = event.get("minute", 0.0)
        
        # Update rolling event window (prune events older than 300 seconds / 5 mins)
        self.recent_events.append(event)
        while self.recent_events and (self.current_minute - self.recent_events[0].get("minute", 0.0) > 5.0):
            self.recent_events.popleft()

        # Update player record
        actor_code = event.get("actor")
        actor_name = event.get("actor_name", actor_code)
        if actor_code:
            self._init_player(actor_code, actor_name, team)

        derived = event.get("derived", {})
        risk = event.get("risk", {})
        pressure = risk.get("pressure_at_receipt", 0.0)
        
        if pressure > 0.6 and actor_code:
            self.player_stats[actor_code]["high_pressure_touches"] += 1

        # Track player physical indicators (distance and sprint threshold)
        if actor_code and actor_code in self.player_stats:
            p_stat = self.player_stats[actor_code]
            p_stat["distance_covered_km"] = round(p_stat["distance_covered_km"] + 0.035, 2)
            if pressure > 0.68 or (derived.get("ball_speed_kmh", 0.0) > 68.0):
                sprint_speed = round(min(34.2, max(28.5, 27.2 + pressure * 6.8)), 1)
                if sprint_speed > p_stat["top_speed_kmh"]:
                    p_stat["top_speed_kmh"] = sprint_speed

        fact_sheet: Optional[Dict[str, Any]] = None

        # --- PROCESS PASS ---
        if ev_type == "pass":
            self.pass_counts[team]["attempted"] += 1
            if actor_code:
                self.player_stats[actor_code]["passes_attempted"] += 1
            
            outcome = event.get("outcome", "complete")
            pos = event.get("pos", {"x": 50, "y": 34})
            end_pos = event.get("end_pos", {"x": 50, "y": 34})
            
            dist = derived.get("pass_distance_m") or euclidean_distance(pos["x"], pos["y"], end_pos["x"], end_pos["y"])
            derived["pass_distance_m"] = dist
            
            if outcome == "complete":
                self.pass_counts[team]["completed"] += 1
                if actor_code:
                    self.player_stats[actor_code]["passes_completed"] += 1
                    self.player_stats[actor_code]["total_pass_distance_m"] += dist
                
                self.active_possession_chain.append(event)
                
                # Check for line-breaking pass moment
                difficulty = derived.get("pass_difficulty", 30.0)
                if is_line_breaking_pass(pos["x"], end_pos["x"], difficulty):
                    self.moment_seq += 1
                    recipient_code = event.get("recipient", "")
                    recipient_name = event.get("recipient_name", "")
                    fact_sheet = {
                        "moment_id": f"{self.match_id}-m{self.moment_seq:04d}",
                        "match_id": self.match_id,
                        "t_code": self.last_t_code,
                        "minute": self.current_minute,
                        "trigger_type": "line_break_pass",
                        "team": team,
                        "players": [actor_code, recipient_code] if recipient_code else [actor_code],
                        "facts": [
                            {"fact_id": f"fact-{seq}-dist", "name": "Pass Distance", "value": dist, "unit": "meters", "events": [seq]},
                            {"fact_id": f"fact-{seq}-diff", "name": "Pass Difficulty", "value": difficulty, "unit": "/100", "events": [seq]},
                            {"fact_id": f"fact-{seq}-press", "name": "Pressure Beaten", "value": pressure, "unit": "index", "events": [seq]},
                            {"fact_id": f"fact-{seq}-speed", "name": "Ball Speed", "value": derived.get("ball_speed_kmh", 45.0), "unit": "km/h", "events": [seq]}
                        ],
                        "context": self._get_context_dict()
                    }
            else:
                self.active_possession_chain.clear()

        # --- PROCESS SHOT OR GOAL ---
        elif ev_type in ("shot", "goal"):
            self.shot_counts[team] += 1
            if actor_code:
                self.player_stats[actor_code]["shots"] += 1
            
            xg = derived.get("xg")
            if xg is None:
                pos = event.get("pos", {"x": 90, "y": 34})
                xg = calculate_xg(pos["x"], pos["y"])
                derived["xg"] = xg
            
            self.xg_accumulated[team] = round(self.xg_accumulated[team] + xg, 3)
            
            if ev_type == "goal" or event.get("outcome") == "scored":
                self.score[team] += 1
                if actor_code:
                    self.player_stats[actor_code]["goals"] += 1
                
                self.moment_seq += 1
                fact_sheet = {
                    "moment_id": f"{self.match_id}-m{self.moment_seq:04d}",
                    "match_id": self.match_id,
                    "t_code": self.last_t_code,
                    "minute": self.current_minute,
                    "trigger_type": "goal",
                    "team": team,
                    "players": [actor_code],
                    "facts": [
                        {"fact_id": f"fact-{seq}-xg", "name": "Chance Quality (xG)", "value": xg, "unit": "xG", "events": [seq]},
                        {"fact_id": f"fact-{seq}-speed", "name": "Shot Velocity", "value": derived.get("shot_speed_kmh", 85.0), "unit": "km/h", "events": [seq]},
                        {"fact_id": f"fact-{seq}-dist", "name": "Shot Distance", "value": derived.get("pass_distance_m", 16.0), "unit": "meters", "events": [seq]},
                        {"fact_id": f"fact-{seq}-score", "name": "New Scoreline", "value": f"{self.home_team} {self.score[self.home_team]} - {self.score[self.away_team]} {self.away_team}", "unit": "score", "events": [seq]}
                    ],
                    "context": self._get_context_dict()
                }
            elif xg >= 0.18:
                # Dangerous high-xG chance
                self.moment_seq += 1
                fact_sheet = {
                    "moment_id": f"{self.match_id}-m{self.moment_seq:04d}",
                    "match_id": self.match_id,
                    "t_code": self.last_t_code,
                    "minute": self.current_minute,
                    "trigger_type": "shot_threat",
                    "team": team,
                    "players": [actor_code],
                    "facts": [
                        {"fact_id": f"fact-{seq}-xg", "name": "Expected Goals (xG)", "value": xg, "unit": "xG", "events": [seq]},
                        {"fact_id": f"fact-{seq}-speed", "name": "Shot Speed", "value": derived.get("shot_speed_kmh", 80.0), "unit": "km/h", "events": [seq]},
                        {"fact_id": f"fact-{seq}-outcome", "name": "Shot Outcome", "value": event.get("outcome", "saved"), "unit": "result", "events": [seq]}
                    ],
                    "context": self._get_context_dict()
                }
            self.active_possession_chain.clear()

        # --- PROCESS TACKLE / TURNOVER ---
        elif ev_type in ("tackle", "possession_change", "card"):
            self.tackle_counts[team] += 1
            if actor_code:
                self.player_stats[actor_code]["tackles"] += 1
            
            pos = event.get("pos", {"x": 50, "y": 34})
            # High press turnover: turnover forced in attacking half (x >= 65)
            if pos["x"] >= 65.0:
                self.moment_seq += 1
                fact_sheet = {
                    "moment_id": f"{self.match_id}-m{self.moment_seq:04d}",
                    "match_id": self.match_id,
                    "t_code": self.last_t_code,
                    "minute": self.current_minute,
                    "trigger_type": "high_press_turnover",
                    "team": team,
                    "players": [actor_code],
                    "facts": [
                        {"fact_id": f"fact-{seq}-presszone", "name": "Press Recovery Pitch X", "value": pos["x"], "unit": "meters", "events": [seq]},
                        {"fact_id": f"fact-{seq}-pressure", "name": "Defensive Contact Pressure", "value": pressure, "unit": "index", "events": [seq]}
                    ],
                    "context": self._get_context_dict()
                }
            self.active_possession_chain.clear()

        # Check sprint speed threshold milestone
        if fact_sheet is None and actor_code and actor_code in self.player_stats:
            p_stat = self.player_stats[actor_code]
            if p_stat["top_speed_kmh"] >= 31.0 and "sprint_31" not in p_stat["milestones"] and self.current_minute >= 8.0:
                p_stat["milestones"].append("sprint_31")
                self.moment_seq += 1
                fact_sheet = {
                    "moment_id": f"{self.match_id}-m{self.moment_seq:04d}",
                    "match_id": self.match_id,
                    "t_code": self.last_t_code,
                    "minute": self.current_minute,
                    "trigger_type": "player_milestone",
                    "team": team,
                    "players": [actor_name or actor_code],
                    "facts": [
                        {"fact_id": f"fact-{seq}-sprint", "name": "Sprint Peak Speed", "value": p_stat["top_speed_kmh"], "unit": "km/h", "events": [seq]},
                        {"fact_id": f"fact-{seq}-distcov", "name": "Distance Covered", "value": p_stat["distance_covered_km"], "unit": "km", "events": [seq]}
                    ],
                    "context": self._get_context_dict()
                }

        # Update rolling momentum and indices
        self._update_rolling_indices()
        
        event["derived"] = derived
        return event, fact_sheet

    def _update_rolling_indices(self):
        """Recompute EWMA momentum differential, control index, and chaos index over recent window."""
        if not self.recent_events:
            return

        home_actions = 0.0
        away_actions = 0.0
        turnovers_in_window = 0
        total_in_window = len(self.recent_events)

        for ev in self.recent_events:
            t = ev.get("team")
            ev_type = ev.get("type")
            weight = 1.0
            if ev_type == "shot":
                weight = 3.5
            elif ev_type == "goal":
                weight = 7.0
            elif ev_type == "tackle":
                weight = 1.8
                turnovers_in_window += 1
            
            if t == self.home_team:
                home_actions += weight
            else:
                away_actions += weight

        total_actions = home_actions + away_actions
        if total_actions > 0:
            diff = (home_actions - away_actions) / total_actions
            # Smooth momentum update
            self.momentum_diff = round(0.85 * self.momentum_diff + 0.15 * diff, 3)

        # Control Index: share of passes completed reaching forward progression
        home_passes = max(1, self.pass_counts[self.home_team]["attempted"])
        away_passes = max(1, self.pass_counts[self.away_team]["attempted"])
        home_acc = self.pass_counts[self.home_team]["completed"] / home_passes
        away_acc = self.pass_counts[self.away_team]["completed"] / away_passes
        
        self.control_index[self.home_team] = round(min(0.95, max(0.15, home_acc * 0.9)), 2)
        self.control_index[self.away_team] = round(min(0.95, max(0.15, away_acc * 0.9)), 2)
        
        # Chaos Index: turnover density in recent window
        self.chaos_index = round(min(0.92, max(0.08, (turnovers_in_window / max(5, total_in_window)) * 2.8)), 2)

    def _get_context_dict(self) -> Dict[str, Any]:
        return {
            "score": {
                "home": self.score[self.home_team],
                "away": self.score[self.away_team]
            },
            "home_team": self.home_team,
            "away_team": self.away_team,
            "momentum_diff": self.momentum_diff,
            "control_index": self.control_index[self.home_team],
            "chaos_index": self.chaos_index,
            "high_press_payoff": self.tackle_counts[self.home_team] > 3
        }

    def get_summary_snapshot(self) -> Dict[str, Any]:
        """Provides full real-time match state snapshot for frontend or API consumers."""
        return {
            "match_id": self.match_id,
            "clock_t_code": self.last_t_code,
            "minute": self.current_minute,
            "score": self.score,
            "xg": self.xg_accumulated,
            "passes": self.pass_counts,
            "shots": self.shot_counts,
            "tackles": self.tackle_counts,
            "momentum_diff": self.momentum_diff,
            "control_index": self.control_index,
            "chaos_index": self.chaos_index,
            "players": list(self.player_stats.values())
        }
