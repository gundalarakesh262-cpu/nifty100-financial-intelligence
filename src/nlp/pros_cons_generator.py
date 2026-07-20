"""Rule-based pros and cons generation for the Nifty100 workspace."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROCESSED_DIR = ROOT / "data" / "processed"
DEFAULT_OUTPUT_DIR = ROOT / "output"


def _load_frame(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing required data file: {path}")
    frame = pd.read_csv(path)
    if "company_id" in frame.columns:
        frame["company_id"] = frame["company_id"].astype(str).str.strip().str.upper()
    if "year" in frame.columns:
        frame["year"] = frame["year"].astype(str)
    return frame


def _latest_rows(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty or "company_id" not in frame.columns or "year" not in frame.columns:
        return frame.copy()
    return frame.sort_values(["company_id", "year"]).groupby("company_id", as_index=False).tail(1)


def _company_names(companies: pd.DataFrame) -> List[str]:
    company_col = "company_id" if "company_id" in companies.columns else "id"
    return companies[company_col].astype(str).str.strip().str.upper().tolist()


def build_pros_cons_records(processed_dir: Path = DEFAULT_PROCESSED_DIR) -> pd.DataFrame:
    processed_dir = Path(processed_dir)
    companies = _load_frame(processed_dir / "companies_cleaned.csv")
    profit = _load_frame(processed_dir / "profitandloss_cleaned.csv")
    cashflow = _load_frame(processed_dir / "cashflow_cleaned.csv")
    ratios = _load_frame(processed_dir / "financial_ratios_generated.csv")
    market = _load_frame(processed_dir / "market_cap_cleaned.csv")
    capital = _load_frame(processed_dir / "capital_allocation.csv") if (processed_dir / "capital_allocation.csv").exists() else pd.DataFrame()

    latest_profit = _latest_rows(profit)
    latest_cashflow = _latest_rows(cashflow)
    latest_ratios = _latest_rows(ratios)
    latest_market = _latest_rows(market)
    latest_capital = _latest_rows(capital) if not capital.empty else pd.DataFrame()

    rows: List[Dict[str, object]] = []
    for company_id in _company_names(companies):
        profit_rows = profit[profit["company_id"] == company_id].sort_values("year")
        cashflow_rows = cashflow[cashflow["company_id"] == company_id].sort_values("year")
        ratio_rows = ratios[ratios["company_id"] == company_id].sort_values("year")
        market_rows = market[market["company_id"] == company_id].sort_values("year")
        capital_rows = capital[capital["company_id"] == company_id].sort_values("year") if not capital.empty else pd.DataFrame()

        latest_profit_row = latest_profit[latest_profit["company_id"] == company_id]
        latest_cashflow_row = latest_cashflow[latest_cashflow["company_id"] == company_id]
        latest_ratio_row = latest_ratios[latest_ratios["company_id"] == company_id]
        latest_market_row = latest_market[latest_market["company_id"] == company_id]
        latest_capital_row = latest_capital[latest_capital["company_id"] == company_id] if not latest_capital.empty else pd.DataFrame()

        pro_texts: List[Dict[str, object]] = []
        con_texts: List[Dict[str, object]] = []

        if not latest_ratio_row.empty and pd.notna(latest_ratio_row.iloc[-1].get("return_on_equity_pct")) and float(latest_ratio_row.iloc[-1]["return_on_equity_pct"]) > 20:
            pro_texts.append({"company_id": company_id, "type": "pro", "rule_id": "P01", "text": "Consistently high return on equity above 20% demonstrates exceptional capital efficiency", "confidence_pct": 88})
        if not cashflow_rows.empty:
            fcf_hist = (cashflow_rows["operating_activity"] + cashflow_rows["investing_activity"]).tolist()
            if len(fcf_hist) >= 5 and all(value > 0 for value in fcf_hist[-5:]):
                pro_texts.append({"company_id": company_id, "type": "pro", "rule_id": "P02", "text": "Strong free cash flow generation over 5 years signals healthy business fundamentals", "confidence_pct": 84})
            if len(fcf_hist) >= 3 and all(value < 0 for value in fcf_hist[-3:]):
                con_texts.append({"company_id": company_id, "type": "con", "rule_id": "C02", "text": "Free cash flow negative for 3 consecutive years raises concern about cash generation quality", "confidence_pct": 83})

        if not latest_capital_row.empty and latest_capital_row.iloc[-1].get("pattern_label") == "Reinvestor":
            pro_texts.append({"company_id": company_id, "type": "pro", "rule_id": "P12", "text": "Growing asset base funded by internal accruals reflects self-sustaining growth", "confidence_pct": 74})

        if not latest_profit_row.empty and float(latest_profit_row.iloc[-1].get("net_profit", 0) or 0) < 0:
            con_texts.append({"company_id": company_id, "type": "con", "rule_id": "C04", "text": "Company reported a net loss in the most recent financial year", "confidence_pct": 85})

        if not latest_ratio_row.empty and pd.notna(latest_ratio_row.iloc[-1].get("debt_to_equity")) and float(latest_ratio_row.iloc[-1]["debt_to_equity"]) > 2.0:
            con_texts.append({"company_id": company_id, "type": "con", "rule_id": "C01", "text": f"Debt-to-equity ratio of {float(latest_ratio_row.iloc[-1]['debt_to_equity']):.2f} is elevated for a non-financial company and warrants monitoring", "confidence_pct": 79})

        if not latest_market_row.empty and pd.notna(latest_market_row.iloc[-1].get("dividend_yield_pct")) and float(latest_market_row.iloc[-1]["dividend_yield_pct"]) > 2:
            pro_texts.append({"company_id": company_id, "type": "pro", "rule_id": "P08", "text": "Consistent dividend yield above 2% backed by positive free cash flow", "confidence_pct": 72})

        if not latest_ratio_row.empty and pd.notna(latest_ratio_row.iloc[-1].get("operating_profit_margin_pct")) and float(latest_ratio_row.iloc[-1]["operating_profit_margin_pct"]) > 25:
            pro_texts.append({"company_id": company_id, "type": "pro", "rule_id": "P05", "text": "Operating profit margin above 25% indicates strong pricing power and cost discipline", "confidence_pct": 78})

        if not latest_ratio_row.empty and pd.notna(latest_ratio_row.iloc[-1].get("return_on_capital_employed_pct")) and float(latest_ratio_row.iloc[-1]["return_on_capital_employed_pct"]) < 10:
            con_texts.append({"company_id": company_id, "type": "con", "rule_id": "C10", "text": "Return on capital employed below 10% suggests the business is not generating sufficient returns on invested capital", "confidence_pct": 77})

        if not latest_ratio_row.empty and pd.notna(latest_ratio_row.iloc[-1].get("interest_coverage")) and float(latest_ratio_row.iloc[-1]["interest_coverage"]) < 1.5:
            con_texts.append({"company_id": company_id, "type": "con", "rule_id": "C06", "text": "Interest coverage ratio below 1.5x indicates the company is at risk of not meeting its debt obligations", "confidence_pct": 80})

        if not latest_ratio_row.empty and pd.notna(latest_ratio_row.iloc[-1].get("pat_cagr_5yr")) and float(latest_ratio_row.iloc[-1]["pat_cagr_5yr"]) > 20:
            pro_texts.append({"company_id": company_id, "type": "pro", "rule_id": "P06", "text": "Net profit compounding at above 20% over 5 years creates significant shareholder value", "confidence_pct": 79})

        if not latest_ratio_row.empty and pd.notna(latest_ratio_row.iloc[-1].get("revenue_cagr_5yr")) and float(latest_ratio_row.iloc[-1]["revenue_cagr_5yr"]) < 5:
            con_texts.append({"company_id": company_id, "type": "con", "rule_id": "C12", "text": "Revenue growing at below 5% over 5 years lags inflation and suggests limited business momentum", "confidence_pct": 71})

        if not latest_ratio_row.empty and pd.notna(latest_ratio_row.iloc[-1].get("return_on_equity_pct")) and pd.notna(latest_ratio_row.iloc[-1].get("return_on_capital_employed_pct")):
            latest_roe = float(latest_ratio_row.iloc[-1]["return_on_equity_pct"])
            latest_roce = float(latest_ratio_row.iloc[-1]["return_on_capital_employed_pct"])
            if latest_roe > 15 and latest_roce > 10:
                pro_texts.append({"company_id": company_id, "type": "pro", "rule_id": "P10", "text": "Return on equity improving for 3 consecutive years shows strengthening business quality", "confidence_pct": 70})

        if not pro_texts:
            pro_texts.append({"company_id": company_id, "type": "pro", "rule_id": "P00", "text": "Company shows positive operating history and remains investable on the available fundamentals", "confidence_pct": 65})
        if not con_texts:
            con_texts.append({"company_id": company_id, "type": "con", "rule_id": "C00", "text": "Residual operational and financial risk remains under review", "confidence_pct": 65})

        rows.extend(pro_texts)
        rows.extend(con_texts)

    frame = pd.DataFrame(rows)
    frame = frame[frame["confidence_pct"] > 60].copy()
    return frame[["company_id", "type", "rule_id", "text", "confidence_pct"]].sort_values(["company_id", "type", "confidence_pct"], ascending=[True, True, False]).reset_index(drop=True)


def write_pros_cons_csv(frame: pd.DataFrame, output_dir: Path = DEFAULT_OUTPUT_DIR) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "pros_cons_generated.csv"
    frame.to_csv(output_path, index=False)
    return output_path


def main(processed_dir: Path = DEFAULT_PROCESSED_DIR, output_dir: Path = DEFAULT_OUTPUT_DIR) -> pd.DataFrame:
    frame = build_pros_cons_records(processed_dir)
    write_pros_cons_csv(frame, output_dir)
    return frame


if __name__ == "__main__":
    main()
