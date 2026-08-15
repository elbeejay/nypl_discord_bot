# GCP Setup & Cloud Run Deployment Guide ☁️🚀

This guide walks you through deploying the **NYC & NYPL Discord Bot** to **Google Cloud Run** using **GCP Secret Manager** and **Google GenAI / Vertex AI**.

---

## 🌟 Why Cloud Run for this Discord Bot?

- **Scale to Zero ($0 Idle Cost)**: The bot spins down to 0 instances when inactive, remaining well within GCP's free tier (2 million requests/month free).
- **Fast Execution**: Auto-scales instantly when Discord webhook calls arrive.
- **Serverless Security**: Secrets are securely mounted from GCP Secret Manager directly into the container environment.
- **Containerized**: Built from a lightweight Python 3.11 Slim container.

---

## 📋 Prerequisites

1. A **Google Cloud Platform (GCP)** Account with billing enabled ([cloud.google.com](https://cloud.google.com/)).
2. The **Google Cloud SDK (`gcloud` CLI)** installed on your machine ([cloud.google.com/sdk/docs/install](https://cloud.google.com/sdk/docs/install)).
3. Docker installed locally *(optional; Cloud Build builds the container in the cloud)*.

---

## 🛠️ Step 1: Initial GCP Project Setup

1. **Authenticate the `gcloud` CLI**:
   ```bash
   gcloud auth login
   ```

2. **Create or select your GCP Project**:
   ```bash
   # Set your desired Project ID
   export PROJECT_ID="your-nypl-discord-bot-project"

   # Create the project (or use an existing one)
   gcloud projects create $PROJECT_ID --name="NYC NYPL Discord Bot"

   # Set active project
   gcloud config set project $PROJECT_ID
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

## 🔒 Step 2: Store Secrets in GCP Secret Manager

Never bake API keys or Discord tokens into your Docker image. Store them securely in GCP Secret Manager:

```bash
# 1. Discord Public Key (64-character hex)
gcloud secrets create DISCORD_PUBLIC_KEY --replication-policy="automatic"
echo -n "your_discord_public_key_hex" | gcloud secrets versions add DISCORD_PUBLIC_KEY --data-file=-

# 2. Discord Application ID
gcloud secrets create DISCORD_APP_ID --replication-policy="automatic"
echo -n "your_discord_app_id" | gcloud secrets versions add DISCORD_APP_ID --data-file=-

# 3. Discord Bot Token
gcloud secrets create DISCORD_BOT_TOKEN --replication-policy="automatic"
echo -n "your_discord_bot_token" | gcloud secrets versions add DISCORD_BOT_TOKEN --data-file=-

# 4. Google Gemini API Key
gcloud secrets create GEMINI_API_KEY --replication-policy="automatic"
echo -n "your_gemini_api_key" | gcloud secrets versions add GEMINI_API_KEY --data-file=-

# 5. (Optional) NYC Open Data Socrata App Token
gcloud secrets create NYC_SOCRATA_APP_TOKEN --replication-policy="automatic"
echo -n "your_socrata_token" | gcloud secrets versions add NYC_SOCRATA_APP_TOKEN --data-file=-

# 6. (Optional) NYPL API Token
gcloud secrets create NYPL_API_TOKEN --replication-policy="automatic"
echo -n "your_nypl_token" | gcloud secrets versions add NYPL_API_TOKEN --data-file=-
```

---

## 🛡️ Step 3: Configure IAM Permissions for Secret Manager

Cloud Run needs permission to read secrets from Secret Manager during container startup.

Grant the **Secret Manager Secret Accessor** role to your project's Cloud Run compute service account:

```bash
# Get your Project Number
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

# Grant secret accessor role to Compute Engine default service account
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

---

## 🚀 Step 4: Deploy to Cloud Run

Run `gcloud run deploy` directly from the project root directory. Google Cloud Build will automatically build the container from `Dockerfile` and deploy it.

> [!IMPORTANT]
> **Why `--no-cpu-throttling` is Critical**:
> Discord slash commands require an immediate `< 3s` HTTP response (`type: 5`), while the AI agent runs in a FastAPI background task.
> By default, standard Cloud Run throttles CPU to near zero as soon as the HTTP response finishes, which would freeze the agent background worker!
> `--no-cpu-throttling` ensures the container retains dedicated CPU to finish running the Gemini agent and patch the Discord response webhook.

### Deploy Command:

```bash
gcloud run deploy nypl-discord-bot \
  --source . \
  --region us-east4 \
  --platform managed \
  --allow-unauthenticated \
  --no-cpu-throttling \
  --min-instances 0 \
  --max-instances 5 \
  --memory 512Mi \
  --cpu 1 \
  --set-env-vars ENVIRONMENT=production,LOG_LEVEL=INFO,ORCHESTRATOR_MODEL=gemini-2.0-flash,EXPERT_MODEL=gemini-2.0-flash \
  --set-secrets \
DISCORD_PUBLIC_KEY=DISCORD_PUBLIC_KEY:latest,\
DISCORD_APP_ID=DISCORD_APP_ID:latest,\
DISCORD_BOT_TOKEN=DISCORD_BOT_TOKEN:latest,\
GEMINI_API_KEY=GEMINI_API_KEY:latest,\
NYC_SOCRATA_APP_TOKEN=NYC_SOCRATA_APP_TOKEN:latest,\
NYPL_API_TOKEN=NYPL_API_TOKEN:latest
```

*(Note: If you are not using optional NYC or NYPL tokens, simply omit them from `--set-secrets`).*

---

## ✅ Step 5: Verify Deployment

Once deployment completes, Cloud Run outputs your Service URL (e.g., `https://nypl-discord-bot-xyz-uk.a.run.app`).

1. **Test Root Status**:
   ```bash
   curl https://nypl-discord-bot-xyz-uk.a.run.app/
   ```
   Expected response:
   ```json
   {
     "status": "healthy",
     "service": "nypl_discord_bot",
     "environment": "production",
     "models": {
       "orchestrator": "gemini-2.0-flash",
       "expert": "gemini-2.0-flash"
     }
   }
   ```

2. **Test Health Check**:
   ```bash
   curl https://nypl-discord-bot-xyz-uk.a.run.app/health
   ```
   Expected response:
   ```json
   {"status": "ok"}
   ```

---

## 🔗 Step 6: Connect to Discord Developer Portal

1. Copy your Cloud Run URL and append `/interactions`:
   ```text
   https://nypl-discord-bot-xyz-uk.a.run.app/interactions
   ```
2. Go to [Discord Developer Portal](https://discord.com/developers/applications) -> Select your App -> **General Information**.
3. Paste the URL into **Interactions Endpoint URL**.
4. Click **Save Changes**. Discord will send a ping to verify the signature and display a green success checkmark!

---

## 📜 Step 7: Register Production Slash Commands

Now that your production service is live and verified, register the commands globally so users can interact with your bot:

```bash
# Register global commands (takes ~1 hour to appear everywhere)
python scripts/register_commands.py

# Or register directly to your production server for immediate availability:
python scripts/register_commands.py --guild YOUR_SERVER_ID
```

---

## 📊 Monitoring & Viewing Logs

You can stream live logs from Cloud Run in your terminal:

```bash
# Live log streaming
gcloud beta run services logs tail nypl-discord-bot --region us-east4

# Or view recent logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=nypl-discord-bot" --limit 50
```

---

## 🛠️ Common Cloud Run Troubleshooting

| Symptom | Cause | Solution |
| :--- | :--- | :--- |
| **Discord says: "Endpoint verification failed"** | `DISCORD_PUBLIC_KEY` secret is invalid or service account cannot access it. | Check `gcloud secrets versions access latest --secret=DISCORD_PUBLIC_KEY` and verify IAM permissions in Step 3. |
| **Bot says: "Bot is thinking..." but never updates** | CPU throttling stopped the background task after HTTP 200/5 ack. | Ensure `--no-cpu-throttling` (or `--cpu-allocation-policy=always`) was supplied when deploying to Cloud Run. |
| **Permission Denied / 403 reading secrets** | Cloud Run Service Account lacks `roles/secretmanager.secretAccessor`. | Run the IAM binding command in Step 3. |
| **504 Gateway Timeout during cold start** | Cold container startup took longer than expected. | Set `--min-instances 1` if you want a warm container at all times (costs ~$5-$10/month), or leave `--min-instances 0` for 100% free idle tier. |
