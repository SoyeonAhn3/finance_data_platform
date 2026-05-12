🌐 [한국어](./README_ko.md) | [English](./README.md)

# Finance Data Platform

> End-to-end financial data pipeline: collect market data via APIs, model in Snowflake Star Schema, and visualize KPIs in Power BI

---

## Overview

A learning-oriented data engineering project that builds a complete financial analytics pipeline from scratch. Collects US stock prices and economic indicators from free APIs, loads them into Snowflake, transforms into a Star Schema model, and delivers interactive dashboards through Power BI. A v2 milestone adds natural language querying via Text-to-SQL AI.

---

## Table of Contents

- [How It Works](#how-it-works)
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
[yfinance / FRED API]
        ↓
  Python Collectors        ← Collect OHLCV + economic indicators
        ↓
  Data Validator           ← Check missing values, outliers, duplicates
        ↓
  Snowflake raw_data       ← Full Refresh load (TRUNCATE + INSERT)
        ↓
  Star Schema (SQL)        ← Fact 2 + Dim 3 tables (ELT pattern)
        ↓
  Mart Views               ← Performance / Risk / Macro analysis
        ↓
  Power BI Dashboard       ← KPI charts with date & ticker filters
```

---

## Technology Stack

| Technology | Role | Why |
|---|---|---|
| Python 3.x | Data collection & orchestration | Rich financial data libraries (yfinance, fredapi), accessible for learning |
| yfinance | US stock OHLCV data | Free, no API key required, unofficial but widely used |
| FRED API | Economic indicators (rates, CPI) | Official Federal Reserve data, free with API key |
| Snowflake | Cloud data warehouse | Industry standard, free trial available, native Star Schema support |
| Star Schema | Data modeling pattern | Optimized for analytics, best practice for BI workloads |
| Power BI Desktop | Dashboard visualization | Free desktop version, native Snowflake connector |
| python-dotenv | Configuration management | Simple .env-based secret management |

---

## Quick Start

### Prerequisites

- Python 3.x
- Power BI Desktop
- Snowflake free trial account
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
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_user
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_DATABASE=FINANCE_DB
SNOWFLAKE_WAREHOUSE=XS_WH
SNOWFLAKE_SCHEMA=RAW_DATA
FRED_API_KEY=your_fred_key
```

### Snowflake Setup

Run the schema initialization script in Snowflake:

```sql
-- Execute sql/setup.sql in Snowflake UI or via Python connector
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
│   │   ├── yfinance_collector.py
│   │   └── fred_collector.py
│   ├── validators/              # Data quality checks
│   │   └── quality_checker.py
│   ├── loaders/                 # Snowflake data loading
│   │   └── snowflake_loader.py
│   ├── transformers/            # Star Schema transformation
│   │   └── star_schema.py
│   ├── utils/                   # Config & logging utilities
│   │   ├── config.py
│   │   └── logger.py
│   └── main.py                  # Pipeline entry point
├── sql/
│   ├── setup.sql                # Snowflake schema initialization
│   ├── mart_views.sql           # Mart View definitions
│   └── seed_dimensions.sql      # Dimension seed data
├── config/
│   └── symbols.yaml             # Ticker & indicator lists
├── Phase/                       # Development phase documentation
├── docs/
│   └── data_dictionary.md       # Table/column definitions
├── pre-requirement/
│   └── finance_data_platform_kickoff.md
├── .env.example
├── .gitignore
└── requirements.txt
```

---

## Current Status

| Phase | Status | Deliverable |
|---|---|---|
| Phase 1 — Project Setup | 🔲 Not Started | Environment config, Snowflake schema init, utility modules |
| Phase 2 — Data Collection | 🔲 Not Started | yfinance + FRED API collection modules |
| Phase 3 — Data Loading & Validation | 🔲 Not Started | Snowflake loader + quality checker |
| Phase 4 — Star Schema & Mart | 🔲 Not Started | Fact/Dim tables + 3 Mart Views |
| Phase 5 — Power BI Dashboard | 🔲 Not Started | KPI charts with filters |

---

## AI Components (v2)

> Planned for v2 — not included in MVP

| Feature | Input | Output | Model |
|---|---|---|---|
| Text-to-SQL | Natural language question (Korean/English) | Snowflake SQL query | Claude Haiku / Sonnet |
| Result Interpretation | SQL query + results | Korean language explanation | Claude Haiku / Sonnet |

- SELECT queries only (DML/DDL blocked)
- Monthly budget cap: $10
- Model configurable via `.env` (`AI_MODEL` variable)

---

## Limitations

- **Learning project** — designed for skill development, not production use
- **Free tier constraints** — Snowflake trial credits, API rate limits
- **No scheduling** — manual batch execution (no Airflow/Prefect)
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
