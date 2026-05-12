# Phase 4 — Star Schema & Mart `🔲 Not Started`

> Transform raw data into Star Schema (Fact/Dim) and create Mart Views for analysis

**Status**: 🔲 Not Started
**Prerequisites**: Phase 3 completion (raw_data loaded in Snowflake)

---

## Overview

Transform raw_data into a Star Schema model inside Snowflake using SQL (ELT pattern, ADR-001). Create 2 Fact tables, 3 Dimension tables, and 3 Mart Views for performance, risk, and macro analysis. The Python transformer module orchestrates SQL execution.

---

## Deliverables

| # | Module | Status | Type |
|---|---|---|---|
| 1 | `src/transformers/star_schema.py` | 🔲 | project-specific |
| 2 | `src/transformers/__init__.py` | 🔲 | project-specific |
| 3 | `sql/mart_views.sql` | 🔲 | project-specific |
| 4 | `sql/seed_dimensions.sql` | 🔲 | project-specific |
| 5 | Fact table transformation verification | 🔲 | project-specific |
| 6 | Mart View query verification | 🔲 | project-specific |

---

## Module Details

### 1. star_schema.py

#### Purpose
Execute Snowflake SQL to transform raw_data into Star Schema tables and manage Mart Views.

#### Implementation Spec
- **Pattern**: CTAS (CREATE TABLE AS SELECT) for Fact tables, Snowflake SQL execution via Python
- **Dim tables**: Populated from raw data + seed data
- **Mart Views**: CREATE OR REPLACE VIEW

#### Key Functions
```python
def transform_to_star_schema(conn: Connection) -> dict
def populate_dim_date(conn: Connection, start_date: str, end_date: str) -> int
def populate_dim_symbol(conn: Connection) -> int
def populate_dim_indicator(conn: Connection) -> int
def create_fact_daily_price(conn: Connection) -> int
def create_fact_economic_indicator(conn: Connection) -> int
def create_mart_views(conn: Connection) -> dict
```

### 2. Star Schema Tables

#### fact_daily_price
- **Source**: `raw_daily_price` JOIN `dim_date` + `dim_symbol`
- **Transform**: Map natural keys to surrogate keys (date_key, symbol_key)
- **Grain**: One row per (date, symbol)

#### fact_economic_indicator
- **Source**: `raw_economic_indicator` JOIN `dim_date` + `dim_indicator`
- **Transform**: Map natural keys to surrogate keys (date_key, indicator_key)
- **Grain**: One row per (date, indicator)

#### dim_date
- **Source**: Generated date range (e.g., 2020-01-01 to today)
- **Key**: `date_key` = YYYYMMDD integer
- **Fields**: year, quarter, month, day_of_week, is_trading_day

#### dim_symbol
- **Source**: `raw_daily_price` distinct symbols + `config/symbols.yaml` metadata
- **Key**: `symbol_key` auto-increment
- **Fields**: ticker, company_name, sector, market

#### dim_indicator
- **Source**: `raw_economic_indicator` distinct codes + `sql/seed_dimensions.sql` metadata
- **Key**: `indicator_key` auto-increment
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
| Transformation engine | Snowflake SQL (ELT) | Leverage Snowflake compute, clear separation from Python collection (ADR-001) |
| Fact table refresh | CTAS re-creation | Simple, consistent results each run |
| Dim date generation | Pre-generated range | Covers all possible dates, includes non-trading days for joins |
| Mart implementation | Views (not tables) | Always reflect latest Fact/Dim data, no refresh needed |

---

## Prerequisites & Dependencies

- Phase 3 completed (raw_data tables populated)
- Snowflake connection active
- `setup.sql` tables exist (Fact/Dim/Mart DDL)
- `sql/seed_dimensions.sql` prepared (indicator metadata)

---

## Development Notes

- Dimension tables are cumulative — new symbols/indicators are added, never deleted
- `dim_date.is_trading_day` can be simplified to weekday check for MVP (no holiday calendar)
- Mart Views are read-only — Power BI connects to these in Phase 5
- Test each Mart View with sample queries before connecting Power BI

---

## Change Log

| Date | Description |
|---|---|
| 2026-05-12 | Initial creation |

---
---

# Phase 4 — Star Schema & Mart `🔲 미시작`

> raw 데이터를 Star Schema(Fact/Dim)로 변환하고 분석용 Mart View 생성

**상태**: 🔲 미시작
**선행 조건**: Phase 3 완료 (Snowflake에 raw_data 적재 완료)

---

## 개요

Snowflake 내부에서 SQL로 raw_data를 Star Schema 모델로 변환한다 (ELT 패턴, ADR-001). Fact 테이블 2개, Dimension 테이블 3개, Mart View 3개를 생성하여 수익률, 리스크, 매크로 분석을 지원한다. Python transformer 모듈이 SQL 실행을 오케스트레이션한다.

---

## 완료 예정 / 완료 항목

| # | 모듈 | 상태 | 타입 |
|---|---|---|---|
| 1 | `src/transformers/star_schema.py` | 🔲 | project-specific |
| 2 | `src/transformers/__init__.py` | 🔲 | project-specific |
| 3 | `sql/mart_views.sql` | 🔲 | project-specific |
| 4 | `sql/seed_dimensions.sql` | 🔲 | project-specific |
| 5 | Fact 테이블 변환 검증 | 🔲 | project-specific |
| 6 | Mart View 쿼리 검증 | 🔲 | project-specific |

---

## 모듈 상세

### 1. star_schema.py

#### 목적
Snowflake SQL을 실행하여 raw_data를 Star Schema 테이블로 변환하고 Mart View를 관리한다.

#### 구현 명세
- **패턴**: CTAS (CREATE TABLE AS SELECT)로 Fact 테이블 생성, Python에서 Snowflake SQL 실행
- **Dim 테이블**: raw 데이터 + seed 데이터로 채움
- **Mart View**: CREATE OR REPLACE VIEW

#### 핵심 함수
```python
def transform_to_star_schema(conn: Connection) -> dict
def populate_dim_date(conn: Connection, start_date: str, end_date: str) -> int
def populate_dim_symbol(conn: Connection) -> int
def populate_dim_indicator(conn: Connection) -> int
def create_fact_daily_price(conn: Connection) -> int
def create_fact_economic_indicator(conn: Connection) -> int
def create_mart_views(conn: Connection) -> dict
```

### 2. Star Schema 테이블

#### fact_daily_price
- **소스**: `raw_daily_price` JOIN `dim_date` + `dim_symbol`
- **변환**: 자연키를 대리키로 매핑 (date_key, symbol_key)
- **단위**: (날짜, 종목)당 1행

#### fact_economic_indicator
- **소스**: `raw_economic_indicator` JOIN `dim_date` + `dim_indicator`
- **변환**: 자연키를 대리키로 매핑 (date_key, indicator_key)
- **단위**: (날짜, 지표)당 1행

#### dim_date
- **소스**: 생성된 날짜 범위 (예: 2020-01-01 ~ 오늘)
- **키**: `date_key` = YYYYMMDD 정수
- **필드**: year, quarter, month, day_of_week, is_trading_day

#### dim_symbol
- **소스**: `raw_daily_price` 고유 종목 + `config/symbols.yaml` 메타데이터
- **키**: `symbol_key` 자동증가
- **필드**: ticker, company_name, sector, market

#### dim_indicator
- **소스**: `raw_economic_indicator` 고유 코드 + `sql/seed_dimensions.sql` 메타데이터
- **키**: `indicator_key` 자동증가
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
| 변환 엔진 | Snowflake SQL (ELT) | Snowflake 컴퓨팅 파워 활용, Python 수집과 역할 분리 명확 (ADR-001) |
| Fact 테이블 갱신 | CTAS 재생성 | 단순, 매 실행 일관된 결과 |
| Dim date 생성 | 사전 생성된 날짜 범위 | 모든 날짜 커버, 비거래일 포함하여 조인 가능 |
| Mart 구현 | View (테이블 아님) | 항상 최신 Fact/Dim 데이터 반영, 별도 갱신 불필요 |

---

## 선행 조건 및 의존성

- Phase 3 완료 (raw_data 테이블에 데이터 적재)
- Snowflake 연결 활성
- `setup.sql` 테이블 존재 (Fact/Dim/Mart DDL)
- `sql/seed_dimensions.sql` 준비 (지표 메타데이터)

---

## 개발 시 주의사항

- Dimension 테이블은 누적 — 새 종목/지표 추가만, 삭제 없음
- `dim_date.is_trading_day`는 MVP에서 평일 체크로 단순화 가능 (공휴일 캘린더 없음)
- Mart View는 읽기 전용 — Phase 5에서 Power BI가 연결
- Power BI 연결 전 샘플 쿼리로 각 Mart View 테스트

---

## 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-05-12 | 최초 작성 |
