"""파이프라인 진입점 (오케스트레이터).

전체 흐름:  유니버스 → 수집(주가·지표) → 검증 → 적재 → 변환
Phase 2 현재: 수집까지 구현(각 수집기는 DataFrame 반환).
검증(Phase 3)·적재(Phase 3)·변환(Phase 4)은 이후 구현.

실행:
    python -m src.main
"""
from __future__ import annotations

import uuid

from src.collectors.fred_collector import collect_economic_data
from src.collectors.price_collector import collect_stock_data
from src.collectors.universe_collector import fetch_universe
from src.utils import config
from src.utils.bq_client import test_connection
from src.utils.logger import get_logger, log_stage

logger = get_logger("main")


def run() -> None:
    execution_id = f"run-{uuid.uuid4().hex[:8]}"
    logger.info("파이프라인 시작 (execution_id=%s)", execution_id)

    # 0) 설정 확인 (필수 환경변수)
    config.validate()

    # 1) BigQuery 연결 확인
    if not test_connection():
        log_stage(logger, "setup", "failure", message="BigQuery 연결 실패 — 중단")
        return

    # 2) 유니버스 수집 (구성종목 명단)
    universe_df = fetch_universe()
    log_stage(logger, "universe", "success", count=len(universe_df),
              message=f"고유 {universe_df['ticker'].nunique()}종목")

    # 3) 주가 수집 (유니버스 종목 대상, max_symbols 상한 적용)
    tickers = universe_df["ticker"].dropna().unique().tolist()
    price_df = collect_stock_data(tickers)

    # 4) 경제지표 수집
    econ_df = collect_economic_data()

    # 5) 검증·적재·변환 — Phase 3~4 에서 구현
    for stage in ["validate", "load", "transform"]:
        log_stage(logger, stage, "warning", message="아직 미구현 (Phase 3~4 예정)")

    logger.info("수집 요약 — universe=%d행, price=%d행, econ=%d행",
                len(universe_df), len(price_df), len(econ_df))
    logger.info("파이프라인 종료 (execution_id=%s)", execution_id)


if __name__ == "__main__":
    run()
