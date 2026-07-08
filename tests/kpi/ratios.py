import sys
import os

current_dir = os.path.abspath(os.path.dirname(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    roe,
    roce,
    roa,
    opm_difference,
    debt_to_equity,
    high_leverage_flag,
    interest_coverage_ratio,
    icr_label,
    net_debt,
    asset_turnover,
)


def test_net_profit_margin_normal():
    assert net_profit_margin(50, 200) == 25.0


def test_net_profit_margin_zero_sales():
    assert net_profit_margin(50, 0) is None


def test_roe_negative_equity_returns_none():
    assert roe(10, -5, -5) is None


def test_roce_normal():
    assert round(roce(20, 50, 10, 30), 4) == 22.2222


def test_roa_zero_assets():
    assert roa(10, 0) is None


def test_operating_profit_margin_normal():
    assert operating_profit_margin(40, 200) == 20.0


def test_debt_to_equity_zero_borrowings_returns_zero():
    assert debt_to_equity(0, 100, 50) == 0.0


def test_interest_coverage_zero_interest_returns_none():
    assert interest_coverage_ratio(100, 20, 0) is None


def test_icr_label_debt_free():
    assert icr_label(None) == "Debt Free"
    assert icr_label(2.0) is None


def test_high_de_ratio_flag_for_non_financials():
    assert high_leverage_flag(5.1, "Industrials") is True


def test_high_de_ratio_flag_suppressed_for_financials():
    assert high_leverage_flag(6.0, "Financials") is False


def test_opm_cross_check_mismatch_flag():
    computed = operating_profit_margin(25, 100)
    diff, flag = opm_difference(computed, 23.5)
    assert round(diff, 4) == 1.5
    assert flag is True


def test_opm_cross_check_no_flag():
    computed = operating_profit_margin(25, 100)
    diff, flag = opm_difference(computed, 24.5)
    assert round(diff, 4) == 0.5
    assert flag is False


def test_net_debt_and_asset_turnover():
    assert net_debt(150, 40) == 110
    assert asset_turnover(200, 100) == 2.0
    assert asset_turnover(200, 0) is None


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-q"])
