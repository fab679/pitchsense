"""
PitchSense Scout HTTP tool API for external agents and QA.
Exposes read-only match telemetry and verification tools; this is not an MCP protocol server.
"""

from typing import Dict, Any, List, Optional
import json

class PitchSenseMCPServer:
    def __init__(self, scout_engine=None, orchestrator=None, video_scout=None):
        self.scout_engine = scout_engine
        self.orchestrator = orchestrator
        self.video_scout = video_scout

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "get_match_summary",
                "description": "Returns match state from the local Scout engine: score, xG, momentum, control index, and chaos index.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "match_id": {"type": "string", "description": "Match seed identifier"}
                    }
                }
            },
            {
                "name": "get_player_stats",
                "description": "Returns player metrics from the local Scout engine: passes completed, accuracy, shots, tackles, and high pressure touches.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "player_code": {"type": "string", "description": "Player code (e.g. sal_08, bra_10)"}
                    },
                    "required": ["player_code"]
                }
            },
            {
                "name": "verify_cue_evidence",
                "description": "Inspects a broadcast cue and returns the grounding audit status and refusal history.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "cue_id": {"type": "string", "description": "Cue identifier"}
                    },
                    "required": ["cue_id"]
                }
            },
            {
                "name": "get_auto_eventing_accuracy",
                "description": "Returns measured agreement between trajectory-derived distance estimates and generated ground-truth distances; this is not image-based event detection accuracy.",
                "parameters": {"type": "object", "properties": {}}
            }
        ]

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if name == "get_match_summary":
            if self.scout_engine:
                return self.scout_engine.get_summary_snapshot()
            return {"status": "waiting_for_kickoff"}

        elif name == "get_player_stats":
            p_code = arguments.get("player_code", "")
            if self.scout_engine and p_code in self.scout_engine.player_stats:
                return self.scout_engine.player_stats[p_code]
            return {"error": f"Player {p_code} not found in active match roster"}

        elif name == "verify_cue_evidence":
            cid = arguments.get("cue_id", "")
            if self.orchestrator and cid in self.orchestrator.producer_agent.cues:
                cue = self.orchestrator.producer_agent.cues[cid]
                return {
                    "cue_id": cid,
                    "validated": cue["receipt"].get("validated", True),
                    "evidence_cites": cue["payload"]["evidence"],
                    "receipt": cue["receipt"]
                }
            return {"error": f"Cue {cid} not found"}

        elif name == "get_auto_eventing_accuracy":
            if self.video_scout:
                return self.video_scout.get_reconciliation_summary()
            return {"agreement_percentage": 0.0, "total_detections": 0, "agreed_detections": 0, "status": "no_telemetry"}

        return {"error": f"Unknown tool: {name}"}
