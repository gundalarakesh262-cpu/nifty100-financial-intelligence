"""Cash flow KPI calculators and capital allocation pattern classification."""

import csv
import os
from typing import Dict, Iterable, List, Optional, Tuple


def free_cash_flow(operating_activity: float, investing_activity: float) -> float:
    """Return free cash flow. Negative values are allowed."""
    return (operating_activity or 0) + (investing_activity or 0)


def cfo_pat_ratio(cfo: float, pat: float) -> Optional[float]:
    """Return the CFO/PAT ratio or None when PAT is zero or missing."""
    if pat == 0 or pat is None:
        return None
    return (cfo or 0) / pat


def cfo_quality_score(cfo_history: List[Optional[float]], pat_history: List[Optional[float]]) -> Optional[float]:
    """Return average CFO/PAT ratio over the last 5 years or None if PAT is zero or insufficient."""
    if len(cfo_history) < 5 or len(pat_history) < 5:
        return None

    last_cfo = cfo_history[-5:]
    last_pat = pat_history[-5:]
    ratios = []
    for cfo, pat in zip(last_cfo, last_pat):
        if pat == 0 or pat is None:
            return None
        ratios.append((cfo or 0) / pat)

    if not ratios:
        return None
    return sum(ratios) / len(ratios)


def cfo_quality_label(score: Optional[float]) -> Optional[str]:
    """Return CFO quality classification based on average CFO/PAT ratio."""
    if score is None:
        return None
    if score > 1.0:
        return "High Quality"
    if score >= 0.5:
        return "Moderate"
    return "Accrual Risk"


def capex_intensity(sales: float, investing_activity: float) -> Optional[float]:
    """Return CapEx Intensity percentage or None when sales is zero or missing."""
    if sales == 0 or sales is None:
        return None
    return abs(investing_activity or 0) / sales * 100


def capex_intensity_label(intensity_pct: Optional[float]) -> Optional[str]:
    """Return CapEx intensity category label."""
    if intensity_pct is None:
        return None
    if intensity_pct < 3:
        return "Asset Light"
    if intensity_pct <= 8:
        return "Moderate"
    return "Capital Intensive"


def fcf_conversion_rate(fcf: float, operating_profit: float) -> Optional[float]:
    """Return FCF conversion rate percentage or None if operating profit is zero."""
    if operating_profit == 0 or operating_profit is None:
        return None
    return (fcf or 0) / operating_profit * 100


def cashflow_sign(value: Optional[float]) -> str:
    """Return the sign label used by the capital allocation pattern."""
    if value is None:
        return "-"
    return "+" if value >= 0 else "-"


def capital_allocation_pattern_label(
    cfo: float,
    cfi: float,
    cff: float,
    cfo_pat_ratio_value: Optional[float] = None,
) -> str:
    """Return the capital allocation pattern label for a company-year."""
    signs = (cashflow_sign(cfo), cashflow_sign(cfi), cashflow_sign(cff))
    if signs == ("+", "-", "-"):
        if cfo_pat_ratio_value is not None and cfo_pat_ratio_value > 1.0:
            return "Shareholder Returns"
        return "Reinvestor"
    if signs == ("+", "+", "-"):
        return "Liquidating Assets"
    if signs == ("-", "+", "+"):
        return "Distress Signal"
    if signs == ("-", "-", "+"):
        return "Growth Funded by Debt"
    if signs == ("+", "+", "+"):
        return "Cash Accumulator"
    if signs == ("-", "-", "-"):
        return "Pre-Revenue"
    if signs == ("+", "-", "+"):
        return "Mixed"
    return "Mixed"


def generate_capital_allocation_rows(
    rows: Iterable[Dict[str, object]],
) -> List[Dict[str, object]]:
    """Generate capital allocation output rows from input cashflow rows."""
    output_rows: List[Dict[str, object]] = []
    for row in rows:
        cfo = row.get("cfo")
        cfi = row.get("cfi")
        cff = row.get("cff")
        cfo_pat_ratio_value = row.get("cfo_pat_ratio")
        pattern_label = capital_allocation_pattern_label(cfo, cfi, cff, cfo_pat_ratio_value)

        output_rows.append(
            {
                "company_id": row.get("company_id"),
                "year": row.get("year"),
                "cfo_sign": cashflow_sign(cfo),
                "cfi_sign": cashflow_sign(cfi),
                "cff_sign": cashflow_sign(cff),
                "pattern_label": pattern_label,
            }
        )
    return output_rows


def write_capital_allocation_csv(rows: List[Dict[str, object]], file_path: str) -> None:
    """Write capital allocation rows to a CSV file."""
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

    fieldnames = [
        "company_id",
        "year",
        "cfo_sign",
        "cfi_sign",
        "cff_sign",
        "pattern_label",
    ]

    with open(file_path, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
