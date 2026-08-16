# GCP Setup & Cloud Run Modern Deployment Guide ☁️🚀

This guide walks you through safely, securely, and cost-effectively deploying the **NYC & NYPL Multi-Channel Assistant Backend** to **Google Cloud Run** using **GCP Secret Manager**, **IAM Least-Privilege Service Accounts**, and **Google GenAI / Gemini 3.5 Flash Lite**.

---

## 🌟 Why Cloud Run for this Architecture?

- **Scale to Zero ($0 Idle Cost)**: Spins down to 0 instances when idle, remaining well within GCP's generous free tier (2 million requests/month, 360,000 vCPU-seconds free).
- **Startup CPU Boost**: Dramatically reduces cold-start latency when scaling up from zero.
- **Serverless Security**: Secrets are securely injected from GCP Secret Manager directly into the container memory at runtime—never baked into Docker images or committed to Git.
- **Dedicated Service Account**: Operates under strict least-privilege IAM roles rather than broad default service accounts.
- **HTTP Interactions (No WebSockets)**: Discord delivers slash command events via HTTP POST to `/interactions`, requiring zero persistent connection overhead.

---

## 📋 Prerequisites

1. A **Google Cloud Platform (GCP)** Account with billing enabled ([cloud.google.com](https://cloud.google.com/)).
2. The **Google Cloud SDK (`gcloud` CLI)** installed and updated:
   ```bash
   gcloud components update
   ```
3. Your Discord Bot credentials (Application ID, Public Key, Bot Token from [Discord Developer Portal](https://discord.com/developers/applications)).
4. A Google Gemini API Key from [Google AI Studio](https://aistudio.google.com/) (or Vertex AI enabled).

---

## 🛠️ Step 1: Project Setup & API Activation

1. **Authenticate the `gcloud` CLI**:
   ```bash
   gcloud auth login
   ```

2. **Select or Create your GCP Project**:
   ```bash
   # Set your Project ID
   export PROJECT_ID="your-nypl-discord-bot-project"
   export REGION="us-east4"  # or us-central1, us-east1

   # Create the project (skip if using an existing project)
   gcloud projects create $PROJECT_ID --name="NYC NYPL Discord Bot"

   # Set active project and default region
   gcloud config set project $PROJECT_ID
   gcloud config set run/region $REGION
   ```

3. **Enable Required Google Cloud APIs**:
   ```bash
   gcloud services enable \
     run.googleapis.com \
     secretmanager.googleapis.com \
     cloudbuild.googleapis.com \
     artifactregistry.googleapis.com \
     aiplatform.googleapis.com
   ```

---

## 🛡️ Step 2: Create a Dedicated IAM Service Account (Least Privilege)

> [!IMPORTANT]
> **Security Best Practice**: Never run production Cloud Run workloads with the default Compute Engine service account. Create a dedicated service account restricted *only* to accessing the required secrets and invoking AI models.

1. **Create the dedicated service account**:
   ```bash
   gcloud iam service-accounts create nypl-bot-runner \
     --description="Service account for NYC & NYPL Discord Bot Cloud Run service" \
     --display-name="NYPL Bot Runner"
   ```

2. **Retrieve your Project Number**:
   ```bash
   export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
   ```

3. **Grant Secret Manager Access** (allows the bot to read secrets):
   ```bash
   gcloud projects add-iam-policy-binding $PROJECT_ID \
     --member="serviceAccount:nypl-bot-runner@${PROJECT_ID}.iam.gserviceaccount.com" \
     --role="roles/secretmanager.secretAccessor"
   ```

4. *(Optional — If using Vertex AI instead of a Gemini API Key)*:
   ```bash
   gcloud projects add-iam-policy-binding $PROJECT_ID \
     --member="serviceAccount:nypl-bot-runner@${PROJECT_ID}.iam.gserviceaccount.com" \
     --role="roles/aiplatform.user"
   ```

---

## 🔒 Step 3: Store Secrets in GCP Secret Manager

Never store credentials in environment files or Dockerfiles. Create them in Secret Manager:

### A. Required Secrets
```bash
# 1. Discord Public Key (64-char hex string for Ed25519 webhook verification)
echo -n "YOUR_DISCORD_PUBLIC_KEY" | gcloud secrets create DISCORD_PUBLIC_KEY \
  --replication-policy="automatic" \
  --data-file=-

# 2. Discord Application ID
echo -n "YOUR_DISCORD_APPLICATION_ID" | gcloud secrets create DISCORD_APP_ID \
  --replication-policy="automatic" \
  --data-file=-

# 3. Discord Bot Token
echo -n "YOUR_DISCORD_BOT_TOKEN" | gcloud secrets create DISCORD_BOT_TOKEN \
  --replication-policy="automatic" \
  --data-file=-

# 4. Google Gemini API Key (if using AI Studio key)
echo -n "YOUR_GEMINI_API_KEY" | gcloud secrets create GEMINI_API_KEY \
  --replication-policy="automatic" \
  --data-file=-
```

### B. Optional Secrets (Create only if you use them)
```bash
# 5. NYC Open Data App Token (optional, raises SODA rate limit to 50k requests/hr)
echo -n "YOUR_SOCRATA_TOKEN" | gcloud secrets create NYC_SOCRATA_APP_TOKEN \
  --replication-policy="automatic" \
  --data-file=-

# 6. NYPL Digital Collections API Token (optional)
echo -n "YOUR_NYPL_API_TOKEN" | gcloud secrets create NYPL_API_TOKEN \
  --replication-policy="automatic" \
  --data-file=-

# 7. Frontend API Key (optional, secures /api/v1 endpoints for web/mobile apps)
echo -n "YOUR_CUSTOM_FRONTEND_API_KEY" | gcloud secrets create FRONTEND_API_KEY \
  --replication-policy="automatic" \
  --data-file=-
```

---

## 🚀 Step 4: Deploy to Google Cloud Run

Deploy directly from source. Cloud Build will package the container from `Dockerfile` and deploy to Cloud Run with full security settings.

> [!IMPORTANT]
> **Why `--no-cpu-throttling` is Required**:
> Discord slash commands require an immediate `< 3s` HTTP response (`type: 5`), while the AI agent background task executes the query and patches Discord via webhook.
> Standard Cloud Run throttles CPU to 0% once the initial HTTP response ends, which halts background tasks. `--no-cpu-throttling` keeps CPU active until the background agent finishes!

### Standard Production Deployment Command:

```bash
gcloud run deploy nypl-discord-bot \
  --source . \
  --region us-east4 \
  --platform managed \
  --allow-unauthenticated \
  --service-account nypl-bot-runner@${PROJECT_ID}.iam.gserviceaccount.com \
  --execution-environment gen2 \
  --cpu-boost \
  --no-cpu-throttling \
  --min-instances 0 \
  --max-instances 5 \
  --concurrency 80 \
  --memory 512Mi \
  --cpu 1 \
  --timeout 120s \
  --set-env-vars ENVIRONMENT=production,LOG_LEVEL=INFO,ORCHESTRATOR_MODEL=gemini-3.5-flash-lite,EXPERT_MODEL=gemini-3.5-flash-lite \
  --set-secrets \
DISCORD_PUBLIC_KEY=DISCORD_PUBLIC_KEY:latest,\
DISCORD_APP_ID=DISCORD_APP_ID:latest,\
DISCORD_BOT_TOKEN=DISCORD_BOT_TOKEN:latest,\
GEMINI_API_KEY=GEMINI_API_KEY:latest
```

*(Note: If you created optional secrets like `NYC_SOCRATA_APP_TOKEN` or `FRONTEND_API_KEY`, append them to `--set-secrets` as `KEY=KEY:latest`).*

---

## ✅ Step 5: Verify Deployment & Health

Once deployment succeeds, Cloud Run outputs your Service URL (e.g. `https://nypl-discord-bot-xyz-uk.a.run.app`).

1. **Verify Root Health Check**:
   ```bash
   curl -s https://nypl-discord-bot-xyz-uk.a.run.app/health
   ```
   **Expected Output**:
   ```json
   {"status": "ok"}
   ```

2. **Verify Redacted Production Root**:
   ```bash
   curl -s https://nypl-discord-bot-xyz-uk.a.run.app/
   ```
   **Expected Output**:
   ```json
   {
     "status": "healthy",
     "service": "nypl_discord_bot"
   }
   ```
   *(Note: OpenAPI/Swagger documentation at `/docs` and debug `/chat` are automatically disabled in production mode for security).*

---

## 🔗 Step 6: Configure Discord Developer Portal

1. Copy your Cloud Run Service URL and append `/interactions`:
   ```text
   https://nypl-discord-bot-xyz-uk.a.run.app/interactions
   ```
2. Navigate to [Discord Developer Portal](https://discord.com/developers/applications) -> Select your Application -> **General Information**.
3. Paste the URL into **Interactions Endpoint URL**.
4. Click **Save Changes**. Discord will immediately send an Ed25519 signed `PING` payload. Your Cloud Run bot verifies the signature and replies with `{"type": 1}`, displaying a green success banner in Discord!

---

## 📜 Step 7: Register Slash Commands

Register your slash commands globally or to your test guild:

```bash
# Register global commands (available across all servers; takes ~1 hour to propagate globally)
python scripts/register_commands.py

# Or register directly to a specific Discord Server / Guild for instant availability:
python scripts/register_commands.py --guild YOUR_GUILD_ID
```

---

## 📊 Monitoring, Logs, & Security Auditing

1. **Stream Live Cloud Run Logs**:
   ```bash
   gcloud beta run services logs tail nypl-discord-bot --region us-east4
   ```

2. **Inspect Recent Logs for Errors**:
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=nypl-discord-bot AND severity>=WARNING" --limit 20
   ```

3. **Check Secret Access Audit**:
   ```bash
   gcloud logging read "protoPayload.serviceName=secretmanager.googleapis.com" --limit 10
   ```

---

## 🛠️ Production Troubleshooting Checklist

| Issue | Root Cause | Solution |
| :--- | :--- | :--- |
| **Discord: "Endpoint verification failed"** | `DISCORD_PUBLIC_KEY` secret is wrong, or service account lacks secret accessor permissions. | Verify public key hex string and verify that `nypl-bot-runner` has `roles/secretmanager.secretAccessor`. |
| **Discord: "Bot is thinking..." but never replies** | Cloud Run paused container CPU before background task completed. | Ensure `--no-cpu-throttling` is specified on the Cloud Run deployment. |
| **Build error: "Secret not found" during deploy** | A secret named in `--set-secrets` was not created in Secret Manager. | Remove the uncreated secret from `--set-secrets` or create it with `gcloud secrets create`. |
| **504 Gateway Timeout during cold start** | First invocation container boot took longer than Discord 3s timeout. | Enable `--cpu-boost` or set `--min-instances 1` for 100% warm containers. |
| **API returns 429 Too Many Requests** | Built-in sliding-window rate limit was exceeded. | Increase `RATE_LIMIT_PER_MINUTE` environment variable (default: 60/min). |

