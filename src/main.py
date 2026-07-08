"""파이프라인 진입점 (오케스트레이터).

흐름:  유니버스 → 수집(주가·지표) → 검증 → 적재(BigQuery raw) → 변환(Star Schema/Mart)
각 단계 실행 로그와 품질 검증 결과를 BigQuery 운영 테이블에 기록한다.

실행:
    python -m src.main
"""
from __future__ import annotations

import pandas as pd

from src.collectors.fred_collector import collect_economic_data
from src.collectors.price_collector import collect_stock_data
from src.collectors.universe_collector import fetch_universe
from src.loaders.bigquery_loader import load_to_bigquery
from src.loaders.operations_logger import (
    new_execution_id,
    write_execution_logs,
    write_quality_logs,
)
from src.transformers.star_schema import transform_to_star_schema
from src.utils import config
from src.utils.bq_client import get_bigquery_client, test_connection
from src.utils.logger import get_logger, log_stage
from src.validators.quality_checker import run_all_checks

logger = get_logger("main")


def _now():
    return pd.Timestamp.now(tz="UTC")


def run() -> None:
    execution_id = new_execution_id()
    logger.info("파이프라인 시작 (execution_id=%s)", execution_id)

    # 0) 설정 + 연결 확인
    config.validate()
    if not test_connection():
        log_stage(logger, "setup", "failure", message="BigQuery 연결 실패 — 중단")
        return

    exec_records: list[dict] = []
    quality_results: list[dict] = []

    def record(stage, status, count=0, error=None, start=None):
        exec_records.append({
            "stage": stage, "status": status, "record_count": count,
            "error_message": error, "started_at": start or _now(), "ended_at": _now(),
        })

    # 1) 유니버스 수집 (구성종목 명단)
    t = _now()
    universe_df = fetch_universe()
    universe_tickers = universe_df["ticker"].dropna().unique().tolist()
    record("universe", "success", len(universe_df), start=t)

    # 2) 주가 + 경제지표 수집
    t = _now()
    price_df = collect_stock_data(universe_tickers)
    record("collect", "success", len(price_df), start=t)
    econ_df = collect_economic_data()

    # 3) 검증 (경고만, 적재를 막지 않음)
    #    완전성 검증은 '실제 수집 시도한 종목'(max_symbols 상한 적용) 기준으로 비교
    attempted = universe_tickers[:config.MAX_SYMBOLS] if config.MAX_SYMBOLS else universe_tickers
    quality_results += run_all_checks(universe_df, "raw_universe")
    quality_results += run_all_checks(price_df, "raw_daily_price", universe_tickers=attempted)
    quality_results += run_all_checks(econ_df, "raw_economic_indicator")

    # 4) 적재 (WRITE_TRUNCATE — 빈 df면 건너뜀=기존 유지)
    for df, table in [(universe_df, "raw_universe"),
                      (price_df, "raw_daily_price"),
                      (econ_df, "raw_economic_indicator")]:
        t = _now()
        res = load_to_bigquery(df, table)
        record("load", res["status"], res["rows"], start=t)

    # 5) Star Schema 변환 (raw → dim/fact → mart view)
    t = _now()
    try:
        counts = transform_to_star_schema(get_bigquery_client())
        n = int(counts.get("fact_daily_price", 0)) + int(counts.get("fact_economic_indicator", 0))
        record("transform", "success", n, start=t)
    except Exception as exc:  # noqa: BLE001 — 변환 실패해도 로그 남기고 파이프라인 마무리
        log_stage(logger, "transform", "failure", message=str(exc))
        record("transform", "failure", 0, error=str(exc), start=t)

    # 6) 운영 로그 기록 (실행 + 품질)
    write_execution_logs(execution_id, exec_records)
    write_quality_logs(execution_id, quality_results)

    logger.info("파이프라인 종료 (execution_id=%s) — universe=%d, price=%d, econ=%d행",
                execution_id, len(universe_df), len(price_df), len(econ_df))


if __name__ == "__main__":
    run()
