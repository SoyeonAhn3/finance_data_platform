"""파이프라인 진입점 (오케스트레이터) — Phase 1 스켈레톤.

전체 흐름:  유니버스 → 수집 → 검증 → 적재 → 변환
각 단계는 Phase 2~4 에서 구현된다. 지금은 뼈대만 있으며,
설정/로깅/BigQuery 연결이 준비됐는지 확인하는 역할까지만 한다.

실행 (키 발급 후):
    python -m src.main
"""
from __future__ import annotations

import uuid

from src.utils import config
from src.utils.bq_client import test_connection
from src.utils.logger import get_logger, log_stage

logger = get_logger("main")

# 이후 Phase 에서 구현될 단계들
_PENDING_STAGES = ["universe", "collect", "validate", "load", "transform"]


def run() -> None:
    execution_id = f"run-{uuid.uuid4().hex[:8]}"
    logger.info("파이프라인 시작 (execution_id=%s)", execution_id)

    # 0) 설정 확인 (필수 환경변수)
    config.validate()

    # 1) BigQuery 연결 확인
    if not test_connection():
        log_stage(logger, "setup", "failure", message="BigQuery 연결 실패 — 중단")
        return

    # 2~5) 이후 단계 — Phase 2~4 에서 구현
    for stage in _PENDING_STAGES:
        log_stage(logger, stage, "warning", message="아직 미구현 (Phase 2~4 예정)")

    logger.info("파이프라인 종료 (execution_id=%s)", execution_id)


if __name__ == "__main__":
    run()
