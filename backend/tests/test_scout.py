import json
from pathlib import Path
import jsonschema
import pytest
from backend.scout.metrics import calculate_xg, calculate_pass_difficulty, is_line_breaking_pass
from backend.scout.engine import ScoutEngine
from backend.generate.gen import SyntheticMatchGenerator

FACT_SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "fact.schema.json"

@pytest.fixture(scope="module")
def fact_schema():
    with open(FACT_SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def test_xg_bounds_and_monotonicity():
    # Close-range central shot must have high xG
    xg_close = calculate_xg(100.0, 34.0)
    assert 0.40 <= xg_close <= 0.95
    
    # Far-range shot near touchline must have low xG
    xg_far = calculate_xg(65.0, 5.0)
    assert 0.015 <= xg_far <= 0.10
    
    # Closer shots should generally have higher xG than further shots along central axis
    assert xg_close > xg_far

def test_pass_difficulty():
    diff_easy = calculate_pass_difficulty(distance_m=5.0, pressure=0.1, vertical_gain_m=0.0)
    diff_hard = calculate_pass_difficulty(distance_m=35.0, pressure=0.85, vertical_gain_m=25.0)
    
    assert 5.0 <= diff_easy <= 30.0
    assert 70.0 <= diff_hard <= 99.0
    assert diff_hard > diff_easy

def test_scout_engine_fact_sheet_schema(fact_schema):
    engine = ScoutEngine()
    validator = jsonschema.Draft7Validator(fact_schema)
    
    gen = SyntheticMatchGenerator(seed=21)
    fact_sheets_found = 0
    
    for ev, _ in gen.generate_match_events():
        _, fact_sheet = engine.process_event(ev)
        if fact_sheet:
            validator.validate(fact_sheet)
            fact_sheets_found += 1
            if fact_sheets_found >= 15:
                break
                
    assert fact_sheets_found >= 10, "Scout should trigger multiple fact sheets across match"

def test_scout_rolling_metrics_stability():
    engine = ScoutEngine()
    gen = SyntheticMatchGenerator(seed=21)
    
    for ev, _ in gen.generate_match_events():
        engine.process_event(ev)
        assert -1.0 <= engine.momentum_diff <= 1.0
        assert 0.0 <= engine.control_index["SAL"] <= 1.0
        assert 0.0 <= engine.control_index["BRA"] <= 1.0
        assert 0.0 <= engine.chaos_index <= 1.0
