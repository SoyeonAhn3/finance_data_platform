🌐 [한국어](./README_ko.md) | [English](./README.md)

# Finance Data Platform

> End-to-end financial data pipeline: collect market data via APIs, model in BigQuery Star Schema, and visualize KPIs in Power BI

---

## Overview

A learning-oriented data engineering project that builds a complete financial analytics pipeline from scratch. Collects US stock prices and economic indicators from free APIs, loads them into BigQuery, transforms into a Star Schema model, and delivers interactive dashboards through Power BI. A v2 milestone adds natural language querying via Text-to-SQL AI.

---

## Table of Contents

- [How It Works](#how-it-works)
- [Data Universe](#data-universe)
- [Technology Stack](#technology-stack)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Current Status](#current-status)
- [AI Components (v2)](#ai-components-v2)
- [Limitations](#limitations)
- [Future Plans](#future-plans)

---

## How It Works

```
  Universe Fetch           ← ETF holdings (IVV/QQQ) → S&P 500 + Nasdaq-100 constituents
        ↓
[yfinance / FRED API]
        ↓
  Python Collectors        ← Collect OHLCV + economic indicators
        ↓
  Data Validator           ← Check missing values, outliers, duplicates
        ↓
  BigQuery raw dataset     ← Full Refresh (WRITE_TRUNCATE load job)
        ↓
  Star Schema (SQL)        ← Fact 2 + Dim 3 tables (ELT pattern)
        ↓
  Mart Views               ← Performance / Risk / Macro analysis
        ↓
  Power BI Dashboard       ← KPI charts with date & ticker filters
```

---

## Data Universe

The analysis universe is the **S&P 500 + Nasdaq-100** constituents. Rather than hand-listing tickers, the constituent list is **fetched from ETF holdings on every run**, so index additions, removals, and delistings are reflected automatically.

| Index | ETF | Provider | Source of truth |
|---|---|---|---|
| S&P 500 | IVV | BlackRock (iShares) | Fund manager's daily-published holdings |
| Nasdaq-100 | QQQ | Invesco | Same |

- **Fund holdings over Wikipedia** — authoritative, free, no API key required, GICS sector included.
- **Automatic add/drop & delisting** — every run re-fetches constituents, so a name that leaves an index falls out of `dim_symbol` (and therefore the fact tables) on the next run, while newly added names are included automatically — no manual ticker toggling.
- **Cache fallback** — if a fetch fails, `raw_universe` keeps the last successful list (no truncate); index membership changes only quarterly, so a one-day-old cache is safe.
- **Scale** — ~510–530 unique symbols across both indices (heavy overlap) → ~650K rows in `fact_daily_price` over five years, comfortably within the BigQuery free tier.

`config/symbols.yaml` therefore does **not** list individual stocks — it holds only the universe source, FRED indicators, and settings:

```yaml
universe:
  sp500:     { enabled: true, source: etf_holdings, etf: IVV }
  nasdaq100: { enabled: true, source: etf_holdings, etf: QQQ }
  include_extra: []      # tickers to force-include (not in the index)
  exclude:       []      # tickers to force-exclude (escape hatch)

indicators:              # FRED indicators — hand-listed (few & stable) → dim_indicator seed
  - { code: FEDFUNDS, name: Federal Funds Rate,   unit: "%",   source: FRED }
  - { code: CPIAUCSL, name: Consumer Price Index, unit: index, source: FRED }

settings:
  date_range: { start: "2020-01-01" }
```

---

## Technology Stack

| Technology | Role | Why |
|---|---|---|
| Python 3.x | Data collection & orchestration | Rich financial data libraries (yfinance, fredapi), accessible for learning |
| ETF holdings (IVV/QQQ) | Index constituents (S&P 500 + Nasdaq-100) | Fund-manager-published daily holdings — authoritative, free, no API key; auto-reflects index add/drop & delistings |
| yfinance | US stock OHLCV data | Free, no API key required, unofficial but widely used |
| FRED API | Economic indicators (rates, CPI) | Official Federal Reserve data, free with API key |
| Google BigQuery | Serverless cloud data warehouse | Industry standard, permanent free tier, native Star Schema support |
| Star Schema | Data modeling pattern | Optimized for analytics, best practice for BI workloads |
| Power BI Desktop | Dashboard visualization | Free desktop version, native BigQuery connector |
| python-dotenv | Configuration management | Simple .env-based secret management |
| GitHub Actions | Pipeline scheduling (cron) | Free CI runner with native cron scheduling, no extra infrastructure |

---

## Quick Start

### Prerequisites

- Python 3.x
- Power BI Desktop
- GCP project with BigQuery enabled + service account key
- FRED API key ([fred.stlouisfed.org](https://fred.stlouisfed.org))

### Installation

```bash
git clone https://github.com/SoyeonAhn3/finance_data_platform.git
cd finance_data_platform
pip install -r requirements.txt
```

### Environment Setup

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

```
GCP_PROJECT_ID=your_gcp_project_id
BQ_DATASET=finance_db
BQ_LOCATION=US
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json
FRED_API_KEY=your_fred_key
```

### BigQuery Setup

Run the schema initialization script in BigQuery:

```sql
-- Execute sql/setup.sql via the bq CLI or the google-cloud-bigquery Python client
```

### Run Pipeline

```bash
python src/main.py
```

---

## Project Structure

```
finance_data_platform/
├── src/
│   ├── collectors/              # API data collection modules
│   │   ├── universe_collector.py
│   │   ├── yfinance_collector.py
│   │   └── fred_collector.py
│   ├── validators/              # Data quality checks
│   │   └── quality_checker.py
│   ├── loaders/                 # BigQuery data loading
│   │   └── bigquery_loader.py
│   ├── transformers/            # Star Schema transformation
│   │   └── star_schema.py
│   ├── utils/                   # Config & logging utilities
│   │   ├── config.py
│   │   └── logger.py
│   └── main.py                  # Pipeline entry point
├── sql/
│   ├── setup.sql                # BigQuery schema initialization
│   └── mart_views.sql           # Mart View definitions
├── config/
│   └── symbols.yaml             # Universe source + FRED indicators + settings
├── Phase/                       # Development phase documentation
├── docs/
│   └── data_dictionary.md       # Table/column definitions
├── pre-requirement/
│   └── finance_data_platform_kickoff.md
├── .github/
│   └── workflows/
│       └── pipeline.yml         # GitHub Actions scheduled pipeline (cron)
├── .env.example
├── .gitignore
└── requirements.txt
```

---

## Current Status

| Phase | Status | Deliverable |
|---|---|---|
| Phase 1 — Project Setup | 🔲 Not Started | Environment config, BigQuery schema init, utility modules |
| Phase 2 — Data Collection | 🔲 Not Started | yfinance + FRED API collection modules |
| Phase 3 — Data Loading & Validation | 🔲 Not Started | BigQuery loader + quality checker |
| Phase 4 — Star Schema & Mart | 🔲 Not Started | Fact/Dim tables + 3 Mart Views |
| Phase 5 — Power BI Dashboard | 🔲 Not Started | KPI charts with filters |

---

## AI Components (v2)

> Planned for v2 — not included in MVP

| Feature | Input | Output | Model |
|---|---|---|---|
| Text-to-SQL | Natural language question (Korean/English) | BigQuery Standard SQL query | Claude Haiku / Sonnet |
| Result Interpretation | SQL query + results | Korean language explanation | Claude Haiku / Sonnet |

- SELECT queries only (DML/DDL blocked)
- Monthly budget cap: $10
- Model configurable via `.env` (`AI_MODEL` variable)

---

## Limitations

- **Learning project** — designed for skill development, not production use
- **Free tier constraints** — BigQuery free-tier quotas, API rate limits
- **Survivorship bias** — analysis uses current index constituents only; historically dropped/delisted names are excluded, which can flatter returns
- **Basic scheduling** — cron via GitHub Actions, no dedicated orchestrator (Airflow/Prefect)
- **No incremental loading** — Full Refresh on every run
- **No tests** — unit tests planned but not yet implemented
- **Single user** — no authentication or multi-user support

---

## Future Plans

- [ ] **v2: Text-to-SQL AI** — Natural language querying with Claude API
- [ ] **v2: Alpha Vantage** — Technical indicators (RSI, MACD)
- [ ] **v2: KRX data** — Korean stock market integration
- [ ] Unit test coverage for validators and transformers
- [ ] Incremental loading strategy for large datasets

---

<p align="center">Made with AI-assisted development</p>
