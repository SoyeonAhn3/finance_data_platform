"""설정 로더 — 흩어진 설정을 한 곳에서 읽어 제공한다.

  - .env                → 비밀값·연결정보 (API 키, GCP 프로젝트 등)
  - config/symbols.yaml → 무엇을 수집할지 (유니버스·지표·기간)

다른 모듈은 `from src.utils import config` 후 `config.FRED_API_KEY` 처럼 쓰면 된다.
직접 os.environ 이나 yaml 파일을 열 필요가 없다.

주의: import 시점에는 필수값을 강제하지 않는다(=키 없어도 import 가능).
파이프라인 시작 시 `config.validate()` 를 호출해 한 번에 검사한다.
"""
from __future__ import annotations

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

# 프로젝트 루트 = 이 파일(src/utils/config.py) 기준 두 단계 위
ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT_DIR / ".env"
SYMBOLS_PATH = ROOT_DIR / "config" / "symbols.yaml"

# .env 로드 (파일 없어도 조용히 통과 — CI 는 환경변수로 주입)
load_dotenv(ENV_PATH)

# ── 1) 환경변수 (.env) ───────────────────────────────────────
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
BQ_DATASET = os.environ.get("BQ_DATASET", "finance_db")
BQ_LOCATION = os.environ.get("BQ_LOCATION", "US")
GOOGLE_APPLICATION_CREDENTIALS = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
FRED_API_KEY = os.environ.get("FRED_API_KEY")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

# 파이프라인 실행에 반드시 필요한 항목
_REQUIRED = {
    "GCP_PROJECT_ID": GCP_PROJECT_ID,
    "GOOGLE_APPLICATION_CREDENTIALS": GOOGLE_APPLICATION_CREDENTIALS,
    "FRED_API_KEY": FRED_API_KEY,
}


def validate() -> None:
    """필수 환경변수가 모두 있는지 확인. 없으면 한 번에 모아 에러."""
    missing = [name for name, value in _REQUIRED.items() if not value]
    if missing:
        raise RuntimeError(
            "필수 환경변수가 비어 있습니다: "
            + ", ".join(missing)
            + f"\n→ {ENV_PATH} 를 만들고 값을 채우세요 (.env.example 참고)."
        )


# ── 2) 수집 설정 (symbols.yaml) ─────────────────────────────
def _load_symbols() -> dict:
    if not SYMBOLS_PATH.exists():
        raise FileNotFoundError(f"설정 파일이 없습니다: {SYMBOLS_PATH}")
    with open(SYMBOLS_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


_symbols = _load_symbols()

UNIVERSE = _symbols.get("universe", {})       # 유니버스 소스 (ETF)
INDICATORS = _symbols.get("indicators", [])   # FRED 지표 목록 (dim_indicator seed)
_settings = _symbols.get("settings", {})
DATE_RANGE_START = _settings.get("date_range", {}).get("start", "2020-01-01")
