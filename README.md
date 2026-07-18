#  BiasSentinel — Global Media Bias Analyzer

**A quantitative analytics platform for identifying and visualizing systemic bias in international news streams, built on GDELT-style event data.**

🔗 **Live app:** [global-media-bias-analyzer.streamlit.app](https://global-media-bias-analyzer-fbjmdskfcmwj52sucdugs2.streamlit.app/)

---

## Overview

BiasSentinel ingests large-scale global news event data (in the schema popularized by the [GDELT Project](https://www.gdeltproject.org/)) and surfaces how different outlets frame coverage of a given country or region. For any target geography, it aggregates sentiment scores by source, flags outlets as showing systemic negative / positive / neutral coverage, and lets you compare bias signals across two regions side by side.

The dashboard is themed as a "signals intelligence" console — dark UI, monospace type, red/cream accents — and is built entirely in Streamlit with a PostgreSQL backend (Neon serverless Postgres).

## Features

- **Regional Dashboard** — Enter or "spin" a target country and get:
  - Total articles, average sentiment, sources monitored, and most extreme outlet at a glance
  - A ranked media bias table (channel, systemic positive/negative/neutral label, avg score, article count)
  - Sentiment distribution histogram + per-outlet bias bar chart
  - A feed of recent "signal intercepts" with direct links to source articles
- **Compare Regions** — Side-by-side average sentiment for two regions, with a delta readout and grouped bar chart
- **Bias Reporting** — Flag a channel as biased; logged to the database
- **Bureau Audit** — One-click audit log entry for the current session's target
- **Auto-seeding** — On first run, automatically loads `data.csv` into Postgres if the target table is empty

## Tech Stack

| Layer | Tech |
|---|---|
| Frontend / App | [Streamlit](https://streamlit.io/) |
| Data processing | pandas |
| Visualization | Plotly (Express + Graph Objects) |
| Database | PostgreSQL ([Neon](https://neon.tech/) serverless, in production) |
| DB access | psycopg2, SQLAlchemy |
| Data source | GDELT-style event records (`event_id`, `event_date`, `actor_name`, `event_code`, `sentiment_score`, `location_name`, `source_url`) |

## Project Structure

```
.
├── app_deploy.py   # Main deployed app (BiasSentinel v2 UI) — reads DB creds from st.secrets
├── sentinel_app.py # Earlier local-only version (hardcoded localhost DB connection)
├── fix_db.py       # One-off script to seed/replace the `news_signals` table from data.csv
├── data.csv        # Raw GDELT-style event dataset (~120K rows)
└── requirements.txt
```

## Getting Started

### 1. Clone and install dependencies

```bash
git clone https://github.com/jasminekaur7/global-media-bias-analyzer.git
cd global-media-bias-analyzer
pip install -r requirements.txt
```

### 2. Set up a PostgreSQL database

Provision a Postgres instance (e.g. [Neon](https://neon.tech/) free tier, or local Postgres) and create a `news_signals` table with columns matching `data.csv`: `actor_name`, `sentiment_score`, `source_url`, `location_name`. You'll also want a `bias_reports` table with a `report_reason` column for the flagging/audit features.

### 3. Configure secrets

**Never commit database credentials.** For local development, create `.streamlit/secrets.toml`:

```toml
DATABASE_URL = "postgresql://<user>:<password>@<host>/<db>?sslmode=require"
```

For Streamlit Community Cloud, add `DATABASE_URL` under your app's **Settings → Secrets**.

### 4. Seed the database

```bash
python fix_db.py
```

>  Before running, update `fix_db.py` to read its connection string from an environment variable / `secrets.toml` instead of a hardcoded value.

Alternatively, just run the app — `app_deploy.py` will auto-seed `news_signals` from `data.csv` on first launch if the table is empty.

### 5. Run the app

```bash
streamlit run app_deploy.py
```

## Data

The dataset follows the [GDELT Event](https://www.gdeltproject.org/data.html#documentation) schema convention — each row represents a coded global event with an associated actor, location, source article URL, and a tone/sentiment score. Sentiment thresholds used for labeling:

- `score < -4` → **Systemic Negative**
- `score > 4` → **Systemic Positive**
- otherwise → **Neutral**

## Roadmap / Known Issues

- [ ] Move all DB credentials out of source files into environment variables
- [ ] Reconcile `sentinel_app.py` (local Postgres) and `app_deploy.py` (cloud Postgres) into a single configurable entry point
- [ ] Add automated tests for the sentiment aggregation logic
- [ ] Persist bias reports/audits to a dedicated analytics view

