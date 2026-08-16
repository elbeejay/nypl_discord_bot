# NYPL & NYC Urban Data AI Assistant 🗽🤖🏛️

A multi-channel AI agentic system built with **FastAPI**, **Google GenAI (Gemini 2.5 Flash)**, **Discord HTTP Interactions**, and an **interactive React + A2UI Web App** styled in the editorial aesthetic of the **New York Public Library (nypl.org)**.

Designed to scale to zero on **Google Cloud Run** in a **single unified container** for hackathons and production deployments.

---

## 🌟 Key Features

1. **🏛️ NYPL Digital Archives & Collections**: Search historical prints, photographs, manuscripts, maps, and research centers (Schwarzman, Schomburg, LPA, SNFL).
2. **🏙️ NYC Open Data Engine**: Live SODA queries for 311 service complaints (noise, parking, heating), DOHMH restaurant inspection letter grades, and 5-borough street tree census data.
3. **✨ Agent-to-User Interface (A2UI)**: The agent dynamically renders rich, interactive widgets inline with chat answers:
   - **📊 Interactive Charts**: Categorical breakdown of 311 complaints and municipal metrics via Chart.js.
   - **🗺️ Interactive NYC Maps**: Leaflet maps with custom pins and popups for library branches and civic incidents.
   - **🖼️ NYPL Archive Photo Gallery**: Vintage print cards with high-res zoomable modal lightbox and direct archive permalinks.
   - **📈 Metric / KPI Cards**: Color-coded stat indicators with deltas and status flags.
   - **📋 Sortable Data Tables**: Paginated, searchable tables with instant CSV download.
4. **💬 Dual-Channel Access**:
   - **Custom Web Interface**: Real-time Server-Sent Events (SSE) token streaming, multi-turn memory, domain filter selector (`/ask`, `/nypl`, `/nycdata`), and dark/light reading room themes.
   - **Discord Slash Bot**: Instant HTTP webhook response (<200ms) with deferred interaction patching.
5. **🚀 Zero-CORS Single-Container Deployment**: Web frontend, REST/SSE APIs, and Discord webhooks run in a single Cloud Run container.

---

## ⚡ Quick Start (Local Development)

### 1. Install Backend Dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Install Frontend Dependencies & Build
```bash
cd frontend
npm install
npm run build
cd ..
```

### 3. Configure Environment
```bash
cp .env.example .env
# Set GEMINI_API_KEY (or GOOGLE_CLOUD_PROJECT), DISCORD credentials if using bot
```

### 4. Run Automated Tests
```bash
python -m unittest discover tests
```

### 5. Start Full-Stack App
```bash
# Start FastAPI backend (serves both API & Frontend SPA at http://localhost:8080)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

> **Tip for Frontend Iteration**: Run `cd frontend && npm run dev` to launch the Vite development server with Hot Module Replacement on `http://localhost:5173` (requests to `/api` are automatically proxied to FastAPI).

---

## ☁️ Google Cloud Run Single-Container Deployment

Deploy the entire stack (React Web App + FastAPI AI Backend + Discord Bot) in **one command**:

```bash
gcloud run deploy nypl-discord-bot \
  --source . \
  --region us-east4 \
  --allow-unauthenticated \
  --service-account nypl-bot-runner@${PROJECT_ID}.iam.gserviceaccount.com \
  --execution-environment gen2 \
  --cpu-boost \
  --no-cpu-throttling \
  --min-instances 0 \
  --max-instances 5 \
  --set-env-vars ENVIRONMENT=production,LOG_LEVEL=INFO,ORCHESTRATOR_MODEL=gemini-2.5-flash,EXPERT_MODEL=gemini-2.5-flash \
  --set-secrets \
DISCORD_PUBLIC_KEY=DISCORD_PUBLIC_KEY:latest,\
DISCORD_APP_ID=DISCORD_APP_ID:latest,\
DISCORD_BOT_TOKEN=DISCORD_BOT_TOKEN:latest,\
GEMINI_API_KEY=GEMINI_API_KEY:latest
```

Once deployed, your single Cloud Run URL provides:
- 🌐 **Web Interface**: `https://<service-url>/`
- 🤖 **Discord Interactions Endpoint**: `https://<service-url>/interactions`
- ⚡ **SSE Streaming API**: `https://<service-url>/api/v1/chat/stream`
- 🩺 **Health Check**: `https://<service-url>/health`

---

## 📚 Complete Documentation

- 📖 **[High-Level System Explainer](docs/HIGH_LEVEL_EXPLAINER.md)** — Executive summary and request lifecycles.
- 💬 **[Discord User Guide](docs/DISCORD_USER_GUIDE.md)** — Discord slash command reference (`/ask`, `/nypl`, `/nycdata`).
- 📋 **[GCP Deployment Procedural SOP](docs/GCP_DEPLOYMENT_PROCEDURE.md)** — Step-by-step GCP Secret Manager & Cloud Run runbook.
- 💻 **[Local Development Guide](docs/LOCAL_DEVELOPMENT.md)** — Local development & automated testing instructions.
- 🤖 **[Discord Bot Setup Guide](docs/DISCORD_BOT_SETUP.md)** — Discord Developer Portal setup.
- 🏛️ **[Architecture & Agents Guide](docs/ARCHITECTURE_AND_AGENTS.md)** — Agent routing and A2UI schema details.
