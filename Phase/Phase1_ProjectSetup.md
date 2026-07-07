# Phase 1 — Project Setup `✅ Completed`

> Set up the development environment, BigQuery initialization, and project structure

**Status**: ✅ Completed
**Prerequisites**: None

---

## Overview

Establish the foundational project structure, configure environment variables, install dependencies, and initialize the BigQuery dataset schema (`finance_db`). This phase ensures all team members (or the developer) can run the pipeline from a clean setup.

---

## Deliverables

| # | Module | Status | Type |
|---|---|---|---|
| 1 | Project directory structure | ✅ | project-specific |
| 2 | `.env` + `.gitignore` configuration | ✅ | project-specific |
| 3 | `requirements.txt` | ✅ | project-specific |
| 4 | `config/symbols.yaml` | ✅ | project-specific |
| 5 | `sql/setup.sql` (BigQuery schema) | ✅ | project-specific |
| 6 | `src/utils/config.py` | ✅ | project-specific |
| 7 | `src/utils/logger.py` | ✅ | project-specific |
| 8 | BigQuery connection test | ✅ | project-specific |

---

## Module Details

### 1. Project Directory Structure

#### Purpose
Create the folder layout defined in the kickoff document (Section 13-1).

#### Target Structure
```
finance_data_platform/
├── src/
│   ├── collectors/
│   ├── validators/
│   ├── loaders/
│   ├── transformers/
│   ├── utils/
│   └── main.py
├── sql/
├── tests/
├── docs/
├── config/
├── .env.example
├── .gitignore
└── requirements.txt
```

### 2. Environment Configuration

#### Purpose
Manage API keys and GCP credentials securely via `.env` file.

#### Environment Variables
| Variable | Required | Description |
|---|---|---|
| GCP_PROJECT_ID | Y | GCP project ID |
| BQ_DATASET | Y | BigQuery dataset name (finance_db) |
| BQ_LOCATION | Y | BigQuery dataset location (e.g., US) |
| GOOGLE_APPLICATION_CREDENTIALS | Y | Path to service account JSON key file |
| FRED_API_KEY | Y | FRED API key |
| LOG_LEVEL | N | Log level (default: INFO) |

### 3. BigQuery Schema Initialization

#### Purpose
Create all objects in the `finance_db` dataset: raw tables, Star Schema tables, and operations tables via `setup.sql`.

#### Tables Created
- **Raw Layer**: `raw_universe`, `raw_daily_price`, `raw_economic_indicator`
- **Star Schema**: `fact_daily_price`, `fact_economic_indicator`, `dim_date`, `dim_symbol`, `dim_indicator`
- **Operations**: `pipeline_execution_log`, `data_quality_log`

#### DDL Conventions (BigQuery)
- Types per the data dictionary mapping: `STRING` / `NUMERIC` / `INT64` / `BOOL` / `TIMESTAMP`
- Surrogate keys via `FARM_FINGERPRINT(natural_key)` (filled at load time, not AUTOINCREMENT)
- Log IDs via `GENERATE_UUID()`
- `PRIMARY KEY (...) NOT ENFORCED`; no `UNIQUE` constraint (unsupported)
- Raw table columns (`symbol` / `date` / `indicator_code`, etc.) are **nullable**; only `source` and `collected_at` are NOT NULL (raw absorbs dirty data — a single NULL row would fail the whole `WRITE_TRUNCATE` batch)

### 4. Universe & `config/symbols.yaml`

#### Purpose
Define the analysis universe as a **source structure**, not a hand-listed set of tickers. The universe (S&P 500 + Nasdaq-100) is re-collected each run from ETF holdings (IVV + QQQ) into `raw_universe`, which seeds `dim_symbol`; index add/drops and delistings are handled automatically.

#### Structure
`config/symbols.yaml` holds only the universe sources + indicators + settings (no individual tickers):

```yaml
universe:
  sp500:     { enabled: true, source: etf_holdings, etf: IVV }
  nasdaq100: { enabled: true, source: etf_holdings, etf: QQQ }
  include_extra: []      # tickers to force-include (not in the index)
  exclude:       []      # tickers to force-exclude (escape hatch)

indicators:              # FRED indicators listed by hand (few, stable) → dim_indicator seed
  - { code: FEDFUNDS, name: Federal Funds Rate,   unit: "%",   source: FRED }
  - { code: CPIAUCSL, name: Consumer Price Index, unit: index, source: FRED }

settings:
  date_range: { start: "2020-01-01" }
```

See the data dictionary (Section 8) for the full universe design.

### 5. Utility Modules

#### `src/utils/config.py`
Load `.env` variables and the `config/symbols.yaml` universe/indicators settings.

#### `src/utils/logger.py`
Structured logging with timestamp, stage, status, record count (NFR-004).

---

## Design Decisions

| Decision | Choice | Reason |
|---|---|---|
| Config management | `.env` + `python-dotenv` | Simple, no extra infrastructure |
| Logging | Python `logging` module | Built-in, structured format sufficient |
| BigQuery init | Single `setup.sql` script | Learning project, no migration tool needed (ADR in kickoff) |

---

## Prerequisites & Dependencies

- Python 3.x installed
- GCP project created + BigQuery enabled + service account key issued
- FRED API key issued
- Power BI Desktop installed
- (GitHub Secrets will be configured later, in the scheduling phase)

---

## Development Notes

- `.env` file and the service account JSON key must NEVER be committed to git
- BigQuery free tier (1 TB query/month + 10 GB storage); serverless, so no warehouse config needed
- Run `sql/setup.sql` in the BigQuery console or via `google-cloud-bigquery`

---

## Change Log

| Date | Description |
|---|---|
| 2026-05-12 | Initial creation |
| 2026-07-06 | Aligned to BigQuery (types, WRITE_TRUNCATE, FARM_FINGERPRINT keys) |
| 2026-07-06 | Reflected dynamic universe: added `raw_universe`, nullable raw columns, `config/symbols.yaml` universe-source structure, config.py universe load |
| 2026-07-06 | Removed `sql/seed_dimensions.sql` — dims are populated from `raw_universe` / `config/symbols.yaml` / date generation |
| 2026-07-07 | ✅ Phase 1 completed — all deliverables implemented (config.py, logger.py, bq_client.py, setup.sql, symbols.yaml, requirements.txt, main.py skeleton, tests/test_setup.py); BigQuery connection test passed; 10 tables created in `finance_db`; FRED key validated (FEDFUNDS fetch) |

---
---

# Phase 1 — 프로젝트 세팅 `✅ 완료`

> 개발 환경 구성, BigQuery 초기화, 프로젝트 구조 생성

**상태**: ✅ 완료
**선행 조건**: 없음

---

## 개요

프로젝트 폴더 구조를 생성하고, 환경 변수를 설정하고, 의존성을 설치하고, BigQuery 데이터셋(finance_db) 스키마를 초기화한다. 이 Phase가 완료되면 깨끗한 환경에서 파이프라인을 실행할 수 있다.

---

## 완료 예정 / 완료 항목

| # | 모듈 | 상태 | 타입 |
|---|---|---|---|
| 1 | 프로젝트 디렉토리 구조 | ✅ | project-specific |
| 2 | `.env` + `.gitignore` 설정 | ✅ | project-specific |
| 3 | `requirements.txt` | ✅ | project-specific |
| 4 | `config/symbols.yaml` | ✅ | project-specific |
| 5 | `sql/setup.sql` (BigQuery 스키마) | ✅ | project-specific |
| 6 | `src/utils/config.py` | ✅ | project-specific |
| 7 | `src/utils/logger.py` | ✅ | project-specific |
| 8 | BigQuery 연결 테스트 | ✅ | project-specific |

---

## 모듈 상세

### 1. 프로젝트 디렉토리 구조

#### 목적
기획서(섹션 13-1)에 정의된 폴더 레이아웃을 생성한다.

#### 목표 구조
```
finance_data_platform/
├── src/
│   ├── collectors/
│   ├── validators/
│   ├── loaders/
│   ├── transformers/
│   ├── utils/
│   └── main.py
├── sql/
├── tests/
├── docs/
├── config/
├── .env.example
├── .gitignore
└── requirements.txt
```

### 2. 환경 설정

#### 목적
API 키와 GCP 자격 증명을 `.env` 파일로 안전하게 관리한다.

#### 환경 변수
| 변수 | 필수 | 설명 |
|---|---|---|
| GCP_PROJECT_ID | Y | GCP 프로젝트 ID |
| BQ_DATASET | Y | BigQuery 데이터셋명 (finance_db) |
| BQ_LOCATION | Y | BigQuery 데이터셋 위치 (예: US) |
| GOOGLE_APPLICATION_CREDENTIALS | Y | 서비스 계정 JSON 키 파일 경로 |
| FRED_API_KEY | Y | FRED API 키 |
| LOG_LEVEL | N | 로그 레벨 (기본값: INFO) |

### 3. BigQuery 스키마 초기화

#### 목적
`setup.sql`로 `finance_db` 데이터셋의 모든 객체를 생성한다: raw 테이블, Star Schema 테이블, 운영 테이블.

#### 생성 테이블
- **Raw Layer**: `raw_universe`, `raw_daily_price`, `raw_economic_indicator`
- **Star Schema**: `fact_daily_price`, `fact_economic_indicator`, `dim_date`, `dim_symbol`, `dim_indicator`
- **Operations**: `pipeline_execution_log`, `data_quality_log`

#### DDL 규약 (BigQuery)
- 타입은 데이터 사전 매핑을 따름: `STRING` / `NUMERIC` / `INT64` / `BOOL` / `TIMESTAMP`
- 대리키는 `FARM_FINGERPRINT(자연키)` (적재 시 채움, AUTOINCREMENT 아님)
- 로그 ID는 `GENERATE_UUID()`
- `PRIMARY KEY (...) NOT ENFORCED`; `UNIQUE` 제약 없음 (미지원)
- Raw 테이블 컬럼(`symbol` / `date` / `indicator_code` 등)은 **nullable**; `source`·`collected_at`만 NOT NULL (raw가 더러운 데이터를 흡수 — null 한 줄이면 `WRITE_TRUNCATE` 배치 전체가 실패)

### 4. 유니버스 & `config/symbols.yaml`

#### 목적
분석 유니버스를 개별 종목 나열이 아니라 **소스 구조**로 정의한다. 유니버스(S&P 500 + Nasdaq-100)는 매 실행 ETF 보유종목(IVV + QQQ)에서 재수집되어 `raw_universe`에 적재되고, 이것이 `dim_symbol`의 seed가 된다. 지수 편출입·상장폐지는 자동 처리된다.

#### 구조
`config/symbols.yaml`은 개별 종목을 나열하지 않고 유니버스 소스 + 지표 + 설정만 담는다:

```yaml
universe:
  sp500:     { enabled: true, source: etf_holdings, etf: IVV }
  nasdaq100: { enabled: true, source: etf_holdings, etf: QQQ }
  include_extra: []      # 지수에 없지만 꼭 넣을 티커
  exclude:       []      # 강제 제외 티커 (탈출구)

indicators:              # FRED 지표는 손으로 나열 (적고 안정적) → dim_indicator seed
  - { code: FEDFUNDS, name: Federal Funds Rate,   unit: "%",   source: FRED }
  - { code: CPIAUCSL, name: Consumer Price Index, unit: index, source: FRED }

settings:
  date_range: { start: "2020-01-01" }
```

유니버스 전체 설계는 데이터 사전 8장 참고.

### 5. 유틸리티 모듈

#### `src/utils/config.py`
`.env` 변수와 `config/symbols.yaml`의 유니버스·지표 설정을 로드한다.

#### `src/utils/logger.py`
타임스탬프, 단계, 상태, 처리 건수를 포함한 구조화된 로깅 (NFR-004).

---

## 설계 결정 사항

| 결정 | 선택 | 이유 |
|---|---|---|
| 설정 관리 | `.env` + `python-dotenv` | 단순, 추가 인프라 불필요 |
| 로깅 | Python `logging` 모듈 | 내장 모듈, 구조화된 포맷 충분 |
| BigQuery 초기화 | 단일 `setup.sql` 스크립트 | 학습용 프로젝트, 마이그레이션 도구 불필요 (기획서 ADR) |

---

## 선행 조건 및 의존성

- Python 3.x 설치 완료
- GCP 프로젝트 생성 + BigQuery 활성화 + 서비스 계정 키 발급
- FRED API 키 발급
- Power BI Desktop 설치
- (GitHub Secrets는 이후 스케줄링 단계에서 설정)

---

## 개발 시 주의사항

- `.env` 파일과 서비스 계정 JSON 키는 절대 git에 커밋하지 않는다
- BigQuery 무료 티어(월 1TB 쿼리 + 10GB 저장)로 운영; 서버리스라 warehouse 설정 불필요
- `sql/setup.sql`은 BigQuery 콘솔 또는 google-cloud-bigquery로 실행

---

## 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-05-12 | 최초 작성 |
| 2026-07-06 | BigQuery 기준 정비 (타입, WRITE_TRUNCATE, FARM_FINGERPRINT 키) |
| 2026-07-06 | 동적 유니버스 반영: `raw_universe` 추가, raw 컬럼 nullable화, `config/symbols.yaml` 유니버스 소스 구조, config.py 유니버스 로드 |
| 2026-07-06 | `sql/seed_dimensions.sql` 제거 — dim은 `raw_universe`/`config/symbols.yaml`/날짜 생성으로 채워짐 |
| 2026-07-07 | ✅ Phase 1 완료 — 산출물 전부 구현(config.py, logger.py, bq_client.py, setup.sql, symbols.yaml, requirements.txt, main.py 스켈레톤, tests/test_setup.py); BigQuery 연결 테스트 통과; `finance_db`에 테이블 10개 생성; FRED 키 유효성 확인(FEDFUNDS fetch) |
