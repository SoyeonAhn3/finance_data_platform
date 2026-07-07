"""BigQuery 클라이언트 헬퍼 + 연결 테스트 / 스키마 초기화 (Phase 1 산출물 #8).

키(서비스계정 JSON + .env)가 준비된 뒤 실행:
    python -m src.utils.bq_client           # 연결 테스트 (SELECT 1)
    python -m src.utils.bq_client --init     # sql/setup.sql 실행 (테이블 생성)
"""
from __future__ import annotations

import sys
from pathlib import Path

from google.cloud import bigquery

from src.utils import config
from src.utils.logger import get_logger

logger = get_logger(__name__)


def get_bigquery_client() -> bigquery.Client:
    """서비스계정 인증으로 BigQuery 클라이언트를 만든다.

    GOOGLE_APPLICATION_CREDENTIALS(서비스계정 JSON 경로)를 사용한다.
    """
    config.validate()  # 필수 환경변수 없으면 여기서 명확히 에러
    return bigquery.Client.from_service_account_json(
        config.GOOGLE_APPLICATION_CREDENTIALS,
        project=config.GCP_PROJECT_ID,
        location=config.BQ_LOCATION,
    )


def test_connection() -> bool:
    """간단한 쿼리로 인증·연결을 확인한다. 성공 시 True."""
    try:
        client = get_bigquery_client()
        rows = list(client.query("SELECT 1 AS ok").result())
        logger.info(
            "BigQuery 연결 성공 (project=%s, location=%s)",
            config.GCP_PROJECT_ID,
            config.BQ_LOCATION,
        )
        return bool(rows) and rows[0]["ok"] == 1
    except Exception as exc:  # noqa: BLE001 — 연결 실패 원인을 그대로 로그로 보여줌
        logger.error("BigQuery 연결 실패: %s", exc)
        return False


def init_schema(sql_path: str | Path | None = None) -> None:
    """sql/setup.sql 을 실행해 데이터셋과 테이블 11개를 만든다.

    BigQuery 멀티 스테이트먼트 스크립트로 한 번에 실행한다.
    """
    sql_path = Path(sql_path) if sql_path else (config.ROOT_DIR / "sql" / "setup.sql")
    sql = sql_path.read_text(encoding="utf-8")
    client = get_bigquery_client()
    client.query(sql).result()
    logger.info("스키마 초기화 완료: %s", sql_path)


if __name__ == "__main__":
    if "--init" in sys.argv:
        init_schema()
        print("✅ 스키마 초기화 완료 (finance_db)")
    else:
        ok = test_connection()
        print("✅ BigQuery 연결 OK" if ok else "❌ 연결 실패 — 위 로그 확인")
        sys.exit(0 if ok else 1)
