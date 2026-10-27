import pytest
from fastapi.testclient import TestClient
from backend.api.app import app

client = TestClient(app)

def test_healthz_endpoint():
    resp = client.get("/healthz")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["app"] == "pitchsense"

def test_service_discovery_card():
    resp = client.get("/.well-known/agent-card.json")
    assert resp.status_code == 200
    data = resp.json()
    assert "PitchSense" in data["name"]
    assert "trajectory_metric_estimation" in data["capabilities"]
    assert "Microsoft Foundry" in data["hero_technologies"]

def test_match_summary_and_players():
    resp = client.get("/api/match/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert "score" in data
    assert "xg" in data
    assert "momentum_diff" in data

def test_ask_the_match_qa():
    resp = client.post("/api/ask", json={"question": "What is the expected goals xG score?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["verified"] is True
    assert "Expected Goals" in data["answer"]

def test_trajectory_agreement_starts_without_measurements():
    resp = client.get("/api/trajectory/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_detections"] == 0
    assert data["agreed_detections"] == 0
    assert data["agreement_percentage"] == 0.0


def test_mcp_tools():
    # List tools
    resp = client.get("/api/mcp/tools")
    assert resp.status_code == 200
    tools = resp.json()
    assert len(tools) >= 3
    tool_names = [t["name"] for t in tools]
    assert "get_match_summary" in tool_names
    assert "get_player_stats" in tool_names

    # Call tool
    resp2 = client.post("/api/mcp", json={"tool": "get_match_summary", "arguments": {}})
    assert resp2.status_code == 200
    res = resp2.json()
    assert "score" in res

def test_replay_control():
    resp = client.post("/api/replay/control", json={"action": "set_speed", "speed": 8.0})
    assert resp.status_code == 200
    assert resp.json()["speed"] == 8.0
