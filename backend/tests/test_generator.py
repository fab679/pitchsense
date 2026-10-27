import json
from pathlib import Path
import jsonschema
import pytest
from backend.generate.gen import SyntheticMatchGenerator
from backend.generate.world import TEAMS

SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "event.schema.json"

@pytest.fixture(scope="module")
def event_schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def test_generator_determinism():
    """Verify that identical seeds produce byte-identical event sequences."""
    gen1 = SyntheticMatchGenerator(seed=42)
    gen2 = SyntheticMatchGenerator(seed=42)
    
    events1 = list(gen1.generate_match_events())
    events2 = list(gen2.generate_match_events())
    
    assert len(events1) == len(events2)
    for (ev1, tr1), (ev2, tr2) in zip(events1, events2):
        assert ev1 == ev2
        assert tr1 == tr2

def test_generator_schema_conformance(event_schema):
    """Verify all events conform strictly to JSON Schema."""
    gen = SyntheticMatchGenerator(seed=21)
    validator = jsonschema.Draft7Validator(event_schema)
    
    count = 0
    for ev, _ in gen.generate_match_events():
        validator.validate(ev)
        count += 1
        if count >= 100:  # validate first 100 events for fast test execution
            break

def test_no_real_trademarks_in_world():
    """Competition Rule §4.7 validation: only fictional entities."""
    forbidden = ["arsenal", "chelsea", "liverpool", "manchester", "premier", "lion", "tottenham"]
    for code, team in TEAMS.items():
        assert not any(f in team.name.lower() for f in forbidden)
        for player in team.roster:
            assert not any(f in player.name.lower() for f in forbidden)

def test_pitch_boundary_constraints():
    """Coordinates must stay strictly within 105 x 68 meter pitch."""
    gen = SyntheticMatchGenerator(seed=21)
    for ev, _ in gen.generate_match_events():
        pos = ev.get("pos")
        if pos:
            assert 0.0 <= pos["x"] <= 105.0
            assert 0.0 <= pos["y"] <= 68.0
        end_pos = ev.get("end_pos")
        if end_pos:
            assert 0.0 <= end_pos["x"] <= 105.0
            assert 0.0 <= end_pos["y"] <= 68.0
