-- ============================================================
--  setup.sql — BigQuery 스키마 초기화 (finance_db)
--  빈 테이블 10개를 만든다 (raw 3 + dim 3 + fact 2 + 운영 2). 데이터는 이후 Phase 에서 채워진다.
--
--  실행 방법 (키 발급 후 택1):
--    1) python -m src.utils.bq_client --init        (권장)
--    2) bq query --use_legacy_sql=false --location=US < sql/setup.sql
--
--  BigQuery 규약 (docs/data_dictionary.md 0장):
--    - 대리키: FARM_FINGERPRINT(자연키) → 변환 단계에서 채움 (여긴 컬럼만 정의)
--    - 로그 ID: DEFAULT GENERATE_UUID()
--    - PRIMARY/FOREIGN KEY: 반드시 NOT ENFORCED (BigQuery는 강제 안 함, 선언만)
--    - UNIQUE: 미지원 → 변환 시 QUALIFY ROW_NUMBER 로 중복 제거
--    - raw 컬럼은 nullable (source/collected_at 만 NOT NULL)
--  ※ FK 는 문서화 목적(NOT ENFORCED). BigQuery 에디션이 미지원이면 제거해도 됨.
-- ============================================================

CREATE SCHEMA IF NOT EXISTS `finance_db`;

-- ─────────────────────────────────────────────
--  1) RAW 레이어 — API 원본을 "일단 다 받는다"
--     (컬럼 대부분 nullable — 더러운 데이터도 흡수)
-- ─────────────────────────────────────────────

-- 유니버스: S&P500+Nasdaq100 구성종목 명단 (dim_symbol 의 소스)
CREATE TABLE IF NOT EXISTS `finance_db.raw_universe` (
  ticker        STRING,
  company_name  STRING,
  sector        STRING,           -- GICS 섹터
  market        STRING,           -- US
  index_source  STRING,           -- SP500 / NASDAQ100
  weight        NUMERIC,          -- ETF 내 비중 (참고용)
  source        STRING    NOT NULL,                              -- IVV / QQQ
  collected_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP() NOT NULL
);

-- 일별 주가 (yfinance)
CREATE TABLE IF NOT EXISTS `finance_db.raw_daily_price` (
  symbol        STRING,
  date          DATE,
  open          NUMERIC,
  high          NUMERIC,
  low           NUMERIC,
  close         NUMERIC,
  adj_close     NUMERIC,
  volume        INT64,
  source        STRING    NOT NULL,                              -- yfinance
  collected_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP() NOT NULL
);

-- 경제지표 (FRED)
CREATE TABLE IF NOT EXISTS `finance_db.raw_economic_indicator` (
  indicator_code STRING,          -- 예: FEDFUNDS
  date           DATE,
  value          NUMERIC,
  source         STRING    NOT NULL,                             -- FRED
  collected_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP() NOT NULL
);

-- ─────────────────────────────────────────────
--  2) DIMENSION 레이어 — 분석의 축 (승인 명단)
--     (변환 단계에서 CREATE OR REPLACE ... AS SELECT 로 채워짐)
-- ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS `finance_db.dim_date` (
  date_key       INT64  NOT NULL,   -- YYYYMMDD
  full_date      DATE   NOT NULL,
  year           INT64  NOT NULL,
  quarter        INT64  NOT NULL,
  month          INT64  NOT NULL,
  day_of_week    STRING NOT NULL,
  is_trading_day BOOL   NOT NULL,
  PRIMARY KEY (date_key) NOT ENFORCED
);

CREATE TABLE IF NOT EXISTS `finance_db.dim_symbol` (
  symbol_key    INT64  NOT NULL,    -- FARM_FINGERPRINT(ticker)
  ticker        STRING NOT NULL,
  company_name  STRING,
  sector        STRING,
  market        STRING NOT NULL,
  PRIMARY KEY (symbol_key) NOT ENFORCED
);

CREATE TABLE IF NOT EXISTS `finance_db.dim_indicator` (
  indicator_key  INT64  NOT NULL,   -- FARM_FINGERPRINT(indicator_code)
  indicator_code STRING NOT NULL,
  indicator_name STRING NOT NULL,
  source         STRING NOT NULL,
  unit           STRING,
  PRIMARY KEY (indicator_key) NOT ENFORCED
);

-- ─────────────────────────────────────────────
--  3) FACT 레이어 — 측정값
-- ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS `finance_db.fact_daily_price` (
  date_key    INT64   NOT NULL,
  symbol_key  INT64   NOT NULL,
  open_price  NUMERIC,
  high_price  NUMERIC,
  low_price   NUMERIC,
  close_price NUMERIC,
  adj_close   NUMERIC,
  volume      INT64,
  loaded_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP() NOT NULL,
  PRIMARY KEY (date_key, symbol_key) NOT ENFORCED,
  FOREIGN KEY (date_key)   REFERENCES `finance_db.dim_date`(date_key)     NOT ENFORCED,
  FOREIGN KEY (symbol_key) REFERENCES `finance_db.dim_symbol`(symbol_key) NOT ENFORCED
);

CREATE TABLE IF NOT EXISTS `finance_db.fact_economic_indicator` (
  date_key      INT64   NOT NULL,
  indicator_key INT64   NOT NULL,
  value         NUMERIC NOT NULL,
  loaded_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP() NOT NULL,
  PRIMARY KEY (date_key, indicator_key) NOT ENFORCED,
  FOREIGN KEY (date_key)      REFERENCES `finance_db.dim_date`(date_key)           NOT ENFORCED,
  FOREIGN KEY (indicator_key) REFERENCES `finance_db.dim_indicator`(indicator_key) NOT ENFORCED
);

-- ─────────────────────────────────────────────
--  4) OPERATIONS 레이어 — 실행/품질 로그 (Python 이 append)
-- ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS `finance_db.pipeline_execution_log` (
  log_id        STRING    DEFAULT GENERATE_UUID() NOT NULL,
  execution_id  STRING    NOT NULL,          -- 배치 1회 = 1 UUID
  stage         STRING    NOT NULL,          -- universe/collect/validate/load/transform
  status        STRING    NOT NULL,          -- success/failure/warning
  record_count  INT64,
  error_message STRING,
  started_at    TIMESTAMP NOT NULL,
  ended_at      TIMESTAMP,
  PRIMARY KEY (log_id) NOT ENFORCED
);

CREATE TABLE IF NOT EXISTS `finance_db.data_quality_log` (
  check_id      STRING    DEFAULT GENERATE_UUID() NOT NULL,
  execution_id  STRING    NOT NULL,          -- pipeline_execution_log 연계
  check_type    STRING    NOT NULL,          -- missing/outlier/duplicate/completeness/universe
  target_table  STRING    NOT NULL,
  target_field  STRING,
  result        STRING    NOT NULL,          -- pass/warn/fail
  detail        STRING,
  checked_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP() NOT NULL,
  PRIMARY KEY (check_id) NOT ENFORCED
);
