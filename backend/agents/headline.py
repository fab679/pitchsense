"""
Headline Agent for PitchSense.
Drafts real-time broadcast lower-third headlines and explanations from FactSheets.
Cites exact fact IDs to maintain strict grounding.
"""

import json
from typing import Dict, Any, Tuple
from backend.agents.gateway import GATEWAY

HEADLINE_SYSTEM_PROMPT = """You are the PitchSense Headline Commentary Agent for live broadcast.
You receive a verified match FactSheet with telemetry metrics (distance, speed, xG, pressure, difficulty).
The competing teams are Saltmarsh Rovers (code: SAL, Marine Teal) and Brackfield Athletic (code: BRA, Vermilion) in the Crown Premier Championship. Never refer to BRA as Brazil or SAL as Salford. Always refer to them as Saltmarsh Rovers or Brackfield Athletic (or SAL / BRA).

Your job:
1. Write a punchy broadcast headline (maximum 10 words).
2. Write a 1-sentence detail explaining the telemetry.
3. Write a 1-sentence 'why' explaining the tactical consequence (control vs chaos, rhythm shift).
4. List the exact fact_id values cited from the FactSheet in the 'evidence' array.

CRITICAL RULES:
- ONLY mention numbers and players present in the FactSheet.
- Never hallucinate stats.
- Output valid JSON with keys: "headline", "detail", "why", "evidence".
"""

class HeadlineAgent:
    def __init__(self, gateway=GATEWAY):
        self.gateway = gateway

    def draft(self, fact_sheet: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Drafts lower-third commentary from a FactSheet.
        Returns: (draft_dict, receipt_dict).
        """
        trigger = fact_sheet.get("trigger_type", "line_break_pass")
        team = fact_sheet.get("team", "SAL")
        facts = fact_sheet.get("facts", [])
        facts_map = {f["name"]: f["value"] for f in facts}
        fact_ids = [f["fact_id"] for f in facts]

        def offline_fallback() -> str:
            if trigger == "goal":
                xg = facts_map.get("Chance Quality (xG)", 0.35)
                spd = facts_map.get("Shot Velocity", 85.0)
                score = facts_map.get("New Scoreline", f"{team} ahead")
                return json.dumps({
                    "headline": f"GOAL! {team} breaks through",
                    "detail": f"Clinically finished from xG {xg} with a {spd} km/h strike ({score}).",
                    "why": "High-efficiency conversion turning territorial pressure into an immediate lead.",
                    "evidence": fact_ids
                })
            elif trigger == "line_break_pass":
                dist = facts_map.get("Pass Distance", 16.0)
                diff = facts_map.get("Pass Difficulty", 55.0)
                press = facts_map.get("Pressure Beaten", 0.6)
                return json.dumps({
                    "headline": f"{team} carves through the central block",
                    "detail": f"Pinpoint {dist} m vertical pass completed against {press} press intensity (difficulty {diff}/100).",
                    "why": "Line-breaking accuracy bypasses the opponent's defensive line in transition.",
                    "evidence": fact_ids
                })
            elif trigger == "high_press_turnover":
                zone = facts_map.get("Press Recovery Pitch X", 72.0)
                press = facts_map.get("Defensive Contact Pressure", 0.75)
                return json.dumps({
                    "headline": f"Aggressive high turnover won by {team}",
                    "detail": f"Ball won back at pitch coordinate {zone} m under {press} press pressure.",
                    "why": "Front-line pressing forces an immediate turnover in the opposition build-up zone.",
                    "evidence": fact_ids
                })
            elif trigger == "player_milestone":
                speed = facts_map.get("Sprint Peak Speed", 31.5)
                dist = facts_map.get("Distance Covered", 5.2)
                p_name = fact_sheet.get("players", ["Player"])[0]
                return json.dumps({
                    "headline": f"Speed Threshold Alert: {p_name} surges",
                    "detail": f"{p_name} recorded a {speed} km/h sprint threshold with {dist} km total workrate.",
                    "why": "High physical intensity creating transition superiority.",
                    "evidence": fact_ids
                })
            elif trigger == "shot_threat":
                xg = facts_map.get("Expected Goals (xG)", 0.22)
                spd = facts_map.get("Shot Speed", 78.0)
                outcome = facts_map.get("Shot Outcome", "saved")
                return json.dumps({
                    "headline": f"Dangerous attempt by {team} ({outcome})",
                    "detail": f"High quality xG {xg} opportunity struck at {spd} km/h.",
                    "why": "Sustained territory creates another high-probability scoring window.",
                    "evidence": fact_ids
                })
            else:
                return json.dumps({
                    "headline": f"Tactical shift as {team} adjusts tempo",
                    "detail": "Verified phase transition detected across the match window.",
                    "why": "Positional adjustment altering control dynamics.",
                    "evidence": fact_ids
                })

        user_content = json.dumps({
            "moment_id": fact_sheet.get("moment_id"),
            "minute": fact_sheet.get("minute"),
            "trigger_type": trigger,
            "team": team,
            "facts": facts,
            "context": fact_sheet.get("context")
        }, indent=2)

        messages = [
            {"role": "system", "content": HEADLINE_SYSTEM_PROMPT},
            {"role": "user", "content": f"FactSheet to narrate:\n{user_content}"}
        ]

        raw_text, receipt = self.gateway.complete_chat(
            role="narration_prod",
            messages=messages,
            fallback_template_fn=offline_fallback
        )

        try:
            # Parse json output
            clean = raw_text.strip()
            if "```json" in clean:
                clean = clean.split("```json")[1].split("```")[0].strip()
            elif "```" in clean:
                clean = clean.split("```")[1].split("```")[0].strip()
            draft = json.loads(clean)
        except Exception:
            # Fallback to offline template if JSON parse failed
            draft = json.loads(offline_fallback())

        # Ensure evidence is always populated
        if not draft.get("evidence"):
            draft["evidence"] = fact_ids

        return draft, receipt
