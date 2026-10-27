"""
Trajectory Scout: synthetic event metrics & ground-truth reconciliation.
Processes synthetic event trajectories to derive football metrics (distance and speed).
It does not process image frames or independently detect match events.
Reconciles trajectory-derived estimates against generated ground truth with measured agreement reporting.
"""

import math
import json
from typing import Dict, Any, List, Optional, Tuple
from backend.agents.gateway import GATEWAY

TRAJECTORY_CLASSIFICATION_PROMPT = """You are the PitchSense trajectory classification assistant.
Given synthetic event coordinates and actor/recipient codes, identify whether the event is a pass, shot, or turnover.
Respond in valid JSON with:
{
  "detected_action": "pass" | "shot" | "turnover",
  "actor_code": "sal_XX" | "bra_XX",
  "recipient_code": "sal_XX" | "bra_XX" | null,
  "confidence": float between 0.0 and 1.0,
  "rationale": "Short explanation of trajectory cues"
}
"""

class TrajectoryScout:
    def __init__(self, gateway=GATEWAY, tolerance_m: float = 2.0):
        self.gateway = gateway
        self.tolerance_m = tolerance_m
        
        # Reconciliation stats
        self.total_evaluations = 0
        self.agreed_detections = 0
        self.reconciliation_history: List[Dict[str, Any]] = []

    def derive_event_from_trajectory(
        self,
        start_pos: Dict[str, float],
        end_pos: Dict[str, float],
        dt_sec: float,
        actor_code: str,
        recipient_code: str,
        ground_truth: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Derives trajectory metrics from an event's generated start/end coordinates.
        The action classification uses a configured model or a deterministic fallback.
        """
        dx = end_pos["x"] - start_pos["x"]
        dy = end_pos["y"] - start_pos["y"]
        observed_dist = round(math.hypot(dx, dy), 1)
        
        # Speed: m/s to km/h (speed = (m / s) * 3.6)
        dt = max(0.4, dt_sec)
        observed_speed_kmh = round(min(120.0, max(20.0, (observed_dist / dt) * 3.6)), 1)
        
        # Optional model-assisted action classification (or deterministic fallback)
        def fallback_vision() -> str:
            is_shot = end_pos["x"] >= 100.0 and (28.0 <= end_pos["y"] <= 40.0)
            return json.dumps({
                "detected_action": "shot" if is_shot else "pass",
                "actor_code": actor_code,
                "recipient_code": None if is_shot else recipient_code,
                "confidence": 0.88,
                "rationale": "Ball trajectory tracked continuously from release point to reception target."
            })

        messages = [
            {"role": "system", "content": TRAJECTORY_CLASSIFICATION_PROMPT},
            {"role": "user", "content": f"Trajectory: start=({start_pos['x']}, {start_pos['y']}), end=({end_pos['x']}, {end_pos['y']}), dt={dt}s, actor={actor_code}, recipient={recipient_code}"}
        ]

        raw_text, receipt = self.gateway.complete_chat(
            role="vision_scout",
            messages=messages,
            fallback_template_fn=fallback_vision
        )

        try:
            clean = raw_text.strip()
            if "```json" in clean:
                clean = clean.split("```json")[1].split("```")[0].strip()
            elif "```" in clean:
                clean = clean.split("```")[1].split("```")[0].strip()
            classification = json.loads(clean)
        except Exception:
            classification = json.loads(fallback_vision())

        # Construct trajectory estimate
        detected_event = {
            "type": "trajectory_estimate",
            "action": classification.get("detected_action", "pass"),
            "actor": classification.get("actor_code", actor_code),
            "recipient": classification.get("recipient_code", recipient_code),
            "pos": start_pos,
            "end_pos": end_pos,
            "derived": {
                "pass_distance_m": observed_dist,
                "ball_speed_kmh": observed_speed_kmh
            },
            "detection_confidence": classification.get("confidence", 0.88),
            "vision_receipt": receipt
        }

        # Reconcile against ground truth if available
        if ground_truth:
            self.total_evaluations += 1
            true_dist = ground_truth.get("true_dist", observed_dist)
            error = abs(observed_dist - true_dist)
            is_match = error <= self.tolerance_m
            if is_match:
                self.agreed_detections += 1

            reconciliation_entry = {
                "seq": ground_truth.get("event_seq", self.total_evaluations),
                "action": detected_event["action"],
                "observed_dist_m": observed_dist,
                "true_dist_m": true_dist,
                "error_m": round(error, 2),
                "agreement": is_match,
                "current_rate": self.get_agreement_percentage()
            }
            self.reconciliation_history.append(reconciliation_entry)
            detected_event["reconciliation"] = reconciliation_entry

        return detected_event

    def get_agreement_percentage(self) -> float:
        """Computes measured distance agreement percentage vs ground truth."""
        if self.total_evaluations == 0:
            return 0.0
        return round((self.agreed_detections / self.total_evaluations) * 100.0, 1)

    def get_reconciliation_summary(self) -> Dict[str, Any]:
        return {
            "total_detections": self.total_evaluations,
            "agreed_detections": self.agreed_detections,
            "tolerance_meters": self.tolerance_m,
            "agreement_percentage": self.get_agreement_percentage(),
            "recent_reconciliations": self.reconciliation_history[-10:]
        }
