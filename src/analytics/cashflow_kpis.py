"""Cash flow KPI calculators, intelligence outputs, and capital allocation pattern classification."""

import csv
import os
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font


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


def _load_frame(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing required data file: {path}")
    frame = pd.read_csv(path)
    if "company_id" in frame.columns:
        frame["company_id"] = frame["company_id"].astype(str).str.strip().str.upper()
    if "year" in frame.columns:
        frame["year"] = frame["year"].astype(str)
    return frame


def _latest_per_company(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    sort_cols = [column for column in ["company_id", "year"] if column in frame.columns]
    if sort_cols:
        frame = frame.sort_values(sort_cols)
    return frame.groupby("company_id", as_index=False).tail(1)


def _write_excel(frame: pd.DataFrame, path: Path) -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Cashflow Intelligence"
    worksheet.append(list(frame.columns))
    for row in frame.itertuples(index=False):
        worksheet.append(list(row))

    for cell in worksheet[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(wrap_text=True, vertical="top")
    for row in worksheet.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")

    widths = {
        "A": 16,
        "B": 16,
        "C": 18,
        "D": 18,
        "E": 18,
        "F": 16,
        "G": 16,
        "H": 18,
        "I": 12,
        "J": 14,
        "K": 22,
    }
    for column_name, width in widths.items():
        worksheet.column_dimensions[column_name].width = width
    workbook.save(path)


def build_cashflow_intelligence(processed_dir: Path, output_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    processed_dir = Path(processed_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    companies = _load_frame(processed_dir / "companies_cleaned.csv")
    profit = _load_frame(processed_dir / "profitandloss_cleaned.csv")
    cashflow = _load_frame(processed_dir / "cashflow_cleaned.csv")
    balancesheet = _load_frame(processed_dir / "balancesheet_cleaned.csv")
    ratios = _load_frame(processed_dir / "financial_ratios_generated.csv")
    sectors = _load_frame(processed_dir / "sectors_cleaned.csv") if (processed_dir / "sectors_cleaned.csv").exists() else pd.DataFrame()
    capital = _load_frame(processed_dir / "capital_allocation.csv") if (processed_dir / "capital_allocation.csv").exists() else pd.DataFrame()

    latest_cf = _latest_per_company(cashflow)
    latest_pl = _latest_per_company(profit)
    latest_bs = _latest_per_company(balancesheet)
    latest_ratios = _latest_per_company(ratios)
    latest_capital = _latest_per_company(capital) if not capital.empty else pd.DataFrame()

    records: List[Dict[str, object]] = []
    distress_rows: List[Dict[str, object]] = []

    company_col = "company_id" if "company_id" in companies.columns else "id"
    for company_id in companies[company_col].astype(str).str.strip().str.upper().tolist():
        cf_company = cashflow[cashflow["company_id"] == company_id].sort_values("year")
        pl_company = profit[profit["company_id"] == company_id].sort_values("year")
        bs_company = balancesheet[balancesheet["company_id"] == company_id].sort_values("year")
        ratio_company = ratios[ratios["company_id"] == company_id].sort_values("year")
        capital_company = capital[capital["company_id"] == company_id].sort_values("year") if not capital.empty else pd.DataFrame()

        latest_cf_row = latest_cf[latest_cf["company_id"] == company_id]
        latest_pl_row = latest_pl[latest_pl["company_id"] == company_id]
        latest_bs_row = latest_bs[latest_bs["company_id"] == company_id]
        latest_ratio_row = latest_ratios[latest_ratios["company_id"] == company_id]
        latest_cap_row = latest_capital[latest_capital["company_id"] == company_id] if not latest_capital.empty else pd.DataFrame()

        cfo_history = cf_company["operating_activity"].tolist()
        pat_history = pl_company["net_profit"].tolist()
        investing_history = cf_company["investing_activity"].tolist()

        cfo_score = cfo_quality_score(cfo_history, pat_history)
        cfo_label = cfo_quality_label(cfo_score)

        capex_pct = None
        capex_label = None
        fcf_conversion_pct = None
        fcf_cagr_5yr = None
        distress_flag = False
        deleveraging_flag = False
        capital_allocation_label = latest_cap_row.iloc[-1]["pattern_label"] if not latest_cap_row.empty else None
        sector = sectors[sectors["company_id"] == company_id].iloc[-1]["broad_sector"] if not sectors.empty and not sectors[sectors["company_id"] == company_id].empty else (latest_ratio_row.iloc[-1]["broad_sector"] if not latest_ratio_row.empty and "broad_sector" in latest_ratio_row.columns else None)

        if not latest_cf_row.empty and not latest_pl_row.empty:
            capex_pct = capex_intensity(latest_pl_row.iloc[-1]["sales"], latest_cf_row.iloc[-1]["investing_activity"])
            capex_label = capex_intensity_label(capex_pct)
            fcf_conversion_pct = fcf_conversion_rate(free_cash_flow(latest_cf_row.iloc[-1]["operating_activity"], latest_cf_row.iloc[-1]["investing_activity"]), latest_pl_row.iloc[-1]["operating_profit"])
            if latest_cf_row.iloc[-1]["operating_activity"] < 0 and latest_cf_row.iloc[-1]["financing_activity"] > 0:
                distress_flag = True
                distress_rows.append({
                    "company_id": company_id,
                    "cfo_value": latest_cf_row.iloc[-1]["operating_activity"],
                    "cff_value": latest_cf_row.iloc[-1]["financing_activity"],
                    "latest_net_profit": latest_pl_row.iloc[-1]["net_profit"],
                })

        if len(cashflow[cashflow["company_id"] == company_id]) >= 2 and len(bs_company) >= 2:
            if latest_cf_row.iloc[-1]["financing_activity"] < 0 and bs_company.iloc[-1]["borrowings"] < bs_company.iloc[-2]["borrowings"]:
                deleveraging_flag = True

        if len(cfo_history) >= 6:
            start_fcf = free_cash_flow(cfo_history[-6], investing_history[-6])
            end_fcf = free_cash_flow(cfo_history[-1], investing_history[-1])
            if start_fcf and end_fcf and start_fcf > 0 and end_fcf > 0:
                fcf_cagr_5yr = ((end_fcf / start_fcf) ** (1 / 5) - 1) * 100

        records.append({
            "company_id": company_id,
            "sector": sector,
            "cfo_quality_score": cfo_score,
            "cfo_quality_label": cfo_label,
            "capex_intensity_pct": capex_pct,
            "capex_label": capex_label,
            "fcf_cagr_5yr": fcf_cagr_5yr,
            "fcf_conversion_pct": fcf_conversion_pct,
            "distress_flag": distress_flag,
            "deleveraging_flag": deleveraging_flag,
            "capital_allocation_label": capital_allocation_label,
        })

    intelligence_df = pd.DataFrame(records)
    distress_df = pd.DataFrame(distress_rows)

    xlsx_path = output_dir / "cashflow_intelligence.xlsx"
    csv_path = output_dir / "distress_alerts.csv"
    _write_excel(intelligence_df, xlsx_path)
    distress_df.to_csv(csv_path, index=False)
    return intelligence_df, distress_df


def build_pattern_change_records(processed_dir: Path) -> pd.DataFrame:
    processed_dir = Path(processed_dir)
    capital = _load_frame(processed_dir / "capital_allocation.csv")
    capital = capital.sort_values(["company_id", "year"])
    rows = []
    for company_id, group in capital.groupby("company_id"):
        group = group.reset_index(drop=True)
        if len(group) < 2:
            continue
        previous = group.iloc[-2]
        latest = group.iloc[-1]
        if previous["pattern_label"] != latest["pattern_label"]:
            rows.append({
                "company_id": company_id,
                "previous_year": previous["year"],
                "latest_year": latest["year"],
                "previous_pattern": previous["pattern_label"],
                "latest_pattern": latest["pattern_label"],
            })
    return pd.DataFrame(rows)
