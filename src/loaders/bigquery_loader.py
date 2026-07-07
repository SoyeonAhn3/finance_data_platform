"""bigquery_loader — 수집 DataFrame을 BigQuery raw 테이블에 적재.

Full Refresh (WRITE_TRUNCATE load job): 매 실행 테이블을 통째로 교체 (ADR-003).
행 단위 INSERT는 BigQuery 안티패턴이라, load job으로 DataFrame을 한 번에 올린다.

- collected_at 은 DataFrame에 없으며 BigQuery 테이블 DEFAULT(CURRENT_TIMESTAMP)로 채워진다.
- 빈 DataFrame이면 적재를 건너뛴다 → 기존 데이터 유지 (raw_universe 캐시 폴백 포함).
- 적재 건수와 DataFrame 행 수를 비교 (NFR-008).

단독 실행(테스트):
    python -m src.loaders.bigquery_loader
"""
from __future__ import annotations

import pandas as pd
from google.cloud import bigquery

from src.utils import config
from src.utils.bq_client import get_bigquery_client
from src.utils.logger import get_logger, log_stage

logger = get_logger(__name__)


def _prepare_for_load(df: pd.DataFrame) -> pd.DataFrame:
    """적재용 타입 정리.

    - 문자열 날짜를 DATE(파이썬 date)로 변환.
    - collected_at(수집 시각, UTC)을 직접 채운다. WRITE_TRUNCATE load job은
      DataFrame 기준으로 스키마를 재정의하므로, 테이블 DEFAULT에 의존하지 않고
      로더가 명시적으로 채워야 collected_at 컬럼이 유지된다.
    """
    df = df.copy()
    for col in df.columns:
        if col == "date" or col.endswith("_date"):
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.date
    if "collected_at" not in df.columns:
        df["collected_at"] = pd.Timestamp.now(tz="UTC")
    return df


def load_to_bigquery(df: pd.DataFrame, table_name: str) -> dict:
    """DataFrame을 WRITE_TRUNCATE로 적재. 빈 df면 건너뜀(기존 데이터 유지)."""
    if df is None or len(df) == 0:
        log_stage(logger, "load", "warning", count=0,
                  message=f"{table_name} 빈 데이터 → 적재 건너뜀(기존 유지)")
        return {"table": table_name, "rows": 0, "status": "skipped"}

    client = get_bigquery_client()
    table_id = f"{config.BQ_DATASET}.{table_name}"
    prepared = _prepare_for_load(df)
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    try:
        job = client.load_table_from_dataframe(prepared, table_id, job_config=job_config)
        job.result()                     # 업로드 완료 대기
        loaded = job.output_rows         # load job이 보고한 적재 행 수

        # 정합성 체크 (NFR-008): 적재 건수 == DataFrame 행 수
        if loaded != len(df):
            log_stage(logger, "load", "warning", count=loaded,
                      message=f"{table_name} 건수 불일치: df={len(df)} vs 적재={loaded}")
        else:
            log_stage(logger, "load", "success", count=loaded, message=table_name)
        return {"table": table_name, "rows": loaded, "status": "success"}
    except Exception as exc:  # noqa: BLE001
        log_stage(logger, "load", "failure", message=f"{table_name}: {exc}")
        return {"table": table_name, "rows": 0, "status": "failure", "error": str(exc)}


if __name__ == "__main__":
    # 간단 테스트: FRED 경제지표를 실제로 raw_economic_indicator 에 적재
    from src.collectors.fred_collector import collect_economic_data

    econ = collect_economic_data()
    print(f"\n수집: {len(econ)}행")
    result = load_to_bigquery(econ, "raw_economic_indicator")
    print("적재 결과:", result)
