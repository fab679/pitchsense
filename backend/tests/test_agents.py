import json
from pathlib import Path
import jsonschema
import pytest
from backend.agents.orchestrator import AgentOrchestrator
from backend.tests.test_validator import sample_fact_sheet

CUE_SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "cue.schema.json"

@pytest.fixture(scope="module")
def cue_schema():
    with open(CUE_SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def test_agent_orchestrator_end_to_end(cue_schema):
    orchestrator = AgentOrchestrator()
    fs = sample_fact_sheet()
    
    cue = orchestrator.process_moment(fs, audience="casual", lang="en")
    
    # Assert cue conforms strictly to JSON Schema
    validator = jsonschema.Draft7Validator(cue_schema)
    validator.validate(cue)
    
    assert cue["cue_id"].startswith("seed-21-c")
    assert cue["priority"] in (1, 2, 3, 4, 5)
    assert cue["status"] == "queued"
    assert "headline" in cue["payload"]
    assert "evidence" in cue["payload"]
    assert cue["receipt"]["validated"] is True

def test_producer_take_and_kill():
    orchestrator = AgentOrchestrator()
    fs = sample_fact_sheet()
    
    cue = orchestrator.process_moment(fs)
    cid = cue["cue_id"]
    
    taken = orchestrator.producer_agent.take_cue(cid, reviewer="Lead Director")
    assert taken["status"] == "onair"
    assert taken["producer"]["reviewed_by"] == "Lead Director"
    
    killed = orchestrator.producer_agent.kill_cue(cid, reviewer="Lead Director")
    assert killed["status"] == "killed"

def test_lens_personalization_modes():
    orchestrator = AgentOrchestrator()
    fs = sample_fact_sheet()
    
    cue_analyst = orchestrator.process_moment(fs, audience="analyst", lang="en")
    cue_player = orchestrator.process_moment(fs, audience="player_focus", lang="en")
    cue_es = orchestrator.process_moment(fs, audience="casual", lang="es")
    
    # Must produce distinct tailored content
    assert cue_analyst["payload"]["headline"] != cue_es["payload"]["headline"]
    assert cue_player["payload"]["headline"]
    assert cue_player["audience"] == "player_focus"
