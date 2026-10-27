"""
Synthetic football match event generator for PitchSense.
Generates realistic match streams calibrated against professional match distributions.
Seeded and 100% deterministic. Emits events and ground truth data.
"""

import json
import math
import random
from typing import Dict, Any, List, Generator, Tuple, Optional
from backend.generate.world import TEAMS, Team, Player, SALTMARSH_ROVERS, BRACKFIELD_ATHLETIC

# Standard Football Pitch Dimensions (Meters)
PITCH_LENGTH = 105.0
PITCH_WIDTH = 68.0
GOAL_Y_TOP = 30.34
GOAL_Y_BOTTOM = 37.66
GOAL_Y_CENTER = 34.0

class SyntheticMatchGenerator:
    def __init__(self, seed: int = 21, match_id: Optional[str] = None):
        self.seed = seed
        self.match_id = match_id or f"seed-{seed}"
        self.rng = random.Random(seed)
        
        self.home_team = SALTMARSH_ROVERS
        self.away_team = BRACKFIELD_ATHLETIC
        self.current_team = self.home_team
        self.defending_team = self.away_team
        
        self.seq = 0
        self.clock_sec = 0.0  # from 0 to 5400+ (90 mins + stoppage)
        self.home_score = 0
        self.away_score = 0
        
        # State tracking
        self.ball_x = 52.5
        self.ball_y = 34.0
        self.ball_holder: Optional[Player] = self.current_team.roster[7] # default CM
        self.possession_chain_length = 0
        self.match_over = False

    def _format_t_code(self, sec: float) -> str:
        mins = int(sec // 60)
        rem_sec = sec % 60
        return f"{mins:02d}:{rem_sec:04.1f}"

    def _calc_xg(self, x: float, y: float, is_header: bool = False) -> float:
        """Calibrated expected goals (xG) matching professional league distributions."""
        dist = math.hypot(105.0 - x, y - GOAL_Y_CENTER)
        dx = max(0.5, 105.0 - x)
        dy1 = y - GOAL_Y_TOP
        dy2 = y - GOAL_Y_BOTTOM
        angle = abs(math.atan2(dy1, dx) - math.atan2(dy2, dx))
        
        # Calibrated logistic coefficients (league average conversion ~10.5%)
        intercept = -0.80
        c_dist = -0.11
        c_angle = 1.30
        c_header = -0.55 if is_header else 0.0
        
        logit = intercept + (c_dist * dist) + (c_angle * angle) + c_header
        xg = 1.0 / (1.0 + math.exp(-logit))
        return round(min(0.95, max(0.015, xg)), 3)

    def _calc_pass_difficulty(self, dist_m: float, pressure: float, forward_m: float) -> float:
        """Pass difficulty index [0..100] based on distance, opponent pressure, and verticality."""
        base = dist_m * 1.4
        press_weight = pressure * 35.0
        vert_weight = max(0.0, forward_m) * 0.8
        diff = base + press_weight + vert_weight
        return round(min(99.0, max(5.0, diff)), 1)

    def _next_player_in_team(self, team: Team, target_x: float, target_y: float, exclude_code: str) -> Player:
        """Finds candidate receiver closest to target position, with tactical noise."""
        candidates = [p for p in team.roster[:11] if p.code != exclude_code]
        def score(p: Player):
            d = math.hypot(p.preferred_zone_x - target_x, p.preferred_zone_y - target_y)
            return d + self.rng.uniform(-10, 10)
        return min(candidates, key=score)

    def generate_match_events(self) -> Generator[Tuple[Dict[str, Any], Dict[str, Any]], None, None]:
        """
        Main generator loop.
        Yields pairs of (event_dict, ground_truth_dict).
        Produces ~1000 total events across a full 90-minute match.
        """
        # 1. Match Start / Kickoff Whistle
        self.seq += 1
        kickoff_event = {
            "seq": self.seq,
            "match_id": self.match_id,
            "t_code": self._format_t_code(self.clock_sec),
            "minute": round(self.clock_sec / 60.0, 2),
            "type": "whistle",
            "team": self.home_team.code,
            "actor": "ref_01",
            "actor_name": "Match Official",
            "pos": {"x": 52.5, "y": 34.0},
            "outcome": "complete",
            "risk": {"pressure_at_receipt": 0.0, "under_pressure": False}
        }
        yield kickoff_event, {"event_seq": self.seq, "true_xg": 0.0, "true_dist": 0.0}

        # Main timeline loop: until 94 minutes (5640 sec)
        half_time_done = False
        target_total_sec = 5640.0

        while self.clock_sec < target_total_sec:
            # Check half-time transition
            if self.clock_sec >= 2700.0 and not half_time_done:
                half_time_done = True
                self.seq += 1
                yield {
                    "seq": self.seq,
                    "match_id": self.match_id,
                    "t_code": self._format_t_code(self.clock_sec),
                    "minute": 45.0,
                    "type": "whistle",
                    "team": self.current_team.code,
                    "actor": "ref_01",
                    "actor_name": "Match Official",
                    "pos": {"x": 52.5, "y": 34.0},
                    "outcome": "complete",
                    "risk": {"pressure_at_receipt": 0.0, "under_pressure": False}
                }, {"event_seq": self.seq, "note": "half_time"}
                
                # Switch sides / restart
                self.ball_x, self.ball_y = 52.5, 34.0
                self.current_team, self.defending_team = self.away_team, self.home_team
                self.ball_holder = self.current_team.roster[8]
                continue

            # Time increment between events: 2.5 to 6.5 seconds
            dt = self.rng.uniform(2.5, 6.2)
            self.clock_sec += dt
            if self.clock_sec > target_total_sec:
                break

            # Current ball coordinates and tactical pressure
            dist_to_opponent_goal = math.hypot(PITCH_LENGTH - self.ball_x, GOAL_Y_CENTER - self.ball_y)
            pressure_raw = self.defending_team.tactics.press_intensity * (1.0 - (dist_to_opponent_goal / 120.0))
            pressure = round(min(0.95, max(0.08, pressure_raw + self.rng.gauss(0, 0.08))), 3)
            under_pressure = pressure > 0.55

            # Determine next action type
            # In attacking 3rd (<25m from goal), shots are attempted when a reasonable angle exists
            if dist_to_opponent_goal < 24.0 and self.rng.random() < 0.20:
                # --- SHOT EVENT ---
                self.seq += 1
                xg = self._calc_xg(self.ball_x, self.ball_y)
                shot_speed = round(self.rng.uniform(74.0, 116.0) * (self.ball_holder.shot_power if self.ball_holder else 0.8), 1)
                
                # Shot outcome distribution modulated by xG and shooter skill
                r = self.rng.random()
                if r < xg:
                    outcome = "scored"
                    event_type = "goal"
                    if self.current_team == self.home_team:
                        self.home_score += 1
                    else:
                        self.away_score += 1
                elif r < xg + 0.38:
                    outcome = "saved"
                    event_type = "shot"
                elif r < xg + 0.62:
                    outcome = "blocked"
                    event_type = "shot"
                else:
                    outcome = "off_target"
                    event_type = "shot"

                shot_event = {
                    "seq": self.seq,
                    "match_id": self.match_id,
                    "t_code": self._format_t_code(self.clock_sec),
                    "minute": round(self.clock_sec / 60.0, 2),
                    "type": event_type,
                    "team": self.current_team.code,
                    "actor": self.ball_holder.code if self.ball_holder else "sal_09",
                    "actor_name": self.ball_holder.name if self.ball_holder else "Attacker",
                    "pos": {"x": round(self.ball_x, 1), "y": round(self.ball_y, 1)},
                    "end_pos": {"x": 105.0, "y": round(self.rng.uniform(GOAL_Y_TOP - 1, GOAL_Y_BOTTOM + 1), 1)},
                    "derived": {
                        "shot_speed_kmh": shot_speed,
                        "pass_distance_m": round(dist_to_opponent_goal, 1),
                        "xg": xg,
                    },
                    "risk": {
                        "pressure_at_receipt": pressure,
                        "under_pressure": under_pressure
                    },
                    "outcome": outcome
                }

                truth = {
                    "event_seq": self.seq,
                    "true_xg": xg,
                    "true_shot_speed_kmh": shot_speed,
                    "true_dist": dist_to_opponent_goal,
                    "outcome": outcome,
                    "score_after": {"home": self.home_score, "away": self.away_score}
                }
                yield shot_event, truth

                # Reset after goal or dead ball
                if outcome == "scored":
                    self.ball_x, self.ball_y = 52.5, 34.0
                    self.current_team, self.defending_team = self.defending_team, self.current_team
                    self.ball_holder = self.current_team.roster[8]
                    self.possession_chain_length = 0
                else:
                    # Turnover to goalkeeper or defender
                    self.current_team, self.defending_team = self.defending_team, self.current_team
                    self.ball_holder = self.current_team.roster[0] # GK
                    self.ball_x, self.ball_y = 12.0, 34.0
                    self.possession_chain_length = 0
                continue

            # Determine Turnover / Tackle vs Pass
            # Calibrated turnover probability (~45 turnovers/match)
            turnover_prob = 0.025 + (pressure * 0.035) + (0.003 * min(8, self.possession_chain_length))
            if self.rng.random() < turnover_prob:
                # --- TURNOVER / TACKLE EVENT ---
                self.seq += 1
                tackler = self._next_player_in_team(self.defending_team, self.ball_x, self.ball_y, "")
                is_card = self.rng.random() < 0.04  # ~1-3 cards per full match
                outcome = "complete" if not is_card else "fouled"
                event_type = "card" if is_card else "tackle"
                
                turnover_event = {
                    "seq": self.seq,
                    "match_id": self.match_id,
                    "t_code": self._format_t_code(self.clock_sec),
                    "minute": round(self.clock_sec / 60.0, 2),
                    "type": event_type,
                    "team": self.defending_team.code,
                    "actor": tackler.code,
                    "actor_name": tackler.name,
                    "pos": {"x": round(self.ball_x, 1), "y": round(self.ball_y, 1)},
                    "risk": {
                        "pressure_at_receipt": pressure,
                        "under_pressure": True
                    },
                    "outcome": "won" if not is_card else "fouled"
                }

                truth = {
                    "event_seq": self.seq,
                    "turnover": True,
                    "pressure": pressure,
                    "pitch_third": "defensive" if self.ball_x < 35 else ("middle" if self.ball_x < 70 else "attacking")
                }
                yield turnover_event, truth

                # Switch possession
                self.current_team, self.defending_team = self.defending_team, self.current_team
                self.ball_holder = tackler
                self.possession_chain_length = 0
                continue

            # --- PASS EVENT ---
            self.seq += 1
            self.possession_chain_length += 1
            
            # Target receiver
            # Tactical direction: forwards according to directness
            advance_x = self.rng.gauss(14.0 * self.current_team.tactics.directness, 8.0)
            target_x = min(102.0, max(5.0, self.ball_x + advance_x))
            target_y = min(64.0, max(4.0, self.ball_y + self.rng.gauss(0, 16.0)))
            
            receiver = self._next_player_in_team(
                self.current_team,
                target_x,
                target_y,
                self.ball_holder.code if self.ball_holder else ""
            )
            
            pass_dist = math.hypot(target_x - self.ball_x, target_y - self.ball_y)
            pass_diff = self._calc_pass_difficulty(pass_dist, pressure, advance_x)
            pass_speed = round(self.rng.uniform(34.0, 78.0), 1)
            
            # Accuracy rate decreases with difficulty
            success_threshold = 0.94 - (pass_diff / 180.0)
            is_complete = self.rng.random() < success_threshold
            outcome = "complete" if is_complete else "incomplete"

            pass_event = {
                "seq": self.seq,
                "match_id": self.match_id,
                "t_code": self._format_t_code(self.clock_sec),
                "minute": round(self.clock_sec / 60.0, 2),
                "type": "pass",
                "team": self.current_team.code,
                "actor": self.ball_holder.code if self.ball_holder else "sal_08",
                "actor_name": self.ball_holder.name if self.ball_holder else "Midfielder",
                "recipient": receiver.code,
                "recipient_name": receiver.name,
                "pos": {"x": round(self.ball_x, 1), "y": round(self.ball_y, 1)},
                "end_pos": {"x": round(target_x, 1), "y": round(target_y, 1)},
                "derived": {
                    "pass_distance_m": round(pass_dist, 1),
                    "pass_accuracy": round(success_threshold, 2),
                    "pass_difficulty": pass_diff,
                    "ball_speed_kmh": pass_speed
                },
                "risk": {
                    "pressure_at_receipt": pressure,
                    "under_pressure": under_pressure
                },
                "outcome": outcome
            }

            truth = {
                "event_seq": self.seq,
                "true_dist": round(pass_dist, 2),
                "true_difficulty": pass_diff,
                "true_speed_kmh": pass_speed,
                "receiver_pressure": pressure,
                "completed": is_complete
            }
            yield pass_event, truth

            if is_complete:
                self.ball_holder = receiver
                self.ball_x, self.ball_y = target_x, target_y
            else:
                # Interception / turnover
                self.current_team, self.defending_team = self.defending_team, self.current_team
                interceptor = self._next_player_in_team(self.current_team, target_x, target_y, "")
                self.ball_holder = interceptor
                self.ball_x, self.ball_y = target_x, target_y
                self.possession_chain_length = 0

        # Full Time Whistle
        self.seq += 1
        yield {
            "seq": self.seq,
            "match_id": self.match_id,
            "t_code": self._format_t_code(self.clock_sec),
            "minute": round(self.clock_sec / 60.0, 2),
            "type": "whistle",
            "team": self.home_team.code,
            "actor": "ref_01",
            "actor_name": "Match Official",
            "pos": {"x": 52.5, "y": 34.0},
            "outcome": "complete",
            "risk": {"pressure_at_receipt": 0.0, "under_pressure": False}
        }, {
            "event_seq": self.seq,
            "final_score": {"home": self.home_score, "away": self.away_score},
            "total_events": self.seq
        }

def generate_fixture_files(seed: int = 21, events_path: str = "fixtures/seed-21-events.jsonl", truth_path: str = "fixtures/seed-21-truth.jsonl"):
    """Pre-bakes a complete match to jsonl files for deterministic test replay and instant demo loading."""
    import os
    os.makedirs(os.path.dirname(events_path), exist_ok=True)
    gen = SyntheticMatchGenerator(seed=seed)
    with open(events_path, "w", encoding="utf-8") as f_ev, open(truth_path, "w", encoding="utf-8") as f_tr:
        for ev, tr in gen.generate_match_events():
            f_ev.write(json.dumps(ev) + "\n")
            f_tr.write(json.dumps(tr) + "\n")

if __name__ == "__main__":
    import sys
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 21
    print(f"Generating fixture for seed {seed}...")
    generate_fixture_files(seed=seed)
    print("Fixture generated successfully!")
