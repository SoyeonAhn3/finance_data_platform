"""키 없이 돌릴 수 있는 기본 점검 (구조/설정 로딩).

실행: 프로젝트 루트에서  pytest
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_symbols_yaml_loads():
    """config/symbols.yaml 이 파싱되고 필수 키를 갖는다."""
    import yaml

    data = yaml.safe_load((ROOT / "config" / "symbols.yaml").read_text(encoding="utf-8"))
    assert "universe" in data
    assert "indicators" in data
    assert len(data["indicators"]) >= 1


def test_config_imports_without_keys():
    """config 는 .env 없이도 import 되어야 한다 (validate 는 지연)."""
    from src.utils import config

    assert config.BQ_DATASET == "finance_db"
    assert config.DATE_RANGE_START == "2020-01-01"


def test_logger_writes():
    """로거/헬퍼가 예외 없이 동작한다."""
    from src.utils.logger import get_logger, log_stage

    logger = get_logger("test")
    log_stage(logger, "collect", "success", count=100, message="ok")


def test_setup_sql_has_all_tables():
    """setup.sql 이 11개 테이블을 모두 정의한다."""
    sql = (ROOT / "sql" / "setup.sql").read_text(encoding="utf-8")
    expected = [
        "raw_universe",
        "raw_daily_price",
        "raw_economic_indicator",
        "dim_date",
        "dim_symbol",
        "dim_indicator",
        "fact_daily_price",
        "fact_economic_indicator",
        "pipeline_execution_log",
        "data_quality_log",
    ]
    for table in expected:
        assert f"finance_db.{table}`" in sql, f"{table} 누락"
