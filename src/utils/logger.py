"""구조화된 로깅 유틸 (NFR-004: 타임스탬프·단계·상태·건수).

  - get_logger(name): 콘솔 + logs/pipeline.log 에 찍는 표준 로거
  - log_stage(...):   파이프라인 단계 결과를 한 줄로 남기는 헬퍼

예)  2026-07-07 09:00:00 | INFO | collect | [collect] status=success count=651420
"""
from __future__ import annotations

import logging

from src.utils import config

LOG_DIR = config.ROOT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "pipeline.log"

_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
_DATEFMT = "%Y-%m-%d %H:%M:%S"
_configured = False


def _configure_root() -> None:
    """루트 로거를 한 번만 설정한다 (콘솔 + 파일 핸들러)."""
    global _configured
    if _configured:
        return
    handlers = [
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ]
    logging.basicConfig(
        level=config.LOG_LEVEL,
        format=_FORMAT,
        datefmt=_DATEFMT,
        handlers=handlers,
    )
    _configured = True


def get_logger(name: str) -> logging.Logger:
    """모듈별 로거를 돌려준다. name 은 보통 __name__ 또는 'main'."""
    _configure_root()
    return logging.getLogger(name)


def log_stage(
    logger: logging.Logger,
    stage: str,
    status: str,
    count: int | None = None,
    message: str = "",
) -> None:
    """파이프라인 단계 결과를 표준 포맷으로 남긴다.

    stage   : universe / collect / validate / load / transform 등
    status  : success / failure / warning
    count   : 처리 건수 (선택)
    message : 부가 설명 (선택)
    """
    parts = [f"[{stage}]", f"status={status}"]
    if count is not None:
        parts.append(f"count={count}")
    if message:
        parts.append(message)
    line = " ".join(parts)

    if status == "failure":
        logger.error(line)
    elif status == "warning":
        logger.warning(line)
    else:
        logger.info(line)
