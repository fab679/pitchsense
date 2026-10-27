"""
Unit tests for PitchSense MatchRecapAgent (Post-Match Tactical Dossier).
"""

import pytest
from backend.agents.recap import MatchRecapAgent


class MockGateway:
    def complete_chat(self, role, messages, fallback_template_fn):
        return fallback_template_fn(), {
            "model": "gpt-4.1-mini",
            "provider": "azure_foundry",
            "cost_usd": 0.00015,
            "latency_ms": 12.5,
            "input_tokens": 150,
            "output_tokens": 200,
        }


def test_recap_agent_english():
    gateway = MockGateway()
    agent = MatchRecapAgent(gateway=gateway)

    summary = {
        "score": {"SAL": 2, "BRA": 1},
        "xg": {"SAL": 1.84, "BRA": 0.92},
        "passes": {
            "SAL": {"completed": 450, "attempted": 510},
            "BRA": {"completed": 380, "attempted": 460},
        },
        "momentum_diff": 0.22,
    }

    cues = [
        {"cue_id": "c1", "headline": "Saltmarsh Break Through Central Press"}
    ]

    recap = agent.generate_recap(summary=summary, cues=cues, lang="en")
    assert "headline" in recap
    assert "Saltmarsh" in recap["headline"] or "Tactical" in recap["headline"]
    assert "tactical_summary" in recap
    assert "control_vs_chaos_analysis" in recap
    assert len(recap["key_milestones"]) >= 1
    assert len(recap["player_ratings"]) >= 1
    assert recap["receipt"]["provider"] == "azure_foundry"


def test_recap_agent_spanish():
    gateway = MockGateway()
    agent = MatchRecapAgent(gateway=gateway)

    summary = {
        "score": {"SAL": 1, "BRA": 1},
        "xg": {"SAL": 1.2, "BRA": 1.1},
        "passes": {"SAL": {"completed": 400}, "BRA": {"completed": 395}},
        "momentum_diff": 0.05,
    }

    recap = agent.generate_recap(summary=summary, cues=[], lang="es")
    assert "headline" in recap
    assert "Análisis Completo" in recap["headline"]
    assert "control_vs_chaos_analysis" in recap
    assert "verified_metrics" in recap
    assert recap["receipt"]["model"] == "gpt-4.1-mini"
