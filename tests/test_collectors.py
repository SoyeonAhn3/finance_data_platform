"""수집기 순수 함수 단위 테스트 (네트워크 불필요).

실제 수집(라이브)은 각 모듈의 __main__ 으로 확인:
    python -m src.collectors.universe_collector
    python -m src.collectors.fred_collector
    python -m src.collectors.price_collector AAPL
"""
import pandas as pd

from src.collectors import fred_collector as fc
from src.collectors import price_collector as pc
from src.collectors import universe_collector as uc


def test_normalize_ticker():
    """티커 정규화: 공백제거·대문자·점→대시(yfinance 형식)."""
    assert uc._normalize_ticker(" aapl ") == "AAPL"
    assert uc._normalize_ticker("brk.b") == "BRK-B"
    assert uc._normalize_ticker("BF.B") == "BF-B"


def test_find_col_partial_match():
    """컬럼명을 부분 문자열로 찾는다 (Wikipedia 각주 [15] 등에 견고)."""
    df = pd.DataFrame(columns=["Ticker", "Company", "ICB Industry[15]"])
    assert uc._find_col(df, "ticker") == "Ticker"
    assert uc._find_col(df, "icb industry", "sector") == "ICB Industry[15]"
    assert uc._find_col(df, "없는컬럼") is None


def test_fred_codes_extraction():
    """indicators(딕셔너리/문자열 혼합)에서 코드만 추출."""
    mixed = [{"code": "FEDFUNDS", "name": "x"}, "CPIAUCSL", {"name": "코드없음"}]
    assert fc._codes(mixed) == ["FEDFUNDS", "CPIAUCSL"]


def test_price_output_columns_contract():
    """수집기 출력 컬럼 계약이 raw 스키마와 일치."""
    assert pc._OUTPUT_COLS == ["symbol", "date", "open", "high", "low", "close",
                               "adj_close", "volume", "source"]
    assert uc._OUTPUT_COLS == ["ticker", "company_name", "sector", "market",
                               "index_source", "weight", "source"]
    assert fc._OUTPUT_COLS == ["indicator_code", "date", "value", "source"]


def test_unknown_price_source_raises():
    """알 수 없는 소스는 명확히 에러."""
    import pytest
    with pytest.raises(ValueError):
        pc.collect_stock_data(["AAPL"], source="unknown_source")
