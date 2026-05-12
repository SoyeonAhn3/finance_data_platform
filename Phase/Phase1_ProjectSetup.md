# Phase 1 — Project Setup `🔲 Not Started`

> Set up the development environment, Snowflake initialization, and project structure

**Status**: 🔲 Not Started
**Prerequisites**: None

---

## Overview

Establish the foundational project structure, configure environment variables, install dependencies, and initialize the Snowflake data warehouse schema. This phase ensures all team members (or the developer) can run the pipeline from a clean setup.

---

## Deliverables

| # | Module | Status | Type |
|---|---|---|---|
| 1 | Project directory structure | 🔲 | project-specific |
| 2 | `.env` + `.gitignore` configuration | 🔲 | project-specific |
| 3 | `requirements.txt` | 🔲 | project-specific |
| 4 | `config/symbols.yaml` | 🔲 | project-specific |
| 5 | `sql/setup.sql` (Snowflake schema) | 🔲 | project-specific |
| 6 | `sql/seed_dimensions.sql` | 🔲 | project-specific |
| 7 | `src/utils/config.py` | 🔲 | project-specific |
| 8 | `src/utils/logger.py` | 🔲 | project-specific |
| 9 | Snowflake connection test | 🔲 | project-specific |

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
Manage API keys and Snowflake credentials securely via `.env` file.

#### Environment Variables
| Variable | Required | Description |
|---|---|---|
| SNOWFLAKE_ACCOUNT | Y | Snowflake account identifier |
| SNOWFLAKE_USER | Y | Snowflake username |
| SNOWFLAKE_PASSWORD | Y | Snowflake password |
| SNOWFLAKE_DATABASE | Y | Database name (FINANCE_DB) |
| SNOWFLAKE_WAREHOUSE | Y | Warehouse name (XS_WH) |
| SNOWFLAKE_SCHEMA | Y | Schema name (RAW_DATA) |
| FRED_API_KEY | Y | FRED API key |
| LOG_LEVEL | N | Log level (default: INFO) |

### 3. Snowflake Schema Initialization

#### Purpose
Create all database objects: raw tables, Star Schema tables, and operations tables via `setup.sql`.

#### Tables Created
- **Raw Layer**: `raw_daily_price`, `raw_economic_indicator`
- **Star Schema**: `fact_daily_price`, `fact_economic_indicator`, `dim_date`, `dim_symbol`, `dim_indicator`
- **Operations**: `pipeline_execution_log`, `data_quality_log`

### 4. Utility Modules

#### `src/utils/config.py`
Load `.env` variables and `config/symbols.yaml` settings.

#### `src/utils/logger.py`
Structured logging with timestamp, stage, status, record count (NFR-004).

---

## Design Decisions

| Decision | Choice | Reason |
|---|---|---|
| Config management | `.env` + `python-dotenv` | Simple, no extra infrastructure |
| Logging | Python `logging` module | Built-in, structured format sufficient |
| Snowflake init | Single `setup.sql` script | Learning project, no migration tool needed (ADR in kickoff) |

---

## Prerequisites & Dependencies

- Python 3.x installed
- Snowflake free trial account created
- FRED API key issued
- Power BI Desktop installed

---

## Development Notes

- `.env` file must NEVER be committed to git
- Snowflake free trial has credit limits — use XS warehouse only
- Run `sql/setup.sql` manually in Snowflake UI or via Python connector

---

## Change Log

| Date | Description |
|---|---|
| 2026-05-12 | Initial creation |

---
---

# Phase 1 — 프로젝트 세팅 `🔲 미시작`

> 개발 환경 구성, Snowflake 초기화, 프로젝트 구조 생성

**상태**: 🔲 미시작
**선행 조건**: 없음

---

## 개요

프로젝트 폴더 구조를 생성하고, 환경 변수를 설정하고, 의존성을 설치하고, Snowflake 데이터 웨어하우스 스키마를 초기화한다. 이 Phase가 완료되면 깨끗한 환경에서 파이프라인을 실행할 수 있다.

---

## 완료 예정 / 완료 항목

| # | 모듈 | 상태 | 타입 |
|---|---|---|---|
| 1 | 프로젝트 디렉토리 구조 | 🔲 | project-specific |
| 2 | `.env` + `.gitignore` 설정 | 🔲 | project-specific |
| 3 | `requirements.txt` | 🔲 | project-specific |
| 4 | `config/symbols.yaml` | 🔲 | project-specific |
| 5 | `sql/setup.sql` (Snowflake 스키마) | 🔲 | project-specific |
| 6 | `sql/seed_dimensions.sql` | 🔲 | project-specific |
| 7 | `src/utils/config.py` | 🔲 | project-specific |
| 8 | `src/utils/logger.py` | 🔲 | project-specific |
| 9 | Snowflake 연결 테스트 | 🔲 | project-specific |

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
API 키와 Snowflake 자격 증명을 `.env` 파일로 안전하게 관리한다.

#### 환경 변수
| 변수 | 필수 | 설명 |
|---|---|---|
| SNOWFLAKE_ACCOUNT | Y | Snowflake 계정 식별자 |
| SNOWFLAKE_USER | Y | Snowflake 사용자명 |
| SNOWFLAKE_PASSWORD | Y | Snowflake 비밀번호 |
| SNOWFLAKE_DATABASE | Y | 데이터베이스명 (FINANCE_DB) |
| SNOWFLAKE_WAREHOUSE | Y | 웨어하우스명 (XS_WH) |
| SNOWFLAKE_SCHEMA | Y | 스키마명 (RAW_DATA) |
| FRED_API_KEY | Y | FRED API 키 |
| LOG_LEVEL | N | 로그 레벨 (기본값: INFO) |

### 3. Snowflake 스키마 초기화

#### 목적
`setup.sql`로 모든 데이터베이스 객체를 생성한다: raw 테이블, Star Schema 테이블, 운영 테이블.

#### 생성 테이블
- **Raw Layer**: `raw_daily_price`, `raw_economic_indicator`
- **Star Schema**: `fact_daily_price`, `fact_economic_indicator`, `dim_date`, `dim_symbol`, `dim_indicator`
- **Operations**: `pipeline_execution_log`, `data_quality_log`

### 4. 유틸리티 모듈

#### `src/utils/config.py`
`.env` 변수와 `config/symbols.yaml` 설정을 로드한다.

#### `src/utils/logger.py`
타임스탬프, 단계, 상태, 처리 건수를 포함한 구조화된 로깅 (NFR-004).

---

## 설계 결정 사항

| 결정 | 선택 | 이유 |
|---|---|---|
| 설정 관리 | `.env` + `python-dotenv` | 단순, 추가 인프라 불필요 |
| 로깅 | Python `logging` 모듈 | 내장 모듈, 구조화된 포맷 충분 |
| Snowflake 초기화 | 단일 `setup.sql` 스크립트 | 학습용 프로젝트, 마이그레이션 도구 불필요 (기획서 ADR) |

---

## 선행 조건 및 의존성

- Python 3.x 설치 완료
- Snowflake 무료 트라이얼 계정 생성
- FRED API 키 발급
- Power BI Desktop 설치

---

## 개발 시 주의사항

- `.env` 파일은 절대 git에 커밋하지 않는다
- Snowflake 무료 트라이얼은 크레딧 한도가 있으므로 XS warehouse만 사용
- `sql/setup.sql`은 Snowflake UI 또는 Python Connector로 수동 실행

---

## 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-05-12 | 최초 작성 |
