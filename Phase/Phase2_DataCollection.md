# Phase 2 — Data Collection `🔲 Not Started`

> Build data collection modules for yfinance (US stocks) and FRED API (economic indicators)

**Status**: 🔲 Not Started
**Prerequisites**: Phase 1 completion (environment setup, BigQuery connection verified)

---

## Overview

Implement Python modules to collect financial data from external APIs. **universe_collector runs first, collecting the S&P 500 + Nasdaq-100 constituent list from ETF holdings (IVV + QQQ) on every run, so index add/drop and delistings are reflected automatically.** This phase then covers yfinance for US stock OHLCV data and FRED API for economic indicators (interest rates, inflation, etc.). The pipeline logger records success/failure/record counts at each step.

---

## Deliverables

| # | Module | Status | Type |
|---|---|---|---|
| 1 | `src/collectors/universe_collector.py` | 🔲 | project-specific |
| 2 | `src/collectors/yfinance_collector.py` | 🔲 | project-specific |
| 3 | `src/collectors/fred_collector.py` | 🔲 | project-specific |
| 4 | `src/collectors/__init__.py` | 🔲 | project-specific |
| 5 | Pipeline execution logging integration | 🔲 | project-specific |
| 6 | universe collection test (ETF holdings → raw_universe) | 🔲 | project-specific |
| 7 | yfinance sample data collection test | 🔲 | project-specific |
| 8 | FRED API sample data collection test | 🔲 | project-specific |

---

## Module Details

### 1. universe_collector.py

#### Purpose
Collect S&P 500 + Nasdaq-100 constituents from ETF holdings (**IVV** = S&P 500, **QQQ** = Nasdaq-100) and produce the `raw_universe` constituent list. **Runs before yfinance_collector** — its ticker list is the collection target for yfinance, so index add/drop and delistings are picked up every run.

#### Implementation Spec
- **Input**: universe config from `symbols.yaml` (source + ETF codes); no date range needed
- **Output**: pandas DataFrame with columns: `ticker, company_name, sector, market, index_source, weight, source` → `raw_universe`
- **Source field**: `"IVV"` / `"QQQ"` (issuing ETF)
- **Source (pluggable)**: `etf_holdings` (default — issuer-disclosed CSV) / `api` (FMP·Finnhub) / `wikipedia`
- **Cache fallback**: on collection failure, keep the previous successful `raw_universe` (no TRUNCATE) — index membership changes only quarterly, so a day-old list is safe
- **Error handling**: log failure, fall back to cache, continue pipeline (FR-010)

#### Key Functions
```python
def fetch_universe(config) -> pd.DataFrame
```

### 2. yfinance_collector.py

#### Purpose
Collect daily OHLCV data for the US stocks in the `raw_universe` ticker list (produced by universe_collector).

#### Implementation Spec
- **Input**: Ticker list from `raw_universe` (collected by universe_collector — **not** individual tickers listed in `symbols.yaml`), date range
- **Output**: pandas DataFrame with columns: `symbol, date, open, high, low, close, adj_close, volume, source`
- **Source field**: `"yfinance"`
- **API**: yfinance (unofficial, no rate limit)
- **Error handling**: Try-except per ticker, log failures, continue to next ticker (FR-010)

#### Key Functions
```python
def collect_stock_data(symbols: list, start_date: str, end_date: str) -> pd.DataFrame
```

### 3. fred_collector.py

#### Purpose
Collect economic indicators (Fed Funds Rate, CPI, GDP, etc.) from FRED API.

#### Implementation Spec
- **Input**: Indicator code list from `symbols.yaml`, date range
- **Output**: pandas DataFrame with columns: `indicator_code, date, value, source`
- **Source field**: `"FRED"`
- **API**: FRED API (120 requests/min rate limit)
- **Error handling**: Try-except per indicator, log failures, continue (FR-010)
- **API Key**: Loaded from `.env` via `config.py`

#### Key Functions
```python
def collect_economic_data(indicators: list, start_date: str, end_date: str) -> pd.DataFrame
```

### 4. Pipeline Logger Integration

#### Purpose
Record collection stage results: success/failure/record count per API call (FR-010).

#### Log Format
```
[2026-05-12 10:30:00] [collect] [success] yfinance — AAPL: 1,260 records
[2026-05-12 10:30:05] [collect] [failure] FRED — INVALID_CODE: API error 400
```

---

## Design Decisions

| Decision | Choice | Reason |
|---|---|---|
| Per-ticker error handling | Log & skip | One failed ticker should not block entire collection (FR-010) |
| No auto-retry | Log only | Learning project, manual re-run is sufficient |
| DataFrame as intermediate | pandas DataFrame | Standard data structure, easy validation and BigQuery loading |
| Date range config | CLI args or yaml | Flexible for both full history and incremental runs |

---

## Prerequisites & Dependencies

- Phase 1 completed (config.py, logger.py working)
- `yfinance` package installed
- `fredapi` package installed
- FRED API key in `.env`
- `config/symbols.yaml` with universe source config and indicator list (no individual ticker list)

---

## Development Notes

- yfinance is unofficial — API may change without notice
- FRED rate limit: 120 requests/min — with ~10 indicators this is not a concern
- `collected_at` timestamp is added automatically for raw data tracking
- Test with 2-3 tickers first before running full symbol list

---

## Change Log

| Date | Description |
|---|---|
| 2026-05-12 | Initial creation |
| 2026-07-06 | Added dynamic universe: `universe_collector.py` (ETF holdings IVV+QQQ → `raw_universe`, runs before yfinance); yfinance now collects the `raw_universe` ticker list |

---
---

# Phase 2 — 데이터 수집 `🔲 미시작`

> yfinance(미국 주가)와 FRED API(경제지표) 데이터 수집 모듈 구축

**상태**: 🔲 미시작
**선행 조건**: Phase 1 완료 (환경 설정, BigQuery 연결 확인)

---

## 개요

외부 API에서 금융 데이터를 수집하는 Python 모듈을 구현한다. **universe_collector가 가장 먼저 실행되어 매 실행마다 ETF 보유종목(IVV + QQQ)에서 S&P 500 + Nasdaq-100 구성종목 명단을 수집하므로 지수 편출입·상장폐지가 자동 반영된다.** 이어서 yfinance로 미국 주식 일별 OHLCV 데이터를, FRED API로 경제지표(금리, 인플레이션 등)를 수집한다. 파이프라인 로거가 각 단계의 성공/실패/건수를 기록한다.

---

## 완료 예정 / 완료 항목

| # | 모듈 | 상태 | 타입 |
|---|---|---|---|
| 1 | `src/collectors/universe_collector.py` | 🔲 | project-specific |
| 2 | `src/collectors/yfinance_collector.py` | 🔲 | project-specific |
| 3 | `src/collectors/fred_collector.py` | 🔲 | project-specific |
| 4 | `src/collectors/__init__.py` | 🔲 | project-specific |
| 5 | 파이프라인 실행 로그 연동 | 🔲 | project-specific |
| 6 | 유니버스 수집 테스트 (ETF 보유종목 → raw_universe) | 🔲 | project-specific |
| 7 | yfinance 샘플 데이터 수집 테스트 | 🔲 | project-specific |
| 8 | FRED API 샘플 데이터 수집 테스트 | 🔲 | project-specific |

---

## 모듈 상세

### 1. universe_collector.py

#### 목적
ETF 보유종목(**IVV** = S&P 500, **QQQ** = Nasdaq-100)에서 S&P 500 + Nasdaq-100 구성종목을 수집해 `raw_universe` 구성종목 명단을 산출한다. **yfinance_collector보다 먼저 실행** — 여기서 나온 ticker 목록이 yfinance의 수집 대상이 되므로, 매 실행마다 지수 편출입·상장폐지가 반영된다.

#### 구현 명세
- **입력**: `symbols.yaml`의 유니버스 설정(소스 + ETF 코드). 날짜 범위 불필요
- **출력**: pandas DataFrame — 컬럼: `ticker, company_name, sector, market, index_source, weight, source` → `raw_universe`
- **source 필드**: `"IVV"` / `"QQQ"` (출처 ETF)
- **소스(pluggable)**: `etf_holdings`(기본 — 운용사 공시 CSV) / `api`(FMP·Finnhub) / `wikipedia`
- **캐시 폴백**: 수집 실패 시 직전 성공 `raw_universe`를 유지(TRUNCATE 안 함) — 지수 멤버십은 분기 단위로만 바뀌므로 하루 지난 목록도 안전
- **에러 처리**: 실패 로그 기록 후 캐시 폴백, 파이프라인 계속 (FR-010)

#### 핵심 함수
```python
def fetch_universe(config) -> pd.DataFrame
```

### 2. yfinance_collector.py

#### 목적
`raw_universe`의 ticker 목록(universe_collector가 산출)에 있는 미국 주식의 일별 OHLCV 데이터를 수집한다.

#### 구현 명세
- **입력**: `raw_universe`의 ticker 목록(universe_collector가 수집 — `symbols.yaml`에 개별 종목을 나열하는 게 **아님**), 날짜 범위
- **출력**: pandas DataFrame — 컬럼: `symbol, date, open, high, low, close, adj_close, volume, source`
- **source 필드**: `"yfinance"`
- **API**: yfinance (비공식, 요청 제한 없음)
- **에러 처리**: 종목별 try-except, 실패 시 로그 기록 후 다음 종목 계속 (FR-010)

#### 핵심 함수
```python
def collect_stock_data(symbols: list, start_date: str, end_date: str) -> pd.DataFrame
```

### 3. fred_collector.py

#### 목적
FRED API에서 경제지표(연방기금금리, CPI, GDP 등)를 수집한다.

#### 구현 명세
- **입력**: `symbols.yaml`의 지표 코드 목록, 날짜 범위
- **출력**: pandas DataFrame — 컬럼: `indicator_code, date, value, source`
- **source 필드**: `"FRED"`
- **API**: FRED API (120회/분 제한)
- **에러 처리**: 지표별 try-except, 실패 시 로그 기록 후 계속 (FR-010)
- **API 키**: `.env`에서 `config.py`를 통해 로드

#### 핵심 함수
```python
def collect_economic_data(indicators: list, start_date: str, end_date: str) -> pd.DataFrame
```

### 4. 파이프라인 로거 연동

#### 목적
수집 단계 결과를 기록: API 호출별 성공/실패/건수 (FR-010).

#### 로그 형식
```
[2026-05-12 10:30:00] [collect] [success] yfinance — AAPL: 1,260건
[2026-05-12 10:30:05] [collect] [failure] FRED — INVALID_CODE: API error 400
```

---

## 설계 결정 사항

| 결정 | 선택 | 이유 |
|---|---|---|
| 종목별 에러 처리 | 로그 & 건너뜀 | 하나의 실패가 전체 수집을 차단하면 안 됨 (FR-010) |
| 자동 재시도 없음 | 로그만 기록 | 학습용 프로젝트, 수동 재실행으로 충분 |
| 중간 결과물 형태 | pandas DataFrame | 표준 데이터 구조, 검증 및 BigQuery 적재에 용이 |
| 날짜 범위 설정 | CLI 인자 또는 yaml | 전체 이력/증분 실행 모두 유연하게 대응 |

---

## 선행 조건 및 의존성

- Phase 1 완료 (config.py, logger.py 동작 확인)
- `yfinance` 패키지 설치
- `fredapi` 패키지 설치
- `.env`에 FRED API 키 설정
- `config/symbols.yaml`에 유니버스 소스 설정 + 지표 목록 작성 (개별 종목 나열 없음)

---

## 개발 시 주의사항

- yfinance는 비공식 API — 예고 없이 변경될 수 있음
- FRED 요청 제한: 120회/분 — 지표 ~10개 수준에서는 문제 없음
- `collected_at` 타임스탬프는 raw 데이터 추적용으로 자동 추가
- 전체 종목 실행 전 2~3개 종목으로 먼저 테스트

---

## 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-05-12 | 최초 작성 |
| 2026-07-06 | 동적 유니버스 추가: `universe_collector.py`(ETF 보유종목 IVV+QQQ → `raw_universe`, yfinance보다 먼저 실행); yfinance 수집 대상을 `raw_universe`의 ticker 목록으로 변경 |
