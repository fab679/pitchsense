# PitchSense Operational Runbook & Testing Guide

This guide describes how to run, test, and deploy the PitchSense Match Intelligence Studio.

---

## 1. Quickstart (Zero-Key Local Run)

PitchSense is designed to run completely offline without external credentials for evaluation:

```bash
# 1. Install Python dependencies with uv & build frontend
make setup

# 2. Run test suite (asserts determinism & schema conformance)
make test

# 3. Launch the Match Intelligence Studio
make replay
```

Open `http://localhost:8000` in any modern web browser.
* Press `▶ PLAY` to start live event replay.
* Observe the synthetic pitch visualization and trajectory-derived metrics.
* Use the Producer Desk to `TAKE` or `KILL` incoming broadcast cues.
* Switch viewer lenses (Analyst, Casual, Player-Focus) or language (EN / ES).
* Test the **"Ask the Match"** console to query match statistics.

---

## 2. Running with Live LLM Providers

PitchSense supports a provider-agnostic gateway. Set your keys in `.env`:

```env
# Optional Azure OpenAI-compatible chat endpoint
AZURE_OPENAI_API_KEY="your-azure-key"
AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"

# Force offline mode (0 = live models, 1 = offline deterministic)
PSENSE_FAKE_MODEL="0"
```

---

## 3. Azure Container Apps: Low-Cost Judge Deployment

### Before you deploy

- [ ] Confirm the Azure subscription is active and has quota in the target region. Choose a nearby supported region and use the **Consumption** workload profile (not Dedicated) for this small demo.
- [ ] Confirm the Azure CLI, Docker, and an Azure subscription with permission to create a resource group, Container Apps environment, Log Analytics workspace, and registry. A local `az login` and `az account show` should identify the intended subscription.
- [ ] Run `make verify` and `npm run build` from `frontend/`; build the container locally with `docker build -t pitchsense:preflight .` before provisioning cloud resources.
- [ ] Keep `PSENSE_FAKE_MODEL=1` for the judge demo unless live Foundry behavior is deliberately required and tested. Do not copy `.env` or API keys into the image; use Container Apps secrets only if needed.
- [ ] Deploy only the app and its required registry/logging infrastructure. The current `infra/main.bicep` also creates Cosmos DB and a managed identity that this app does not currently use, so avoid deploying that template unchanged for a cost-sensitive demo.

### Suggested deployment defaults

| Setting | Judge-friendly value | Why |
|---|---|---|
| Ingress | External HTTP, target port `8000`, transport `auto` | Public HTTPS endpoint and WebSocket support for `/ws/match`. |
| Workload profile | Consumption | Avoid Dedicated-profile baseline capacity for a small demo. |
| Min replicas during judging | `1` | Avoid cold starts or a sleeping judge-facing app; this trades some idle compute for reliable access. |
| Max replicas | `1` | App state is process-local, so one replica avoids diverging replay state across judges. |
| Scale rule | None for the initial judge deployment | A second replica would have independent in-memory match state; add scale-out only after shared state or tested session affinity is implemented. |
| CPU / memory | Start with `0.5` vCPU / `1 GiB` | Matches the current Bicep app sizing; increase only if logs/metrics show pressure. |
| Revision mode | Single | Simpler rollout and lower chance of accidentally splitting stateful replay users across revisions. |
| Logs | Keep app/console logs; limit Log Analytics retention and avoid verbose/debug logging | Log ingestion/retention can cost more than a low-volume demo. |

**Important app behavior:** the replay state, WebSocket clients, and generated match state live in process memory. Do not use multiple replicas for this single-process demo: clients routed to different replicas will see separate match/replay state. Set `maxReplicas` to `1` for predictable behavior unless the app is changed to use shared state/sticky routing. Keep `minReplicas=1` while judges need access. After judging, scale to zero or delete the resources to stop ongoing compute charges. Azure budgets notify; they are not a hard spending cap.

### Health probes

The app already exposes `GET /healthz` with HTTP 200 while the process is responsive. Configure HTTP probes against it:

- **Startup:** `GET :8000/healthz`, initial delay `2s`, period `5s`, timeout `2s`, failure threshold `12`.
- **Readiness:** `GET :8000/healthz`, period `10s`, timeout `2s`, failure threshold `3`.
- **Liveness:** `GET :8000/healthz`, initial delay `10s`, period `15s`, timeout `2s`, failure threshold `3`.

The startup probe gives Python/FastAPI initialization up to about a minute before liveness matters. This endpoint checks process health, not an external Azure model; that is intentional for offline-mode judging. Container Apps supports HTTP probes with success status 200–399. Do not add a dependency check that marks the app unhealthy just because optional Foundry credentials or services are unavailable. The ingress documentation lists a 240-second HTTP request timeout; exercise the deployed WebSocket through a full replay and have a reconnect/restart plan if a long demo connection closes.

### Deploy from this repository

The root Dockerfile builds both the React frontend and FastAPI backend; the resulting container serves the UI and API on port 8000. After installing Azure CLI and signing in, the documented fast path is:

```bash
az login
az account set --subscription "<subscription-id-or-name>"
az extension add --name containerapp --upgrade
az provider register --namespace Microsoft.App
az provider register --namespace Microsoft.OperationalInsights

az containerapp up \
  --name pitchsense-demo \
  --resource-group rg-pitchsense-demo \
  --location <supported-region> \
  --source . \
  --ingress external
```

`az containerapp up --source .` builds with the root Dockerfile (whose `EXPOSE 8000` declares the target port), pushes an image to a registry, and provisions the app/environment as needed. Record the generated **resource group**, **environment**, and public **FQDN**. Then use `az containerapp update` / the Azure portal to set **min replicas = 1 and max replicas = 1**, and configure the probes above. The fast path creates or uses Azure resources and may incur charges; review the resulting resources before proceeding.

### Verify public judge access

- [ ] Open `https://<app-fqdn>/` from a private/incognito window or a phone hotspot (not just the deployment machine).
- [ ] Check `https://<app-fqdn>/healthz` returns `200` and `status: healthy`.
- [ ] Check `https://<app-fqdn>/.well-known/agent-card.json` returns JSON.
- [ ] Click **PLAY** and confirm the match clock/events update; ensure the browser WebSocket connects to `wss://<app-fqdn>/ws/match`.
- [ ] Exercise player stats, recap, Ask the Match, and cue actions on the public deployment.
- [ ] Confirm Container App revision is healthy, ingress is external, and max replicas remains `1` while process-local state is in use.
- [ ] Put the public URL and short testing steps in the competition submission. Keep it publicly accessible and free of login restrictions through the end of judging.
- [ ] Check Azure Cost Management after deployment; set a budget with email alerts. Remember alerts do not stop resources.
- [ ] After the judging window, delete the dedicated resource group if no longer needed, or scale the app down and remove unused resources.

Azure references: [Deploy from local source with `az containerapp up`](https://learn.microsoft.com/en-us/azure/container-apps/containerapp-up), [Health probes](https://learn.microsoft.com/en-us/azure/container-apps/health-probes), [Scaling](https://learn.microsoft.com/en-us/azure/container-apps/scale-app), [Ingress and WebSockets](https://learn.microsoft.com/en-us/azure/container-apps/ingress-overview), [Azure Monitor costs](https://learn.microsoft.com/en-us/azure/azure-monitor/fundamentals/cost-usage).

---

## 4. Using the Scout HTTP tools

PitchSense exposes a project-specific JSON HTTP tool catalog. This endpoint is not an MCP protocol server.

* Endpoint: `POST /api/mcp`
* Tool Catalog: `GET /api/mcp/tools`
* Available Tools:
  - `get_match_summary`: Returns score, xG, momentum, and chaos indices.
  - `get_player_stats`: Returns player completion rates and high-pressure touches.
  - `verify_cue_evidence`: Audits grounding citations for any broadcast cue.
  - `get_auto_eventing_accuracy`: Returns measured trajectory-distance agreement against generated ground-truth distances; it is not image-based detection accuracy.

---

## 5. Service discovery

The project's service information JSON is accessible at:
```
http://localhost:8000/.well-known/agent-card.json
```
This project-specific document is not a standards-compliant A2A agent card.
