"""operations_logger — 실행/품질 로그를 BigQuery 운영 테이블에 기록.

- pipeline_execution_log : 단계별 성공/실패/건수 (FR-010)
- data_quality_log       : 검증 결과 (FR-009)

로그는 누적되므로 WRITE_APPEND(추가). log_id/check_id 는 Python UUID로 부여하고,
기존 테이블 스키마를 그대로 사용해 타입 드리프트를 막는다.
두 로그는 execution_id(배치 1회 = 1 UUID)로 연결된다.

단독 실행(테스트):
    python -m src.loaders.operations_logger
"""
from __future__ import annotations

import uuid

import pandas as pd
from google.cloud import bigquery

from src.utils import config
from src.utils.bq_client import get_bigquery_client
from src.utils.logger import get_logger

logger = get_logger(__name__)


def new_execution_id() -> str:
    """배치 1회를 식별하는 실행 ID."""
    return f"run-{uuid.uuid4().hex[:8]}"


def _append(rows: list[dict], table_name: str) -> None:
    if not rows:
        return
    client = get_bigquery_client()
    table_id = f"{config.BQ_DATASET}.{table_name}"
    schema = client.get_table(table_id).schema        # 기존 스키마 그대로 사용
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        schema=schema,
    )
    client.load_table_from_dataframe(pd.DataFrame(rows), table_id, job_config=job_config).result()


def write_execution_logs(execution_id: str, stage_records: list[dict]) -> None:
    """stage_records: [{stage, status, record_count, error_message, started_at, ended_at}]."""
    rows = [{
        "log_id": uuid.uuid4().hex,
        "execution_id": execution_id,
        "stage": r["stage"],
        "status": r["status"],
        "record_count": int(r.get("record_count") or 0),
        "error_message": r.get("error_message"),
        "started_at": r.get("started_at") or pd.Timestamp.now(tz="UTC"),
        "ended_at": r.get("ended_at"),
    } for r in stage_records]
    _append(rows, "pipeline_execution_log")
    logger.info("실행 로그 %d건 기록 (execution_id=%s)", len(rows), execution_id)


def write_quality_logs(execution_id: str, check_results: list[dict]) -> None:
    """check_results: quality_checker.run_all_checks() 결과 리스트."""
    now = pd.Timestamp.now(tz="UTC")
    rows = [{
        "check_id": uuid.uuid4().hex,
        "execution_id": execution_id,
        "check_type": c["check_type"],
        "target_table": c["target_table"],
        "target_field": c.get("target_field"),
        "result": c["result"],
        "detail": c.get("detail"),
        "checked_at": now,
    } for c in check_results]
    _append(rows, "data_quality_log")
    logger.info("품질 로그 %d건 기록 (execution_id=%s)", len(rows), execution_id)


if __name__ == "__main__":
    eid = new_execution_id()
    write_execution_logs(eid, [{
        "stage": "collect", "status": "success", "record_count": 154,
        "started_at": pd.Timestamp.now(tz="UTC"), "ended_at": pd.Timestamp.now(tz="UTC"),
    }])
    write_quality_logs(eid, [{
        "check_type": "outlier", "target_table": "raw_daily_price",
        "target_field": "close", "result": "warn", "detail": "테스트 경고",
    }])
    client = get_bigquery_client()
    for t in ["pipeline_execution_log", "data_quality_log"]:
        n = list(client.query(
            f"SELECT COUNT(*) c FROM {config.BQ_DATASET}.{t} WHERE execution_id='{eid}'"
        ).result())[0]["c"]
        print(f"{t}: execution_id={eid} → {n}건")
