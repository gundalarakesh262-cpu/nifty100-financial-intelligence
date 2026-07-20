"""Company tearsheet PDF generation."""

from __future__ import annotations

from pathlib import Path
from typing import List

import matplotlib.pyplot as plt
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import BaseDocTemplate, Frame, Image, PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROCESSED_DIR = ROOT / "data" / "processed"
DEFAULT_OUTPUT_DIR = ROOT / "reports" / "tearsheets"


def _load_frame(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing required data file: {path}")
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


def _chart_buffer():
    from io import BytesIO
    return BytesIO()


def _line_chart(years, series_a, series_b, title, label_a, label_b, color_a="#0B1F3A", color_b="#16A34A"):
    buffer = _chart_buffer()
    fig, ax1 = plt.subplots(figsize=(5.0, 2.7), dpi=180)
    ax2 = ax1.twinx()
    ax1.plot(years, series_a, marker="o", linewidth=1.6, color=color_a, label=label_a)
    ax2.plot(years, series_b, marker="s", linewidth=1.4, color=color_b, label=label_b)
    ax1.set_title(title, fontsize=9)
    ax1.tick_params(axis="x", labelrotation=45, labelsize=7)
    ax1.tick_params(axis="y", labelsize=7)
    ax2.tick_params(axis="y", labelsize=7)
    fig.tight_layout()
    fig.savefig(buffer, format="png", bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)
    return buffer


def _bar_chart(years, values, title, color="#0B1F3A"):
    buffer = _chart_buffer()
    fig, ax = plt.subplots(figsize=(5.0, 2.5), dpi=180)
    ax.bar(years, values, color=color)
    ax.set_title(title, fontsize=9)
    ax.tick_params(axis="x", labelrotation=45, labelsize=7)
    ax.tick_params(axis="y", labelsize=7)
    fig.tight_layout()
    fig.savefig(buffer, format="png", bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)
    return buffer


def _stacked_chart(years, rows, title):
    buffer = _chart_buffer()
    fig, ax = plt.subplots(figsize=(5.2, 2.5), dpi=180)
    equity = [row[0] for row in rows]
    borrowings = [row[1] for row in rows]
    liabilities = [row[2] for row in rows]
    ax.bar(years, equity, color="#0B1F3A", label="Equity")
    ax.bar(years, borrowings, bottom=equity, color="#3B82F6", label="Borrowings")
    ax.bar(years, liabilities, bottom=[a + b for a, b in zip(equity, borrowings)], color="#94A3B8", label="Other liabilities")
    ax.set_title(title, fontsize=9)
    ax.tick_params(axis="x", labelrotation=45, labelsize=7)
    ax.tick_params(axis="y", labelsize=7)
    ax.legend(fontsize=6, loc="upper left")
    fig.tight_layout()
    fig.savefig(buffer, format="png", bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)
    return buffer


def _waterfall_chart(labels, values, title):
    buffer = _chart_buffer()
    fig, ax = plt.subplots(figsize=(4.9, 2.2), dpi=180)
    colors_map = ["#0B1F3A", "#64748B", "#F59E0B", "#16A34A"]
    ax.bar(labels, values, color=colors_map[: len(values)])
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_title(title, fontsize=9)
    ax.tick_params(axis="x", labelrotation=20, labelsize=7)
    ax.tick_params(axis="y", labelsize=7)
    fig.tight_layout()
    fig.savefig(buffer, format="png", bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)
    return buffer


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TearTitle", parent=styles["Title"], textColor=colors.HexColor("#0B1F3A"), fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="Section", parent=styles["Heading3"], textColor=colors.HexColor("#0B1F3A"), spaceBefore=4, spaceAfter=3))
    styles.add(ParagraphStyle(name="BulletGreen", parent=styles["BodyText"], fontSize=8, leading=9, textColor=colors.HexColor("#166534"), leftIndent=6))
    styles.add(ParagraphStyle(name="BulletRed", parent=styles["BodyText"], fontSize=8, leading=9, textColor=colors.HexColor("#B91C1C"), leftIndent=6))
    styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontSize=8, leading=9))
    return styles


def _company_context(company_id: str, processed_dir: Path) -> dict:
    companies = _company_frame(processed_dir / "companies_cleaned.csv")
    pl = _load_frame(processed_dir / "profitandloss_cleaned.csv")
    cf = _load_frame(processed_dir / "cashflow_cleaned.csv")
    bs = _load_frame(processed_dir / "balancesheet_cleaned.csv")
    ratios = _load_frame(processed_dir / "financial_ratios_generated.csv")
    capital = _load_frame(processed_dir / "capital_allocation.csv") if (processed_dir / "capital_allocation.csv").exists() else pd.DataFrame()
    pros_cons = _load_frame(processed_dir / "prosandcons_cleaned.csv") if (processed_dir / "prosandcons_cleaned.csv").exists() else pd.DataFrame()
    sectors = _load_frame(processed_dir / "sectors_cleaned.csv") if (processed_dir / "sectors_cleaned.csv").exists() else pd.DataFrame()

    company_row = companies[companies["company_id"] == company_id].iloc[-1]
    return {
        "company": company_row,
        "pl": pl[pl["company_id"] == company_id].sort_values("year"),
        "cf": cf[cf["company_id"] == company_id].sort_values("year"),
        "bs": bs[bs["company_id"] == company_id].sort_values("year"),
        "ratios": ratios[ratios["company_id"] == company_id].sort_values("year"),
        "capital": capital[capital["company_id"] == company_id].sort_values("year") if not capital.empty else pd.DataFrame(),
        "pros": pros_cons[(pros_cons["company_id"] == company_id) & (pros_cons.get("pros").notna())]["pros"].astype(str).tolist() if not pros_cons.empty and "pros" in pros_cons.columns else [],
        "cons": pros_cons[(pros_cons["company_id"] == company_id) & (pros_cons.get("cons").notna())]["cons"].astype(str).tolist() if not pros_cons.empty and "cons" in pros_cons.columns else [],
        "sector": sectors[sectors["company_id"] == company_id].iloc[-1]["broad_sector"] if not sectors.empty and not sectors[sectors["company_id"] == company_id].empty else None,
    }


def _page_one(ctx: dict, styles) -> List:
    company = ctx["company"]
    ratios = ctx["ratios"]
    pl = ctx["pl"]
    story: List = [Paragraph(f"{company['company_name']} | {company['company_id']}", styles["TearTitle"]), Spacer(1, 3 * mm)]
    latest = ratios.iloc[-1] if not ratios.empty else None
    kpis = [[
        Paragraph(f"<b>ROE</b><br/>{latest['return_on_equity_pct']:.1f}%" if latest is not None and pd.notna(latest.get("return_on_equity_pct")) else "<b>ROE</b><br/>NA", styles["Small"]),
        Paragraph(f"<b>ROCE</b><br/>{latest['return_on_capital_employed_pct']:.1f}%" if latest is not None and pd.notna(latest.get("return_on_capital_employed_pct")) else "<b>ROCE</b><br/>NA", styles["Small"]),
        Paragraph(f"<b>D/E</b><br/>{latest['debt_to_equity']:.2f}" if latest is not None and pd.notna(latest.get("debt_to_equity")) else "<b>D/E</b><br/>NA", styles["Small"]),
    ], [
        Paragraph(f"<b>OPM</b><br/>{latest['operating_profit_margin_pct']:.1f}%" if latest is not None and pd.notna(latest.get("operating_profit_margin_pct")) else "<b>OPM</b><br/>NA", styles["Small"]),
        Paragraph(f"<b>PAT CAGR</b><br/>{latest['pat_cagr_5yr']:.1f}%" if latest is not None and pd.notna(latest.get("pat_cagr_5yr")) else "<b>PAT CAGR</b><br/>NA", styles["Small"]),
        Paragraph(f"<b>Revenue CAGR</b><br/>{latest['revenue_cagr_5yr']:.1f}%" if latest is not None and pd.notna(latest.get("revenue_cagr_5yr")) else "<b>Revenue CAGR</b><br/>NA", styles["Small"]),
    ]]
    story.append(Table(kpis, colWidths=[58 * mm, 58 * mm, 58 * mm], style=TableStyle([("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#CBD5E1")), ("WORDWRAP", (0, 0), (-1, -1), "CJK"), ("VALIGN", (0, 0), (-1, -1), "TOP")])))
    story.append(Spacer(1, 2 * mm))

    years = pl["year"].tail(10).tolist()
    if years:
        story.append(Table([[Image(_bar_chart(years, pl["sales"].tail(10).tolist(), "Revenue"), width=85 * mm, height=42 * mm), Image(_bar_chart(years, pl["net_profit"].tail(10).tolist(), "Net Profit", color="#16A34A"), width=85 * mm, height=42 * mm)]], colWidths=[88 * mm, 88 * mm]))
        story.append(Spacer(1, 2 * mm))
    if not ratios.empty:
        story.append(Image(_line_chart(ratios["year"].tail(10).tolist(), ratios["return_on_equity_pct"].tail(10).tolist(), ratios["return_on_capital_employed_pct"].tail(10).tolist(), "ROE and ROCE", "ROE", "ROCE"), width=170 * mm, height=48 * mm))
    return story


def _page_two(ctx: dict, styles) -> List:
    story: List = [Paragraph("Balance Sheet composition", styles["Section"])]
    bs = ctx["bs"]
    cf = ctx["cf"]
    capital = ctx["capital"]
    if not bs.empty:
        story.append(Image(_stacked_chart(bs["year"].tail(8).tolist(), list(zip(bs["equity_capital"].tail(8), bs["borrowings"].tail(8), bs["other_liabilities"].tail(8))), "Balance Sheet Composition"), width=170 * mm, height=46 * mm))
    story.append(Paragraph("Cash Flow waterfall", styles["Section"]))
    if not cf.empty:
        latest = cf.iloc[-1]
        story.append(Image(_waterfall_chart(["CFO", "CFI", "CFF", "Net"], [latest["operating_activity"], latest["investing_activity"], latest["financing_activity"], latest["net_cash_flow"]], "Latest Year Cash Flow"), width=170 * mm, height=44 * mm))
    story.append(Paragraph("Pros", styles["Section"]))
    for text in ctx["pros"][:4]:
        story.append(Paragraph(f"• {text}", styles["BulletGreen"]))
    story.append(Paragraph("Cons", styles["Section"]))
    for text in ctx["cons"][:4]:
        story.append(Paragraph(f"• {text}", styles["BulletRed"]))
    if not capital.empty:
        story.append(Paragraph(f"Capital Allocation: {capital.iloc[-1]['pattern_label']}", styles["Section"]))
    return story


def build_tearsheet_pdf(company_id: str, processed_dir: Path = DEFAULT_PROCESSED_DIR, output_dir: Path = DEFAULT_OUTPUT_DIR) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    ctx = _company_context(company_id, Path(processed_dir))
    path = output_dir / f"{company_id}_tearsheet.pdf"

    styles = _styles()
    doc = BaseDocTemplate(str(path), pagesize=A4, leftMargin=10 * mm, rightMargin=10 * mm, topMargin=10 * mm, bottomMargin=10 * mm)
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="frame")
    doc.addPageTemplates([PageTemplate(id="one", frames=[frame])])

    story = _page_one(ctx, styles) + [PageBreak()] + _page_two(ctx, styles)
    doc.build(story)
    return path


def build_batch_tearsheets(processed_dir: Path = DEFAULT_PROCESSED_DIR, output_dir: Path = DEFAULT_OUTPUT_DIR, min_years: int = 3):
    companies = _company_frame(Path(processed_dir) / "companies_cleaned.csv")
    profit = _load_frame(Path(processed_dir) / "profitandloss_cleaned.csv")
    generated = []
    skipped = []
    company_col = "company_id" if "company_id" in companies.columns else "id"
    for company_id in companies[company_col].astype(str).str.strip().str.upper().tolist():
        if profit[profit["company_id"] == company_id].shape[0] < min_years:
            skipped.append(company_id)
            continue
        generated.append(build_tearsheet_pdf(company_id, processed_dir, output_dir))
    return generated, skipped
