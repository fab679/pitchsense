import pytest
from backend.agents.validator import GroundingValidator

def sample_fact_sheet():
    return {
        "moment_id": "seed-21-m0001",
        "match_id": "seed-21",
        "t_code": "14:22.0",
        "minute": 14.3,
        "trigger_type": "line_break_pass",
        "team": "SAL",
        "players": ["sal_08", "sal_10"],
        "facts": [
            {"fact_id": "fact-1-dist", "name": "Pass Distance", "value": 18.5, "unit": "meters", "events": [12]},
            {"fact_id": "fact-1-diff", "name": "Pass Difficulty", "value": 62.0, "unit": "/100", "events": [12]},
            {"fact_id": "fact-1-press", "name": "Pressure Beaten", "value": 0.65, "unit": "index", "events": [12]}
        ],
        "context": {
            "score": {"home": 0, "away": 0},
            "momentum_diff": 0.12
        }
    }

def test_validator_accepts_grounded_draft():
    v = GroundingValidator()
    fs = sample_fact_sheet()
    
    headline = "Rosmere threads it through central press"
    detail = "18.5 m pass completed against 0.65 pressure with 62 difficulty."
    evidence = ["fact-1-dist", "fact-1-diff", "fact-1-press"]
    
    is_valid, reason = v.validate(fs, headline, detail, evidence)
    assert is_valid is True
    assert reason is None
    assert len(v.get_refusal_log()) == 0

def test_validator_refuses_hallucinated_number():
    v = GroundingValidator()
    fs = sample_fact_sheet()
    
    headline = "Rosmere blasts 45.0 m thunderbolt"  # 45.0 is ungrounded
    detail = "Completed at 88.0 km/h."             # 88.0 is ungrounded
    evidence = ["fact-1-dist"]
    
    is_valid, reason = v.validate(fs, headline, detail, evidence)
    assert is_valid is False
    assert "Ungrounded numerical claim" in reason
    assert len(v.get_refusal_log()) == 1

def test_validator_refuses_invalid_evidence_id():
    v = GroundingValidator()
    fs = sample_fact_sheet()
    
    headline = "Rosmere pass"
    detail = "Completed pass."
    evidence = ["non_existent_fact_id_999"]
    
    is_valid, reason = v.validate(fs, headline, detail, evidence)
    assert is_valid is False
    assert "not found in verified FactSheet" in reason
