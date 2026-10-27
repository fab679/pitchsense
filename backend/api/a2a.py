"""Project-specific service discovery document for PitchSense."""

from typing import Dict, Any

def get_agent_card() -> Dict[str, Any]:
    return {
        "name": "PitchSense Match Intelligence Studio",
        "version": "0.1.0",
        "description": "Synthetic match intelligence with deterministic metrics, trajectory-derived estimates, grounded broadcast cues, and audience-focused recaps.",
        "author": "PitchSense Contributors",
        "hero_technologies": [
            "Microsoft Foundry",
            "Azure Container Apps",
            "Project-local agent workflow",
            "Read-only Scout HTTP tools"
        ],
        "endpoints": {
            "stream": "/ws/match",
            "rest": "/api",
            "mcp": "/api/mcp",
            "well_known": "/.well-known/agent-card.json"
        },
        "capabilities": [
            "real_time_telemetry_streaming",
            "trajectory_metric_estimation",
            "grounding_verification_critic",
            "multi_audience_personalization",
            "broadcast_cue_direction"
        ]
    }
