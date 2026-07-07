"""price_collector — 미국 주식 일별 OHLCV 수집 (pluggable 소스).

소스는 config(symbols.yaml settings.price_source)에서 교체 가능:
  - alphavantage : Alpha Vantage TIME_SERIES_DAILY (기본 — 무료 키 필요.
                   무료 한도 5회/분·25회/일 → max_symbols 로 종목 수 제한)
  - yfinance     : Yahoo Finance (전체·무제한·무료, 키 불필요)

대상 종목 = universe_collector 가 만든 raw_universe 의 ticker 목록.
출력: symbol, date, open, high, low, close, adj_close, volume, source
(collected_at 은 적재(Phase 3) 시점에 BigQuery DEFAULT 로 채워짐)

단독 실행(테스트, 소수 종목):
    python -m src.collectors.price_collector AAPL MSFT
"""
from __future__ import annotations

import sys
import time

import pandas as pd
import requests

from src.utils import config
from src.utils.logger import get_logger, log_stage

logger = get_logger(__name__)

_OUTPUT_COLS = ["symbol", "date", "open", "high", "low", "close", "adj_close", "volume", "source"]
_AV_URL = "https://www.alphavantage.co/query"
_AV_SLEEP_SEC = 15   # 무료 5회/분 한도 준수 (최소 12초, 안전하게 15초 대기)


# ── Alpha Vantage 소스 ──────────────────────────────────────
def _fetch_alphavantage(symbol: str, start_date: str, end_date: str | None = None) -> pd.DataFrame:
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "outputsize": "compact",    # 무료 티어는 최근 100일 (full=프리미엄)
        "apikey": config.ALPHAVANTAGE_API_KEY,
    }
    resp = requests.get(_AV_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    ts = data.get("Time Series (Daily)")
    if ts is None:
        # 한도 초과/에러 시 Note/Information/Error Message 로 옴
        msg = data.get("Note") or data.get("Information") or data.get("Error Message") or str(data)[:160]
        raise RuntimeError(msg)

    rows = []
    for day, ohlcv in ts.items():
        if day < start_date:
            continue
        if end_date and day > end_date:
            continue
        rows.append({
            "symbol": symbol,
            "date": day,
            "open": ohlcv["1. open"],
            "high": ohlcv["2. high"],
            "low": ohlcv["3. low"],
            "close": ohlcv["4. close"],
            "adj_close": None,           # 무료 티어 미제공 (nullable)
            "volume": ohlcv["5. volume"],
        })
    df = pd.DataFrame(rows)
    df["source"] = "alphavantage"
    return df


# ── yfinance 소스 (전체·무제한, 키 불필요) ──────────────────
def _fetch_yfinance(symbol: str, start_date: str, end_date: str | None = None) -> pd.DataFrame:
    import yfinance as yf

    raw = yf.download(symbol, start=start_date, end=end_date, auto_adjust=False, progress=False)
    if raw.empty:
        raise RuntimeError("yfinance 반환 0건 (상폐/티커 오류?)")
    # 단일 티커도 MultiIndex 컬럼(Price, Ticker)로 오는 버전 대응 → 첫 레벨만 사용
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    raw = raw.reset_index()
    df = pd.DataFrame({
        "symbol": symbol,
        "date": pd.to_datetime(raw["Date"]).dt.strftime("%Y-%m-%d"),
        "open": raw["Open"], "high": raw["High"], "low": raw["Low"],
        "close": raw["Close"], "adj_close": raw.get("Adj Close"), "volume": raw["Volume"],
    })
    df["source"] = "yfinance"
    return df


_FETCHERS = {"alphavantage": _fetch_alphavantage, "yfinance": _fetch_yfinance}


# ── 메인 진입점 ─────────────────────────────────────────────
def collect_stock_data(
    symbols: list[str],
    start_date: str | None = None,
    end_date: str | None = None,
    source: str | None = None,
) -> pd.DataFrame:
    """종목 목록의 일별 OHLCV 를 수집해 DataFrame 반환.

    종목별 try-except — 하나 실패해도 로그만 남기고 다음 종목 계속 (FR-010).
    """
    start_date = start_date or config.DATE_RANGE_START
    source = source or config.PRICE_SOURCE
    fetch = _FETCHERS.get(source)
    if fetch is None:
        raise ValueError(f"알 수 없는 price_source: {source} (alphavantage|yfinance)")

    symbols = list(dict.fromkeys(symbols))   # 중복 제거(순서 유지)
    if config.MAX_SYMBOLS and len(symbols) > config.MAX_SYMBOLS:
        log_stage(logger, "collect", "warning",
                  message=f"{len(symbols)}종목 중 max_symbols={config.MAX_SYMBOLS}개만 수집 (나머지 제외)")
        symbols = symbols[:config.MAX_SYMBOLS]

    frames = []
    for i, sym in enumerate(symbols):
        try:
            df = fetch(sym, start_date, end_date)
            frames.append(df)
            log_stage(logger, "collect", "success", count=len(df), message=f"{source} {sym}")
        except Exception as exc:  # noqa: BLE001
            log_stage(logger, "collect", "failure", message=f"{source} {sym}: {exc}")
        # Alpha Vantage 분당 한도 → 마지막 종목이 아니면 대기
        if source == "alphavantage" and i < len(symbols) - 1:
            time.sleep(_AV_SLEEP_SEC)

    if not frames:
        log_stage(logger, "collect", "failure", message="주가 수집 0건")
        return pd.DataFrame(columns=_OUTPUT_COLS)

    out = pd.concat(frames, ignore_index=True)
    # Alpha Vantage 는 값이 문자열 → 숫자형 변환
    for col in ["open", "high", "low", "close", "adj_close", "volume"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    return out[_OUTPUT_COLS].reset_index(drop=True)


if __name__ == "__main__":
    syms = sys.argv[1:] or ["AAPL", "MSFT"]
    result = collect_stock_data(syms)
    print(f"\n수집 결과: {len(result)}행, 종목 {result['symbol'].nunique()}개")
    if not result.empty:
        print("\n앞 3행:")
        print(result.head(3).to_string())
        print("\n뒤 3행:")
        print(result.tail(3).to_string())
