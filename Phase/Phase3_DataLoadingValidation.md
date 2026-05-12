# Phase 3 — Data Loading & Validation `🔲 Not Started`

> Load collected data into Snowflake raw_data and validate data quality

**Status**: 🔲 Not Started
**Prerequisites**: Phase 2 completion (collectors working, sample data collected)

---

## Overview

Implement the Snowflake data loader (Full Refresh pattern) and data quality validator. The loader truncates and re-inserts raw data into Snowflake. The validator checks for missing values, outliers, and duplicates before loading, logging warnings without blocking the pipeline.

---

## Deliverables

| # | Module | Status | Type |
|---|---|---|---|
| 1 | `src/loaders/snowflake_loader.py` | 🔲 | project-specific |
| 2 | `src/loaders/__init__.py` | 🔲 | project-specific |
| 3 | `src/validators/quality_checker.py` | 🔲 | project-specific |
| 4 | `src/validators/__init__.py` | 🔲 | project-specific |
| 5 | Record count verification (NFR-008) | 🔲 | project-specific |
| 6 | Quality log to Snowflake (`data_quality_log`) | 🔲 | project-specific |
| 7 | Execution log to Snowflake (`pipeline_execution_log`) | 🔲 | project-specific |

---

## Module Details

### 1. snowflake_loader.py

#### Purpose
Load DataFrames into Snowflake `raw_data` schema using Full Refresh (TRUNCATE + INSERT) pattern (ADR-003).

#### Implementation Spec
- **Input**: pandas DataFrame, target table name
- **Output**: Load result (success/failure, record count)
- **Pattern**: TRUNCATE target table → INSERT all rows
- **Connector**: `snowflake-connector-python`
- **Integrity check**: Compare loaded count vs DataFrame row count (NFR-008)

#### Key Functions
```python
def load_to_snowflake(df: pd.DataFrame, table_name: str) -> dict
def get_snowflake_connection() -> Connection
def truncate_table(conn: Connection, table_name: str) -> None
```

### 2. quality_checker.py

#### Purpose
Validate collected data quality before loading (FR-009). Checks run on DataFrames in Python, not in Snowflake.

#### Validation Rules
| Check Type | Rule | Severity |
|---|---|---|
| Missing values | Required fields NOT NULL: `date`, `symbol/indicator_code`, `close/value` | warn |
| Outliers | `close_price > 0` (IR-006), value range sanity check | warn |
| Duplicates | No duplicate `(symbol, date)` or `(indicator_code, date)` pairs | warn |

#### Implementation Spec
- **Input**: pandas DataFrame, check configuration
- **Output**: List of check results (pass/warn/fail + detail)
- **Behavior**: Log warnings, do NOT block loading (kickoff Section 4)
- **Log target**: Python console + Snowflake `data_quality_log` table

#### Key Functions
```python
def check_missing(df: pd.DataFrame, required_columns: list) -> list
def check_outliers(df: pd.DataFrame, rules: dict) -> list
def check_duplicates(df: pd.DataFrame, key_columns: list) -> list
def run_all_checks(df: pd.DataFrame, table_name: str) -> list
```

### 3. Operations Log Integration

#### Purpose
Write execution and quality logs to Snowflake operations tables after each batch run.

#### Tables
- `pipeline_execution_log`: stage, status, record_count, error_message, timestamps
- `data_quality_log`: check_type, target_table, target_field, result, detail

---

## Design Decisions

| Decision | Choice | Reason |
|---|---|---|
| Load pattern | Full Refresh (TRUNCATE + INSERT) | Small data volume, ensures consistency, no dedup logic needed (ADR-003) |
| Validation timing | Before load (in Python) | Catch issues early, DataFrame-level checks are fast |
| Validation failure behavior | Warn & continue | Quality issues should not block learning pipeline (kickoff Section 4) |
| Connector | snowflake-connector-python | Official Snowflake connector, direct DataFrame support |

---

## Prerequisites & Dependencies

- Phase 2 completed (collectors return valid DataFrames)
- Snowflake account active with credits
- `setup.sql` already executed (tables exist)
- `snowflake-connector-python` package installed

---

## Development Notes

- Full Refresh means every run re-loads all data — safe for learning, inefficient at scale
- XS warehouse is sufficient for loading thousands of rows
- Test with small dataset first (1 ticker, 1 year) before full load
- `execution_id` (UUID) links `pipeline_execution_log` and `data_quality_log` entries

---

## Change Log

| Date | Description |
|---|---|
| 2026-05-12 | Initial creation |

---
---

# Phase 3 — 데이터 적재 & 검증 `🔲 미시작`

> 수집된 데이터를 Snowflake raw_data에 적재하고 데이터 품질을 검증

**상태**: 🔲 미시작
**선행 조건**: Phase 2 완료 (수집 모듈 동작, 샘플 데이터 수집 확인)

---

## 개요

Snowflake 데이터 로더(Full Refresh 패턴)와 데이터 품질 검증기를 구현한다. 로더는 raw 데이터를 truncate 후 재적재한다. 검증기는 적재 전 결측값, 이상치, 중복을 체크하고, 경고만 로그에 남기며 파이프라인을 차단하지 않는다.

---

## 완료 예정 / 완료 항목

| # | 모듈 | 상태 | 타입 |
|---|---|---|---|
| 1 | `src/loaders/snowflake_loader.py` | 🔲 | project-specific |
| 2 | `src/loaders/__init__.py` | 🔲 | project-specific |
| 3 | `src/validators/quality_checker.py` | 🔲 | project-specific |
| 4 | `src/validators/__init__.py` | 🔲 | project-specific |
| 5 | 적재 건수 검증 (NFR-008) | 🔲 | project-specific |
| 6 | 품질 로그 Snowflake 적재 (`data_quality_log`) | 🔲 | project-specific |
| 7 | 실행 로그 Snowflake 적재 (`pipeline_execution_log`) | 🔲 | project-specific |

---

## 모듈 상세

### 1. snowflake_loader.py

#### 목적
DataFrame을 Snowflake `raw_data` 스키마에 Full Refresh(TRUNCATE + INSERT) 방식으로 적재 (ADR-003).

#### 구현 명세
- **입력**: pandas DataFrame, 대상 테이블명
- **출력**: 적재 결과 (성공/실패, 건수)
- **패턴**: 대상 테이블 TRUNCATE → 전체 행 INSERT
- **커넥터**: `snowflake-connector-python`
- **정합성 체크**: 적재 건수와 DataFrame 행 수 비교 (NFR-008)

#### 핵심 함수
```python
def load_to_snowflake(df: pd.DataFrame, table_name: str) -> dict
def get_snowflake_connection() -> Connection
def truncate_table(conn: Connection, table_name: str) -> None
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

#### 구현 명세
- **입력**: pandas DataFrame, 검증 설정
- **출력**: 검증 결과 리스트 (pass/warn/fail + 상세 내용)
- **동작**: 경고 로그 기록, 적재를 차단하지 않음 (기획서 섹션 4)
- **로그 대상**: Python 콘솔 + Snowflake `data_quality_log` 테이블

#### 핵심 함수
```python
def check_missing(df: pd.DataFrame, required_columns: list) -> list
def check_outliers(df: pd.DataFrame, rules: dict) -> list
def check_duplicates(df: pd.DataFrame, key_columns: list) -> list
def run_all_checks(df: pd.DataFrame, table_name: str) -> list
```

### 3. 운영 로그 연동

#### 목적
배치 실행 후 실행 로그와 품질 로그를 Snowflake 운영 테이블에 기록.

#### 테이블
- `pipeline_execution_log`: 단계, 상태, 처리 건수, 에러 메시지, 시각
- `data_quality_log`: 검증 유형, 대상 테이블, 대상 필드, 결과, 상세

---

## 설계 결정 사항

| 결정 | 선택 | 이유 |
|---|---|---|
| 적재 패턴 | Full Refresh (TRUNCATE + INSERT) | 소규모 데이터, 일관성 보장, 중복 제거 로직 불필요 (ADR-003) |
| 검증 시점 | 적재 전 (Python) | 조기 발견, DataFrame 레벨 검증은 빠름 |
| 검증 실패 동작 | 경고 & 계속 진행 | 품질 문제가 학습 파이프라인을 차단하면 안 됨 (기획서 섹션 4) |
| 커넥터 | snowflake-connector-python | 공식 Snowflake 커넥터, DataFrame 직접 지원 |

---

## 선행 조건 및 의존성

- Phase 2 완료 (수집 모듈이 유효한 DataFrame 반환)
- Snowflake 계정 활성 상태 (크레딧 여유)
- `setup.sql` 실행 완료 (테이블 존재)
- `snowflake-connector-python` 패키지 설치

---

## 개발 시 주의사항

- Full Refresh는 매 실행 시 전체 재적재 — 학습용으로는 안전, 대규모에서는 비효율
- XS warehouse로 수천 건 적재에 충분
- 전체 적재 전 소규모 데이터셋(종목 1개, 1년)으로 먼저 테스트
- `execution_id`(UUID)가 `pipeline_execution_log`와 `data_quality_log` 항목을 연결

---

## 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-05-12 | 최초 작성 |
