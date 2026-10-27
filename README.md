# PitchSense — The Match Intelligence Studio
> **Inside the Game: Developer Hackathon** (Microsoft × Premier League)  
> *Machines see, agents narrate, directors decide.*

[![PitchSense CI](https://github.com/fab679/pitchsense/actions/workflows/ci.yml/badge.svg)](https://github.com/fab679/pitchsense/actions/workflows/ci.yml)
[![Live Studio](https://img.shields.io/badge/demo-live-22c55e)](https://pitchsense-demo.thankfulbay-81dc82eb.eastus2.azurecontainerapps.io)

**Live deployment:** [Open PitchSense](https://pitchsense-demo.thankfulbay-81dc82eb.eastus2.azurecontainerapps.io) · [Health check](https://pitchsense-demo.thankfulbay-81dc82eb.eastus2.azurecontainerapps.io/healthz)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: >=3.12](https://img.shields.io/badge/Python->=3.12-blue?logo=python)](pyproject.toml)
[![Tailwind CSS: v4](https://img.shields.io/badge/Tailwind_CSS-v4-38bdf8?logo=tailwindcss)](frontend/package.json)

---

## ⚡ 1-Minute Elevator Pitch
**PitchSense** turns seeded synthetic football events into match metrics, broadcast cues, and recaps. It is a React studio backed by FastAPI, with deterministic offline operation and optional Azure OpenAI-compatible chat completions. The public demo runs in deterministic mode.

PitchSense:
1. **Processes generated synthetic match events** and compares trajectory-derived distances with generated ground-truth values; it does not analyze real match video.
2. **Computes deterministic match metrics** including expected goals ($xG$), pass difficulty, momentum, control vs. chaos, and player speed/distance estimates.
3. **Builds grounded broadcast cues** with a local agent workflow and code-based citation/numerical-claim validation.
4. **Personalizes presentation** for casual fans, tactical analysts, and player spotlights in English and Spanish.
5. **Generates post-match recaps** from match telemetry.

---

## 🧠 Match Intelligence Flow

| Stage | PitchSense implementation |
|---|---|
| Ingest | Seeded synthetic football events are generated in-process; event and fact schemas are checked into the repository. |
| Interpret | Deterministic expected-goals, pass-difficulty, player, and momentum metrics. |
| Explain | Broadcast cue drafts cite fact IDs; the grounding validator checks references and numerical claims. |
| Render | React studio overlays metrics and cues alongside a synthetic pitch visualization. |
| Personalize | Casual, analyst, and player-focused views with English and Spanish recap text. |

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
 │  [2. Player Matrix]    Live player tracking, speed thresholds & sprint count     │
 │  [3. Match Recap]      Full-time tactical dossier, turning points, player ratings│
 │  [4. Trust & Tools]    Grounding audit and read-only Scout API console            │
 │                                                                                  │
 └──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Hero Technologies

| Hero Technology | Concrete Project Implementation |
|---|---|
| **Optional hosted model provider** | The gateway can use Azure OpenAI-compatible chat completions when configured; the public instance currently uses deterministic offline responses. |
| **Agent workflow** | Local Headline, Grounding Critic, Lens, and Producer components coordinate cues; this project does not use the Microsoft Agent Framework SDK. |
| **Scout tools** | A project-specific read-only tool catalog and HTTP API are exposed under `/api/mcp`; this is not an MCP-protocol server. |
| **Agent discovery** | A project-specific discovery card is exposed at `/.well-known/agent-card.json`; it is not a standards-compliant A2A implementation. |
| **Azure Container Apps (ACA)** | The public demo is deployed as a container app; the repository Dockerfile builds the frontend and backend. |
| **Tailwind CSS v4 & React 19** | The browser-based studio UI and its match visualizations. |

---

## ✅ Verification

The repository includes automated tests for event generation, metric bounds, citation validation/refusal, agent workflow behavior, recap output, API endpoints, and synthetic trajectory processing. Run `make verify` to execute the Python test suite and check deterministic fixture generation. These tests are local code checks, not a hosted-model benchmark or a measured model-quality or latency scorecard.

---

## 🖥️ Studio: 4 Integrated Views

### Tab 1: Live Broadcast Studio
* **Synthetic Match Feed:** SVG pitch canvas showing ball movement, player positions, passes, and trajectory-derived metrics.
* **Broadcast HUD Overlays:** Live score bug, match clock, rolling momentum differential bar, and takeable lower-third narrative cards.
* **Producer Desk:** Interactive cue inbox allowing broadcast directors to `TAKE` or `KILL` cues and inspect grounding status, provider receipts, and measured trajectory agreement once observations are available.
* **Viewer Persona & Language Switcher:** Switch instantaneously between Casual, Analyst, and Player-Focus perspectives in English or Spanish.
* **"Ask the Match" question routing:** A small set of keyword-matched questions are answered from local Scout metrics.

### Tab 2: Player Intelligence & Threshold Matrix
* **Player statistics:** Speed and distance estimates, pass completion, pressure touches, and $xG$ contribution from generated match events.
* **Speed Threshold Alerts:** The player view flags estimated speed above **31.0 km/h**.
* **Player-Focused Lens:** Filter the player matrix by team and inspect individual players' match statistics.

### Tab 3: Post-Match Executive Dossier & Recap
* **Full-Time Tactical Narrative:** Summary generated from current match telemetry; the offline fallback uses fixed narrative text and example milestones/ratings.
* **Control vs. Chaos Analysis:** Narrative commentary on control and transition patterns.
* **Key Milestones:** Time-stamped turning points with tactical significance.
* **Player Ratings:** Narrative player ratings with editorial verdicts; in offline mode these are illustrative fallback content.
* **One-Click Export:** Download publication-ready Markdown dossier.

### Tab 4: Trust Checks & Scout Tools
* **Grounding audit:** View rejected cue claims when the critic records a refusal.
* **Scout tool console:** Call the app's read-only match and player-stat HTTP tools.

---

## 🚀 Quickstart (Zero-Key Local Run)

PitchSense runs out-of-the-box with **zero API keys required** via its built-in deterministic offline engine. The public Azure demo is currently configured to use that same offline mode.

### Prerequisites
* Python $\ge$ 3.12 (managed via `uv`)
* Node.js $\ge$ 20 & npm

### Commands
```bash
# 1. Clone repository
git clone https://github.com/fab679/pitchsense.git
cd pitchsense

# 2. Setup virtual environment and build frontend
make setup

# 3. Run the verification suite
make verify

# 4. Launch the PitchSense Studio
make replay
```

Open **`http://localhost:8000`** in your browser.
1. Click **`▶ PLAY`** to start the match event replay.
2. Watch the synthetic pitch canvas and observe trajectory-derived metrics during replay.
3. Switch tabs across **Player Intelligence**, **Executive Recap**, and **Trust & Tools**.
4. Test the **Ask the Match** prompt or trigger persona translations.

---

## ⚖️ Synthetic Data & IP

* PitchSense uses fictional clubs (**Saltmarsh Rovers** `SAL` and **Brackfield Athletic** `BRA`) and fictional rosters.
* Match events and trajectories are generated locally; no real match feeds are used.
* **Zero Copyrighted Media:** Match trajectories and coordinates are mathematically generated from a seed (21 by default).

---

## 🔗 Live Deployment

**[Open PitchSense on Azure Container Apps](https://pitchsense-demo.thankfulbay-81dc82eb.eastus2.azurecontainerapps.io)** · [Health check](https://pitchsense-demo.thankfulbay-81dc82eb.eastus2.azurecontainerapps.io/healthz)

---

## 🎥 Demo Video Storyboard

The following is a suggested script, not a published demo video.

| Timestamp | Screen | Narrative Voiceover |
|---|---|---|
| **0:00–0:18** | **Tab 1: Live Studio** | "Football stories don't start and end with the scoreline. Meet PitchSense, a match intelligence studio transforming synthetic matches into explainable broadcast narratives." |
| **0:18–0:38** | **Trajectory Metrics** | "From seeded synthetic events, PitchSense derives pass distance and speed estimates, then compares distances against generated ground truth." |
| **0:38–1:00** | **Producer Desk & Grounding** | "The deterministic Scout calculates xG and control-versus-chaos metrics. A code-based critic validates cited facts and numerical claims before a cue is presented." |
| **1:00–1:20** | **Tab 2: Player Intelligence** | "In the Player Intelligence tab, speed thresholds flag player estimates above 31 km/h, alongside player-focused statistics." |
| **1:20–1:40** | **Tab 3: Executive Recap** | "The Match Recap view presents a tactical summary with milestones and player ratings; offline mode uses illustrative fallback content." |
| **1:40–2:00** | **Trust & Deployment** | "PitchSense pairs deterministic match metrics with a live Azure Container Apps demo." |

---

## 📜 License
MIT License — Copyright (c) 2026 PitchSense Contributors.
