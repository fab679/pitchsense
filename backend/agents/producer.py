"""
Producer Agent & Control Room Desk for PitchSense.
The Director Persona: assigns broadcast priority, display duration,
clock synchronization, and formats into machine-readable broadcast cue contracts.
Manages the cue queue with Take / Kill controls.
"""

import time
from typing import Dict, Any, List, Optional

class ProducerAgent:
    def __init__(self):
        self.cue_counter = 0
        self.cues: Dict[str, Dict[str, Any]] = {}
        self.cue_order: List[str] = []

    def create_cue(
        self,
        fact_sheet: Dict[str, Any],
        payload: Dict[str, Any],
        receipt: Dict[str, Any],
        audience: str = "casual",
        lang: str = "en"
    ) -> Dict[str, Any]:
        """
        Formats validated payload into a formal broadcast cue.
        Conforms strictly to cue.schema.json.
        """
        self.cue_counter += 1
        match_id = fact_sheet.get("match_id", "seed-21")
        cue_id = f"{match_id}-c{self.cue_counter:04d}"
        t_code = fact_sheet.get("t_code", "00:00.0")
        minute = fact_sheet.get("minute", 0.0)
        trigger = fact_sheet.get("trigger_type", "line_break_pass")
        players = fact_sheet.get("players", [])

        # Priority & Kind based on football significance
        if trigger == "goal":
            priority = 1
            kind = "breakout_banner"
            ttl_ms = 12000
        elif trigger in ("shot_threat", "line_break_pass"):
            priority = 2
            kind = "lower_third"
            ttl_ms = 8000
        elif trigger == "high_press_turnover":
            priority = 3
            kind = "stat_card"
            ttl_ms = 7000
        elif trigger == "player_milestone":
            priority = 3
            kind = "spotlight"
            ttl_ms = 7500
        else:
            priority = 4
            kind = "ticker"
            ttl_ms = 6000

        ann = f"{int(minute)}'"

        cue = {
            "cue_id": cue_id,
            "match_id": match_id,
            "t_code": t_code,
            "ann": ann,
            "kind": kind,
            "priority": priority,
            "audience": audience,
            "lang": lang,
            "ttl_ms": ttl_ms,
            "payload": {
                "headline": payload.get("headline", ""),
                "detail": payload.get("detail", ""),
                "evidence": payload.get("evidence", []),
                "why": payload.get("why", "")
            },
            "players": players,
            "status": "queued",
            "receipt": receipt,
            "producer": {
                "reviewed_by": None,
                "taken_at": None
            }
        }

        self.cues[cue_id] = cue
        self.cue_order.append(cue_id)
        return cue

    def take_cue(self, cue_id: str, reviewer: str = "Director") -> Optional[Dict[str, Any]]:
        """Producer action: 'Take' cue to air."""
        if cue_id in self.cues:
            cue = self.cues[cue_id]
            cue["status"] = "onair"
            cue["producer"]["reviewed_by"] = reviewer
            cue["producer"]["taken_at"] = time.strftime("%H:%M:%S")
            return cue
        return None

    def kill_cue(self, cue_id: str, reviewer: str = "Director") -> Optional[Dict[str, Any]]:
        """Producer action: 'Kill' / suppress cue."""
        if cue_id in self.cues:
            cue = self.cues[cue_id]
            cue["status"] = "killed"
            cue["producer"]["reviewed_by"] = reviewer
            return cue
        return None

    def get_all_cues(self) -> List[Dict[str, Any]]:
        return [self.cues[cid] for cid in self.cue_order]

    def get_active_cues(self) -> List[Dict[str, Any]]:
        return [c for c in self.cues.values() if c["status"] in ("queued", "onair")]
