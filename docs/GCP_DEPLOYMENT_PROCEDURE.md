# GCP Cloud Run Deployment: Standard Operating Procedure (SOP) 📋☁️

This document is a step-by-step procedural runbook for deploying, configuring, verifying, and maintaining the **NYC & NYPL Multi-Channel AI Assistant** on **Google Cloud Platform (GCP)**.

---

## 🎯 Procedural Checklist

- [ ] **Phase 1: Environment & CLI Pre-flight**
- [ ] **Phase 2: Project Setup & API Initialization**
- [ ] **Phase 3: IAM Service Account Provisioning**
- [ ] **Phase 4: Secret Manager Secret Storage**
- [ ] **Phase 5: Cloud Run Deployment Execution**
- [ ] **Phase 6: Verification & Post-Deployment Smoke Tests**
- [ ] **Phase 7: Discord Interactions Handshake & Command Registration**
- [ ] **Phase 8: Day-2 Operations & Monitoring**

---

## 🛠️ Phase 1: Environment & CLI Pre-flight

1. **Verify Google Cloud SDK installation**:
   ```bash
   gcloud --version
   ```

2. **Authenticate with Google Cloud**:
   ```bash
   gcloud auth login
   ```

3. **Set Shell Environment Variables**:
   ```bash
   export PROJECT_ID="your-gcp-project-id"
   export REGION="us-east4"  # or us-central1 / us-east1
   export SERVICE_NAME="nypl-discord-bot"

   gcloud config set project $PROJECT_ID
   gcloud config set run/region $REGION
   ```

4. **Confirm Project Number**:
   ```bash
   export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
   echo "Target Project Number: $PROJECT_NUMBER"
   ```

---

## ⚙️ Phase 2: Project Setup & API Initialization

Enable all required Google Cloud APIs:

```bash
gcloud services enable \
  run.googleapis.com \
  secretmanager.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  compute.googleapis.com \
  aiplatform.googleapis.com
```

> [!IMPORTANT]
> **Why `compute.googleapis.com` is required**:
> Cloud Build's default source builder relies on the default Compute Engine service account (`${PROJECT_NUMBER}-compute@developer.gserviceaccount.com`). Enabling `compute.googleapis.com` ensures this account is generated. Wait **30–60 seconds** after enabling APIs before proceeding.

---

## 🛡️ Phase 3: IAM Service Account Provisioning (Least Privilege)

Create an isolated runtime identity for Cloud Run rather than using broad default credentials:

1. **Create the dedicated service account**:
   ```bash
   gcloud iam service-accounts create nypl-bot-runner \
     --description="Runtime service account for NYPL Discord Bot" \
     --display-name="NYPL Bot Runner"
   ```

2. **Grant Secret Accessor permissions**:
   ```bash
   gcloud projects add-iam-policy-binding $PROJECT_ID \
     --member="serviceAccount:nypl-bot-runner@${PROJECT_ID}.iam.gserviceaccount.com" \
     --role="roles/secretmanager.secretAccessor"
   ```

3. *(Optional: If using Vertex AI instead of Gemini API Key)*:
   ```bash
   gcloud projects add-iam-policy-binding $PROJECT_ID \
     --member="serviceAccount:nypl-bot-runner@${PROJECT_ID}.iam.gserviceaccount.com" \
     --role="roles/aiplatform.user"
   ```

---

## 🔒 Phase 4: Secret Manager Secret Storage

Store secrets in Secret Manager. Use `--data-file=-` to stream values without writing plaintext credentials to disk or shell history.

### A. Required Secrets

```bash
# 1. Discord Public Key (64-character hex string)
echo -n "YOUR_DISCORD_PUBLIC_KEY" | gcloud secrets create DISCORD_PUBLIC_KEY \
  --data-file=- --replication-policy="automatic"

# 2. Discord Application ID
echo -n "YOUR_DISCORD_APP_ID" | gcloud secrets create DISCORD_APP_ID \
  --data-file=- --replication-policy="automatic"

# 3. Discord Bot Token
echo -n "YOUR_DISCORD_BOT_TOKEN" | gcloud secrets create DISCORD_BOT_TOKEN \
  --data-file=- --replication-policy="automatic"

# 4. Google Gemini API Key
echo -n "YOUR_GEMINI_API_KEY" | gcloud secrets create GEMINI_API_KEY \
  --data-file=- --replication-policy="automatic"

# 5. Frontend API Key (Secures /api/v1 endpoints for web & mobile apps)
echo -n "YOUR_FRONTEND_API_KEY" | gcloud secrets create FRONTEND_API_KEY \
  --data-file=- --replication-policy="automatic"
```

### B. Optional Secrets (Create only if utilized)

```bash
# NYC Open Data App Token (raises SODA rate limits to 50k requests/hr)
echo -n "YOUR_SOCRATA_TOKEN" | gcloud secrets create NYC_SOCRATA_APP_TOKEN \
  --data-file=- --replication-policy="automatic"

# NYPL Digital Collections API Token
echo -n "YOUR_NYPL_TOKEN" | gcloud secrets create NYPL_API_TOKEN \
  --data-file=- --replication-policy="automatic"
```

> [!TIP]
> **To update an existing secret value in the future**:
> ```bash
> echo -n "NEW_VALUE" | gcloud secrets versions add SECRET_NAME --data-file=-
> ```

---

## 🚀 Phase 5: Cloud Run Deployment Execution

Execute the deployment from the repository root:

```bash
gcloud run deploy $SERVICE_NAME \
  --source . \
  --region $REGION \
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
  --set-env-vars="ENVIRONMENT=production,LOG_LEVEL=INFO,ORCHESTRATOR_MODEL=gemini-3.5-flash-lite,EXPERT_MODEL=gemini-3.5-flash-lite" \
  --set-secrets="DISCORD_PUBLIC_KEY=DISCORD_PUBLIC_KEY:latest,DISCORD_APP_ID=DISCORD_APP_ID:latest,DISCORD_BOT_TOKEN=DISCORD_BOT_TOKEN:latest,GEMINI_API_KEY=GEMINI_API_KEY:latest,FRONTEND_API_KEY=FRONTEND_API_KEY:latest"
```

### Key Flag Rationale:
| Flag | Purpose |
| :--- | :--- |
| `--no-cpu-throttling` | Keeps CPU active so async background workers can complete Gemini calls and patch Discord webhooks after HTTP 200 ack. |
| `--cpu-boost` | Allocates extra CPU during container boot to eliminate cold-start lag. |
| `--execution-environment gen2` | Second-generation Linux virtualization for faster networking and syscall performance. |
| `--min-instances 0` | Scales to 0 when idle ($0 idle cost). Set to `1` if zero cold-start is strictly required. |
| `--service-account` | Restricts container permissions strictly to Secret Manager read access. |

---

## 🧪 Phase 6: Verification & Smoke Tests

Extract the live Cloud Run Service URL:
```bash
export SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)")
echo "Service URL: $SERVICE_URL"
```

1. **Test Bare Health Endpoint (Unauthenticated)**:
   ```bash
   curl -i "$SERVICE_URL/health"
   ```
   *Expected: `HTTP/2 200` with `{"status": "ok"}`*

2. **Test Production Root (Redacted Metadata)**:
   ```bash
   curl -i "$SERVICE_URL/"
   ```
   *Expected: `HTTP/2 200` with `{"status": "healthy", "service": "nypl_discord_bot"}`*

3. **Test Frontend Security (Without Key)**:
   ```bash
   curl -i "$SERVICE_URL/api/v1/a2ui/catalog"
   ```
   *Expected: `HTTP/2 401 Unauthorized` with `{"detail": "Missing API Key..."}`*

4. **Test Frontend Security (With Valid Key)**:
   ```bash
   curl -i -H "X-API-Key: YOUR_FRONTEND_API_KEY" "$SERVICE_URL/api/v1/a2ui/catalog"
   ```
   *Expected: `HTTP/2 200 OK` with A2UI component catalog schema.*

---

## 🔗 Phase 7: Discord Interactions Handshake & Command Registration

1. **Connect Discord Interactions Endpoint**:
   - Open [Discord Developer Portal](https://discord.com/developers/applications) -> Select your App -> **General Information**.
   - Set **Interactions Endpoint URL** to:
     ```text
     https://<YOUR_SERVICE_URL>/interactions
     ```
   - Click **Save Changes**. Discord will perform an automated Ed25519 signature test ping; your backend will reply with `{"type": 1}`, and Discord will show a green checkmark.

2. **Register Production Slash Commands**:
   ```bash
   # Register commands to your test server (Instant availability):
   python scripts/register_commands.py --guild YOUR_DISCORD_GUILD_ID

   # Or register globally (available across all servers; propagates in ~1 hr):
   python scripts/register_commands.py
   ```

3. **Live Test in Discord**:
   Run `/ask query: Top 311 noise complaints in Brooklyn` in any channel where the bot is invited.

---

## 📊 Phase 8: Day-2 Operations & Maintenance

### 1. Live Log Streaming
```bash
gcloud beta run services logs tail $SERVICE_NAME --region $REGION
```

### 2. Querying Recent Error Logs
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME AND severity>=ERROR" --limit 25
```

### 3. Updating Secrets Without Code Deployment
```bash
# Add a new version in Secret Manager:
echo -n "NEW_KEY" | gcloud secrets versions add FRONTEND_API_KEY --data-file=-

# Update Cloud Run to deploy a revision with the updated secret:
gcloud run services update $SERVICE_NAME --region $REGION
```

### 4. Rollback to a Previous Revision
```bash
# List revision history
gcloud run revisions list --service $SERVICE_NAME --region $REGION

# Direct 100% traffic to a known good revision
gcloud run services update-traffic $SERVICE_NAME --region $REGION --to-revisions=REVISION_NAME=100
```
