# Discord Bot Setup & Developer Portal Guide 🤖

This guide provides a comprehensive walkthrough for creating, configuring, and inviting your **NYC & NYPL Discord Assistant** using the [Discord Developer Portal](https://discord.com/developers/applications).

---

## 🎯 High-Level Overview

Unlike traditional Discord bots that maintain a permanent WebSocket connection (Gateway), this bot uses **Discord's HTTP Interaction Webhooks**:
- **Cloud-Native & Serverless**: No long-running background daemon needed.
- **Fast**: Discord delivers incoming slash commands directly to your HTTPS endpoint.
- **Reliable**: Reboots, scaling, and cold starts on Cloud Run happen transparently.

---

## 🛠️ Step 1: Create a Discord Application

1. Navigate to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Log in with your Discord account.
3. Click the **New Application** button (top right).
4. Enter a name (e.g., `NYC & NYPL Assistant`) and accept the Developer Terms of Service.
5. Click **Create**.

---

## 🔑 Step 2: Retrieve App ID & Public Key

On the **General Information** page of your application:

1. **Application ID**:
   - Locate **Application ID** and click **Copy**.
   - Paste into `.env` as `DISCORD_APP_ID=...`.
2. **Public Key**:
   - Locate **Public Key** (a 64-character hex string) and click **Copy**.
   - Paste into `.env` as `DISCORD_PUBLIC_KEY=...`.
   *(This key is used to cryptographically verify that incoming HTTP requests truly originated from Discord via Ed25519).*
3. *(Optional)* Upload an App Icon (e.g., a photo of the NYPL Lion or NYC Skyline).
4. *(Optional)* Add a description: *"Agentic assistant for NYC Open Data (311, restaurant inspections) and NYPL Digital Collections."*

---

## 🤖 Step 3: Create Bot User & Retrieve Bot Token

1. In the left navigation sidebar, click on **Bot**.
2. Click **Add Bot** (or verify the default bot user is created).
3. Under **Token**, click **Reset Token** (confirm with your 2FA if prompted).
4. Click **Copy** to copy the token.
5. Paste into `.env` as `DISCORD_BOT_TOKEN=...`.

> [!CAUTION]
> Treat your **Bot Token** like a root password. Never commit your `.env` file or paste this token in public repositories or Discord chats.

### Bot Settings:
- **Public Bot**: Enabled (allows others to add the bot, or disable if private to your server).
- **Requires OAuth2 Code Grant**: Disabled (uncheck).
- **Gateway Privileged Intents**: *(None needed!)* Because this bot uses HTTP Interactions, you do **not** need to enable Presence Intent, Server Members Intent, or Message Content Intent.

---

## 🔗 Step 4: Generate Bot Invite Link (OAuth2)

1. In the left navigation sidebar, click **OAuth2** -> **URL Generator**.
2. Under **Scopes**, select:
   - `bot`
   - `applications.commands` (Critical for slash commands!)
3. Under **Bot Permissions**, select:
   - **Send Messages**
   - **Embed Links**
   - **Attach Files**
   - **Read Message History**
   - **Use External Emojis**
4. Copy the generated URL at the bottom of the page (e.g. `https://discord.com/oauth2/authorize?client_id=YOUR_APP_ID&permissions=...&scope=bot%20applications.commands`).
5. Paste the URL into your browser, select your Discord server, and click **Authorize**.

---

## ⚡ Step 5: Register Slash Commands

Discord requires you to register your slash command schemas so that Discord's UI presents the commands (with autocomplete and descriptions) to users.

### Method A: Fast Guild-Specific Registration (For Testing)
When developing or testing, registering commands to a specific Discord server is **instant**:

1. In Discord, enable **Developer Mode** (User Settings -> Advanced -> Developer Mode -> On).
2. Right-click your Discord server icon in the left server bar and click **Copy Server ID**.
3. Run the registration script:
   ```bash
   python scripts/register_commands.py --guild YOUR_SERVER_ID
   ```
4. Check your Discord server: type `/` in any channel, and `/ask`, `/nypl`, and `/nycdata` will appear immediately!

### Method B: Global Registration (For Production)
Global commands are available in all servers where the bot is installed, but Discord caches global commands for up to 1 hour:

```bash
python scripts/register_commands.py
```

---

## 🌐 Step 6: Configure Interactions Endpoint URL

Once your backend is accessible on the public Internet (via **ngrok** locally or **Cloud Run** in production):

1. Open the [Discord Developer Portal](https://discord.com/developers/applications).
2. Select your Application -> **General Information**.
3. In the **Interactions Endpoint URL** field, enter your full HTTPS URL ending with `/interactions`:
   - **Local Testing**: `https://YOUR_NGROK_SUBDOMAIN.ngrok-free.app/interactions`
   - **Production (Cloud Run)**: `https://YOUR-SERVICE-NAME-xyz.a.run.app/interactions`
4. Click **Save Changes**.

### What happens under the hood?
Discord immediately sends an HTTP `POST` with header `X-Signature-Ed25519` and body `{"type": 1}`.
Our FastAPI app validates the signature using your `DISCORD_PUBLIC_KEY` and responds with `{"type": 1}`.
If the response is valid, Discord saves the endpoint URL with a green banner.

---

## 📋 Summary of Registered Commands

| Command | Option | Description |
| :--- | :--- | :--- |
| `/ask` | `query` *(string)* | General query routed dynamically by the Gateway Orchestrator (e.g. *"Tell me about the Schwarzman building and 311 noise complaints nearby"*). |
| `/nypl` | `query` *(string)* | Search NYPL Digital Collections archives, photographs, public domain manuscripts, or branch locations. |
| `/nycdata` | `query` *(string)* | Query NYC Open Data (311 complaints, restaurant health inspection grades, 2015 street tree census). |
