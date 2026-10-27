"""
Lens Personalization Agent for PitchSense.
Re-dresses verified intelligence for different audiences:
- Analyst (tactical depth, xG, metrics)
- Casual (clear storytelling, plain English/Spanish)
- Player-Focus (spotlighting individual player impact)
- Club-Focus (partisan broadcast perspective)
- Single-Metric (stat card banner)
Supports bilingual outputs (EN / ES).
"""

import json
from typing import Dict, Any, Tuple
from backend.agents.gateway import GATEWAY

LENS_SYSTEM_PROMPT = """You are the PitchSense Lens Agent.
You take a verified broadcast cue and re-dress its tone and focus for a specific audience and language.
Audience Modes:
- analyst: emphasize spatial data, xG, pass difficulty, press resistance, and tactical structure.
- casual: punchy, simple language, excitement, storytelling, scoreline context.
- player_focus: spotlight the primary player's action and impact on the match.
- club_focus: frame the moment from the perspective of the attacking club's supporters.
- single_metric: minimal banner focusing squarely on the headline stat.

Languages:
- en: English
- es: Spanish (Latin American football broadcast tone)

CRITICAL:
- Keep all numerical facts and evidence IDs completely intact.
- Output valid JSON with keys: "headline", "detail", "why".
"""

class LensAgent:
    def __init__(self, gateway=GATEWAY):
        self.gateway = gateway

    def personalize(
        self,
        draft: Dict[str, Any],
        fact_sheet: Dict[str, Any],
        audience: str = "casual",
        lang: str = "en"
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Personalizes a verified draft for a specific audience and language.
        Returns: (personalized_draft, receipt).
        """
        if audience == "casual" and lang == "en":
            # Default already prepared by headline agent
            return draft, {"provider": "passthrough", "latency_ms": 0.1, "validated": True}

        headline = draft.get("headline", "")
        detail = draft.get("detail", "")
        why = draft.get("why", "")
        evidence = draft.get("evidence", [])
        team = fact_sheet.get("team", "SAL")
        players = fact_sheet.get("players", [""])
        primary_player = players[0] if players else "Player"

        # Deterministic offline translation/re-dressing
        def offline_fallback() -> str:
            if lang == "es":
                if audience == "analyst":
                    return json.dumps({
                        "headline": f"Análisis táctico: {team} rompe líneas",
                        "detail": f"{detail} Datos confirmados por Scout.",
                        "why": f"Estructura táctica: {why}"
                    })
                elif audience == "player_focus":
                    return json.dumps({
                        "headline": f"Protagonismo: {primary_player} en acción clave",
                        "detail": f"{primary_player} ejecuta con precisión bajo presión.",
                        "why": f"Impacto directo en la posesión de {team}."
                    })
                else: # casual es
                    return json.dumps({
                        "headline": f"¡Momento clave para {team}!",
                        "detail": detail.replace("Pinpoint", "Preciso").replace("pass", "pase"),
                        "why": "Jugada que enciende el ritmo del partido."
                    })
            else: # lang == "en"
                if audience == "analyst":
                    return json.dumps({
                        "headline": f"Tactical Breakdown: {team} Vertical Phase",
                        "detail": f"Telemetry verified: {detail}",
                        "why": f"Structural impact: {why}"
                    })
                elif audience == "player_focus":
                    return json.dumps({
                        "headline": f"Spotlight: {primary_player} Drives Play",
                        "detail": f"Key execution by {primary_player} under direct pressure.",
                        "why": f"Individual contribution unlocks possession for {team}."
                    })
                elif audience == "single_metric":
                    return json.dumps({
                        "headline": f"{team} Metric Alert",
                        "detail": detail,
                        "why": why
                    })
                else:
                    return json.dumps({
                        "headline": headline,
                        "detail": detail,
                        "why": why
                    })

        # Gateway call
        user_content = f"Personalize for audience={audience}, lang={lang}:\nHeadline: {headline}\nDetail: {detail}\nWhy: {why}"
        if audience == "player_focus":
            user_content += f"\nIMPORTANT: Focus squarely on player {primary_player}. Include the player reference '{primary_player}' in the headline or detail."

        messages = [
            {"role": "system", "content": LENS_SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ]

        raw_text, receipt = self.gateway.complete_chat(
            role="lens_localize",
            messages=messages,
            fallback_template_fn=offline_fallback
        )

        try:
            clean = raw_text.strip()
            if "```json" in clean:
                clean = clean.split("```json")[1].split("```")[0].strip()
            elif "```" in clean:
                clean = clean.split("```")[1].split("```")[0].strip()
            res = json.loads(clean)
        except Exception:
            res = json.loads(offline_fallback())

        return {
            "headline": res.get("headline", headline),
            "detail": res.get("detail", detail),
            "why": res.get("why", why),
            "evidence": evidence
        }, receipt
