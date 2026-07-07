"""quality_checker — 적재 전 데이터 품질 검증 (FR-009).

검증(validate)은 문제를 **찾아 경고만** 남긴다 — 데이터를 바꾸지 않고, 적재를 막지도 않는다.
실제 정제(중복제거·정규화)는 Phase 4 의 raw→fact 변환에서 수행한다.

검증 4종:
  - missing      : 필수 필드 결측
  - outlier      : 가격 <= 0 등 이상치 (IR-006)
  - duplicate    : (symbol,date) / (indicator_code,date) 중복
  - completeness : 승인 종목(유니버스)인데 수집 0건 → 이상 감지 (상폐·API 한도·오류, IR-008)

각 검증은 결과 dict 리스트를 반환:
  {check_type, target_table, target_field, result(pass/warn/fail), detail}

단독 실행(테스트):
    python -m src.validators.quality_checker
"""
from __future__ import annotations

import pandas as pd

from src.utils.logger import get_logger, log_stage

logger = get_logger(__name__)

# 테이블별 검증 규칙
_TABLE_RULES = {
    "raw_daily_price":        {"required": ["date", "symbol", "close"],
                               "keys": ["symbol", "date"], "positive": ["close"]},
    "raw_economic_indicator": {"required": ["date", "indicator_code", "value"],
                               "keys": ["indicator_code", "date"], "positive": []},
    "raw_universe":           {"required": ["ticker"],
                               "keys": ["ticker", "index_source"], "positive": []},
}


def _result(check_type, table, field, result, detail=None) -> dict:
    return {"check_type": check_type, "target_table": table,
            "target_field": field, "result": result, "detail": detail}


def check_missing(df: pd.DataFrame, required_columns: list, table_name: str) -> list:
    out = []
    for col in required_columns:
        if col not in df.columns:
            out.append(_result("missing", table_name, col, "warn", f"컬럼 없음: {col}"))
            continue
        n = int(df[col].isna().sum())
        out.append(_result("missing", table_name, col,
                            "warn" if n else "pass", f"결측 {n}건" if n else None))
    return out


def check_outliers(df: pd.DataFrame, positive_cols: list, table_name: str) -> list:
    out = []
    for col in positive_cols:
        if col not in df.columns:
            continue
        bad = int((pd.to_numeric(df[col], errors="coerce") <= 0).sum())
        out.append(_result("outlier", table_name, col,
                            "warn" if bad else "pass", f"{col} <= 0 인 {bad}건" if bad else None))
    return out


def check_duplicates(df: pd.DataFrame, key_columns: list, table_name: str) -> list:
    cols = [c for c in key_columns if c in df.columns]
    if not cols:
        return []
    dup = int(df.duplicated(subset=cols).sum())
    return [_result("duplicate", table_name, "+".join(cols),
                    "warn" if dup else "pass", f"중복 {dup}건" if dup else None)]


def check_completeness(df: pd.DataFrame, universe_tickers: list, table_name: str,
                       symbol_col: str = "symbol") -> list:
    """승인 종목(유니버스 명단)인데 df에 0건인 종목 → 이상 감지 (상폐·API 한도·오류, IR-008)."""
    if symbol_col not in df.columns or not universe_tickers:
        return []
    collected = set(df[symbol_col].dropna().unique())
    missing = [t for t in universe_tickers if t not in collected]
    if not missing:
        return [_result("completeness", table_name, symbol_col, "pass", None)]
    preview = ", ".join(missing[:5]) + (" ..." if len(missing) > 5 else "")
    return [_result("completeness", table_name, symbol_col, "warn",
                    f"승인 종목 {len(missing)}개 수집 0건 (상폐·API 한도·오류 등 원인 확인 필요): {preview}")]


def run_all_checks(df: pd.DataFrame, table_name: str, universe_tickers: list | None = None) -> list:
    """테이블 규칙에 따라 모든 검증을 실행하고 결과 리스트 반환 (+ 경고 로그)."""
    rules = _TABLE_RULES.get(table_name, {})
    results = []
    results += check_missing(df, rules.get("required", []), table_name)
    results += check_outliers(df, rules.get("positive", []), table_name)
    results += check_duplicates(df, rules.get("keys", []), table_name)
    if universe_tickers is not None:
        results += check_completeness(df, universe_tickers, table_name)

    warns = [r for r in results if r["result"] == "warn"]
    for r in warns:
        log_stage(logger, "validate", "warning",
                  message=f"{r['check_type']} {r['target_table']}.{r['target_field']}: {r['detail']}")
    log_stage(logger, "validate", "success", count=len(results),
              message=f"{table_name} 검증 {len(results)}건 (경고 {len(warns)})")
    return results


if __name__ == "__main__":
    # 일부러 더러운 데이터로 모든 검증이 걸리는지 확인 (네트워크 불필요)
    dirty = pd.DataFrame({
        "symbol": ["AAPL", "AAPL", "MSFT", None],   # (AAPL,1/2) 중복 + symbol 결측
        "date":   ["2026-01-02", "2026-01-02", "2026-01-03", "2026-01-05"],
        "close":  [185.2, 185.2, -5.0, 50.0],        # MSFT 음수(이상치)
    })
    print("\n=== 검증 결과 (승인 명단: AAPL, MSFT, GOOGL) ===")
    for r in run_all_checks(dirty, "raw_daily_price", universe_tickers=["AAPL", "MSFT", "GOOGL"]):
        print(" ", r)
