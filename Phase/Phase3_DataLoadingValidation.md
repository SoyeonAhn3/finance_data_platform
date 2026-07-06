# Phase 3 — Data Loading & Validation `🔲 Not Started`

> Load collected data into BigQuery raw_data and validate data quality

**Status**: 🔲 Not Started
**Prerequisites**: Phase 2 completion (collectors working, sample data collected)

---

## Overview

Implement the BigQuery data loader (Full Refresh pattern) and data quality validator. The loader replaces raw data in BigQuery using a WRITE_TRUNCATE load job (write_disposition=WRITE_TRUNCATE), clearing existing data and loading the entire DataFrame — including `raw_universe` (the dynamic S&P 500 + Nasdaq-100 membership list), except that a failed universe collection keeps the existing `raw_universe` as a cache fallback. The validator checks for missing values, outliers, duplicates, and completeness before loading, logging warnings without blocking the pipeline.

---

## Deliverables

| # | Module | Status | Type |
|---|---|---|---|
| 1 | `src/loaders/bigquery_loader.py` | 🔲 | project-specific |
| 2 | `src/loaders/__init__.py` | 🔲 | project-specific |
| 3 | `src/validators/quality_checker.py` | 🔲 | project-specific |
| 4 | `src/validators/__init__.py` | 🔲 | project-specific |
| 5 | Record count verification (NFR-008) | 🔲 | project-specific |
| 6 | Quality log to BigQuery (`data_quality_log`) | 🔲 | project-specific |
| 7 | Execution log to BigQuery (`pipeline_execution_log`) | 🔲 | project-specific |

---

## Module Details

### 1. bigquery_loader.py

#### Purpose
Load DataFrames into BigQuery `raw_data` schema using Full Refresh (WRITE_TRUNCATE load job) pattern (ADR-003).

#### Implementation Spec
- **Input**: pandas DataFrame, target table name
- **Output**: Load result (success/failure, record count)
- **Pattern**: WRITE_TRUNCATE load job (write_disposition=WRITE_TRUNCATE) — clears existing data and replaces it with the entire DataFrame; row-by-row INSERT is a BigQuery anti-pattern
- **Target tables**: `raw_universe`, `raw_daily_price`, `raw_economic_indicator` — all loaded via WRITE_TRUNCATE. **Exception (cache fallback)**: if universe collection failed, keep the existing `raw_universe` — do NOT truncate it (index membership changes only quarterly, so a one-day-old cache is fine)
- **Raw schema — nullable, NOT REQUIRED**: API-provided columns (`symbol`/`date`/`indicator_code`, prices, etc.) load as nullable; only `source`/`collected_at` are NOT NULL. raw follows a "take everything in" principle so it absorbs dirty data — a NOT NULL/REQUIRED column would fail the entire WRITE_TRUNCATE batch on a single null row. Cleaning happens later at the raw→fact transform stage
- **Connector**: `google-cloud-bigquery`
- **Integrity check**: Compare loaded count vs DataFrame row count (NFR-008)

#### Key Functions
```python
def load_to_bigquery(df: pd.DataFrame, table_name: str) -> dict  # client.load_table_from_dataframe + LoadJobConfig(write_disposition=WRITE_TRUNCATE); API columns stay NULLABLE (not REQUIRED)
def get_bigquery_client() -> Client
# truncate_table() no longer needed — WRITE_TRUNCATE handles the replacement
# raw_universe: skip the WRITE_TRUNCATE load when universe collection failed (cache fallback — keep the previous list)
```

### 2. quality_checker.py

#### Purpose
Validate collected data quality before loading (FR-009). Checks run on DataFrames in Python, not in BigQuery.

#### Validation Rules
| Check Type | Rule | Severity |
|---|---|---|
| Missing values | Required fields NOT NULL: `date`, `symbol/indicator_code`, `close/value` | warn |
| Outliers | `close_price > 0` (IR-006), value range sanity check | warn |
| Duplicates | No duplicate `(symbol, date)` or `(indicator_code, date)` pairs | warn |
| Completeness | Approved symbol (in the universe list) with 0 collected rows → suspected delisting (IR-008, FR-009) | warn |

#### Implementation Spec
- **Input**: pandas DataFrame, check configuration
- **Output**: List of check results (pass/warn/fail + detail)
- **Behavior**: Log warnings, do NOT block loading (kickoff Section 4)
- **Log target**: Python console + BigQuery `data_quality_log` table

#### Key Functions
```python
def check_missing(df: pd.DataFrame, required_columns: list) -> list
def check_outliers(df: pd.DataFrame, rules: dict) -> list
def check_duplicates(df: pd.DataFrame, key_columns: list) -> list
def check_completeness(df: pd.DataFrame, universe: list) -> list  # approved symbols with 0 collected rows → suspected delisting (IR-008)
def run_all_checks(df: pd.DataFrame, table_name: str) -> list
```

### 3. Operations Log Integration

#### Purpose
Write execution and quality logs to BigQuery operations tables after each batch run.

#### Tables
- `pipeline_execution_log`: log_id (`GENERATE_UUID()`), stage, status, record_count, error_message, timestamps
- `data_quality_log`: check_id (`GENERATE_UUID()`), check_type (missing/outlier/duplicate/completeness/universe), target_table, target_field, result, detail

---

## Design Decisions

| Decision | Choice | Reason |
|---|---|---|
| Load pattern | Full Refresh (WRITE_TRUNCATE load job) | Small data volume, ensures consistency, no dedup logic needed (ADR-003) |
| Validation timing | Before load (in Python) | Catch issues early, DataFrame-level checks are fast |
| Validation failure behavior | Warn & continue | Quality issues should not block learning pipeline (kickoff Section 4) |
| Connector | google-cloud-bigquery | Official BigQuery connector, direct DataFrame support |

---

## Prerequisites & Dependencies

- Phase 2 completed (collectors return valid DataFrames)
- GCP/BigQuery active + service account key
- `setup.sql` already executed (tables exist)
- `google-cloud-bigquery` package installed

---

## Development Notes

- Full Refresh means every run re-loads all data — safe for learning, inefficient at scale
- BigQuery serverless is sufficient for loading thousands of rows (within free tier)
- Test with small dataset first (1 ticker, 1 year) before full load
- `execution_id` (UUID) links `pipeline_execution_log` and `data_quality_log` entries

---

## Change Log

| Date | Description |
|---|---|
| 2026-05-12 | Initial creation |
| 2026-07-06 | Revised for Snowflake → BigQuery migration (WRITE_TRUNCATE load job, google-cloud-bigquery connector) |
| 2026-07-06 | Dynamic universe reflected: raw columns load as nullable (not REQUIRED), loader also WRITE_TRUNCATEs `raw_universe` (cache fallback on universe-collection failure), added `completeness` check (approved-but-0-rows → suspected delisting, IR-008/FR-009); `data_quality_log.check_type` now includes completeness/universe |

---
---

# Phase 3 — 데이터 적재 & 검증 `🔲 미시작`

> 수집된 데이터를 BigQuery raw_data에 적재하고 데이터 품질을 검증

**상태**: 🔲 미시작
**선행 조건**: Phase 2 완료 (수집 모듈 동작, 샘플 데이터 수집 확인)

---

## 개요

BigQuery 데이터 로더(Full Refresh 패턴)와 데이터 품질 검증기를 구현한다. 로더는 load job의 write_disposition=WRITE_TRUNCATE로 기존 데이터를 지우고 DataFrame 전체를 교체 적재하며, 여기에는 `raw_universe`(동적 S&P 500 + Nasdaq-100 구성종목 명단)도 포함된다. 단, 유니버스 수집이 실패한 경우엔 기존 `raw_universe`를 캐시 폴백으로 유지한다. 검증기는 적재 전 결측값, 이상치, 중복, 완전성(completeness)을 체크하고, 경고만 로그에 남기며 파이프라인을 차단하지 않는다.

---

## 완료 예정 / 완료 항목

| # | 모듈 | 상태 | 타입 |
|---|---|---|---|
| 1 | `src/loaders/bigquery_loader.py` | 🔲 | project-specific |
| 2 | `src/loaders/__init__.py` | 🔲 | project-specific |
| 3 | `src/validators/quality_checker.py` | 🔲 | project-specific |
| 4 | `src/validators/__init__.py` | 🔲 | project-specific |
| 5 | 적재 건수 검증 (NFR-008) | 🔲 | project-specific |
| 6 | 품질 로그 BigQuery 적재 (`data_quality_log`) | 🔲 | project-specific |
| 7 | 실행 로그 BigQuery 적재 (`pipeline_execution_log`) | 🔲 | project-specific |

---

## 모듈 상세

### 1. bigquery_loader.py

#### 목적
DataFrame을 BigQuery `raw_data` 스키마에 Full Refresh(WRITE_TRUNCATE load job) 방식으로 적재 (ADR-003).

#### 구현 명세
- **입력**: pandas DataFrame, 대상 테이블명
- **출력**: 적재 결과 (성공/실패, 건수)
- **패턴**: load job의 write_disposition=WRITE_TRUNCATE로 기존 데이터를 지우고 DataFrame 전체를 교체 적재 (행 단위 INSERT는 BigQuery 안티패턴)
- **대상 테이블**: `raw_universe`, `raw_daily_price`, `raw_economic_indicator` — 모두 WRITE_TRUNCATE로 적재. **예외(캐시 폴백)**: 유니버스 수집이 실패하면 기존 `raw_universe`를 유지하고 TRUNCATE하지 않음 (지수 멤버십은 분기마다 바뀌므로 하루 캐시는 문제없음)
- **raw 스키마 — nullable, REQUIRED 아님**: API가 주는 컬럼(`symbol`/`date`/`indicator_code`, 가격 등)은 nullable로 적재하고 `source`/`collected_at`만 NOT NULL. raw는 "일단 다 받는다" 원칙이라 더러운 데이터를 흡수 — NOT NULL/REQUIRED로 걸면 null 한 줄에 WRITE_TRUNCATE 배치 전체가 실패한다. 정제는 이후 raw→fact 변환 단계에서 수행
- **커넥터**: `google-cloud-bigquery`
- **정합성 체크**: 적재 건수와 DataFrame 행 수 비교 (NFR-008)

#### 핵심 함수
```python
def load_to_bigquery(df: pd.DataFrame, table_name: str) -> dict  # client.load_table_from_dataframe + LoadJobConfig(write_disposition=WRITE_TRUNCATE); API 컬럼은 NULLABLE 유지 (REQUIRED 아님)
def get_bigquery_client() -> Client
# truncate_table()은 WRITE_TRUNCATE가 대체하므로 불필요
# raw_universe: 유니버스 수집 실패 시 WRITE_TRUNCATE 적재를 건너뜀 (캐시 폴백 — 직전 명단 유지)
```

### 2. quality_checker.py

#### 목적
적재 전 수집 데이터의 품질을 검증 (FR-009). 검증은 Python DataFrame 레벨에서 수행.

#### 검증 규칙
| 검증 유형 | 규칙 | 심각도 |
|---|---|---|
| 결측값 | 필수 필드 NOT NULL: `date`, `symbol/indicator_code`, `close/value` | warn |
| 이상치 | `close_price > 0` (IR-006), 값 범위 합리성 체크 | warn |
| 중복 | `(symbol, date)` 또는 `(indicator_code, date)` 쌍 중복 없음 | warn |
| 완전성(completeness) | 승인 종목(유니버스 명단)인데 수집 0건 → 상장폐지 의심 (IR-008, FR-009) | warn |

#### 구현 명세
- **입력**: pandas DataFrame, 검증 설정
- **출력**: 검증 결과 리스트 (pass/warn/fail + 상세 내용)
- **동작**: 경고 로그 기록, 적재를 차단하지 않음 (기획서 섹션 4)
- **로그 대상**: Python 콘솔 + BigQuery `data_quality_log` 테이블

#### 핵심 함수
```python
def check_missing(df: pd.DataFrame, required_columns: list) -> list
def check_outliers(df: pd.DataFrame, rules: dict) -> list
def check_duplicates(df: pd.DataFrame, key_columns: list) -> list
def check_completeness(df: pd.DataFrame, universe: list) -> list  # 승인 종목인데 수집 0건 → 상장폐지 의심 (IR-008)
def run_all_checks(df: pd.DataFrame, table_name: str) -> list
```

### 3. 운영 로그 연동

#### 목적
배치 실행 후 실행 로그와 품질 로그를 BigQuery 운영 테이블에 기록.

#### 테이블
- `pipeline_execution_log`: log_id (`GENERATE_UUID()`), 단계, 상태, 처리 건수, 에러 메시지, 시각
- `data_quality_log`: check_id (`GENERATE_UUID()`), 검증 유형 (missing/outlier/duplicate/completeness/universe), 대상 테이블, 대상 필드, 결과, 상세

---

## 설계 결정 사항

| 결정 | 선택 | 이유 |
|---|---|---|
| 적재 패턴 | Full Refresh (WRITE_TRUNCATE load job) | 소규모 데이터, 일관성 보장, 중복 제거 로직 불필요 (ADR-003) |
| 검증 시점 | 적재 전 (Python) | 조기 발견, DataFrame 레벨 검증은 빠름 |
| 검증 실패 동작 | 경고 & 계속 진행 | 품질 문제가 학습 파이프라인을 차단하면 안 됨 (기획서 섹션 4) |
| 커넥터 | google-cloud-bigquery | 공식 BigQuery 커넥터, DataFrame 직접 지원 |

---

## 선행 조건 및 의존성

- Phase 2 완료 (수집 모듈이 유효한 DataFrame 반환)
- GCP/BigQuery 활성 상태 + 서비스계정 키
- `setup.sql` 실행 완료 (테이블 존재)
- `google-cloud-bigquery` 패키지 설치

---

## 개발 시 주의사항

- Full Refresh는 매 실행 시 전체 재적재 — 학습용으로는 안전, 대규모에서는 비효율
- BigQuery 서버리스로 수천 건 적재에 충분 (무료 티어 내)
- 전체 적재 전 소규모 데이터셋(종목 1개, 1년)으로 먼저 테스트
- `execution_id`(UUID)가 `pipeline_execution_log`와 `data_quality_log` 항목을 연결

---

## 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-05-12 | 최초 작성 |
| 2026-07-06 | Snowflake → BigQuery 전환 반영 (WRITE_TRUNCATE load job, google-cloud-bigquery 커넥터) |
| 2026-07-06 | 동적 유니버스 반영: raw 컬럼 nullable 적재(REQUIRED 아님), 로더가 `raw_universe`도 WRITE_TRUNCATE(유니버스 수집 실패 시 캐시 폴백), `completeness` 검증 추가(승인 종목 0건 → 상폐 의심, IR-008/FR-009); `data_quality_log.check_type`에 completeness/universe 포함 |
