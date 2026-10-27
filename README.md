# PitchSense — The Match Intelligence Studio
> **Inside the Game: Developer Hackathon** (Microsoft × Premier League)  
> *Machines see, agents narrate, directors decide.*

[![PitchSense CI](https://github.com/fab679/pitchsense/actions/workflows/ci.yml/badge.svg)](https://github.com/fab679/pitchsense/actions/workflows/ci.yml) · [![Live Studio](https://img.shields.io/badge/demo-live-22c55e)](https://pitchsense-demo.thankfulbay-81dc82eb.eastus2.azurecontainerapps.io) · [![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Live deployment:** [Open PitchSense](https://pitchsense-demo.thankfulbay-81dc82eb.eastus2.azurecontainerapps.io) · [Health check](https://pitchsense-demo.thankfulbay-81dc82eb.eastus2.azurecontainerapps.io/healthz)

---

## ⚡ Pitch
**PitchSense** turns seeded synthetic football events into match metrics, broadcast cues, and recaps. It is a React studio backed by FastAPI, with deterministic offline operation and optional Azure OpenAI-compatible chat completions. The public demo runs in deterministic mode.

PitchSense:
- Processes generated match events into deterministic metrics such as expected goals ($xG$), pass difficulty, momentum, and control vs. chaos.
- Produces broadcast cues with fact citations and code-based checks for evidence IDs and numerical claims.
- Presents player statistics and audience-focused views in a React studio backed by FastAPI.
- Offers an optional Azure OpenAI-compatible chat provider; the public demo uses deterministic offline responses.

Trajectory distance comparisons use generated coordinates and ground truth. This is not image-based event detection and does not analyze real match video.

---

## 🧠 How It Works

| Stage | PitchSense implementation |
|---|---|
| Ingest | Seeded synthetic football events generated in-process. |
| Interpret | Deterministic expected-goals, pass-difficulty, player, and momentum metrics. |
| Explain | Cue drafts cite fact IDs; a code validator checks citations and numerical claims. |
| Render | React studio with a synthetic pitch visualization and metric overlays. |
| Personalize | Casual, analyst, and player-focused views; English and Spanish recap text. |

---

## 🏗️ Architecture

```
                 Synthetic Match Event Stream (gen.py, seeded)
                                     │
         ┌───────────────────────────┴───────────────────────────┐
         ▼                                                       ▼
   Trajectory Metrics                                  Deterministic Scout
 • Synthetic event coordinates                      • xG & Pass Difficulty
 • Derives speed/distance estimates                  • Control vs Chaos Indices
 • Compares estimates to generated truth             • Sprint (>31 km/h) & Distance Alerts
         │                                                       │
         └───────────────────────────┬───────────────────────────┘
                                     ▼ (Fact Sheet Bus)
 ┌──────────────────── PitchSense Local Agent Workflow ─────────────────────────────┐
 │                                                                                  │
 │  [Headline Agent]  ──► Drafts lower-third commentary citing exact fact IDs       │
 │                                    │                                             │
 │  [Grounding Critic] ──► Code-only validator recomputes numbers; REFUSES errors   │
 │                                    │                                             │
 │  [Lens Agent]      ──► Personalizes for Analyst / Casual / Player-Focus (EN/ES)  │
 │                                    │                                             │
 │  [Producer Agent]  ──► Priority queue (TAKE/KILL), TTL management & clock sync   │
 │                                                                                  │
 └───────────────────────────────────┬──────────────────────────────────────────────┘
                                     ▼
                     FastAPI WebSocket event stream
                                     ▼
 ┌────────────────────── PitchSense Production Studio UI ───────────────────────────┐
 │                                                                                  │
 │  [1. Live Studio]      Synthetic pitch view, metric overlays, Producer Desk      │
 │  [2. Player Matrix]    Generated player statistics & speed estimates             │
 │  [3. Match Recap]      Full-time tactical dossier, turning points, player ratings│
 │  [4. Trust & Tools]    Grounding audit and read-only Scout API console            │
 │                                                                                  │
 └──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Technology

| Technology | Project implementation |
|---|---|
| **Optional hosted model provider** | The gateway can use Azure OpenAI-compatible chat completions when configured; the public instance currently uses deterministic offline responses. |
| **Agent workflow** | Local Headline, Grounding Critic, Lens, and Producer components coordinate cues; this project does not use the Microsoft Agent Framework SDK. |
| **Scout tools** | A project-specific read-only tool catalog and HTTP API are exposed under `/api/mcp`; this is not an MCP-protocol server. |
| **Service discovery** | Project-specific JSON is exposed at `/.well-known/agent-card.json`. |
| **Azure Container Apps (ACA)** | The public demo is deployed as a container app; the repository Dockerfile builds the frontend and backend. |
| **Tailwind CSS v4 & React 19** | The browser-based studio UI and its match visualizations. |

---

## ✅ Verification

Run `make verify` for the Python tests and deterministic generator check, then `cd frontend && npm ci && npm run build` for the UI build. These are local code checks, not a hosted-model benchmark or a measured model-quality or latency scorecard.

---

## 🖥️ Studio Views

### Tab 1: Live Broadcast Studio
* **Synthetic Match Feed:** SVG pitch canvas showing ball movement, player positions, passes, and trajectory-derived metrics.
* **Broadcast HUD Overlays:** Score, match clock, rolling momentum differential, and lower-third narrative cards.
* **Producer Desk:** Interactive cue inbox allowing broadcast directors to `TAKE` or `KILL` cues and inspect grounding status, provider receipts, and measured trajectory agreement once observations are available.
* **Viewer Persona & Language Switcher:** Switch instantaneously between Casual, Analyst, and Player-Focus perspectives in English or Spanish.
* **"Ask the Match":** Keyword-matched questions are answered from local Scout metrics.

### Tab 2: Player Intelligence & Threshold Matrix
* **Player statistics:** Speed and distance estimates, pass completion, pressure touches, and $xG$ contribution from generated events; these are simulated metrics, not optical tracking of video.
* **Speed Threshold Alerts:** The player view flags estimated speed above **31.0 km/h**; speed values are generated estimates, not video tracking measurements.
* **Player-Focused Lens:** Filter the player matrix by team and inspect individual players' match statistics.

### Tab 3: Match Recap
The recap is generated from current telemetry. In offline mode, some narrative text, milestones, and player ratings are illustrative fallback content rather than match-derived findings. The dossier can be copied as Markdown.

### Tab 4: Trust Checks & Scout Tools
* Inspect blocked cue claims recorded by the grounding validator.
* Call the project's read-only Scout HTTP tools under `/api/mcp` (a JSON HTTP API, not the MCP protocol).

---

## 🚀 Local Quickstart

Run the deterministic demo without API keys. The public Azure deployment uses the same offline mode.

### Prerequisites
* Python $\ge$ 3.12 (managed via `uv`)
* Node.js $\ge$ 20 & npm

### Commands
```bash
git clone https://github.com/fab679/pitchsense.git
cd pitchsense
make setup
make verify
make replay
```

Open **`http://localhost:8000`** in your browser.
1. Click **`▶ PLAY`** to start the generated match replay.
2. Follow the score, synthetic pitch visualization, metrics, and broadcast cue queue.
3. Open **Player Intelligence**, **Executive Recap**, or **Trust & Tools**.
4. Try one of the suggested Ask the Match questions.

---

## ⚖️ Synthetic Data

PitchSense uses fictional clubs (**Saltmarsh Rovers** `SAL` and **Brackfield Athletic** `BRA`) and fictional rosters. Match events and trajectories are generated locally from a seed (21 by default); no real match feeds or match video are used.

---

## 📜 License
MIT License — Copyright (c) 2026 PitchSense Contributors.
