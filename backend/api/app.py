"""
PitchSense Core FastAPI Application.
Coordinates the synthetic match replay engine, WebSocket streaming,
REST controls, Scout HTTP tool endpoints, and service discovery.
"""

import os
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.generate.gen import SyntheticMatchGenerator
from backend.generate.world import TEAMS
from backend.scout.engine import ScoutEngine
from backend.agents.orchestrator import AgentOrchestrator
from backend.agents.gateway import GATEWAY
from backend.agents.recap import MatchRecapAgent
from backend.vision.scout import TrajectoryScout
from backend.mcp_server.server import PitchSenseMCPServer
from backend.api.a2a import get_agent_card

app = FastAPI(
    title="PitchSense API",
    version="0.1.0",
    description="Live Match Intelligence Studio API"
)

# Enable CORS for local dev and preview
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Replay & Match State Manager
class ReplayManager:
    def __init__(self, seed: int = 21):
        self.seed = seed
        self.speed = 4.0
        self.is_running = False
        self.generator = SyntheticMatchGenerator(seed=seed)
        self.scout = ScoutEngine(match_id=f"seed-{seed}")
        self.orchestrator = AgentOrchestrator()
        self.video_scout = TrajectoryScout(tolerance_m=2.0)
        self.mcp_server = PitchSenseMCPServer(self.scout, self.orchestrator, self.video_scout)
        
        self.active_connections: List[WebSocket] = []
        self.events_cache: List[Dict[str, Any]] = []
        self.truth_cache: List[Dict[str, Any]] = []
        self.event_index = 0
        self.replay_task: Optional[asyncio.Task] = None
        self._load_or_generate_fixture()

    def _load_or_generate_fixture(self):
        self.events_cache.clear()
        self.truth_cache.clear()
        for ev, tr in self.generator.generate_match_events():
            self.events_cache.append(ev)
            self.truth_cache.append(tr)
        self.event_index = 0

    def reset(self, seed: int = 21, speed: float = 4.0):
        self.seed = seed
        self.speed = speed
        self.generator = SyntheticMatchGenerator(seed=seed)
        self.scout = ScoutEngine(match_id=f"seed-{seed}")
        self.orchestrator = AgentOrchestrator()
        self.video_scout = TrajectoryScout(tolerance_m=2.0)
        self.mcp_server = PitchSenseMCPServer(self.scout, self.orchestrator, self.video_scout)
        self._load_or_generate_fixture()

    async def broadcast(self, message: Dict[str, Any]):
        dead = []
        for ws in self.active_connections:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            if ws in self.active_connections:
                self.active_connections.remove(ws)

    async def run_replay_loop(self):
        self.is_running = True
        try:
            while self.is_running and self.event_index < len(self.events_cache):
                ev = self.events_cache[self.event_index]
                tr = self.truth_cache[self.event_index]
                self.event_index += 1

                # 1. Deterministic Scout Engine Processing
                augmented_ev, fact_sheet = self.scout.process_event(ev)

                # 2. Derive trajectory metrics and reconcile distances against generated truth
                video_detection = None
                if ev.get("type") in ("pass", "shot") and ev.get("end_pos"):
                    video_detection = self.video_scout.derive_event_from_trajectory(
                        start_pos=ev["pos"],
                        end_pos=ev["end_pos"],
                        dt_sec=1.2,
                        actor_code=ev.get("actor", ""),
                        recipient_code=ev.get("recipient", ""),
                        ground_truth=tr
                    )

                # 3. Agentic Workflow Trigger
                cue = None
                if fact_sheet:
                    cue = self.orchestrator.process_moment(fact_sheet)

                # 4. Stream Message Package
                msg = {
                    "type": "tick",
                    "event": augmented_ev,
                    "summary": self.scout.get_summary_snapshot(),
                    "cue": cue,
                    "trajectory_estimate": video_detection,
                    "trajectory_accuracy": self.video_scout.get_reconciliation_summary(),
                    "progress": {
                        "current_index": self.event_index,
                        "total_events": len(self.events_cache),
                        "speed": self.speed
                    }
                }
                await self.broadcast(msg)

                # Sleep interval based on replay speed (simulated ~3s interval / speed)
                delay = max(0.04, 2.0 / max(0.5, self.speed))
                await asyncio.sleep(delay)
        finally:
            self.is_running = False

REPLAY = ReplayManager(seed=21)
RECAP_AGENT = MatchRecapAgent()

# --- WebSocket Streaming Endpoint ---
@app.websocket("/ws/match")
async def websocket_match_stream(websocket: WebSocket):
    await websocket.accept()
    REPLAY.active_connections.append(websocket)
    
    # Send initial state snapshot immediately upon connection
    init_msg = {
        "type": "init",
        "summary": REPLAY.scout.get_summary_snapshot(),
        "cues": REPLAY.orchestrator.get_all_cues(),
        "refusals": REPLAY.orchestrator.get_refusal_log(),
        "trajectory_accuracy": REPLAY.video_scout.get_reconciliation_summary(),
        "is_running": REPLAY.is_running,
        "speed": REPLAY.speed,
        "offline_mode": GATEWAY.is_offline()
    }
    await websocket.send_json(init_msg)

    try:
        while True:
            # Client commands over WS
            data = await websocket.receive_text()
            cmd = json.loads(data)
            action = cmd.get("action")
            if action == "play":
                if not REPLAY.is_running:
                    REPLAY.replay_task = asyncio.create_task(REPLAY.run_replay_loop())
            elif action == "pause":
                REPLAY.is_running = False
            elif action == "set_speed":
                REPLAY.speed = float(cmd.get("speed", 4.0))
            elif action == "restart":
                REPLAY.is_running = False
                REPLAY.reset(seed=cmd.get("seed", 21), speed=cmd.get("speed", 4.0))
                REPLAY.replay_task = asyncio.create_task(REPLAY.run_replay_loop())
    except WebSocketDisconnect:
        if websocket in REPLAY.active_connections:
            REPLAY.active_connections.remove(websocket)

# --- REST Endpoints ---
@app.get("/healthz")
@app.get("/api/healthz")
async def health_check():
    return {
        "status": "healthy",
        "app": "pitchsense",
        "version": "0.1.0",
        "offline_mode": GATEWAY.is_offline(),
        "active_clients": len(REPLAY.active_connections),
        "replay_running": REPLAY.is_running
    }

@app.get("/.well-known/agent-card.json")
async def service_discovery_card():
    return get_agent_card()

@app.get("/api/match/summary")
async def match_summary():
    return REPLAY.scout.get_summary_snapshot()

@app.get("/api/match/players")
async def match_players():
    return list(REPLAY.scout.player_stats.values())

@app.get("/api/recap")
async def get_match_recap(lang: str = "en"):
    summary = REPLAY.scout.get_summary_snapshot()
    cues = REPLAY.orchestrator.get_all_cues()
    return RECAP_AGENT.generate_recap(summary, cues, lang=lang)

@app.get("/api/cues")
async def list_cues():
    return REPLAY.orchestrator.get_all_cues()

@app.post("/api/cues/{cue_id}/take")
async def take_cue(cue_id: str):
    res = REPLAY.orchestrator.producer_agent.take_cue(cue_id)
    if not res:
        raise HTTPException(status_code=404, detail="Cue not found")
    await REPLAY.broadcast({"type": "cue_update", "cue": res})
    return res

@app.post("/api/cues/{cue_id}/kill")
async def kill_cue(cue_id: str):
    res = REPLAY.orchestrator.producer_agent.kill_cue(cue_id)
    if not res:
        raise HTTPException(status_code=404, detail="Cue not found")
    await REPLAY.broadcast({"type": "cue_update", "cue": res})
    return res

@app.get("/api/refusals")
async def get_refusals():
    return {
        "total_refusals": len(REPLAY.orchestrator.get_refusal_log()),
        "refusals": REPLAY.orchestrator.get_refusal_log()
    }

@app.get("/api/trajectory/summary")
async def trajectory_summary():
    return REPLAY.video_scout.get_reconciliation_summary()

class ReplayControlRequest(BaseModel):
    action: str  # play, pause, restart, set_speed
    speed: Optional[float] = 4.0
    seed: Optional[int] = 21

@app.post("/api/replay/control")
async def replay_control(req: ReplayControlRequest):
    if req.action == "play":
        if not REPLAY.is_running:
            REPLAY.replay_task = asyncio.create_task(REPLAY.run_replay_loop())
    elif req.action == "pause":
        REPLAY.is_running = False
    elif req.action == "set_speed":
        REPLAY.speed = float(req.speed or 4.0)
    elif req.action == "restart":
        REPLAY.is_running = False
        REPLAY.reset(seed=req.seed or 21, speed=req.speed or 4.0)
        REPLAY.replay_task = asyncio.create_task(REPLAY.run_replay_loop())
    return {
        "is_running": REPLAY.is_running,
        "speed": REPLAY.speed,
        "seed": REPLAY.seed,
        "event_index": REPLAY.event_index
    }

class AskRequest(BaseModel):
    question: str

@app.post("/api/ask")
async def ask_the_match(req: AskRequest):
    """
    'Ask the Match': Tool-augmented QA grounded in live Scout metrics.
    """
    summary = REPLAY.scout.get_summary_snapshot()
    q = req.question.lower()
    
    # Tool-calling logic
    if "xg" in q or "expected" in q:
        ans = f"Total Expected Goals (xG): Saltmarsh Rovers {summary['xg']['SAL']}, Brackfield Athletic {summary['xg']['BRA']}."
    elif "score" in q or "who is winning" in q:
        ans = f"Current Scoreline: Saltmarsh Rovers {summary['score']['SAL']} - {summary['score']['BRA']} Brackfield Athletic (Minute {int(summary['minute'])}')."
    elif "momentum" in q:
        m = summary['momentum_diff']
        leader = "Saltmarsh Rovers" if m > 0 else "Brackfield Athletic"
        ans = f"Current Momentum differential is {m} in favor of {leader}."
    elif "pass" in q:
        p_sal = summary['passes']['SAL']
        p_bra = summary['passes']['BRA']
        ans = f"Passes: SAL completed {p_sal['completed']}/{p_sal['attempted']} ({round(p_sal['completed']/max(1, p_sal['attempted'])*100, 1)}%), BRA completed {p_bra['completed']}/{p_bra['attempted']} ({round(p_bra['completed']/max(1, p_bra['attempted'])*100, 1)}%)."
    elif "accuracy" in q or "vision" in q or "video" in q:
        trajectory_summary = REPLAY.video_scout.get_reconciliation_summary()
        if trajectory_summary["total_detections"] == 0:
            ans = "No trajectory-to-ground-truth measurements have been recorded yet. Start the replay to collect measurements."
        else:
            ans = f"Measured trajectory distance agreement vs generated ground truth is {trajectory_summary['agreement_percentage']}% across {trajectory_summary['total_detections']} observations at ±{trajectory_summary['tolerance_meters']}m tolerance. This is not image-based event detection accuracy."
    else:
        ans = f"Match Minute {int(summary['minute'])}': Saltmarsh {summary['score']['SAL']} - {summary['score']['BRA']} Brackfield. Control Index: SAL {summary['control_index']['SAL']} vs BRA {summary['control_index']['BRA']}."

    return {
        "question": req.question,
        "answer": ans,
        "verified": True,
        "grounded_sources": ["scout_engine", "match_telemetry"]
    }

class MCPCallRequest(BaseModel):
    tool: str
    arguments: Optional[Dict[str, Any]] = {}

@app.post("/api/mcp")
async def mcp_tool_call(req: MCPCallRequest):
    return REPLAY.mcp_server.call_tool(req.tool, req.arguments or {})

@app.get("/api/mcp/tools")
async def mcp_list_tools():
    return REPLAY.mcp_server.list_tools()

# Mount frontend if built
dist_dir = Path(__file__).parent.parent.parent / "frontend" / "dist"
if dist_dir.exists():
    app.mount("/", StaticFiles(directory=dist_dir, html=True), name="frontend")
