# NYPL / NYC Data Discord Bot 🗽🤖

An AI agentic backend built with **FastAPI**, **Google GenAI (Gemini 2.0 Flash)**, and **Discord HTTP Interactions**, designed to scale to zero on **Google Cloud Run** to query NYC Open Data (311, restaurant inspections, tree census) and NYPL Digital Collections.

---

## 📚 Complete Documentation

Comprehensive guides are available in the [`docs/`](docs/README.md) directory:

- 📖 **[High-Level System Explainer](docs/HIGH_LEVEL_EXPLAINER.md)** — Executive summary, end-to-end request lifecycles, and architecture overview.
- 💬 **[Discord User Guide](docs/DISCORD_USER_GUIDE.md)** — User guide for interacting with `/ask`, `/nypl`, and `/nycdata` slash commands.
- 📋 **[GCP Deployment Procedural SOP](docs/GCP_DEPLOYMENT_PROCEDURE.md)** — Step-by-step procedural runbook for provisioning, secrets, deployment, and verification.
- 💻 **[Local Development Guide](docs/LOCAL_DEVELOPMENT.md)** — Step-by-step instructions for running locally with virtualenv, ngrok tunneling, and running automated tests.
- 🤖 **[Discord Bot Setup Guide](docs/DISCORD_BOT_SETUP.md)** — Developer Portal walkthrough, credentials, OAuth2 bot invite link, and slash commands.
- ☁️ **[GCP Setup & Cloud Run Deployment](docs/GCP_SETUP_AND_DEPLOYMENT.md)** — GCP Secret Manager configuration, `--no-cpu-throttling` deployment, and production verification.
- 🏛️ **[Architecture & Agents Guide](docs/ARCHITECTURE_AND_AGENTS.md)** — Agent-to-Agent (A2A) orchestration model, SODA SoQL queries, and the Discord 3-second deferred interaction flow.

---

## ⚡ Quick Start (Local)

### 1. Install Dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Fill in GEMINI_API_KEY, DISCORD_APP_ID, DISCORD_PUBLIC_KEY, DISCORD_BOT_TOKEN
```

### 3. Run Automated Tests
```bash
python -m unittest discover tests
```

### 4. Start Local Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

### 5. Register Slash Commands
```bash
# Instant registration for your development server
python scripts/register_commands.py --guild YOUR_DISCORD_SERVER_ID

# Or global registration
python scripts/register_commands.py
```

---

## 💡 Overview & Architecture

Building an AI agentic backend on Cloud Run with Discord interactions over HTTP is an ideal architecture for querying urban datasets:
- **Serverless & Cost-Effective**: Scales to 0 when idle ($0 when unused, runs comfortably within GCP's free tier).
- **Agent-to-Agent (A2A) Routing**: An Orchestrator Agent triages user requests and delegates to domain-expert agents (NYPL archives & NYC Open Data).
- **HTTP Interactions vs. Gateway**: Uses Discord's modern HTTP webhook interactions rather than persistent WebSocket connections.
- **3-Second Deferral Rule**: Instantly returns `{"type": 5}` (`DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE`) in `< 200ms` and patches the original message via background task after running the agent tools.

---

## ☁️ Google Cloud Run Deployment

Deploy directly from source with secrets mounted from Secret Manager:

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

Once deployed, copy your Cloud Run endpoint URL (`https://<service-url>/interactions`) and set it as the **Interactions Endpoint URL** in the [Discord Developer Portal](https://discord.com/developers/applications). Detailed setup guide is in [`docs/GCP_SETUP_AND_DEPLOYMENT.md`](docs/GCP_SETUP_AND_DEPLOYMENT.md).

