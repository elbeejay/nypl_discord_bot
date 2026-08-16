# Discord User Guide: NYC & NYPL Assistant 🗽🤖

Welcome to your AI assistant for **New York City Open Data** and the **New York Public Library (NYPL) Digital Collections**!

This guide explains how to interact with the bot in Discord using slash commands and example prompts.

---

## ⚡ Slash Commands

| Command | Purpose | Example Usage |
| :--- | :--- | :--- |
| **`/ask`** | **Universal Assistant**: Ask questions spanning city data, library history, or combined queries. | `/ask query: What are top 311 complaints near Bryant Park and what is the history of the Schwarzman building?` |
| **`/nypl`** | **Digital Archives & Branches**: Search public domain archive photos, vintage maps, prints, or find library branches. | `/nypl query: Vintage 1930s photographs of the Brooklyn Bridge` |
| **`/nycdata`** | **Civic & Municipal Data**: Query real-time 311 complaints, DOHMH restaurant health inspection grades, and street trees. | `/nycdata query: Health inspection grade for Joe's Pizza in Manhattan` |

---

## 💡 Example Queries to Try

### 1. 🚨 NYC 311 & Civic Data
* `/nycdata query: What are the most common noise complaints in Astoria, Queens?`
* `/nycdata query: Find recent illegal parking service requests in Bushwick`
* `/nycdata query: Heat and hot water complaints in the Bronx`

### 2. 🍕 Restaurant Health Inspection Grades
* `/nycdata query: Sanitation inspection grade and violations for Katz's Delicatessen`
* `/nycdata query: What grade did Peter Luger Steak House receive on its last inspection?`

### 3. 📸 NYPL Historical Archives & Photos
* `/nypl query: High resolution public domain photos of the Flatiron Building`
* `/nypl query: Historical 19th-century subway and transit maps of Manhattan`
* `/nypl query: Vintage photos of Central Park in winter`

### 4. 🏛️ NYPL Branch Locations & Research Centers
* `/nypl query: Where is the Schomburg Center for Research in Black Culture located?`
* `/nypl query: Find library branches near Grand Central Terminal`

### 5. 🧠 Multi-Domain Queries (Combined Knowledge)
* `/ask query: Tell me about the historic Stephen A. Schwarzman Building and find any recent 311 complaints around 42nd St & 5th Ave`

---

## ⏱️ How It Works in Discord

1. **Instant Acknowledgment**: When you hit Enter, you will see `Bot is thinking...` within milliseconds.
2. **Live Data & AI Synthesis**: Behind the scenes, the bot formulates database queries to NYC Open Data and NYPL digital archives, feeding the results to Google Gemini.
3. **Formatted Markdown**: Within 2–4 seconds, the bot replaces the placeholder with structured markdown, direct links to high-res archives, and formatted data tables.

---

## 🎯 Tips for Best Results

* **Specify Boroughs & Neighborhoods**: Adding `"in Crown Heights"` or `"in Staten Island"` helps narrow down 311 and restaurant queries accurately.
* **Exact Restaurant Names**: When checking health inspections, include the business name and borough (e.g. `"Carbone in Manhattan"`).
* **Historical Time Periods**: When searching NYPL archives, mention specific decades or eras (e.g. `"1920s Harlem"`, `"1970s Coney Island"`).
