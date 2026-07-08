"""Profitability, leverage, and efficiency ratio functions."""

from typing import Optional, Tuple


def net_profit_margin(net_profit: float, sales: float) -> Optional[float]:
    """Return net profit margin percentage or None if sales is zero."""
    if sales == 0 or sales is None:
        return None
    return (net_profit / sales) * 100


def operating_profit_margin(operating_profit: float, sales: float) -> Optional[float]:
    """Return operating profit margin percentage or None if sales is zero."""
    if sales == 0 or sales is None:
        return None
    return (operating_profit / sales) * 100


def roe(net_profit: float, equity_capital: float, reserves: float) -> Optional[float]:
    """Return return on equity percentage or None if equity plus reserves is <= 0."""
    equity_base = (equity_capital or 0) + (reserves or 0)
    if equity_base <= 0:
        return None
    return (net_profit / equity_base) * 100


def roce(ebit: float, equity_capital: float, reserves: float, borrowings: float) -> Optional[float]:
    """Return return on capital employed percentage or None if capital employed is <= 0."""
    capital_employed = (equity_capital or 0) + (reserves or 0) + (borrowings or 0)
    if capital_employed <= 0:
        return None
    return (ebit / capital_employed) * 100


def roa(net_profit: float, total_assets: float) -> Optional[float]:
    """Return return on assets percentage or None if total assets is zero."""
    if total_assets == 0 or total_assets is None:
        return None
    return (net_profit / total_assets) * 100


def opm_difference(
    computed_opm: Optional[float],
    opm_percentage: Optional[float],
    threshold: float = 1.0,
) -> Tuple[Optional[float], bool]:
    """Cross-check computed OPM against reported opm_percentage.

    Returns the absolute difference and a flag indicating whether it exceeds the threshold.
    """
    if computed_opm is None or opm_percentage is None:
        return None, False

    diff = abs(computed_opm - opm_percentage)
    return diff, diff > threshold


def debt_to_equity(
    borrowings: float,
    equity_capital: float,
    reserves: float,
) -> Optional[float]:
    """Return debt-to-equity ratio, or 0 when borrowings are zero."""
    borrowings_val = 0 if borrowings is None else borrowings
    if borrowings_val == 0:
        return 0.0

    equity_base = (equity_capital or 0) + (reserves or 0)
    if equity_base == 0:
        return None
    return borrowings_val / equity_base


def high_leverage_flag(
    debt_to_equity_ratio: Optional[float],
    broad_sector: Optional[str],
    threshold: float = 5.0,
) -> bool:
    """Return True if D/E is high and company is not in the Financials sector."""
    if debt_to_equity_ratio is None:
        return False

    if broad_sector and broad_sector.strip().lower() == "financials":
        return False

    return debt_to_equity_ratio > threshold


def interest_coverage_ratio(
    operating_profit: float,
    other_income: float,
    interest: float,
) -> Optional[float]:
    """Return interest coverage ratio or None if interest is zero."""
    if interest == 0 or interest is None:
        return None
    return (operating_profit or 0 + other_income or 0) / interest


def icr_label(icr: Optional[float]) -> Optional[str]:
    """Return Debt Free label when ICR is unavailable."""
    return "Debt Free" if icr is None else None


def icr_warning_flag(icr: Optional[float], threshold: float = 1.5) -> bool:
    """Return True when interest coverage is below the warning threshold."""
    if icr is None:
        return False
    return icr < threshold


def net_debt(borrowings: float, investments: float) -> float:
    """Return net debt using borrowings minus investments."""
    return (borrowings or 0) - (investments or 0)


def asset_turnover(sales: float, total_assets: float) -> Optional[float]:
    """Return asset turnover or None if total assets is zero."""
    if total_assets == 0 or total_assets is None:
        return None
    return (sales or 0) / total_assets
