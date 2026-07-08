-- ============================================================
--  mart_views.sql — 분석용 Mart View 3종 (Phase 4)
--  Fact/Dim 위에 얹는 읽기 전용 뷰. Power BI(Phase 5)가 여기에 연결한다.
--
--  실행: src/transformers/star_schema.py 의 create_mart_views() 가
--        이 파일을 통째로 읽어 멀티 스테이트먼트로 실행한다.
--
--  공통 규약:
--    - 가격은 COALESCE(adj_close, close_price) 사용:
--      수정종가(adj_close)가 있으면 쓰고, NULL(예: Alpha Vantage 무료 티어)이면 close_price 로 대체.
--    - 수익률 분모 0 방지: NULLIF(x, 0)
--    - 계산은 전부 뷰에서 (Fact 는 원본 측정값만 저장)
-- ============================================================

-- ─────────────────────────────────────────────
--  1) mart_performance — 종목 성과 (종목 × 날짜 단위)
--     일간/주간/월간/누적 수익률
-- ─────────────────────────────────────────────
CREATE OR REPLACE VIEW `finance_db.mart_performance` AS
WITH base AS (
  SELECT
    f.symbol_key,
    s.ticker, s.company_name, s.sector,
    d.full_date, d.year, d.quarter, d.month,
    f.close_price, f.volume,
    COALESCE(f.adj_close, f.close_price) AS px   -- 수정종가 없으면 종가로 대체
  FROM `finance_db.fact_daily_price` f
  JOIN `finance_db.dim_symbol` s ON f.symbol_key = s.symbol_key
  JOIN `finance_db.dim_date`   d ON f.date_key   = d.date_key
)
SELECT
  ticker, company_name, sector,
  full_date, year, quarter, month,
  close_price,
  px AS adj_close_used,
  volume,
  px / NULLIF(LAG(px, 1)  OVER w, 0) - 1 AS daily_return,    -- 전 거래일 대비
  px / NULLIF(LAG(px, 5)  OVER w, 0) - 1 AS weekly_return,   -- 5거래일 전 대비(≈1주)
  px / NULLIF(LAG(px, 21) OVER w, 0) - 1 AS monthly_return,  -- 21거래일 전 대비(≈1개월)
  px / NULLIF(FIRST_VALUE(px) OVER w, 0) - 1 AS cumulative_return  -- 시작일 대비 누적
FROM base
WINDOW w AS (PARTITION BY symbol_key ORDER BY full_date);


-- ─────────────────────────────────────────────
--  2) mart_risk — 리스크 지표 (종목당 1행 요약)
--     연율화 변동성 / 연율화 수익 / 최대 낙폭
-- ─────────────────────────────────────────────
CREATE OR REPLACE VIEW `finance_db.mart_risk` AS
WITH prices AS (
  SELECT
    f.symbol_key, s.ticker, s.company_name, s.sector,
    d.full_date,
    COALESCE(f.adj_close, f.close_price) AS px
  FROM `finance_db.fact_daily_price` f
  JOIN `finance_db.dim_symbol` s ON f.symbol_key = s.symbol_key
  JOIN `finance_db.dim_date`   d ON f.date_key   = d.date_key
),
daily AS (
  SELECT
    ticker, company_name, sector, px,
    px / NULLIF(LAG(px) OVER w, 0) - 1 AS daily_return,   -- 일간 수익률
    MAX(px) OVER w                     AS running_peak     -- 현재까지 누적 최고가
  FROM prices
  WINDOW w AS (PARTITION BY symbol_key ORDER BY full_date)
)
SELECT
  ticker,
  ANY_VALUE(company_name) AS company_name,
  ANY_VALUE(sector)       AS sector,
  COUNT(*)                AS trading_days,
  ROUND(STDDEV_SAMP(daily_return) * SQRT(252), 4) AS annualized_volatility,  -- 연율화 변동성
  ROUND(AVG(daily_return)          * 252,       4) AS annualized_return,      -- 연율화 평균수익(근사)
  ROUND(MIN(px / NULLIF(running_peak, 0) - 1),  4) AS max_drawdown            -- 고점 대비 최대 낙폭
FROM daily
GROUP BY ticker;


-- ─────────────────────────────────────────────
--  3) mart_macro — 경제지표 ↔ 시장 상관관계 (지표당 1행)
--     시장 프록시 = 전 종목 일간수익률 평균 (등가중)
--     지표는 거래일 단위로 forward-fill (FRED 는 월간/비정기 발표)
-- ─────────────────────────────────────────────
CREATE OR REPLACE VIEW `finance_db.mart_macro` AS
WITH prices AS (
  SELECT
    f.symbol_key, d.full_date,
    COALESCE(f.adj_close, f.close_price) AS px
  FROM `finance_db.fact_daily_price` f
  JOIN `finance_db.dim_date` d ON f.date_key = d.date_key
),
stock_ret AS (   -- 종목별 일간 수익률
  SELECT
    full_date,
    px / NULLIF(LAG(px) OVER (PARTITION BY symbol_key ORDER BY full_date), 0) - 1 AS daily_return
  FROM prices
),
market AS (      -- 날짜별 시장 수익률(전 종목 평균)
  SELECT full_date, AVG(daily_return) AS market_return
  FROM stock_ret
  GROUP BY full_date
),
ind_daily AS (   -- 지표를 거래일 단위로 forward-fill
  SELECT
    d.full_date,
    i.indicator_code, i.indicator_name, i.unit,
    LAST_VALUE(e.value IGNORE NULLS) OVER (
      PARTITION BY i.indicator_key ORDER BY d.full_date
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW   -- 미래값 참조 금지(과거~현재만)
    ) AS value
  FROM `finance_db.dim_date` d
  CROSS JOIN `finance_db.dim_indicator` i               -- 모든 거래일 × 모든 지표 격자
  LEFT JOIN `finance_db.fact_economic_indicator` e       -- 발표 없는 날은 value=NULL → forward-fill
    ON e.date_key = d.date_key AND e.indicator_key = i.indicator_key
  WHERE d.is_trading_day
)
SELECT
  x.indicator_code,
  ANY_VALUE(x.indicator_name) AS indicator_name,
  ANY_VALUE(x.unit)           AS unit,
  COUNT(*)                    AS observations,
  ROUND(CORR(x.value, m.market_return), 4) AS corr_with_market_return  -- 지표값 ↔ 시장수익률 상관(-1~+1)
FROM ind_daily x
JOIN market m ON x.full_date = m.full_date
WHERE x.value IS NOT NULL AND m.market_return IS NOT NULL
GROUP BY x.indicator_code;
