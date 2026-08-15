# Local Development Guide 💻

This guide walks you through setting up, running, testing, and debugging the **NYC & NYPL Discord Bot** locally on your machine.

---

## 📋 Prerequisites

Before getting started, ensure you have:
1. **Python 3.10+** (Python 3.10, 3.11, or 3.12 recommended).
2. **A Discord Developer Account** ([discord.com/developers](https://discord.com/developers/applications)).
3. **A Google Gemini API Key** ([ai.google.dev](https://ai.google.dev/)).
4. **An HTTP Tunneling Tool** like **ngrok** ([ngrok.com](https://ngrok.com/)) or **Cloudflare Tunnel (`cloudflared`)** to expose your local FastAPI server to Discord's webhooks.

---

## 🛠️ Step 1: Clone and Set Up Virtual Environment

Open your terminal and create an isolated virtual environment:

```bash
# 1. Navigate to the project folder
cd /path/to/nypl_discord_bot

# 2. Create virtual environment
python3 -m venv .venv

# 3. Activate virtual environment
# On Linux / macOS:
source .venv/bin/activate

# On Windows (PowerShell):
# .venv\Scripts\Activate.ps1

# 4. Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🔑 Step 2: Environment Configuration (`.env`)

Create your `.env` file from the provided template:

```bash
cp .env.example .env
```

Open `.env` and fill in the required variables:

```ini
# ==============================================================================
# DISCORD CREDENTIALS
# Found at https://discord.com/developers/applications -> [Your App]
# ==============================================================================
DISCORD_APP_ID=123456789012345678
DISCORD_PUBLIC_KEY=a1b2c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef0
DISCORD_BOT_TOKEN=OTk5...YourBotToken...

# Optional: Set your test Discord Server (Guild) ID for INSTANT slash command updates
DISCORD_GUILD_ID=987654321098765432

# ==============================================================================
# GOOGLE GENAI CONFIGURATION
# Generate a free key at https://aistudio.google.com/
# ==============================================================================
GEMINI_API_KEY=AIzaSy...YourGeminiKey

# GenAI Models
ORCHESTRATOR_MODEL=gemini-2.0-flash
EXPERT_MODEL=gemini-2.0-flash

# ==============================================================================
# EXTERNAL DATA APIS (Optional - Increases rate limits)
# ==============================================================================
# NYC Open Data App Token: https://data.cityofnewyork.us/profile/edit/developer_settings
NYC_SOCRATA_APP_TOKEN=

# NYPL API Token: https://api.repo.nypl.org/
NYPL_API_TOKEN=

# ==============================================================================
# SERVER CONFIGURATION
# ==============================================================================
ENVIRONMENT=development
PORT=8080
LOG_LEVEL=INFO
```

---

## 🚀 Step 3: Run the FastAPI Server

Start the local development server with hot reloading enabled:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

Verify that the server is running:
- Open your browser or run: `curl http://localhost:8080/`
- Expected response:
  ```json
  {
    "status": "healthy",
    "service": "nypl_discord_bot",
    "environment": "development",
    "models": {
      "orchestrator": "gemini-2.0-flash",
      "expert": "gemini-2.0-flash"
    }
  }
  ```

---

## 🧪 Step 4: Test Locally (Without Discord First)

You can test the full AI agent reasoning loop and tool execution locally without needing Discord webhooks or tunnels.

### Method A: Interactive Terminal Tester (Recommended)
Run the built-in interactive CLI test script:

```bash
# Start interactive chat in your terminal
python scripts/test_agent.py
```
You can chat with the agents directly:
```text
You > What are recent 311 noise complaints in Astoria?
You > Where is the Schomburg Center located?
You > /nypl 1930s subway photos
You > /nycdata Health inspection grade for Katz's Delicatessen
```

Or run single one-shot queries from the command line:
```bash
python scripts/test_agent.py "What are the latest 311 complaints in Brooklyn?"
```

### Method B: Test via Swagger UI or cURL (`POST /chat`)
When Uvicorn is running (`uvicorn app.main:app --reload`), visit **FastAPI Interactive Docs**:
- Open **http://localhost:8080/docs** in your browser.
- Expand `POST /chat` -> Click **Try it out** -> Enter your query -> Click **Execute**.

Or via cURL:
```bash
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Show 311 noise issues in Williamsburg"}'
```

---

## 🌐 Step 5: Expose Localhost to Discord (Tunneling)

Discord requires an **HTTPS** endpoint to deliver slash command interactions. In local development, you must create a public tunnel to your localhost port `8080`.

### Option A: Using `ngrok` (Recommended)

1. Start the tunnel:
   ```bash
   ngrok http 8080
   ```
2. Copy the public forwarding HTTPS URL (e.g., `https://a1b2-34-56-78.ngrok-free.app`).

### Option B: Using Cloudflare Tunnel (`cloudflared`)

1. Start a free tunnel:
   ```bash
   cloudflared tunnel --url http://localhost:8080
   ```
2. Copy the generated `https://...trycloudflare.com` URL.

---

## 🤖 Step 5: Configure Discord Interactions Endpoint

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Select your application and click the **General Information** tab.
3. Locate the **Interactions Endpoint URL** field.
4. Enter your tunnel URL followed by `/interactions`:
   ```text
   https://a1b2-34-56-78.ngrok-free.app/interactions
   ```
5. Click **Save Changes**.

> [!NOTE]
> When you click **Save Changes**, Discord immediately sends an Ed25519 signed `PING (Type 1)` request to verify your endpoint.
> If your server is running and `DISCORD_PUBLIC_KEY` in `.env` is correct, Discord will accept the URL instantly with a green checkmark!

---

## ⚡ Step 6: Register Slash Commands

Run the command registration script:

### Instant Registration to Test Guild (Recommended for Local Dev)
Global Discord commands can take up to 1 hour to propagate. By specifying your test Server (Guild) ID, commands are registered **instantly**:

```bash
# If DISCORD_GUILD_ID is in your .env:
python scripts/register_commands.py

# Or pass via CLI flag:
python scripts/register_commands.py --guild 987654321098765432
```

### Global Registration (For Production / All Servers)
```bash
python scripts/register_commands.py
```

### Available Slash Commands Registered:
- `/ask query:<your question>`: General triage to either or both agents (311, restaurant grades, NYPL archives).
- `/nypl query:<search term>`: Direct query to NYPL Expert Agent for digital collections, historical photos, maps, and branches.
- `/nycdata query:<search term>`: Direct query to NYC Open Data Specialist for 311 complaints, restaurant health inspections, and street tree census data.

---

## 🧪 Step 7: Running Automated Tests

Run the full automated test suite to ensure all cryptographic verification, endpoint handlers, and tool parsers function properly:

```bash
python -m unittest discover tests
```

Expected output:
```text
Ran 8 tests in 0.25s

OK
```

---

## 🔍 Troubleshooting & FAQs

### 1. Discord says "Endpoint verification failed"
- **Cause**: The `DISCORD_PUBLIC_KEY` in your `.env` does not match the **Public Key** in your Discord Application General Information page.
- **Fix**: Check that there are no extra spaces or quotes around `DISCORD_PUBLIC_KEY` in `.env`.
- Ensure your local uvicorn server and ngrok tunnel are both active and responding.

### 2. "The application did not respond" in Discord
- **Cause**: Discord requires an acknowledgment (`type: 5`) within **3.0 seconds**.
- **Fix**: The bot immediately returns `{"type": 5}` and uses background tasks to process the query. Ensure your network or proxy is not buffering the initial response.

### 3. Missing Gemini API Key Error
- **Message**: `Missing Gemini credentials. Please set GEMINI_API_KEY...`
- **Fix**: Get an API key from [Google AI Studio](https://aistudio.google.com/) and place it in `.env` as `GEMINI_API_KEY=AIzaSy...`. Restart Uvicorn so it reloads `.env`.

### 4. Discord Bot Token vs. Public Key vs. App ID
- **Application ID**: Numbers only (e.g. `133984719283749102`), found under **General Information**.
- **Public Key**: 64-character hex string, found under **General Information**.
- **Bot Token**: Base64-like secret string (e.g. `MTMzOT...`), found under **Bot** -> **Reset Token**.
