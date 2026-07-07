🌐 [한국어](./README_ko.md) | [English](./README.md)

# Finance Data Platform

> 금융 데이터 End-to-End 파이프라인: API로 시장 데이터 수집, BigQuery Star Schema 모델링, Power BI KPI 시각화

---

## 개요

데이터 엔지니어링 학습을 목적으로 금융 분석 파이프라인을 처음부터 구축하는 프로젝트. 먼저 분석 대상 유니버스(S&P 500 + Nasdaq-100 구성종목)를 매 실행 수집한 뒤, 무료 소스에서 미국 주가와 경제지표를 수집하고, BigQuery에 적재하여 Star Schema로 변환한 뒤, Power BI 대시보드로 시각화한다. v2에서는 Text-to-SQL AI를 통한 자연어 질의 기능을 추가할 예정이다.

---

## 목차

- [동작 흐름](#동작-흐름)
- [유니버스 (분석 대상)](#유니버스-분석-대상)
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
[Wikipedia 구성종목 표]
        ↓
  Universe Collector       ← S&P500 + Nasdaq-100 구성종목 수집 (매 실행)
        ↓
[Alpha Vantage / FRED API]
        ↓
  Python Collectors        ← OHLCV + 경제지표 수집 (대상 = 유니버스)
        ↓
  Data Validator           ← 결측값, 이상치, 중복 검증
        ↓
  BigQuery raw             ← Full Refresh 적재 (WRITE_TRUNCATE load job)
        ↓
  Star Schema (SQL)        ← Fact 2 + Dim 3 테이블 (ELT 패턴)
        ↓
  Mart Views               ← 수익률 / 리스크 / 매크로 분석
        ↓
  Power BI Dashboard       ← KPI 차트 + 날짜/종목 필터
```

---

## 유니버스 (분석 대상)

분석 대상은 **S&P 500 + Nasdaq-100** 구성종목이다. 종목을 코드에 손으로 나열하지 않고, **매 실행마다 구성종목 목록을 수집**한다 (소스는 교체 가능 — 기본 `wikipedia`, `etf_holdings` 옵션).

| 지수 | ETF | 운용사 | 근거 |
|---|---|---|---|
| S&P 500 | **IVV** | BlackRock (iShares) | 운용사가 공시하는 실제 보유 명세 (무료·키 불필요) |
| Nasdaq-100 | **QQQ** | Invesco | 동일 |

- **편출입·상장폐지 자동 반영** — 매 실행 재수집하므로 지수에서 빠진 종목은 다음 실행에 자동 제외되고, 새로 편입된 종목은 자동 포함된다. 사용자가 종목을 수동으로 켜고 끌 필요가 없다.
- **명단 기반 필터링** — 수집한 구성종목이 `dim_symbol`(승인 명단)이 되어, 명단 밖 종목·오타·결측은 Star Schema 변환의 inner JOIN에서 걸러진다.
- **캐시 폴백** — 수집 실패 시 직전 성공 목록을 유지한다.
- `config/symbols.yaml`은 개별 종목을 나열하지 않고 **유니버스 소스 + FRED 지표 + 설정**만 담는다.

> 유니버스·`symbols.yaml`의 상세 정의는 [`docs/data_dictionary.md`](./docs/data_dictionary.md) 8장 참조.

---

## 기술 스택

| Technology | Role | Why |
|---|---|---|
| Python 3.x | 데이터 수집 & 오케스트레이션 | 금융 데이터 라이브러리 풍부 (yfinance, fredapi), 학습 접근성 |
| Wikipedia / ETF 보유종목 | 지수 구성종목 (S&P500 + Nasdaq-100) | 교체 가능 — Wikipedia(기본, 무료·GICS 섹터) 또는 ETF 보유종목; 편출입·상폐 자동 반영 |
| Alpha Vantage / yfinance | 미국 주식 OHLCV 데이터 | 교체 가능 — Alpha Vantage(기본, 무료 키) 또는 yfinance |
| FRED API | 경제지표 (금리, CPI) | 미국 연방준비제도 공식 데이터, 무료 API 키 |
| Google BigQuery | 서버리스 클라우드 DW | 영구 무료티어, 서버리스, Star Schema 네이티브 |
| Star Schema | 데이터 모델링 패턴 | 분석 최적화, BI 워크로드 표준 패턴 |
| Power BI Desktop | 대시보드 시각화 | 무료 Desktop 버전, BigQuery 네이티브 커넥터 |
| GitHub Actions | 파이프라인 스케줄링(cron) | 무료 CI, 인프라 불필요 |
| python-dotenv | 설정 관리 | .env 기반 시크릿 관리 |

---

## 빠른 시작

### 사전 요구사항

- Python 3.x
- Power BI Desktop
- GCP 프로젝트 + BigQuery 활성화 + 서비스계정 키
- FRED API 키 ([fred.stlouisfed.org](https://fred.stlouisfed.org))
- Alpha Vantage API 키 ([alphavantage.co](https://www.alphavantage.co/support/#api-key))

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
GCP_PROJECT_ID=your_gcp_project_id
BQ_DATASET=finance_db
BQ_LOCATION=US
GOOGLE_APPLICATION_CREDENTIALS=path/to/service_account.json
FRED_API_KEY=your_fred_key
ALPHAVANTAGE_API_KEY=your_alphavantage_key
```

### BigQuery 설정

BigQuery에서 스키마 초기화 스크립트 실행:

```bash
# bq CLI 또는 google-cloud-bigquery로 sql/setup.sql 실행
bq query --use_legacy_sql=false < sql/setup.sql
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
│   │   ├── universe_collector.py
│   │   ├── price_collector.py
│   │   └── fred_collector.py
│   ├── validators/              # 데이터 품질 검증
│   │   └── quality_checker.py
│   ├── loaders/                 # BigQuery 데이터 적재
│   │   └── bigquery_loader.py
│   ├── transformers/            # Star Schema 변환
│   │   └── star_schema.py
│   ├── utils/                   # 설정 & 로깅 유틸리티
│   │   ├── config.py
│   │   └── logger.py
│   └── main.py                  # 파이프라인 진입점
├── sql/
│   ├── setup.sql                # BigQuery 스키마 초기화
│   └── mart_views.sql           # Mart View 정의
├── config/
│   └── symbols.yaml             # 유니버스 소스 + 지표 + 설정
├── Phase/                       # 개발 Phase 문서
├── docs/
│   └── data_dictionary.md       # 테이블/컬럼 정의
├── pre-requirement/
│   └── finance_data_platform_kickoff.md
├── .github/
│   └── workflows/
│       └── pipeline.yml         # GitHub Actions 스케줄링 (cron)
├── .env.example
├── .gitignore
└── requirements.txt
```

---

## 현재 상태

| Phase | Status | Deliverable |
|---|---|---|
| Phase 1 — 프로젝트 세팅 | ✅ 완료 | 환경 구성, BigQuery 스키마 초기화, 유틸리티 모듈 |
| Phase 2 — 데이터 수집 | ✅ 완료 | 유니버스(Wikipedia) + 주가(Alpha Vantage) + FRED 수집기 |
| Phase 3 — 데이터 적재 & 검증 | 🔲 미시작 | BigQuery 로더 + 품질 검증기 |
| Phase 4 — Star Schema & Mart | 🔲 미시작 | Fact/Dim 테이블 + 3개 Mart View |
| Phase 5 — Power BI 대시보드 | 🔲 미시작 | KPI 차트 + 필터 |
| Phase 6 — 스케줄링 | 🔲 미시작 | GitHub Actions cron 파이프라인 자동 실행 |

---

## AI 구성요소 (v2)

> v2 예정 — MVP에 미포함

| 기능 | 입력 | 출력 | 모델 |
|---|---|---|---|
| Text-to-SQL | 자연어 질문 (한국어/영어) | BigQuery Standard SQL 쿼리 | Claude Haiku / Sonnet |
| 결과 해석 | SQL 쿼리 + 실행 결과 | 한국어 해석 | Claude Haiku / Sonnet |

- SELECT 쿼리만 허용 (DML/DDL 차단)
- 월간 예산 한도: $10
- `.env`의 `AI_MODEL` 변수로 모델 설정 가능

---

## 한계점

- **학습 프로젝트** — 실무가 아닌 스킬 개발 목적
- **무료 티어 제약** — BigQuery 무료티어 쿼터, API 요청 제한
- **스케줄링** — GitHub Actions cron으로 자동 실행 (Airflow/Prefect 미사용)
- **증분 적재 없음** — 매 실행 시 Full Refresh
- **생존 편향** — 현재 지수 구성종목만 분석 (과거 편출·상폐 종목이 빠져 수익률이 실제보다 좋아 보일 수 있음)
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
