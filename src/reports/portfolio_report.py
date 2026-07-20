"""Portfolio summary PDF generation."""

from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import BaseDocTemplate, Frame, PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROCESSED_DIR = ROOT / "data" / "processed"
DEFAULT_OUTPUT_DIR = ROOT / "reports" / "portfolio"


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


def _arrow(prev: float, latest: float) -> str:
    if prev is None or latest is None:
        return "→"
    threshold = abs(prev) * 0.02 if prev != 0 else 0.0
    if latest > prev + threshold:
        return "↑"
    if latest < prev - threshold:
        return "↓"
    return "→"


def _metric_trend(prev: float, latest: float, higher_is_better: bool = True) -> str:
    if prev is None or latest is None:
        return "→"

    if prev == 0:
        return "→" if latest == 0 else ("↑" if higher_is_better and latest > 0 else "↓")

    change_pct = abs((latest - prev) / prev) * 100
    if change_pct <= 2:
        return "→"

    if higher_is_better:
        return "↑" if latest > prev else "↓"
    return "↑" if latest < prev else "↓"


def _latest_two_rows(frame: pd.DataFrame) -> tuple[pd.Series | None, pd.Series | None]:
    if frame.empty:
        return None, None
    ordered = frame.sort_values("year")
    latest = ordered.iloc[-1]
    previous = ordered.iloc[-2] if len(ordered) >= 2 else None
    return previous, latest


def _safe_value(value) -> str:
    if value is None or pd.isna(value):
        return "NA"
    return f"{value}"


def build_portfolio_summary_pdf(processed_dir: Path = DEFAULT_PROCESSED_DIR, output_dir: Path = DEFAULT_OUTPUT_DIR) -> Path:
    processed_dir = Path(processed_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    companies = _company_frame(processed_dir / "companies_cleaned.csv")
    sectors = _load_frame(processed_dir / "sectors_cleaned.csv")
    ratios = _load_frame(processed_dir / "financial_ratios_generated.csv")
    profit = _load_frame(processed_dir / "profitandloss_cleaned.csv")

    company_names = companies.set_index("company_id")["company_name"].to_dict()
    sector_map = sectors.set_index("company_id")["broad_sector"].to_dict()

    path = output_dir / "portfolio_summary.pdf"
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CompanyTitle", parent=styles["Title"], textColor=colors.HexColor("#0B1F3A"), fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="SectionLabel", parent=styles["Heading3"], textColor=colors.HexColor("#0B1F3A"), spaceAfter=3))
    styles.add(ParagraphStyle(name="BodySmall", parent=styles["BodyText"], fontSize=8.5, leading=10))
    doc = BaseDocTemplate(str(path), pagesize=A4, leftMargin=10 * mm, rightMargin=10 * mm, topMargin=10 * mm, bottomMargin=10 * mm)
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="frame")
    doc.addPageTemplates([PageTemplate(id="portfolio", frames=[frame])])

    story: List = [Paragraph("Portfolio Summary", styles["Title"]), Spacer(1, 4 * mm)]
    ordered_companies = sorted(companies["company_id"].astype(str).str.strip().str.upper().tolist())

    for index, company_id in enumerate(ordered_companies):
        ratio_hist = ratios[ratios["company_id"] == company_id].sort_values("year")
        pl_hist = profit[profit["company_id"] == company_id].sort_values("year")
        prev_ratio, latest_ratio = _latest_two_rows(ratio_hist)
        prev_profit, latest_profit = _latest_two_rows(pl_hist)

        company_name = company_names.get(company_id, company_id)
        sector_name = sector_map.get(company_id, "NA")

        def metric_cell(label: str, value: object, arrow: str) -> Paragraph:
            return Paragraph(f"<b>{label}</b><br/>{_safe_value(value)} <font color='#475569'>{arrow}</font>", styles["BodySmall"])

        kpi_rows = [
            [
                metric_cell("ROE %", latest_ratio["return_on_equity_pct"] if latest_ratio is not None else None, _metric_trend(prev_ratio["return_on_equity_pct"] if prev_ratio is not None else None, latest_ratio["return_on_equity_pct"] if latest_ratio is not None else None, True)),
                metric_cell("ROCE %", latest_ratio["return_on_capital_employed_pct"] if latest_ratio is not None else None, _metric_trend(prev_ratio["return_on_capital_employed_pct"] if prev_ratio is not None else None, latest_ratio["return_on_capital_employed_pct"] if latest_ratio is not None else None, True)),
                metric_cell("D/E", latest_ratio["debt_to_equity"] if latest_ratio is not None else None, _metric_trend(prev_ratio["debt_to_equity"] if prev_ratio is not None else None, latest_ratio["debt_to_equity"] if latest_ratio is not None else None, False)),
            ],
            [
                metric_cell("OPM %", latest_ratio["operating_profit_margin_pct"] if latest_ratio is not None else None, _metric_trend(prev_ratio["operating_profit_margin_pct"] if prev_ratio is not None else None, latest_ratio["operating_profit_margin_pct"] if latest_ratio is not None else None, True)),
                metric_cell("Revenue CAGR %", latest_ratio["revenue_cagr_5yr"] if latest_ratio is not None else None, _metric_trend(prev_ratio["revenue_cagr_5yr"] if prev_ratio is not None else None, latest_ratio["revenue_cagr_5yr"] if latest_ratio is not None else None, True)),
                metric_cell("PAT CAGR %", latest_ratio["pat_cagr_5yr"] if latest_ratio is not None else None, _metric_trend(prev_ratio["pat_cagr_5yr"] if prev_ratio is not None else None, latest_ratio["pat_cagr_5yr"] if latest_ratio is not None else None, True)),
            ],
        ]

        if index > 0:
            story.append(PageBreak())

        story.append(Paragraph(f"{company_name}", styles["CompanyTitle"]))
        story.append(Paragraph(f"Ticker: {company_id} | Sector: {sector_name}", styles["BodySmall"]))
        story.append(Spacer(1, 3 * mm))

        summary_table = Table(kpi_rows, colWidths=[58 * mm, 58 * mm, 58 * mm])
        summary_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EFF6FF")),
                    ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#F8FAFC")),
                    ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("WORDWRAP", (0, 0), (-1, -1), "CJK"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(summary_table)
        story.append(Spacer(1, 3 * mm))

        latest_net_profit = latest_profit["net_profit"] if latest_profit is not None else None
        prev_net_profit = prev_profit["net_profit"] if prev_profit is not None else None
        trend_text = _metric_trend(prev_net_profit, latest_net_profit, True)
        story.append(Paragraph(f"<b>Latest Net Profit Trend:</b> {trend_text}", styles["BodySmall"]))
        story.append(Paragraph(f"<b>Latest net profit:</b> {_safe_value(latest_net_profit)}", styles["BodySmall"]))

    doc.build(story)
    return path
