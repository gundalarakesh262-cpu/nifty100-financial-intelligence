"""Sector PDF report generation."""

from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROCESSED_DIR = ROOT / "data" / "processed"
DEFAULT_OUTPUT_DIR = ROOT / "reports" / "sector"


def _load_frame(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    if "company_id" in frame.columns:
        frame["company_id"] = frame["company_id"].astype(str).str.strip().str.upper()
    if "year" in frame.columns:
        frame["year"] = frame["year"].astype(str)
    return frame


def _company_frame(path: Path) -> pd.DataFrame:
    frame = _load_frame(path)
    if "company_id" not in frame.columns and "id" in frame.columns:
        frame = frame.rename(columns={"id": "company_id"})
    frame["company_id"] = frame["company_id"].astype(str).str.strip().str.upper()
    return frame


def build_sector_report_pdf(sector_name: str, processed_dir: Path = DEFAULT_PROCESSED_DIR, output_dir: Path = DEFAULT_OUTPUT_DIR) -> Path:
    processed_dir = Path(processed_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    sectors = _load_frame(processed_dir / "sectors_cleaned.csv")
    companies = _company_frame(processed_dir / "companies_cleaned.csv")
    ratios = _load_frame(processed_dir / "financial_ratios_generated.csv")

    sector_company_ids = sectors[sectors["broad_sector"] == sector_name]["company_id"].tolist()
    latest = ratios[ratios["company_id"].isin(sector_company_ids)].sort_values(["company_id", "year"]).groupby("company_id", as_index=False).tail(1)
    company_names = companies.set_index("company_id")["company_name"].to_dict()

    path = output_dir / f"{sector_name}_report.pdf"
    styles = getSampleStyleSheet()

    doc = BaseDocTemplate(str(path), pagesize=A4, leftMargin=10 * mm, rightMargin=10 * mm, topMargin=10 * mm, bottomMargin=10 * mm)
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="frame")
    doc.addPageTemplates([PageTemplate(id="sector", frames=[frame])])

    story: List = [Paragraph(f"{sector_name} Sector Report", styles["Title"]), Spacer(1, 4 * mm)]
    medians = latest[["return_on_equity_pct", "return_on_capital_employed_pct", "debt_to_equity", "operating_profit_margin_pct", "revenue_cagr_5yr", "pat_cagr_5yr", "eps_cagr_5yr", "composite_quality_score"]].median(numeric_only=True)
    summary_rows = [["Metric", "Median"]] + [[metric, f"{value:.2f}" if pd.notna(value) else "NA"] for metric, value in medians.items()]
    summary = Table(summary_rows, colWidths=[90 * mm, 60 * mm])
    summary.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B1F3A")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")), ("WORDWRAP", (0, 0), (-1, -1), "CJK")]))
    story.append(summary)
    story.append(Spacer(1, 4 * mm))

    table_rows = [["Company", "ROE", "ROCE", "D/E", "OPM", "Revenue CAGR", "PAT CAGR", "EPS CAGR", "Quality"]]
    for row in latest.itertuples(index=False):
        table_rows.append([
            company_names.get(row.company_id, row.company_id),
            f"{row.return_on_equity_pct:.1f}" if pd.notna(row.return_on_equity_pct) else "NA",
            f"{row.return_on_capital_employed_pct:.1f}" if pd.notna(row.return_on_capital_employed_pct) else "NA",
            f"{row.debt_to_equity:.2f}" if pd.notna(row.debt_to_equity) else "NA",
            f"{row.operating_profit_margin_pct:.1f}" if pd.notna(row.operating_profit_margin_pct) else "NA",
            f"{row.revenue_cagr_5yr:.1f}" if pd.notna(row.revenue_cagr_5yr) else "NA",
            f"{row.pat_cagr_5yr:.1f}" if pd.notna(row.pat_cagr_5yr) else "NA",
            f"{row.eps_cagr_5yr:.1f}" if pd.notna(row.eps_cagr_5yr) else "NA",
            f"{row.composite_quality_score:.2f}" if pd.notna(row.composite_quality_score) else "NA",
        ])
    company_table = Table(table_rows, colWidths=[50 * mm, 14 * mm, 14 * mm, 14 * mm, 14 * mm, 16 * mm, 16 * mm, 14 * mm, 18 * mm])
    company_table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#166534")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")), ("FONTSIZE", (0, 0), (-1, -1), 6.5), ("WORDWRAP", (0, 0), (-1, -1), "CJK")]))
    story.append(company_table)
    doc.build(story)
    return path


def build_all_sector_reports(processed_dir: Path = DEFAULT_PROCESSED_DIR, output_dir: Path = DEFAULT_OUTPUT_DIR) -> List[Path]:
    sectors = _load_frame(Path(processed_dir) / "sectors_cleaned.csv")
    paths: List[Path] = []
    for sector_name in sorted(sectors["broad_sector"].dropna().astype(str).unique().tolist()):
        paths.append(build_sector_report_pdf(sector_name, processed_dir, output_dir))

    summary_path = output_dir / "All_Sectors_report.pdf"
    ratios = _load_frame(Path(processed_dir) / "financial_ratios_generated.csv")
    styles = getSampleStyleSheet()
    doc = BaseDocTemplate(str(summary_path), pagesize=A4, leftMargin=10 * mm, rightMargin=10 * mm, topMargin=10 * mm, bottomMargin=10 * mm)
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="frame")
    doc.addPageTemplates([PageTemplate(id="summary", frames=[frame])])
    latest = ratios.sort_values(["company_id", "year"]).groupby("company_id", as_index=False).tail(1)
    summary_rows = [["Sector", "Companies", "Median ROE", "Median ROCE", "Median OPM"]]
    sector_join = latest.merge(sectors[["company_id", "broad_sector"]].rename(columns={"broad_sector": "sector_group"}), on="company_id", how="left")
    for sector_name, sector_frame in sector_join.groupby("sector_group"):
        summary_rows.append([
            str(sector_name),
            str(sector_frame.shape[0]),
            f"{sector_frame['return_on_equity_pct'].median():.2f}" if pd.notna(sector_frame['return_on_equity_pct'].median()) else "NA",
            f"{sector_frame['return_on_capital_employed_pct'].median():.2f}" if pd.notna(sector_frame['return_on_capital_employed_pct'].median()) else "NA",
            f"{sector_frame['operating_profit_margin_pct'].median():.2f}" if pd.notna(sector_frame['operating_profit_margin_pct'].median()) else "NA",
        ])
    summary = Table(summary_rows, colWidths=[50 * mm, 24 * mm, 28 * mm, 28 * mm, 28 * mm])
    summary.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B1F3A")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")), ("FONTSIZE", (0, 0), (-1, -1), 7), ("WORDWRAP", (0, 0), (-1, -1), "CJK")]))
    doc.build([Paragraph("All Sectors Summary", styles["Title"]), Spacer(1, 4 * mm), summary])
    paths.append(summary_path)
    return paths
