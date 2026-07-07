# Phase 4 — Star Schema & Mart `🔲 Not Started`

> Transform raw data into Star Schema (Fact/Dim) and create Mart Views for analysis

**Status**: 🔲 Not Started
**Prerequisites**: Phase 3 completion (raw_data loaded in BigQuery)

---

## Overview

Transform raw_data into a Star Schema model inside BigQuery using BigQuery Standard SQL (ELT pattern, ADR-001). Create 2 Fact tables, 3 Dimension tables, and 3 Mart Views for performance, risk, and macro analysis. The Python transformer module (`src/transformers/star_schema.py`) orchestrates BigQuery SQL (CTAS) execution.

---

## Deliverables

| # | Module | Status | Type |
|---|---|---|---|
| 1 | `src/transformers/star_schema.py` | 🔲 | project-specific |
| 2 | `src/transformers/__init__.py` | 🔲 | project-specific |
| 3 | `sql/mart_views.sql` | 🔲 | project-specific |
| 4 | Fact table transformation verification | 🔲 | project-specific |
| 5 | Mart View query verification | 🔲 | project-specific |

---

## Module Details

### 1. star_schema.py

#### Purpose
Execute BigQuery Standard SQL to transform raw_data into Star Schema tables and manage Mart Views.

#### Implementation Spec
- **Pattern**: CTAS (`CREATE OR REPLACE TABLE AS SELECT`) for Fact tables, BigQuery Standard SQL execution via Python (`bigquery.Client`)
- **Dim tables**: Populated from raw data + seed data
- **Mart Views**: `CREATE OR REPLACE VIEW` (BigQuery-supported; `LAG`/`STDDEV`/`CORR` all available)

#### Key Functions
```python
def transform_to_star_schema(client: bigquery.Client) -> dict
def populate_dim_date(client: bigquery.Client, start_date: str, end_date: str) -> int
def populate_dim_symbol(client: bigquery.Client) -> int
def populate_dim_indicator(client: bigquery.Client) -> int
def create_fact_daily_price(client: bigquery.Client) -> int
def create_fact_economic_indicator(client: bigquery.Client) -> int
def create_mart_views(client: bigquery.Client) -> dict
```

### 2. Star Schema Tables

#### fact_daily_price
- **Source**: `raw_daily_price` JOIN `dim_date` + `dim_symbol`
- **Transform**: Normalize `UPPER(TRIM(symbol))` → dedup `QUALIFY ROW_NUMBER() OVER(PARTITION BY symbol,date ORDER BY collected_at DESC)=1` → obtain surrogate keys via **inner JOIN** to `dim_symbol`; `date_key = CAST(FORMAT_DATE('%Y%m%d', date) AS INT64)`. Because `dim_symbol` is now the approved roster (built from `raw_universe`), this inner JOIN **actually filters out** symbols outside the roster, nulls, and typos — the integrity filter genuinely works now.
- **Grain**: One row per (date, symbol)

#### fact_economic_indicator
- **Source**: `raw_economic_indicator` JOIN `dim_date` + `dim_indicator`
- **Transform**: Same pattern — normalize `UPPER(TRIM(indicator_code))` → dedup `QUALIFY ROW_NUMBER() OVER(PARTITION BY indicator_code,date ORDER BY collected_at DESC)=1` → map `indicator_code` → `indicator_key` via **inner JOIN** to `dim_indicator` (rows absent from dim excluded)
- **Grain**: One row per (date, indicator)

#### dim_date
- **Source**: `GENERATE_DATE_ARRAY('2020-01-01', CURRENT_DATE())` + `UNNEST` (BigQuery)
- **Key**: `date_key` = `CAST(FORMAT_DATE('%Y%m%d', d) AS INT64)` (YYYYMMDD integer)
- **Fields**: year, quarter, month, day_of_week, is_trading_day

#### dim_symbol
- **Source**: `raw_universe` (S&P 500 + Nasdaq-100 constituents, from ETF holdings IVV+QQQ) — **not** `raw_daily_price` distinct symbols. Building `dim_symbol` from the universe roster (not from raw prices) is the key: only then does the fact inner JOIN actually filter out symbols outside the roster.
- **Transform**: `WHERE ticker IS NOT NULL` → normalize `UPPER(TRIM(ticker))` → `DISTINCT` dedup (merges tickers listed in both indices) → `FARM_FINGERPRINT(ticker)` surrogate key
- **Key**: `symbol_key` = `FARM_FINGERPRINT(UPPER(TRIM(ticker)))` (deterministic INT64; BigQuery has no AUTOINCREMENT/sequence, so the same ticker yields the same key across Full Refresh runs)
- **Fields**: ticker, company_name, sector, market

#### dim_indicator
- **Source**: `config/symbols.yaml` `indicators` list (hand-managed seed — indicators are few and stable), **not** `raw_economic_indicator` distinct codes
- **Key**: `indicator_key` = `FARM_FINGERPRINT(UPPER(TRIM(indicator_code)))` (deterministic INT64; no AUTOINCREMENT in BigQuery)
- **Fields**: indicator_code, indicator_name, source, unit

### 3. Mart Views

#### mart_performance
- **Base**: `fact_daily_price` + `dim_symbol` + `dim_date`
- **Calculations**: `LAG()` for daily/weekly/monthly returns, cumulative return
- **Use case**: Stock performance comparison

#### mart_risk
- **Base**: `fact_daily_price` + `dim_symbol`
- **Calculations**: `STDDEV()` for volatility, max drawdown, beta
- **Use case**: Risk analysis dashboard

#### mart_macro
- **Base**: `fact_economic_indicator` + `fact_daily_price` + `dim_date`
- **Calculations**: `CORR()` for interest rate-stock correlation, indicator impact
- **Use case**: Macroeconomic analysis

---

## Design Decisions

| Decision | Choice | Reason |
|---|---|---|
| Transformation engine | BigQuery SQL (ELT) | Leverage BigQuery compute, clear separation from Python collection (ADR-001) |
| Fact table refresh | CTAS re-creation | Simple, consistent results each run |
| Dim date generation | Pre-generated range | Covers all possible dates, includes non-trading days for joins |
| Mart implementation | Views (not tables) | Always reflect latest Fact/Dim data, no refresh needed |

---

## Prerequisites & Dependencies

- Phase 3 completed (raw_data tables populated)
- BigQuery connection active
- `setup.sql` tables exist (Fact/Dim/Mart DDL) — though BigQuery CTAS (`CREATE OR REPLACE TABLE AS SELECT`) creates Fact/Dim tables on the fly, so predefined DDL is optional

---

## Development Notes

- Dimensions are rebuilt each run (Full Refresh): `dim_symbol`/`dim_indicator` reflect the current universe/seed — constituents removed from the index drop out — while `dim_date` only extends forward
- `dim_date.is_trading_day` can be simplified to weekday check for MVP (no holiday calendar)
- Mart Views are read-only — Power BI connects to these in Phase 5
- Test each Mart View with sample queries before connecting Power BI

---

## Change Log

| Date | Description |
|---|---|
| 2026-05-12 | Initial creation |
| 2026-07-06 | Aligned to BigQuery (FARM_FINGERPRINT surrogate keys, QUALIFY dedup, GENERATE_DATE_ARRAY dim_date, BigQuery Standard SQL / `bigquery.Client`) |
| 2026-07-06 | Dynamic universe: `dim_symbol` now sourced from `raw_universe` (S&P 500 + Nasdaq-100 constituents) instead of `raw_daily_price` distinct symbols, and `dim_indicator` from the `config/symbols.yaml` `indicators` seed — so the fact inner JOIN genuinely filters out-of-roster symbols, nulls, and typos |
| 2026-07-06 | Removed `sql/seed_dimensions.sql` — dims are populated from `raw_universe` / `config/symbols.yaml` `indicators` / date generation |

---
---

# Phase 4 — Star Schema & Mart `🔲 미시작`

> raw 데이터를 Star Schema(Fact/Dim)로 변환하고 분석용 Mart View 생성

**상태**: 🔲 미시작
**선행 조건**: Phase 3 완료 (BigQuery에 raw_data 적재 완료)

---

## 개요

BigQuery 내부에서 BigQuery Standard SQL로 raw_data를 Star Schema 모델로 변환한다 (ELT 패턴, ADR-001). Fact 테이블 2개, Dimension 테이블 3개, Mart View 3개를 생성하여 수익률, 리스크, 매크로 분석을 지원한다. Python transformer 모듈(`src/transformers/star_schema.py`)이 BigQuery SQL(CTAS) 실행을 오케스트레이션한다.

---

## 완료 예정 / 완료 항목

| # | 모듈 | 상태 | 타입 |
|---|---|---|---|
| 1 | `src/transformers/star_schema.py` | 🔲 | project-specific |
| 2 | `src/transformers/__init__.py` | 🔲 | project-specific |
| 3 | `sql/mart_views.sql` | 🔲 | project-specific |
| 4 | Fact 테이블 변환 검증 | 🔲 | project-specific |
| 5 | Mart View 쿼리 검증 | 🔲 | project-specific |

---

## 모듈 상세

### 1. star_schema.py

#### 목적
BigQuery Standard SQL을 실행하여 raw_data를 Star Schema 테이블로 변환하고 Mart View를 관리한다.

#### 구현 명세
- **패턴**: CTAS (`CREATE OR REPLACE TABLE AS SELECT`)로 Fact 테이블 생성, Python(`bigquery.Client`)에서 BigQuery Standard SQL 실행
- **Dim 테이블**: raw 데이터 + seed 데이터로 채움
- **Mart View**: `CREATE OR REPLACE VIEW` (BigQuery 지원; `LAG`/`STDDEV`/`CORR` 모두 사용 가능)

#### 핵심 함수
```python
def transform_to_star_schema(client: bigquery.Client) -> dict
def populate_dim_date(client: bigquery.Client, start_date: str, end_date: str) -> int
def populate_dim_symbol(client: bigquery.Client) -> int
def populate_dim_indicator(client: bigquery.Client) -> int
def create_fact_daily_price(client: bigquery.Client) -> int
def create_fact_economic_indicator(client: bigquery.Client) -> int
def create_mart_views(client: bigquery.Client) -> dict
```

### 2. Star Schema 테이블

#### fact_daily_price
- **소스**: `raw_daily_price` JOIN `dim_date` + `dim_symbol`
- **변환**: `UPPER(TRIM(symbol))` 정규화 → `QUALIFY ROW_NUMBER() OVER(PARTITION BY symbol,date ORDER BY collected_at DESC)=1` 중복 제거 → `dim_symbol`에 **inner JOIN**하여 대리키 획득; `date_key = CAST(FORMAT_DATE('%Y%m%d', date) AS INT64)`. `dim_symbol`이 이제 승인 명단(`raw_universe` 기반)이므로, 이 inner JOIN이 명단 밖 종목·null·오타를 **실제로 걸러냄** — 무결성 필터가 이제 진짜로 동작.
- **단위**: (날짜, 종목)당 1행

#### fact_economic_indicator
- **소스**: `raw_economic_indicator` JOIN `dim_date` + `dim_indicator`
- **변환**: 동일 패턴 — `UPPER(TRIM(indicator_code))` 정규화 → `QUALIFY ROW_NUMBER() OVER(PARTITION BY indicator_code,date ORDER BY collected_at DESC)=1` 중복 제거 → `dim_indicator`에 **inner JOIN**하여 `indicator_code` → `indicator_key` 매핑(dim에 없는 행 제외)
- **단위**: (날짜, 지표)당 1행

#### dim_date
- **소스**: `GENERATE_DATE_ARRAY('2020-01-01', CURRENT_DATE())` + `UNNEST` (BigQuery)
- **키**: `date_key` = `CAST(FORMAT_DATE('%Y%m%d', d) AS INT64)` (YYYYMMDD 정수)
- **필드**: year, quarter, month, day_of_week, is_trading_day

#### dim_symbol
- **소스**: `raw_universe` (S&P500+Nasdaq100 구성종목, ETF 보유종목 IVV+QQQ 기반) — `raw_daily_price` 고유 종목이 **아님**. `raw_daily_price`가 아니라 유니버스(명단)에서 생성하는 게 핵심 — 그래야 fact의 inner JOIN이 명단 밖 종목을 실제로 걸러냄.
- **처리**: `WHERE ticker IS NOT NULL` → `UPPER(TRIM)` 정규화 → `DISTINCT` 중복 제거(두 지수 중복 합침) → `FARM_FINGERPRINT(ticker)` 대리키 생성
- **키**: `symbol_key` = `FARM_FINGERPRINT(UPPER(TRIM(ticker)))` (결정적 INT64; BigQuery엔 AUTOINCREMENT/시퀀스 없음 → Full Refresh에도 동일 ticker는 동일 키)
- **필드**: ticker, company_name, sector, market

#### dim_indicator
- **소스**: `config/symbols.yaml`의 `indicators` 목록 (손으로 관리하는 seed — 지표는 적고 안정적), `raw_economic_indicator` 고유 코드 **아님**
- **키**: `indicator_key` = `FARM_FINGERPRINT(UPPER(TRIM(indicator_code)))` (결정적 INT64; BigQuery엔 AUTOINCREMENT 없음)
- **필드**: indicator_code, indicator_name, source, unit

### 3. Mart View

#### mart_performance
- **기반**: `fact_daily_price` + `dim_symbol` + `dim_date`
- **계산**: `LAG()`로 일간/주간/월간 수익률, 누적 수익률
- **용도**: 종목 성과 비교

#### mart_risk
- **기반**: `fact_daily_price` + `dim_symbol`
- **계산**: `STDDEV()`로 변동성, 최대 낙폭, 베타
- **용도**: 리스크 분석 대시보드

#### mart_macro
- **기반**: `fact_economic_indicator` + `fact_daily_price` + `dim_date`
- **계산**: `CORR()`로 금리-주가 상관관계, 경제지표 영향도
- **용도**: 매크로 경제 분석

---

## 설계 결정 사항

| 결정 | 선택 | 이유 |
|---|---|---|
| 변환 엔진 | BigQuery SQL (ELT) | BigQuery 컴퓨팅 활용, Python 수집과 역할 분리 명확 (ADR-001) |
| Fact 테이블 갱신 | CTAS 재생성 | 단순, 매 실행 일관된 결과 |
| Dim date 생성 | 사전 생성된 날짜 범위 | 모든 날짜 커버, 비거래일 포함하여 조인 가능 |
| Mart 구현 | View (테이블 아님) | 항상 최신 Fact/Dim 데이터 반영, 별도 갱신 불필요 |

---

## 선행 조건 및 의존성

- Phase 3 완료 (raw_data 테이블에 데이터 적재)
- BigQuery 연결 활성
- `setup.sql` 테이블 존재 (Fact/Dim/Mart DDL) — 단 BigQuery는 CTAS(`CREATE OR REPLACE TABLE AS SELECT`)가 Fact/Dim 테이블을 생성하므로 사전 DDL은 선택 사항

---

## 개발 시 주의사항

- Dimension은 매 실행 재생성(Full Refresh): `dim_symbol`/`dim_indicator`는 현재 유니버스/seed를 반영 — 지수에서 빠진 종목은 제외 — `dim_date`는 앞으로만 확장
- `dim_date.is_trading_day`는 MVP에서 평일 체크로 단순화 가능 (공휴일 캘린더 없음)
- Mart View는 읽기 전용 — Phase 5에서 Power BI가 연결
- Power BI 연결 전 샘플 쿼리로 각 Mart View 테스트

---

## 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-05-12 | 최초 작성 |
| 2026-07-06 | BigQuery 기준 정비 (FARM_FINGERPRINT 대리키, QUALIFY 중복 제거, GENERATE_DATE_ARRAY dim_date, BigQuery Standard SQL / `bigquery.Client`) |
| 2026-07-06 | 동적 유니버스 반영: `dim_symbol` 소스를 `raw_daily_price` 고유 종목 → `raw_universe`(S&P500+Nasdaq100 구성종목)로, `dim_indicator` 소스를 `config/symbols.yaml`의 `indicators` seed로 변경 — fact의 inner JOIN이 명단 밖 종목·null·오타를 실제로 걸러냄 |
| 2026-07-06 | `sql/seed_dimensions.sql` 제거 — dim은 `raw_universe`/`config/symbols.yaml` `indicators`/날짜 생성으로 채워짐 |
