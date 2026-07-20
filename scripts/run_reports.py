"""Run batch report generation for tearsheets, sector reports, portfolio summary, and related logs."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd


BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from src.analytics.cashflow_kpis import build_cashflow_intelligence, build_pattern_change_records
from src.reports.portfolio_report import build_portfolio_summary_pdf
from src.reports.sector_report import build_all_sector_reports
from src.reports.tearsheet import build_batch_tearsheets


PROCESSED_DIR = BASE / "data" / "processed"
OUTPUT_DIR = BASE / "output"
TEARSHEETS_DIR = BASE / "reports" / "tearsheets"
SECTOR_DIR = BASE / "reports" / "sector"
PORTFOLIO_DIR = BASE / "reports" / "portfolio"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEARSHEETS_DIR.mkdir(parents=True, exist_ok=True)
    SECTOR_DIR.mkdir(parents=True, exist_ok=True)
    PORTFOLIO_DIR.mkdir(parents=True, exist_ok=True)

    generated_tearsheets, skipped = build_batch_tearsheets(PROCESSED_DIR, TEARSHEETS_DIR)
    pd.DataFrame({"company_id": skipped}).to_csv(OUTPUT_DIR / "skipped_tearsheets.csv", index=False)

    sector_paths = build_all_sector_reports(PROCESSED_DIR, SECTOR_DIR)
    build_portfolio_summary_pdf(PROCESSED_DIR, PORTFOLIO_DIR)

    build_cashflow_intelligence(PROCESSED_DIR, OUTPUT_DIR)
    build_pattern_change_records(PROCESSED_DIR).to_csv(OUTPUT_DIR / "pattern_changes.csv", index=False)

    print({
        "generated_tearsheets": len(generated_tearsheets),
        "skipped_tearsheets": len(skipped),
        "sector_reports": len(sector_paths),
        "portfolio_reports": 1,
    })


if __name__ == "__main__":
    main()
