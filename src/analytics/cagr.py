"""CAGR engine for revenue, profit and EPS growth metrics."""

import math
from typing import List, Optional, Tuple


CAGR_FLAG_DECLINE_TO_LOSS = "DECLINE_TO_LOSS"
CAGR_FLAG_TURNAROUND = "TURNAROUND"
CAGR_FLAG_BOTH_NEGATIVE = "BOTH_NEGATIVE"
CAGR_FLAG_ZERO_BASE = "ZERO_BASE"
CAGR_FLAG_INSUFFICIENT = "INSUFFICIENT"


def compute_cagr(start_value: float, end_value: float, years: int) -> Tuple[Optional[float], Optional[str]]:
    """Compute CAGR percentage for an interval with edge case handling."""
    if years <= 0:
        raise ValueError("years must be a positive integer")

    if start_value is None or end_value is None:
        return None, CAGR_FLAG_INSUFFICIENT

    if start_value == 0:
        return None, CAGR_FLAG_ZERO_BASE

    if start_value > 0 and end_value > 0:
        cagr_value = math.pow(end_value / start_value, 1 / years) - 1
        return cagr_value * 100, None

    if start_value > 0 and end_value < 0:
        return None, CAGR_FLAG_DECLINE_TO_LOSS

    if start_value < 0 and end_value > 0:
        return None, CAGR_FLAG_TURNAROUND

    if start_value < 0 and end_value < 0:
        return None, CAGR_FLAG_BOTH_NEGATIVE

    # If end_value is zero and start_value positive, compute normally to allow -100% case.
    if start_value > 0 and end_value == 0:
        return -100.0, None

    # If start_value is negative and end_value == 0, treat as insufficiently defined for CAGR.
    return None, CAGR_FLAG_INSUFFICIENT


def cagr_from_history(values: List[Optional[float]], years: int) -> Tuple[Optional[float], Optional[str]]:
    """Compute CAGR from a history series over the requested window."""
    if len(values) < years + 1:
        return None, CAGR_FLAG_INSUFFICIENT

    start_value = values[-(years + 1)]
    end_value = values[-1]
    return compute_cagr(start_value, end_value, years)


def revenue_cagr(start_revenue: float, end_revenue: float, years: int) -> Tuple[Optional[float], Optional[str]]:
    """Return revenue CAGR and flag."""
    return compute_cagr(start_revenue, end_revenue, years)


def pat_cagr(start_pat: float, end_pat: float, years: int) -> Tuple[Optional[float], Optional[str]]:
    """Return PAT CAGR and flag."""
    return compute_cagr(start_pat, end_pat, years)


def eps_cagr(start_eps: float, end_eps: float, years: int) -> Tuple[Optional[float], Optional[str]]:
    """Return EPS CAGR and flag."""
    return compute_cagr(start_eps, end_eps, years)
