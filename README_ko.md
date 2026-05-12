🌐 [한국어](./README_ko.md) | [English](./README.md)

# Finance Data Platform

> 금융 데이터 End-to-End 파이프라인: API로 시장 데이터 수집, Snowflake Star Schema 모델링, Power BI KPI 시각화

---

## 개요

데이터 엔지니어링 학습을 목적으로 금융 분석 파이프라인을 처음부터 구축하는 프로젝트. 무료 API에서 미국 주가와 경제지표를 수집하고, Snowflake에 적재하여 Star Schema로 변환한 뒤, Power BI 대시보드로 시각화한다. v2에서는 Text-to-SQL AI를 통한 자연어 질의 기능을 추가할 예정이다.

---

## 목차

- [동작 흐름](#동작-흐름)
- [기술 스택](#기술-스택)
- [빠른 시작](#빠른-시작)
- [프로젝트 구조](#프로젝트-구조)
- [현재 상태](#현재-상태)
- [AI 구성요소 (v2)](#ai-구성요소-v2)
- [한계점](#한계점)
- [향후 계획](#향후-계획)

---

## 동작 흐름

```
[yfinance / FRED API]
        ↓
  Python Collectors        ← OHLCV + 경제지표 수집
        ↓
  Data Validator           ← 결측값, 이상치, 중복 검증
        ↓
  Snowflake raw_data       ← Full Refresh 적재 (TRUNCATE + INSERT)
        ↓
  Star Schema (SQL)        ← Fact 2 + Dim 3 테이블 (ELT 패턴)
        ↓
  Mart Views               ← 수익률 / 리스크 / 매크로 분석
        ↓
  Power BI Dashboard       ← KPI 차트 + 날짜/종목 필터
```

---

## 기술 스택

| Technology | Role | Why |
|---|---|---|
| Python 3.x | 데이터 수집 & 오케스트레이션 | 금융 데이터 라이브러리 풍부 (yfinance, fredapi), 학습 접근성 |
| yfinance | 미국 주식 OHLCV 데이터 | 무료, API 키 불필요, 비공식이지만 널리 사용 |
| FRED API | 경제지표 (금리, CPI) | 미국 연방준비제도 공식 데이터, 무료 API 키 |
| Snowflake | 클라우드 데이터 웨어하우스 | 업계 표준, 무료 트라이얼, Star Schema 네이티브 지원 |
| Star Schema | 데이터 모델링 패턴 | 분석 최적화, BI 워크로드 표준 패턴 |
| Power BI Desktop | 대시보드 시각화 | 무료 Desktop 버전, Snowflake 네이티브 커넥터 |
| python-dotenv | 설정 관리 | .env 기반 시크릿 관리 |

---

## 빠른 시작

### 사전 요구사항

- Python 3.x
- Power BI Desktop
- Snowflake 무료 트라이얼 계정
- FRED API 키 ([fred.stlouisfed.org](https://fred.stlouisfed.org))

### 설치

```bash
git clone https://github.com/SoyeonAhn3/finance_data_platform.git
cd finance_data_platform
pip install -r requirements.txt
```

### 환경 설정

`.env.example`을 `.env`로 복사하고 자격 증명을 입력:

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

### Snowflake 설정

Snowflake에서 스키마 초기화 스크립트 실행:

```sql
-- Snowflake UI 또는 Python Connector로 sql/setup.sql 실행
```

### 파이프라인 실행

```bash
python src/main.py
```

---

## 프로젝트 구조

```
finance_data_platform/
├── src/
│   ├── collectors/              # API 데이터 수집 모듈
│   │   ├── yfinance_collector.py
│   │   └── fred_collector.py
│   ├── validators/              # 데이터 품질 검증
│   │   └── quality_checker.py
│   ├── loaders/                 # Snowflake 데이터 적재
│   │   └── snowflake_loader.py
│   ├── transformers/            # Star Schema 변환
│   │   └── star_schema.py
│   ├── utils/                   # 설정 & 로깅 유틸리티
│   │   ├── config.py
│   │   └── logger.py
│   └── main.py                  # 파이프라인 진입점
├── sql/
│   ├── setup.sql                # Snowflake 스키마 초기화
│   ├── mart_views.sql           # Mart View 정의
│   └── seed_dimensions.sql      # Dimension 초기 데이터
├── config/
│   └── symbols.yaml             # 종목 & 지표 목록
├── Phase/                       # 개발 Phase 문서
├── docs/
│   └── data_dictionary.md       # 테이블/컬럼 정의
├── pre-requirement/
│   └── finance_data_platform_kickoff.md
├── .env.example
├── .gitignore
└── requirements.txt
```

---

## 현재 상태

| Phase | Status | Deliverable |
|---|---|---|
| Phase 1 — 프로젝트 세팅 | 🔲 미시작 | 환경 구성, Snowflake 스키마 초기화, 유틸리티 모듈 |
| Phase 2 — 데이터 수집 | 🔲 미시작 | yfinance + FRED API 수집 모듈 |
| Phase 3 — 데이터 적재 & 검증 | 🔲 미시작 | Snowflake 로더 + 품질 검증기 |
| Phase 4 — Star Schema & Mart | 🔲 미시작 | Fact/Dim 테이블 + 3개 Mart View |
| Phase 5 — Power BI 대시보드 | 🔲 미시작 | KPI 차트 + 필터 |

---

## AI 구성요소 (v2)

> v2 예정 — MVP에 미포함

| 기능 | 입력 | 출력 | 모델 |
|---|---|---|---|
| Text-to-SQL | 자연어 질문 (한국어/영어) | Snowflake SQL 쿼리 | Claude Haiku / Sonnet |
| 결과 해석 | SQL 쿼리 + 실행 결과 | 한국어 해석 | Claude Haiku / Sonnet |

- SELECT 쿼리만 허용 (DML/DDL 차단)
- 월간 예산 한도: $10
- `.env`의 `AI_MODEL` 변수로 모델 설정 가능

---

## 한계점

- **학습 프로젝트** — 실무가 아닌 스킬 개발 목적
- **무료 티어 제약** — Snowflake 트라이얼 크레딧, API 요청 제한
- **스케줄링 없음** — 수동 배치 실행 (Airflow/Prefect 미사용)
- **증분 적재 없음** — 매 실행 시 Full Refresh
- **테스트 없음** — 단위 테스트 계획은 있으나 미구현
- **단일 사용자** — 인증 및 다중 사용자 미지원

---

## 향후 계획

- [ ] **v2: Text-to-SQL AI** — Claude API 기반 자연어 질의
- [ ] **v2: Alpha Vantage** — 기술지표 (RSI, MACD)
- [ ] **v2: KRX 데이터** — 한국 주식시장 연동
- [ ] 검증/변환 로직 단위 테스트 작성
- [ ] 대규모 데이터셋을 위한 증분 적재 전략

---

<p align="center">Made with AI-assisted development</p>
