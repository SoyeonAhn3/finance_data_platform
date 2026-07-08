"""star_schema — raw 데이터를 Star Schema(Fact/Dim)로 변환하고 Mart View 생성 (Phase 4).

ELT 패턴(ADR-001): 변환은 BigQuery Standard SQL 이 수행하고, 이 모듈은 실행을 지휘한다.

흐름 (의존 순서):
    dim_date / dim_symbol / dim_indicator      ← 먼저 생성 (Fact 가 inner JOIN)
        ↓
    fact_daily_price / fact_economic_indicator ← Dim 에 inner JOIN → 명단 밖·오타·null 탈락
        ↓
    mart_performance / mart_risk / mart_macro  ← sql/mart_views.sql 실행

규약:
    - Fact/Dim: CTAS (`CREATE OR REPLACE TABLE AS SELECT`) 로 매 실행 재생성 (Full Refresh)
    - 대리키: FARM_FINGERPRINT(자연키) — BigQuery 엔 AUTOINCREMENT 없음 → 같은 자연키=같은 키
    - 중복 제거: QUALIFY ROW_NUMBER() ... = 1 (최신 collected_at 우선)
    - CTAS 는 setup.sql 의 PK/FK(NOT ENFORCED) 선언을 재정의로 지우지만, NOT ENFORCED =
      문서용이라 MVP 영향 없음.

단독 실행(테스트):
    python -m src.transformers.star_schema
"""
from __future__ import annotations

from google.cloud import bigquery

from src.utils import config
from src.utils.bq_client import get_bigquery_client
from src.utils.logger import get_logger, log_stage

logger = get_logger(__name__)

MART_VIEWS = ["mart_performance", "mart_risk", "mart_macro"]


# ── 내부 헬퍼 ───────────────────────────────────────────────
def _run_ctas(
    client: bigquery.Client,
    sql: str,
    table_name: str,
    params: list | None = None,
) -> int:
    """CTAS 쿼리를 실행하고 생성된 테이블 행 수를 돌려준다.

    CREATE OR REPLACE TABLE ... AS SELECT 는 num_dml_affected_rows 가 없으므로,
    실행 후 테이블 메타데이터(num_rows)로 건수를 읽는다.
    """
    job_config = bigquery.QueryJobConfig(query_parameters=params or [])
    client.query(sql, job_config=job_config).result()
    n = client.get_table(f"{config.BQ_DATASET}.{table_name}").num_rows
    log_stage(logger, "transform", "success", count=n, message=table_name)
    return n


# ── 1) Dimension ───────────────────────────────────────────
def populate_dim_date(
    client: bigquery.Client,
    start_date: str | None = None,
    end_date: str | None = None,
) -> int:
    """dim_date 생성. raw 에서 뽑는 게 아니라 날짜 범위를 생성한다.

    start_date~end_date(기본: config 시작일~오늘)의 모든 날짜를 한 행씩 만든다.
    비거래일(주말)도 포함하여 Fact 조인 시 날짜 누락이 없게 한다.
    """
    start_date = start_date or config.DATE_RANGE_START
    sql = f"""
    CREATE OR REPLACE TABLE `{config.BQ_DATASET}.dim_date` AS
    SELECT
      CAST(FORMAT_DATE('%Y%m%d', d) AS INT64) AS date_key,   -- 2024-01-05 → 20240105
      d                        AS full_date,
      EXTRACT(YEAR    FROM d)  AS year,
      EXTRACT(QUARTER FROM d)  AS quarter,
      EXTRACT(MONTH   FROM d)  AS month,
      FORMAT_DATE('%A', d)     AS day_of_week,               -- Monday … Sunday
      -- BigQuery DAYOFWEEK: 일=1 … 토=7 → 평일(월~금)=2~6. 공휴일 캘린더는 MVP 제외
      EXTRACT(DAYOFWEEK FROM d) BETWEEN 2 AND 6 AS is_trading_day
    FROM UNNEST(GENERATE_DATE_ARRAY(
      DATE(@start_date),
      IFNULL(SAFE.PARSE_DATE('%Y-%m-%d', @end_date), CURRENT_DATE())  -- end 없으면 오늘까지
    )) AS d
    """
    params = [
        bigquery.ScalarQueryParameter("start_date", "STRING", start_date),
        bigquery.ScalarQueryParameter("end_date", "STRING", end_date),
    ]
    return _run_ctas(client, sql, "dim_date", params)


def populate_dim_symbol(client: bigquery.Client) -> int:
    """dim_symbol 생성. 소스는 raw_universe(승인 명단) — raw_daily_price 가 아님.

    두 지수(S&P500·Nasdaq100)에 겹치는 티커는 GROUP BY 로 1행으로 합친다.
    이 명단이 Fact inner JOIN 의 필터 기준이 된다.
    """
    sql = f"""
    CREATE OR REPLACE TABLE `{config.BQ_DATASET}.dim_symbol` AS
    SELECT
      FARM_FINGERPRINT(ticker) AS symbol_key,   -- 같은 티커 → 항상 같은 정수 키
      ticker,
      ANY_VALUE(company_name)  AS company_name,  -- 중복 행 중 대표값
      ANY_VALUE(sector)        AS sector,
      ANY_VALUE(market)        AS market
    FROM (
      SELECT
        UPPER(TRIM(ticker))    AS ticker,        -- 공백·대소문자 정규화
        company_name,
        sector,
        COALESCE(market, 'US') AS market         -- dim_symbol.market 은 NOT NULL
      FROM `{config.BQ_DATASET}.raw_universe`
      WHERE ticker IS NOT NULL AND TRIM(ticker) != ''
    )
    GROUP BY ticker                              -- 두 지수 중복 티커 → 1행
    """
    return _run_ctas(client, sql, "dim_symbol")


def populate_dim_indicator(client: bigquery.Client) -> int:
    """dim_indicator 생성. 소스는 config/symbols.yaml 의 indicators seed.

    지표 메타(이름·단위)는 raw 에 없고 YAML 에만 있으므로, config.INDICATORS 를
    쿼리 파라미터(문자열 배열 4개)로 넘겨 WITH OFFSET 으로 위치 매칭(zip)한다.
    파라미터를 쓰는 이유: 문자열을 SQL 에 직접 붙일 때의 인젝션·따옴표 문제 회피.
    """
    indicators = config.INDICATORS
    if not indicators:
        raise RuntimeError("config/symbols.yaml 의 indicators 가 비어 있습니다 (dim_indicator seed 없음)")

    sql = f"""
    CREATE OR REPLACE TABLE `{config.BQ_DATASET}.dim_indicator` AS
    SELECT
      FARM_FINGERPRINT(UPPER(TRIM(c))) AS indicator_key,
      UPPER(TRIM(c))                   AS indicator_code,
      n                                AS indicator_name,
      s                                AS source,
      u                                AS unit
    FROM UNNEST(@codes) AS c WITH OFFSET AS o1
    JOIN UNNEST(@names) AS n WITH OFFSET AS o2 ON o1 = o2
    JOIN UNNEST(@units) AS u WITH OFFSET AS o3 ON o1 = o3
    JOIN UNNEST(@srcs)  AS s WITH OFFSET AS o4 ON o1 = o4
    """
    params = [
        bigquery.ArrayQueryParameter("codes", "STRING", [i["code"] for i in indicators]),
        bigquery.ArrayQueryParameter("names", "STRING", [i["name"] for i in indicators]),
        bigquery.ArrayQueryParameter("units", "STRING", [i.get("unit") for i in indicators]),
        bigquery.ArrayQueryParameter("srcs", "STRING", [i["source"] for i in indicators]),
    ]
    return _run_ctas(client, sql, "dim_indicator", params)


# ── 2) Fact ────────────────────────────────────────────────
def create_fact_daily_price(client: bigquery.Client) -> int:
    """fact_daily_price 생성.

    1) 정규화 + 중복 제거(QUALIFY): (종목,날짜)당 최신 수집분 1행
    2) dim_symbol/dim_date 에 inner JOIN → 명단 밖·오타·null 탈락 + 정수 키 획득
    """
    sql = f"""
    CREATE OR REPLACE TABLE `{config.BQ_DATASET}.fact_daily_price` AS
    WITH deduped AS (
      SELECT
        UPPER(TRIM(symbol)) AS ticker,
        date, open, high, low, close, adj_close, volume
      FROM `{config.BQ_DATASET}.raw_daily_price`
      WHERE symbol IS NOT NULL AND date IS NOT NULL
      QUALIFY ROW_NUMBER() OVER (
        PARTITION BY UPPER(TRIM(symbol)), date
        ORDER BY collected_at DESC
      ) = 1
    )
    SELECT
      d.date_key,
      s.symbol_key,
      p.open      AS open_price,
      p.high      AS high_price,
      p.low       AS low_price,
      p.close     AS close_price,
      p.adj_close AS adj_close,
      p.volume    AS volume,
      CURRENT_TIMESTAMP() AS loaded_at         -- CTAS 는 DEFAULT 미적용 → 직접 채움
    FROM deduped AS p
    JOIN `{config.BQ_DATASET}.dim_symbol` AS s ON p.ticker = s.ticker   -- 명단 필터
    JOIN `{config.BQ_DATASET}.dim_date`   AS d ON p.date   = d.full_date
    """
    return _run_ctas(client, sql, "fact_daily_price")


def create_fact_economic_indicator(client: bigquery.Client) -> int:
    """fact_economic_indicator 생성. fact_daily_price 와 동일 패턴(지표 버전)."""
    sql = f"""
    CREATE OR REPLACE TABLE `{config.BQ_DATASET}.fact_economic_indicator` AS
    WITH deduped AS (
      SELECT
        UPPER(TRIM(indicator_code)) AS indicator_code,
        date, value
      FROM `{config.BQ_DATASET}.raw_economic_indicator`
      WHERE indicator_code IS NOT NULL AND date IS NOT NULL AND value IS NOT NULL
      QUALIFY ROW_NUMBER() OVER (
        PARTITION BY UPPER(TRIM(indicator_code)), date
        ORDER BY collected_at DESC
      ) = 1
    )
    SELECT
      d.date_key,
      i.indicator_key,
      e.value,
      CURRENT_TIMESTAMP() AS loaded_at
    FROM deduped AS e
    JOIN `{config.BQ_DATASET}.dim_indicator` AS i ON e.indicator_code = i.indicator_code  -- seed 필터
    JOIN `{config.BQ_DATASET}.dim_date`      AS d ON e.date          = d.full_date
    """
    return _run_ctas(client, sql, "fact_economic_indicator")


# ── 3) Mart View ───────────────────────────────────────────
def create_mart_views(client: bigquery.Client) -> dict:
    """sql/mart_views.sql 을 실행해 Mart View 3종을 생성/교체한다."""
    sql_path = config.ROOT_DIR / "sql" / "mart_views.sql"
    sql = sql_path.read_text(encoding="utf-8")
    client.query(sql).result()      # 멀티 스테이트먼트 스크립트로 한 번에 실행
    result = {v: "created" for v in MART_VIEWS}
    log_stage(logger, "transform", "success", count=len(MART_VIEWS),
              message="mart views: " + ", ".join(MART_VIEWS))
    return result


# ── 오케스트레이터 ──────────────────────────────────────────
def transform_to_star_schema(client: bigquery.Client | None = None) -> dict:
    """raw → Star Schema → Mart View 전체 변환을 의존 순서대로 실행한다.

    반환: 각 단계 산출물 건수 dict (fact/dim 은 행 수, mart 는 뷰 상태).
    """
    client = client or get_bigquery_client()
    logger.info("Star Schema 변환 시작")
    result: dict = {}
    # Dim 먼저 (Fact 가 inner JOIN)
    result["dim_date"] = populate_dim_date(client)
    result["dim_symbol"] = populate_dim_symbol(client)
    result["dim_indicator"] = populate_dim_indicator(client)
    # Fact
    result["fact_daily_price"] = create_fact_daily_price(client)
    result["fact_economic_indicator"] = create_fact_economic_indicator(client)
    # Mart View
    result["mart_views"] = create_mart_views(client)
    logger.info("Star Schema 변환 완료: %s", result)
    return result


if __name__ == "__main__":
    counts = transform_to_star_schema()
    print("변환 결과:")
    for k, v in counts.items():
        print(f"  {k}: {v}")
