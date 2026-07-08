import sys
import os

current_dir = os.path.abspath(os.path.dirname(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.analytics.cagr import (
    compute_cagr,
    cagr_from_history,
    revenue_cagr,
    pat_cagr,
    eps_cagr,
    CAGR_FLAG_DECLINE_TO_LOSS,
    CAGR_FLAG_TURNAROUND,
    CAGR_FLAG_BOTH_NEGATIVE,
    CAGR_FLAG_ZERO_BASE,
    CAGR_FLAG_INSUFFICIENT,
)


def test_compute_cagr_normal():
    value, flag = compute_cagr(100, 125, 5)
    assert round(value, 4) == 4.5640
    assert flag is None


def test_compute_cagr_turnaround_flag():
    value, flag = compute_cagr(-50, 100, 5)
    assert value is None
    assert flag == CAGR_FLAG_TURNAROUND


def test_compute_cagr_decline_to_loss_flag():
    value, flag = compute_cagr(50, -10, 5)
    assert value is None
    assert flag == CAGR_FLAG_DECLINE_TO_LOSS


def test_compute_cagr_both_negative_flag():
    value, flag = compute_cagr(-50, -100, 5)
    assert value is None
    assert flag == CAGR_FLAG_BOTH_NEGATIVE


def test_compute_cagr_zero_base_flag():
    value, flag = compute_cagr(0, 100, 5)
    assert value is None
    assert flag == CAGR_FLAG_ZERO_BASE


def test_compute_cagr_insufficient_data_flag():
    value, flag = cagr_from_history([100, 110, 120], 5)
    assert value is None
    assert flag == CAGR_FLAG_INSUFFICIENT


def test_revenue_cagr_5yr():
    value, flag = revenue_cagr(200, 400, 5)
    assert round(value, 4) == 14.8698
    assert flag is None


def test_pat_cagr_5yr():
    value, flag = pat_cagr(100, 150, 5)
    assert round(value, 4) == 8.4472
    assert flag is None


def test_eps_cagr_5yr():
    value, flag = eps_cagr(20, 30, 5)
    assert round(value, 4) == 8.4472
    assert flag is None


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-q"])
