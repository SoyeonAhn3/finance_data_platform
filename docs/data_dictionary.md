# 데이터 사전 (Data Dictionary) — finance_data_platform

> raw 데이터가 정제·가공을 거쳐 어떤 테이블에 어떤 데이터로 들어가는지 정의하는 문서 (FR-011)

| 항목 | 내용 |
|---|---|
| 프로젝트 | finance_data_platform |
| 대상 플랫폼 | **Google BigQuery** |
| 데이터셋 | `finance_db` |
| 적재 방식 | **Full Refresh** (`WRITE_TRUNCATE` — 매 실행 통째로 교체) |
| 대리키 생성 | **`FARM_FINGERPRINT(자연키)`** (결정적 정수 키) |
| 로그 ID 생성 | `GENERATE_UUID()` |
| 유니버스 | **S&P 500 + Nasdaq-100** (구성종목을 매 실행 수집 — 기본 `wikipedia`, `etf_holdings` 옵션) |
| 주가 소스 | **Alpha Vantage** (기본, 무료 키) / `yfinance` (옵션) |
| 스케줄링 | GitHub Actions (cron + `workflow_dispatch`) |
| 최종 수정 | 2026-07-08 |

> 이 문서는 **BigQuery 기준 정본**입니다. 기획서·Phase 문서·README도 BigQuery 기준으로 개정 완료되었습니다.

---

## 목차

- [0. BigQuery 규약](#0-bigquery-규약)
- [1. 데이터 흐름](#1-데이터-흐름)
- [2. 정제·가공 규칙](#2-정제가공-규칙)
- [3. 테이블 정의](#3-테이블-정의)
- [4. 데이터 소스 매핑](#4-데이터-소스-매핑)
- [5. Mart 계산 공식](#5-mart-계산-공식)
- [6. 정합성 규칙](#6-정합성-규칙)
- [7. 테이블 관계](#7-테이블-관계)
- [8. 유니버스 & symbols.yaml](#8-유니버스--symbolsyaml)

---

## 0. BigQuery 규약

이 프로젝트에서 지켜야 하는 BigQuery 규약입니다.

| 항목 | 규약 | 이유 |
|---|---|---|
| 대리키 | `FARM_FINGERPRINT(자연키)` → INT64 | BigQuery엔 AUTOINCREMENT/시퀀스 없음. 결정적 해시라 Full Refresh에도 키가 안 바뀜 |
| 로그 ID | `GENERATE_UUID()` → STRING | 자연키 없는 이벤트 로그용 |
| PRIMARY KEY | `PRIMARY KEY(...) NOT ENFORCED` | BigQuery는 PK를 강제하지 않음(선언만 가능). 안 붙이면 문법 오류 |
| FOREIGN KEY | `FOREIGN KEY(...) NOT ENFORCED` | 참조 무결성은 변환 시 JOIN(inner)으로 보장 |
| UNIQUE | **미지원** | `SELECT DISTINCT` + 품질검증으로 대체 |
| raw 컬럼 nullable | API가 주는 컬럼은 nullable | "일단 다 받는다" 원칙 + NOT NULL이면 null 한 줄에 `WRITE_TRUNCATE` 배치 전체 실패 |
| 적재 | Load Job `WRITE_TRUNCATE` | 행 단위 `INSERT`는 BigQuery 안티패턴(쿼터·비용·스트리밍 버퍼) |
| 타입 | `STRING`/`NUMERIC`/`INT64`/`BOOL`/`TIMESTAMP` | 아래 [타입 매핑](#타입-매핑) 참고 |

### 타입 매핑

| BigQuery 타입 | 용도 | 비고 |
|---|---|---|
| `STRING` | ticker·회사명·지표코드 등 문자열 | 길이 제한 없음 |
| `NUMERIC` | 가격·지표 값 | precision 38 / scale 9 이내 |
| `INT64` (volume) | 거래량 | INT64 범위 충분 |
| `INT64` (date_key) | 날짜 키 | YYYYMMDD 8자리 정수 |
| `TIMESTAMP` | 수집/적재 시각 | UTC 기준, `DEFAULT CURRENT_TIMESTAMP()` |
| `BOOLEAN` | `BOOL` | |

---

## 1. 데이터 흐름

```
① 유니버스 수집          ② 수집            ③ 검증      ④ 적재(raw)       ⑤ 변환(star)         ⑥ Mart뷰   ⑦ 소비
Wikipedia 구성종목표   → AlphaVantage/FRED → 품질체크 →  BigQuery raw  →  dim/fact 재생성  →  분석용 View → Power BI
= S&P500+Nasdaq100       (DataFrame)     (경고만)   (WRITE_TRUNCATE)  (FARM_FINGERPRINT
  목록(명단/seed)                                                      + JOIN)
```

> ①에서 받은 구성종목 목록이 `dim_symbol`의 소스(명단)가 됩니다. 매 실행 재수집하므로 지수 편출입·상장폐지가 자동 반영됩니다. (자세히는 [8장](#8-유니버스--symbolsyaml))

### 레이어 구조

| 레이어 | 테이블/뷰 | 역할 | 정제 여부 |
|---|---|---|---|
| **Raw** | `raw_universe`, `raw_daily_price`, `raw_economic_indicator` | API 원본 보존 | ❌ 원본 그대로 |
| **Dimension** | `dim_date`, `dim_symbol`, `dim_indicator` | 분석의 축(사전/명단) | ✅ 정규화·해시키 |
| **Fact** | `fact_daily_price`, `fact_economic_indicator` | 측정값 | ✅ 정제 5종 전부 |
| **Operations** | `pipeline_execution_log`, `data_quality_log` | 실행·품질 로그 | — (Python이 기록) |
| **Mart (View)** | `mart_performance`, `mart_risk`, `mart_macro` | 분석용 계산 | 조회 시 계산 |

> **핵심 원칙**: `raw`는 API가 준 걸 그대로(지저분해도) 보존하고, **실제 정제는 `raw → fact/dim` 변환에서** 일어납니다. raw만 있으면 언제든 다시 깨끗하게 만들 수 있습니다.

---

## 2. 정제·가공 규칙

### 검증 vs 정제 — 다른 단계

| | 언제 | 무엇을 | 데이터를 바꾸나 |
|---|---|---|---|
| **검증 (validate)** | 적재 전 (Python `quality_checker`) | 결측·이상치·중복을 찾아 **경고 로그만** | ❌ 안 바꿈 |
| **정제 (transform)** | raw→star 변환 (BigQuery SQL) | 정규화·중복제거·타입변환·키매핑·무결성필터 | ✅ 여기서 정제됨 |

### 정제·가공 5종 (raw → fact)

| # | 처리 | 규칙(SQL) | 예시 |
|---|---|---|---|
| 1 | **정규화** | `UPPER(TRIM(symbol))` | `' aapl '` → `'AAPL'` |
| 2 | **중복 제거** | `QUALIFY ROW_NUMBER() OVER(PARTITION BY symbol,date ORDER BY collected_at DESC)=1` | 같은 (AAPL,1/2) 2건 → 최신 1건 |
| 3 | **타입 변환** | `CAST(... AS NUMERIC/INT64)`, 날짜→`date_key` | `"185.2"` → `185.2`, `2026-01-02` → `20260102` |
| 4 | **키 매핑** | dim(명단)에 JOIN → 대리키 획득 | `'AAPL'` → `symbol_key = -4776...` |
| 5 | **무결성 필터** | dim(명단)과 inner `JOIN` → 매칭 안 되면 제외 | 명단에 없는 `'XYZ'` 행 제외 |

### 정제 예시: 지저분한 raw → 깨끗한 fact

**입력 — `raw_daily_price` (문제 있는 데이터, raw는 nullable이라 다 들어옴):**

```
symbol  | date       | close | volume   | source   | collected_at
 aapl   | 2026-01-02 | 185.2 | 50000000 | alphavantage | 09:05    ← 소문자+공백
AAPL    | 2026-01-02 | 185.2 | 50000000 | alphavantage | 09:00    ← 정규화 후 위와 중복
XYZ     | 2026-01-02 |  10.0 | 100      | alphavantage | 09:00    ← 명단(dim_symbol)에 없음
(null)  | 2026-01-05 |  50.0 | 999      | alphavantage | 09:00    ← symbol 결측(raw는 허용)
MSFT    | 2026-01-03 |  -5.0 | 30000000 | alphavantage | 09:00    ← 음수 종가(이상치)
```

**출력 — `fact_daily_price` (정제 결과):**

```
date_key | symbol_key         | close_price | volume
20260102 | -4776...(AAPL해시)  | 185.2       | 50000000   ← ①정규화 ②중복제거로 1건
20260103 |  8823...(MSFT해시)  | -5.0        | 30000000   ← 이상치지만 경고만, 적재됨
```

- `' aapl '` + `'AAPL'` → 정규화 후 같은 종목 → **중복 제거**로 1건
- `'XYZ'` → **승인 명단(`dim_symbol`)에 없어** inner JOIN에서 탈락. `dim_symbol`은 raw가 아니라 **유니버스(명단)에서 생성**되므로, 명단 밖 종목이 진짜로 걸러집니다 ([8장](#8-유니버스--symbolsyaml)). + `data_quality_log`에 "명단 밖 종목" 경고
- `symbol=null` → 명단에 매칭 안 됨 → 제외 (raw는 nullable로 받되, dim이 null을 안 가지므로 fact에서 탈락)
- `MSFT -5.0` → 이상치로 **`data_quality_log`에 경고** 기록, 값은 적재 (막지 않음)

---

## 3. 테이블 정의

### 3.1 Raw 레이어

> raw는 "일단 다 받는다"가 원칙이라, API가 주는 컬럼(symbol/date/가격 등)은 **모두 nullable**입니다. Python이 직접 채우는 `source`/`collected_at`만 NOT NULL. (NOT NULL로 걸면 null 한 줄에 `WRITE_TRUNCATE` 배치 전체가 실패하므로, 더러운 데이터는 raw가 흡수하고 정제는 fact 단계에서 합니다.)

#### `raw_universe`

- **설명**: S&P 500 + Nasdaq-100 구성종목 명단 (매 실행 수집). **`dim_symbol`의 소스.**
- **소스**: **Wikipedia**(기본, 무료·키불필요, ticker+회사명+GICS 섹터) 또는 ETF 보유종목(IVV/QQQ) — 교체 가능([8장](#8-유니버스--symbolsyaml))
- **처리**: 없음 (원본 보존). 수집 실패 시 직전 성공 목록 유지(캐시 폴백)

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| ticker | STRING | | 종목 코드 |
| company_name | STRING | | 회사명 |
| sector | STRING | | 섹터 (GICS) |
| market | STRING | | 시장 (US) |
| index_source | STRING | | 출처 지수 (SP500 / NASDAQ100) |
| weight | NUMERIC | | ETF 내 비중 (참고용) |
| source | STRING | NOT NULL | 데이터 소스 (`wikipedia` 또는 `IVV`/`QQQ`) |
| collected_at | TIMESTAMP | NOT NULL, DEFAULT `CURRENT_TIMESTAMP()` | 수집 시각 (UTC) |

> AAPL처럼 두 지수에 다 있으면 `index_source`가 다른 2행으로 들어오고, `dim_symbol` 생성 시 DISTINCT ticker로 1개로 합쳐집니다.

#### `raw_daily_price`

- **설명**: 미국 주식 일별 OHLCV 원본
- **소스**: **Alpha Vantage**(기본) 또는 yfinance (수집 대상 = `raw_universe`의 ticker 목록)
- **처리**: 없음 (원본 + `source`, `collected_at` 추가)

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| symbol | STRING | | 종목 코드 (raw는 nullable) |
| date | DATE | | 거래일 (raw는 nullable) |
| open | NUMERIC | | 시가 |
| high | NUMERIC | | 고가 |
| low | NUMERIC | | 저가 |
| close | NUMERIC | | 종가 |
| adj_close | NUMERIC | | 수정 종가 (Alpha Vantage 무료 티어는 미제공 → NULL; mart에서 `COALESCE(adj_close, close_price)`로 대체) |
| volume | INT64 | | 거래량 |
| source | STRING | NOT NULL | 데이터 소스 (`alphavantage`/`yfinance`) |
| collected_at | TIMESTAMP | NOT NULL, DEFAULT `CURRENT_TIMESTAMP()` | 수집 시각 (UTC) |

#### `raw_economic_indicator`

- **설명**: FRED에서 수집한 경제지표 원본
- **소스**: FRED API
- **처리**: 없음 (원본 + `source`, `collected_at` 추가)

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| indicator_code | STRING | | 지표 코드 (raw는 nullable, 예: `FEDFUNDS`) |
| date | DATE | | 기준일 (raw는 nullable) |
| value | NUMERIC | | 지표 값 |
| source | STRING | NOT NULL | 데이터 소스 (`FRED`) |
| collected_at | TIMESTAMP | NOT NULL, DEFAULT `CURRENT_TIMESTAMP()` | 수집 시각 (UTC) |

---

### 3.2 Dimension 레이어

#### `dim_date`

- **설명**: 날짜 축. 유일하게 raw가 아닌 **생성** 테이블
- **소스**: `GENERATE_DATE_ARRAY('2020-01-01', CURRENT_DATE())`
- **처리**: 각 날짜에서 연/분기/월/요일 추출, 주말이면 거래일=false

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| date_key | INT64 | PK (NOT ENFORCED) | 고유 키 (YYYYMMDD) |
| full_date | DATE | NOT NULL | 전체 날짜 |
| year | INT64 | NOT NULL | 연도 |
| quarter | INT64 | NOT NULL | 분기 (1~4) |
| month | INT64 | NOT NULL | 월 (1~12) |
| day_of_week | STRING | NOT NULL | 요일 |
| is_trading_day | BOOL | NOT NULL | 거래일 여부 (MVP: 평일 체크) |

**예시 데이터:**

```
date_key | full_date  | year | quarter | month | day_of_week | is_trading_day
20260102 | 2026-01-02 | 2026 |    1    |   1   | Friday      | true
20260103 | 2026-01-03 | 2026 |    1    |   1   | Saturday    | false
```

#### `dim_symbol`

- **설명**: 종목 사전 (ticker → 대리키 + 메타데이터). **승인 명단(allowlist) 역할** — fact는 여기 있는 종목만 통과.
- **소스**: **`raw_universe`** (S&P500+Nasdaq100 구성종목). raw_daily_price가 아니라 유니버스에서 생성하는 게 핵심 — 그래야 명단 밖 종목이 fact에서 진짜로 걸러짐.
- **처리**: `WHERE ticker IS NOT NULL` → 정규화(`UPPER/TRIM`) → `DISTINCT` 중복 제거(두 지수 중복 합침) → `FARM_FINGERPRINT(ticker)`로 대리키 생성

```sql
CREATE OR REPLACE TABLE finance_db.dim_symbol AS
SELECT
  FARM_FINGERPRINT(ticker) AS symbol_key,   -- 이미 정규화된 ticker 를 해시
  ticker,
  ANY_VALUE(company_name)  AS company_name,
  ANY_VALUE(sector)        AS sector,
  ANY_VALUE(market)        AS market
FROM (
  SELECT UPPER(TRIM(ticker)) AS ticker,      -- 정규화
         company_name, sector, COALESCE(market, 'US') AS market
  FROM finance_db.raw_universe
  WHERE ticker IS NOT NULL AND TRIM(ticker) != ''
)
GROUP BY ticker;      -- ticker 기준 중복 제거 (두 지수에 걸친 종목 합침)
```

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| symbol_key | INT64 | PK (NOT ENFORCED) | `FARM_FINGERPRINT(ticker)` |
| ticker | STRING | NOT NULL | 종목 코드 (정규화됨, DISTINCT로 유일성 보장) |
| company_name | STRING | | 회사명 |
| sector | STRING | | 섹터 |
| market | STRING | NOT NULL | 시장 (US/KR) |

**예시 데이터:**

```
symbol_key         | ticker | company_name | sector     | market
-4776...(AAPL해시)  | AAPL   | Apple Inc    | Technology | US
 8823...(MSFT해시)  | MSFT   | Microsoft    | Technology | US
```

#### `dim_indicator`

- **설명**: 경제지표 사전 (지표코드 → 대리키 + 메타데이터). 승인 명단 역할.
- **소스**: **`config/symbols.yaml`의 `indicators` 목록** (손으로 관리하는 seed — 지표는 적고 안정적). raw가 아니라 명단에서 생성.
- **처리**: Python이 `config.INDICATORS`(YAML seed)를 쿼리 파라미터로 전달 → 정규화(`UPPER/TRIM`) → `FARM_FINGERPRINT(indicator_code)`로 대리키 생성 (raw 테이블에서 읽지 않음)

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| indicator_key | INT64 | PK (NOT ENFORCED) | `FARM_FINGERPRINT(indicator_code)` |
| indicator_code | STRING | NOT NULL | 지표 코드 |
| indicator_name | STRING | NOT NULL | 지표명 |
| source | STRING | NOT NULL | 출처 (FRED) |
| unit | STRING | | 단위 (%, index 등) |

**예시 데이터:**

```
indicator_key | indicator_code | indicator_name       | source | unit
 3391...       | FEDFUNDS       | Federal Funds Rate   | FRED   | %
 5502...       | CPIAUCSL       | Consumer Price Index | FRED   | index
```

---

### 3.3 Fact 레이어

#### `fact_daily_price`

- **설명**: 일별 주가 측정값 (분석의 중심)
- **소스**: `raw_daily_price` + `dim_date` + `dim_symbol` (JOIN)
- **처리**: [정제 5종](#정제가공-5종-raw--fact) 전부 적용. `dim_symbol`이 승인 명단(유니버스)이라, inner JOIN이 **명단 밖 종목·null·오타를 실제로 걸러냅니다.**
- **단위(grain)**: (날짜, 종목)당 1행

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| date_key | INT64 | FK → dim_date, NOT NULL | 날짜 키 |
| symbol_key | INT64 | FK → dim_symbol, NOT NULL | 종목 키 |
| open_price | NUMERIC | | 시가 |
| high_price | NUMERIC | | 고가 |
| low_price | NUMERIC | | 저가 |
| close_price | NUMERIC | | 종가 |
| adj_close | NUMERIC | | 수정 종가 (원본 그대로 — Alpha Vantage면 NULL. 폴백은 mart에서) |
| volume | INT64 | | 거래량 |
| loaded_at | TIMESTAMP | NOT NULL, DEFAULT `CURRENT_TIMESTAMP()` | 적재 시각 |

**예시 데이터:**

```
date_key | symbol_key        | open_price | close_price | volume   | loaded_at
20260102 | -4776...(AAPL해시) | 184.0      | 185.2       | 50000000 | (적재시각)
```

**변환 SQL (핵심):**

```sql
CREATE OR REPLACE TABLE finance_db.fact_daily_price AS
WITH deduped AS (                                              -- ① 정규화 + 중복 제거
  SELECT UPPER(TRIM(symbol)) AS ticker,
         date, open, high, low, close, adj_close, volume
  FROM finance_db.raw_daily_price
  WHERE symbol IS NOT NULL AND date IS NOT NULL
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY UPPER(TRIM(symbol)), date ORDER BY collected_at DESC
  ) = 1
)
SELECT                                                         -- ② 키 매핑 + 무결성 필터(inner JOIN)
  d.date_key,                                                  -- dim_date JOIN 으로 획득
  s.symbol_key,                                                -- dim_symbol JOIN 으로 획득
  p.open AS open_price, p.high AS high_price, p.low AS low_price,
  p.close AS close_price, p.adj_close, p.volume,
  CURRENT_TIMESTAMP() AS loaded_at
FROM deduped p
JOIN finance_db.dim_symbol s ON p.ticker = s.ticker           -- 명단 밖·오타·null 탈락
JOIN finance_db.dim_date   d ON p.date   = d.full_date;       -- 날짜 키 + 범위 필터
```

#### `fact_economic_indicator`

- **설명**: 경제지표 측정값
- **소스**: `raw_economic_indicator` + `dim_date` + `dim_indicator` (JOIN)
- **처리**: 동일 패턴 (`indicator_code` → `indicator_key` 매핑, 명단 밖 지표 제외)
- **단위(grain)**: (날짜, 지표)당 1행

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| date_key | INT64 | FK → dim_date, NOT NULL | 날짜 키 |
| indicator_key | INT64 | FK → dim_indicator, NOT NULL | 지표 키 |
| value | NUMERIC | NOT NULL | 지표 값 |
| loaded_at | TIMESTAMP | NOT NULL, DEFAULT `CURRENT_TIMESTAMP()` | 적재 시각 |

**예시 데이터:**

```
date_key | indicator_key      | value | loaded_at
20260102 | 3391...(FEDFUNDS)  | 5.33  | (적재시각)
```

---

### 3.4 Operations 레이어

> raw에서 오는 게 아니라, 파이프라인 실행 중 Python이 기록합니다.

#### `pipeline_execution_log`

- **설명**: 각 단계(수집/검증/적재/변환)의 성공/실패/건수 기록 (FR-010)

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| log_id | STRING | PK, DEFAULT `GENERATE_UUID()` | 고유 ID |
| execution_id | STRING | NOT NULL | 실행 ID (배치 1회 = 1 UUID) |
| stage | STRING | NOT NULL | 단계 (universe/collect/validate/load/transform) |
| status | STRING | NOT NULL | 상태 (success/failure/warning) |
| record_count | INT64 | | 처리 건수 |
| error_message | STRING | | 에러 메시지 |
| started_at | TIMESTAMP | NOT NULL | 시작 시각 |
| ended_at | TIMESTAMP | | 종료 시각 |

**예시 데이터:**

```
log_id  | execution_id | stage     | status  | record_count | started_at
a1b1... | run-0708     | universe  | success | 517          | 08:59:00
a1b2... | run-0708     | collect   | success | 1900         | 09:00:00   ← max_symbols=20 상한 적용
a1b3... | run-0708     | load      | success | 1900         | 09:02:00
a1b4... | run-0708     | transform | success | 2054         | 09:03:00   ← fact 2종 합계(1900+154)
```

#### `data_quality_log`

- **설명**: 결측/이상치/중복/완전성 검증 결과 (FR-009)

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| check_id | STRING | PK, DEFAULT `GENERATE_UUID()` | 고유 ID |
| execution_id | STRING | NOT NULL | 실행 ID (`pipeline_execution_log` 연계) |
| check_type | STRING | NOT NULL | 검증 유형 (missing/outlier/duplicate/completeness/universe) |
| target_table | STRING | NOT NULL | 대상 테이블 |
| target_field | STRING | | 대상 필드 |
| result | STRING | NOT NULL | 결과 (pass/warn/fail) |
| detail | STRING | | 상세 내용 |
| checked_at | TIMESTAMP | NOT NULL, DEFAULT `CURRENT_TIMESTAMP()` | 검증 시각 |

**예시 데이터:**

```
check_id | execution_id | check_type   | target_table    | result | detail
c7d8...  | run-0706     | outlier      | raw_daily_price | warn   | MSFT close=-5.0 (음수)
c7d9...  | run-0706     | duplicate    | raw_daily_price | warn   | (AAPL,2026-01-02) 2건
c7da...  | run-0706     | completeness | raw_daily_price | warn   | AAPL 0건 (상장폐지 의심)
c7db...  | run-0706     | universe     | raw_daily_price | warn   | XYZ 명단 밖 종목 → 제외
```

---

### 3.5 Mart 레이어 (View)

> 테이블이 아니라 **View** — 데이터를 저장하지 않고 조회할 때마다 fact를 읽어 계산합니다. fact가 갱신되면 자동으로 최신 반영됩니다.
>
> **가격 기준**: 세 뷰 모두 `COALESCE(adj_close, close_price)`를 씁니다 — 수정종가가 NULL(Alpha Vantage 무료)이면 종가로 대체하여 수익률·변동성·상관계수가 계속 계산됩니다.

#### `mart_performance`

- **기반**: `fact_daily_price` + `dim_symbol` + `dim_date`
- **계산**: `LAG()`로 일간/주간/월간 수익률, 누적 수익률
- **용도**: 종목 성과 비교

**예시 (조회 시 계산 결과):**

```
date       | ticker | close_price | daily_return
2026-01-02 | AAPL   | 185.2       | +1.20%
2026-01-05 | AAPL   | 187.4       | +1.19%
```

#### `mart_risk`

- **기반**: `fact_daily_price` + `dim_symbol`
- **계산**: 연율화 변동성(`STDDEV_SAMP × √252`), 연율화 평균수익, 최대 낙폭 — **종목당 1행 요약**. *베타는 벤치마크 시계열이 필요 → v2*
- **용도**: 리스크 분석

#### `mart_macro`

- **기반**: `fact_economic_indicator` + `fact_daily_price` + `dim_date`
- **계산**: 지표를 거래일 단위로 forward-fill(월간 지표 대응) → 전 종목 평균수익률(**시장 프록시**)과 `CORR()` — **지표당 1행**
- **용도**: 매크로 경제 분석

---

## 4. 데이터 소스 매핑

| API/소스 | 수집 데이터 | → Raw 테이블 | → 대상 테이블 | 필수 |
|---|---|---|---|---|
| **Wikipedia (기본) / ETF 보유종목** | S&P500+Nasdaq100 구성종목·회사명·섹터 | `raw_universe` | `dim_symbol` | ✅ |
| **Alpha Vantage (기본) / yfinance** | 미국 주식 일별 OHLCV | `raw_daily_price` | `fact_daily_price` | ✅ |
| **FRED API** | 경제지표 (금리, CPI 등) | `raw_economic_indicator` | `fact_economic_indicator` | ✅ |
| **symbols.yaml (indicators)** | 지표명·단위 (seed) | — | `dim_indicator` | ✅ |
| Alpha Vantage | 기술지표 (RSI, MACD) | `raw_technical_indicator` | — | ❌ (v2) |
| KRX/공공데이터 | 한국 주가 | `raw_daily_price` (market=KR) | `fact_daily_price` | ❌ (v2) |

---

## 5. Mart 계산 공식

> 아래 `px`는 `COALESCE(adj_close, close_price)`(수정종가 우선, 없으면 종가). 실제 정의는 `sql/mart_views.sql`.

### 일간/주간/월간 수익률 (mart_performance)

```sql
px / NULLIF(LAG(px, 1)  OVER w, 0) - 1  AS daily_return    -- 전 거래일 대비
px / NULLIF(LAG(px, 5)  OVER w, 0) - 1  AS weekly_return   -- 5거래일 전(≈1주)
px / NULLIF(LAG(px, 21) OVER w, 0) - 1  AS monthly_return  -- 21거래일 전(≈1개월)
-- WINDOW w AS (PARTITION BY symbol_key ORDER BY full_date)
```
`LAG(px, n)`은 n칸 앞(과거) 행의 값. `NULLIF(x, 0)`으로 0 나누기 방지.

### 누적 수익률 (mart_performance)

```sql
px / NULLIF(FIRST_VALUE(px) OVER w, 0) - 1  AS cumulative_return
```
기간 첫날 대비 현재까지의 총 변화율.

### 리스크 지표 (mart_risk) — 종목당 1행 (`GROUP BY ticker`)

```sql
STDDEV_SAMP(daily_return) * SQRT(252)   AS annualized_volatility  -- 연율화 변동성
AVG(daily_return)          * 252         AS annualized_return      -- 연율화 평균수익
MIN(px / NULLIF(running_peak, 0) - 1)   AS max_drawdown            -- 고점 대비 최대 낙폭
-- running_peak = MAX(px) OVER (PARTITION BY symbol_key ORDER BY full_date)
```
`252` = 연간 거래일 수(연율화 관행). 최대낙폭 = 누적 최고가 대비 하락폭의 최솟값.

### 지표-시장 상관 (mart_macro) — 지표당 1행

```sql
-- 1) 시장 프록시: 날짜별 전 종목 평균 수익률(market_return)
-- 2) 지표를 거래일 단위로 forward-fill: LAST_VALUE(value IGNORE NULLS) OVER (...)
CORR(indicator_value, market_return)  AS corr_with_market_return
```
월간 지표(CPI 등)를 거래일마다 이어붙인(forward-fill) 뒤, 시장 수익률과의 상관계수(-1 ~ +1)를 계산. 금리·물가와 시장이 같이 움직이는지 반대인지 측정.

---

## 6. 정합성 규칙

| ID | 규칙 | 대상 | 보장 방법 (BigQuery) |
|---|---|---|---|
| IR-001 | 필수 필드 NOT NULL | fact `date_key`, `symbol_key` | NOT NULL 제약 + 변환 시 결측 키 행 제외 |
| IR-002 | 날짜-종목 복합 유니크 | `fact_daily_price` (date_key+symbol_key) | UNIQUE 미지원 → `QUALIFY ROW_NUMBER()`로 중복 제거 |
| IR-003 | 날짜-지표 복합 유니크 | `fact_economic_indicator` | 동일 (QUALIFY 중복 제거) |
| IR-004 | FK 참조 무결성 | fact → dim 모든 FK | inner `JOIN` — dim(승인 명단)에 없으면 fact에서 제외. dim이 raw가 아닌 **유니버스/seed에서 생성**되므로 명단 밖 종목이 실제로 걸러짐 |
| IR-005 | 수집-적재 건수 일치 | raw 건수 = API 수집 건수 | Python에서 비교 (NFR-008), 불일치 시 경고 |
| IR-006 | 가격 양수 | `raw_daily_price.close > 0` | `quality_checker` 검증 (경고, 막지 않음) |
| IR-007 | date_key 형식 | `dim_date.date_key` YYYYMMDD 8자리 | `CAST(FORMAT_DATE('%Y%m%d', d) AS INT64)` |
| IR-008 | 승인 종목 완전성 | 명단 종목의 수집 0건 | `completeness` 검증 → 상폐 의심 경고 (FR-009) |

---

## 7. 테이블 관계

| 소스 | 대상 | 관계 | 연결 키 |
|---|---|---|---|
| `dim_symbol` | `raw_universe` | (파생) | ticker — dim_symbol이 raw_universe에서 생성됨 |
| `fact_daily_price` | `dim_date` | N:1 | date_key |
| `fact_daily_price` | `dim_symbol` | N:1 | symbol_key |
| `fact_economic_indicator` | `dim_date` | N:1 | date_key |
| `fact_economic_indicator` | `dim_indicator` | N:1 | indicator_key |
| `data_quality_log` | `pipeline_execution_log` | N:1 | execution_id |

```
  raw_universe ──(파생)──> dim_symbol ──┐
                                        │
        dim_date ──┐                    │
                   ├──> fact_daily_price ┘
                   │
                   ├──> fact_economic_indicator ── dim_indicator
                   │
        (dim_date는 두 fact가 공유)

  pipeline_execution_log ──< data_quality_log   (execution_id)
```

---

## 8. 유니버스 & symbols.yaml

### 동적 유니버스 — 명단을 소스에서 받아온다

분석 대상은 **S&P 500 + Nasdaq-100**입니다. 종목을 손으로 나열하지 않고, **구성종목 목록을 매 실행마다 수집**합니다. 소스는 교체 가능(pluggable):

| 소스 | 설명 |
|---|---|
| **`wikipedia`** (기본) | Wikipedia 구성종목 표 — 무료·키 불필요, ticker+회사명+GICS 섹터 포함 |
| `etf_holdings` (옵션) | 운용사 공시 보유종목 (S&P500=IVV/BlackRock, Nasdaq100=QQQ/Invesco) — ETF 내 비중 포함 |

- **캐시 폴백**: 수집 실패 시 `raw_universe`를 직전 성공 목록으로 유지(TRUNCATE 안 함). 지수 멤버십은 분기마다 바뀌므로 하루 캐시는 문제없음.
- 규모: 두 지수 합쳐 ~510–530 유니크 종목(겹침 많음). BigQuery 무료티어 여유. (현재는 `max_symbols`로 실행당 수집 종목 수를 제한)

### 편출입·상장폐지는 자동 처리

매 실행 구성종목을 재수집하므로:
- 종목이 지수에서 빠지면(상폐·편출) → 다음 실행 명단에 없음 → `dim_symbol`에서 빠짐 → fact에서 자동 제외
- 새 종목 편입 → 자동 포함
- **사용자가 수동으로 종목을 켜고 끄는 작업이 없습니다.** (지수 제공자가 편출입 관리 대행)
- 승인 종목인데 주가 소스가 0건 반환(상폐 직후 등) → `data_quality_log`에 `completeness` 경고 (IR-008, FR-009)
- Full Refresh라 "전날 데이터가 박혀서 수동 교정"할 일이 없음 — 매 실행이 통째로 재적재

### `config/symbols.yaml` 구조

개별 종목을 나열하지 않고, **유니버스 소스 + 지표 + 설정**만 담습니다:

```yaml
universe:
  sp500:     { enabled: true, source: wikipedia, etf: IVV }
  nasdaq100: { enabled: true, source: wikipedia, etf: QQQ }
  include_extra: []      # 지수에 없지만 꼭 넣을 티커
  exclude:       []      # 강제 제외 티커 (탈출구)

indicators:              # FRED 지표는 손으로 나열 (적고 안정적) → dim_indicator seed
  - { code: FEDFUNDS, name: Federal Funds Rate,   unit: "%",   source: FRED }
  - { code: CPIAUCSL, name: Consumer Price Index, unit: index, source: FRED }

settings:
  date_range:   { start: "2020-01-01" }
  price_source: alphavantage   # 주가 소스: alphavantage(기본, 무료 키) | yfinance
  max_symbols:  20             # 실행당 수집 종목 수 상한 (0 = 무제한)
```

### 알려진 한계 — 생존 편향 (survivorship bias)

"현재 구성종목"만 분석하면, 과거에 편출·상폐된 종목(주로 부진주)이 빠져 **수익률이 실제보다 좋아 보이는 편향**이 생깁니다. 학습용에선 감수하지만, 정확히 하려면 "시점별 과거 구성종목"이 필요합니다(무료로는 확보 어려움).

---

## 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-07-06 | 최초 작성 — BigQuery 기준, FARM_FINGERPRINT 대리키 + Full Refresh 반영 |
| 2026-07-06 | 동적 유니버스(S&P500+Nasdaq100, ETF 보유종목 IVV+QQQ) 도입: `raw_universe` 신설, `dim_symbol`을 유니버스 seed에서 생성, raw 컬럼 nullable화, XYZ 예시·IR-004 정합화, `symbols.yaml` 구조 확정, IR-008(완전성) 추가 |
| 2026-07-08 | **Phase 4 구현 동기화**: 주가 소스 yfinance→**Alpha Vantage(기본)**, 유니버스 소스 ETF→**Wikipedia(기본)**, adj_close NULL 시 mart에서 **`COALESCE(adj_close, close_price)`** 폴백 명시, mart_risk 베타 제거(연율화 변동성/수익/최대낙폭), mart_macro forward-fill+시장프록시 CORR, `dim_symbol`/`fact_daily_price` 변환 SQL 실제 반영, `symbols.yaml` 예시(wikipedia/alphavantage/max_symbols) 갱신 |
