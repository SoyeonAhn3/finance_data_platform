"""fred_collector — FRED 경제지표 시계열 수집.

symbols.yaml 의 indicators 목록(FEDFUNDS, CPIAUCSL 등)을 받아
지표별 시계열(날짜→값)을 수집한다. 지표별 try-except (하나 실패해도 계속).

출력: indicator_code, date, value, source
(collected_at 은 적재(Phase 3) 시점에 BigQuery DEFAULT 로 채워짐)

단독 실행(테스트):
    python -m src.collectors.fred_collector
"""
from __future__ import annotations

import pandas as pd
from fredapi import Fred

from src.utils import config
from src.utils.logger import get_logger, log_stage

logger = get_logger(__name__)

_OUTPUT_COLS = ["indicator_code", "date", "value", "source"]


def _codes(indicators) -> list[str]:
    """indicators(딕셔너리 목록 또는 코드 문자열 목록)에서 지표 코드만 추출."""
    codes = []
    for item in indicators:
        code = item.get("code") if isinstance(item, dict) else item
        if code:
            codes.append(code)
    return codes


def collect_economic_data(
    indicators=None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """지표 목록의 시계열을 수집해 DataFrame 반환 (지표별 try-except)."""
    indicators = indicators if indicators is not None else config.INDICATORS
    start_date = start_date or config.DATE_RANGE_START
    fred = Fred(api_key=config.FRED_API_KEY)

    frames = []
    for code in _codes(indicators):
        try:
            series = fred.get_series(code, observation_start=start_date, observation_end=end_date)
            series = series.dropna()   # 결측 관측치 제거
            df = pd.DataFrame({
                "indicator_code": code,
                "date": pd.to_datetime(series.index).strftime("%Y-%m-%d"),
                "value": series.values,
            })
            df["source"] = "FRED"
            frames.append(df)
            log_stage(logger, "collect", "success", count=len(df), message=f"FRED {code}")
        except Exception as exc:  # noqa: BLE001
            log_stage(logger, "collect", "failure", message=f"FRED {code}: {exc}")

    if not frames:
        log_stage(logger, "collect", "failure", message="경제지표 수집 0건")
        return pd.DataFrame(columns=_OUTPUT_COLS)

    out = pd.concat(frames, ignore_index=True)
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    return out[_OUTPUT_COLS].reset_index(drop=True)


if __name__ == "__main__":
    result = collect_economic_data()
    print(f"\n수집 결과: {len(result)}행, 지표 {result['indicator_code'].nunique()}개")
    if not result.empty:
        print("\n지표별 건수:")
        print(result.groupby("indicator_code").size().to_string())
        print("\n샘플:")
        print(result.head(3).to_string())
        print(result.tail(3).to_string())
