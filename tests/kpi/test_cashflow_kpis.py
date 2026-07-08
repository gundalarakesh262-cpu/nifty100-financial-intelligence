import sys
import os

current_dir = os.path.abspath(os.path.dirname(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.analytics.cashflow_kpis import (
    free_cash_flow,
    cfo_pat_ratio,
    cfo_quality_score,
    cfo_quality_label,
    capex_intensity,
    capex_intensity_label,
    fcf_conversion_rate,
    capital_allocation_pattern_label,
    generate_capital_allocation_rows,
)


def test_free_cash_flow_positive_and_negative():
    assert free_cash_flow(100, -30) == 70


def test_cfo_pat_ratio_returns_none_on_zero_pat():
    assert cfo_pat_ratio(100, 0) is None


def test_cfo_quality_score_high_quality():
    cfo_history = [100, 110, 120, 130, 140]
    pat_history = [80, 90, 100, 110, 120]
    assert round(cfo_quality_score(cfo_history, pat_history), 4) == 1.2041


def test_cfo_quality_score_none_on_zero_pat():
    cfo_history = [100, 110, 120, 130, 140]
    pat_history = [80, 90, 0, 110, 120]
    assert cfo_quality_score(cfo_history, pat_history) is None


def test_capex_intensity_labels():
    assert capex_intensity_label(capex_intensity(1000, -10)) == "Asset Light"
    assert capex_intensity_label(capex_intensity(1000, -50)) == "Moderate"
    assert capex_intensity_label(capex_intensity(1000, -200)) == "Capital Intensive"


def test_fcf_conversion_rate_none_on_zero_operating_profit():
    assert fcf_conversion_rate(50, 0) is None


def test_capital_allocation_pattern_labels():
    assert capital_allocation_pattern_label(100, -50, -20) == "Reinvestor"
    assert capital_allocation_pattern_label(100, -50, -20, 2.0) == "Shareholder Returns"
    assert capital_allocation_pattern_label(100, 50, -20) == "Liquidating Assets"
    assert capital_allocation_pattern_label(-100, 50, 50) == "Distress Signal"
    assert capital_allocation_pattern_label(-100, -50, 50) == "Growth Funded by Debt"
    assert capital_allocation_pattern_label(100, 50, 20) == "Cash Accumulator"
    assert capital_allocation_pattern_label(-100, -50, -20) == "Pre-Revenue"
    assert capital_allocation_pattern_label(100, -50, 20) == "Mixed"


def test_generate_capital_allocation_rows_creates_expected_output():
    rows = [
        {
            "company_id": "TCS",
            "year": "2024",
            "cfo": 100,
            "cfi": -50,
            "cff": -20,
            "cfo_pat_ratio": 1.2,
        }
    ]
    output = generate_capital_allocation_rows(rows)
    assert output == [
        {
            "company_id": "TCS",
            "year": "2024",
            "cfo_sign": "+",
            "cfi_sign": "-",
            "cff_sign": "-",
            "pattern_label": "Shareholder Returns",
        }
    ]


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-q"])
