"""universe_collector — S&P 500 + Nasdaq-100 구성종목 명단 수집.

yfinance_collector 보다 **먼저** 실행된다. 여기서 나온 ticker 목록이
주가 수집 대상이 되므로, 매 실행마다 지수 편출입·상장폐지가 자동 반영된다.

소스는 config(symbols.yaml)에서 교체 가능(pluggable):
  - wikipedia    : Wikipedia 구성종목 표 (기본 — 무료·키불필요, ticker+회사명+섹터)
  - etf_holdings : 운용사(IVV/QQQ) 공시 CSV (비중 포함). 실패 시 wikipedia 로 자동 폴백.

출력: raw_universe 스키마에 맞춘 pandas DataFrame
  ticker, company_name, sector, market, index_source, weight, source
  (collected_at 은 적재(Phase 3) 시점에 BigQuery DEFAULT 로 채워짐)

단독 실행(테스트):
    python -m src.collectors.universe_collector
"""
from __future__ import annotations

import io

import pandas as pd
import requests

from src.utils import config
from src.utils.logger import get_logger, log_stage

logger = get_logger(__name__)

_HEADERS = {"User-Agent": "Mozilla/5.0 (finance_data_platform; learning project)"}
_OUTPUT_COLS = ["ticker", "company_name", "sector", "market", "index_source", "weight", "source"]

WIKI_SP500 = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
WIKI_NDX = "https://en.wikipedia.org/wiki/Nasdaq-100"

# 운용사 공시 CSV (IVV=iShares, QQQ=Invesco)
_ISHARES_URLS = {
    "IVV": "https://www.ishares.com/us/products/239726/ishares-core-sp-500-etf/"
           "1467271812596.ajax?fileType=csv&fileName=IVV_holdings&dataType=fund",
}
_INVESCO_URLS = {
    "QQQ": "https://www.invesco.com/us/financial-products/etfs/holdings/main/holdings/0"
           "?audienceType=Investor&action=download&ticker=QQQ",
}


# ── 공용 헬퍼 ────────────────────────────────────────────────
def _normalize_ticker(t) -> str:
    """티커 정규화: 대문자·공백제거 + yfinance 형식(점→대시, 예: BRK.B→BRK-B)."""
    return str(t).strip().upper().replace(".", "-")


def _find_col(df: pd.DataFrame, *candidates: str):
    """부분 문자열로 컬럼명을 찾는다 (Wikipedia 표의 각주 [15] 등에 견고)."""
    for cand in candidates:
        for col in df.columns:
            if cand.lower() in str(col).lower():
                return col
    return None


# ── Wikipedia 소스 ──────────────────────────────────────────
def _read_wiki_tables(url: str) -> list[pd.DataFrame]:
    resp = requests.get(url, headers=_HEADERS, timeout=30)
    resp.raise_for_status()
    return pd.read_html(io.StringIO(resp.text))


def _fetch_wikipedia_sp500() -> pd.DataFrame:
    tables = _read_wiki_tables(WIKI_SP500)
    table = next((t for t in tables if _find_col(t, "symbol") and _find_col(t, "security")), None)
    if table is None:
        raise ValueError("S&P 500 구성종목 표를 찾지 못함 (Wikipedia 구조 변경?)")
    tick = _find_col(table, "symbol")
    name = _find_col(table, "security")
    sector = _find_col(table, "gics sector", "sector")
    out = pd.DataFrame({
        "ticker": table[tick].map(_normalize_ticker),
        "company_name": table[name].astype(str).str.strip(),
        "sector": table[sector].astype(str).str.strip() if sector else None,
    })
    out["index_source"] = "SP500"
    return out


def _fetch_wikipedia_nasdaq100() -> pd.DataFrame:
    tables = _read_wiki_tables(WIKI_NDX)
    table = next((t for t in tables if _find_col(t, "ticker") and _find_col(t, "company")), None)
    if table is None:
        raise ValueError("Nasdaq-100 구성종목 표를 찾지 못함 (Wikipedia 구조 변경?)")
    tick = _find_col(table, "ticker")
    name = _find_col(table, "company")
    sector = _find_col(table, "icb industry", "gics sector", "sector")
    out = pd.DataFrame({
        "ticker": table[tick].map(_normalize_ticker),
        "company_name": table[name].astype(str).str.strip(),
        "sector": table[sector].astype(str).str.strip() if sector else None,
    })
    out["index_source"] = "NASDAQ100"
    return out


# ── ETF 운용사 CSV 소스 (best-effort) ───────────────────────
def _parse_ishares(url: str, index_source: str) -> pd.DataFrame:
    resp = requests.get(url, headers=_HEADERS, timeout=30)
    resp.raise_for_status()
    lines = resp.text.splitlines()
    # 앞쪽 메타 줄을 건너뛰고 'Ticker' 로 시작하는 헤더를 찾는다
    hdr = next(i for i, ln in enumerate(lines) if ln.lower().lstrip('"').startswith("ticker"))
    df = pd.read_csv(io.StringIO("\n".join(lines[hdr:])))
    if "Asset Class" in df.columns:
        df = df[df["Asset Class"].astype(str).str.contains("Equity", case=False, na=False)]
    out = pd.DataFrame({
        "ticker": df["Ticker"].map(_normalize_ticker),
        "company_name": df.get("Name"),
        "sector": df.get("Sector"),
        "weight": pd.to_numeric(df.get("Weight (%)"), errors="coerce"),
    })
    out["index_source"] = index_source
    return out[out["ticker"].str.len() > 0]


def _parse_invesco(url: str, index_source: str) -> pd.DataFrame:
    resp = requests.get(url, headers=_HEADERS, timeout=30)
    resp.raise_for_status()
    df = pd.read_csv(io.StringIO(resp.text))
    tick = _find_col(df, "holding ticker", "ticker")
    name = _find_col(df, "name", "security")
    sector = _find_col(df, "sector")
    weight = _find_col(df, "weight")
    out = pd.DataFrame({
        "ticker": df[tick].map(_normalize_ticker),
        "company_name": df[name] if name else None,
        "sector": df[sector] if sector else None,
        "weight": pd.to_numeric(df[weight], errors="coerce") if weight else pd.NA,
    })
    out["index_source"] = index_source
    return out[out["ticker"].str.len() > 0]


def _fetch_etf_holdings(etf: str, index_source: str) -> pd.DataFrame:
    if etf in _ISHARES_URLS:
        return _parse_ishares(_ISHARES_URLS[etf], index_source)
    if etf in _INVESCO_URLS:
        return _parse_invesco(_INVESCO_URLS[etf], index_source)
    raise ValueError(f"etf_holdings URL 미등록: {etf}")


# ── 지수 1개 수집 (소스 dispatch + 폴백) ────────────────────
def _fetch_index(key: str, icfg: dict) -> pd.DataFrame:
    index_source = "SP500" if key == "sp500" else "NASDAQ100"
    source = (icfg or {}).get("source", "wikipedia")

    if source == "etf_holdings":
        try:
            df = _fetch_etf_holdings(icfg.get("etf"), index_source)
            df["source"] = icfg.get("etf")   # IVV / QQQ
            return df
        except Exception as exc:  # noqa: BLE001 — 막히면 wikipedia 폴백
            log_stage(logger, "universe", "warning",
                      message=f"{index_source} etf_holdings 실패({exc}) → wikipedia 폴백")

    # wikipedia (기본 또는 폴백)
    df = (_fetch_wikipedia_sp500() if key == "sp500" else _fetch_wikipedia_nasdaq100())
    df["source"] = "wikipedia"
    return df


# ── 메인 진입점 ─────────────────────────────────────────────
def fetch_universe(universe_cfg: dict | None = None) -> pd.DataFrame:
    """S&P 500 + Nasdaq-100 구성종목을 수집해 raw_universe DataFrame 반환.

    수집 완전 실패 시 빈 DataFrame 반환 (적재 단계에서 캐시 폴백 처리).
    """
    cfg = universe_cfg if universe_cfg is not None else config.UNIVERSE
    frames: list[pd.DataFrame] = []

    for key in ("sp500", "nasdaq100"):
        icfg = cfg.get(key, {})
        if not icfg.get("enabled", False):
            continue
        try:
            df = _fetch_index(key, icfg)
            frames.append(df)
            log_stage(logger, "universe", "success", count=len(df), message=f"{key} {len(df)}종목")
        except Exception as exc:  # noqa: BLE001
            log_stage(logger, "universe", "failure", message=f"{key} 수집 실패: {exc}")

    if not frames:
        log_stage(logger, "universe", "failure", message="유니버스 0건 — 캐시 폴백 필요")
        return pd.DataFrame(columns=_OUTPUT_COLS)

    uni = pd.concat(frames, ignore_index=True)
    uni["market"] = "US"
    if "weight" not in uni.columns:
        uni["weight"] = pd.NA

    # 강제 포함/제외 (탈출구)
    for extra in (cfg.get("include_extra") or []):
        tk = _normalize_ticker(extra)
        if tk not in set(uni["ticker"]):
            uni = pd.concat([uni, pd.DataFrame([{
                "ticker": tk, "company_name": None, "sector": None,
                "market": "US", "index_source": "EXTRA", "weight": pd.NA, "source": "manual",
            }])], ignore_index=True)
    exclude = {_normalize_ticker(x) for x in (cfg.get("exclude") or [])}
    uni = uni[~uni["ticker"].isin(exclude)]

    # 빈 티커 제거 + 컬럼 순서 정리
    uni = uni[uni["ticker"].str.len() > 0]
    uni = uni[_OUTPUT_COLS].reset_index(drop=True)
    return uni


if __name__ == "__main__":
    df = fetch_universe()
    unique_tickers = df["ticker"].nunique()
    print(f"\n수집 결과: {len(df)}행, 고유 티커 {unique_tickers}개")
    print("지수별 행 수:")
    print(df["index_source"].value_counts().to_string())
    print("\n샘플 5행:")
    print(df.head().to_string())
