from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px


# ---------------------------------------------------------
# Page Config
# ---------------------------------------------------------
st.set_page_config(
    page_title="Nifty 100 Financial Intelligence Platform",
    page_icon="📊",
    layout="wide"
)


# ---------------------------------------------------------
# Path Setup
# ---------------------------------------------------------
# app.py is inside src/dashboard/
# repo root = two folders above this file
ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data" / "processed"

RATIOS_PATH = DATA_DIR / "financial_ratios_generated.csv"
SCREENER_PATH = DATA_DIR / "screener_full_ranked_universe.csv"
PRESET_PATH = DATA_DIR / "screener_presets_summary.csv"
SECTORS_PATH = DATA_DIR / "sectors_cleaned.csv"
COMPANIES_PATH = DATA_DIR / "companies_cleaned.csv"


# ---------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------
@st.cache_data
def load_csv(path: Path):
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


def format_number(value, decimals=2):
    if pd.isna(value):
        return "N/A"
    return f"{value:,.{decimals}f}"


def format_pct(value):
    if pd.isna(value):
        return "N/A"
    return f"{value:,.2f}%"


# ---------------------------------------------------------
# Load Data
# ---------------------------------------------------------
ratios = load_csv(RATIOS_PATH)
screener = load_csv(SCREENER_PATH)
preset_summary = load_csv(PRESET_PATH)
sectors = load_csv(SECTORS_PATH)
companies = load_csv(COMPANIES_PATH)


# ---------------------------------------------------------
# Basic Validation
# ---------------------------------------------------------
if ratios.empty:
    st.error(
        "financial_ratios_generated.csv not found. "
        "Please place it inside data/processed/."
    )
    st.stop()


# ---------------------------------------------------------
# Prepare Latest Universe
# ---------------------------------------------------------
ratios["fiscal_year"] = pd.to_numeric(ratios["fiscal_year"], errors="coerce")

latest = (
    ratios
    .dropna(subset=["fiscal_year"])
    .sort_values(["company_id", "fiscal_year"])
    .groupby("company_id")
    .tail(1)
    .reset_index(drop=True)
)

# If screener output exists, use it for ranking.
# Otherwise fall back to latest ratio data.
if not screener.empty:
    dashboard_data = screener.copy()
else:
    dashboard_data = latest.copy()

dashboard_data["fiscal_year"] = pd.to_numeric(
    dashboard_data["fiscal_year"],
    errors="coerce"
)


# ---------------------------------------------------------
# Header
# ---------------------------------------------------------
st.title("📊 Nifty 100 Financial Intelligence Platform")
st.caption(
    "A financial analytics dashboard for company screening, KPI tracking, "
    "sector comparison, and investment intelligence."
)

st.divider()


# ---------------------------------------------------------
# Market Health Banner
# ---------------------------------------------------------
company_count = dashboard_data["company_id"].nunique()
latest_year = int(dashboard_data["fiscal_year"].max())

median_roe = dashboard_data["return_on_equity_pct"].median()
median_roce = dashboard_data["return_on_capital_employed_pct"].median()
median_pe = dashboard_data["pe_ratio"].median()
median_score = (
    dashboard_data["composite_score"].median()
    if "composite_score" in dashboard_data.columns
    else None
)

if median_roe >= 15 and median_roce >= 15:
    health_status = "Healthy"
    health_message = "Overall fundamentals look strong based on median ROE and ROCE."
elif median_roe >= 10:
    health_status = "Moderate"
    health_message = "Overall fundamentals look acceptable, but selectivity is needed."
else:
    health_status = "Cautious"
    health_message = "Median profitability is weak; deeper company-level screening is required."

st.info(f"**Market Health: {health_status}** — {health_message}")


# ---------------------------------------------------------
# KPI Cards
# ---------------------------------------------------------
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Companies Covered", company_count)

with col2:
    st.metric("Latest Year", latest_year)

with col3:
    st.metric("Median ROE", format_pct(median_roe))

with col4:
    st.metric("Median ROCE", format_pct(median_roce))

with col5:
    if median_score is not None:
        st.metric("Median Score", format_number(median_score))
    else:
        st.metric("Median P/E", format_number(median_pe))


st.divider()


# ---------------------------------------------------------
# Main Layout
# ---------------------------------------------------------
left_col, right_col = st.columns([1.2, 1])


# ---------------------------------------------------------
# Top Ranked Companies
# ---------------------------------------------------------
with left_col:
    st.subheader("🏆 Top Ranked Companies")

    ranking_cols = [
        "company_id",
        "company_name",
        "broad_sector",
        "fiscal_year",
        "composite_score",
        "return_on_equity_pct",
        "return_on_capital_employed_pct",
        "debt_to_equity",
        "free_cash_flow_cr",
        "pe_ratio",
        "pb_ratio",
    ]

    ranking_cols = [col for col in ranking_cols if col in dashboard_data.columns]

    if "composite_score" in dashboard_data.columns:
        top_ranked = dashboard_data.sort_values(
            "composite_score",
            ascending=False
        ).head(10)
    else:
        top_ranked = dashboard_data.sort_values(
            "return_on_equity_pct",
            ascending=False
        ).head(10)

    st.dataframe(
        top_ranked[ranking_cols],
        use_container_width=True,
        hide_index=True
    )


# ---------------------------------------------------------
# Preset Screener Summary
# ---------------------------------------------------------
with right_col:
    st.subheader("🎯 Screener Presets")

    if not preset_summary.empty:
        st.dataframe(
            preset_summary,
            use_container_width=True,
            hide_index=True
        )

        if {"preset_name", "company_count"}.issubset(preset_summary.columns):
            fig = px.bar(
                preset_summary,
                x="preset_name",
                y="company_count",
                title="Companies Passing Each Preset",
                text="company_count"
            )
            fig.update_layout(
                xaxis_title="Preset",
                yaxis_title="Company Count",
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning(
            "screener_presets_summary.csv not found. "
            "Run Investment_Screener.ipynb first."
        )


st.divider()


# ---------------------------------------------------------
# Sector Distribution
# ---------------------------------------------------------
st.subheader("🏭 Sector Distribution")

if "broad_sector" in dashboard_data.columns:
    sector_counts = (
        dashboard_data["broad_sector"]
        .fillna("Unknown")
        .value_counts()
        .reset_index()
    )
    sector_counts.columns = ["broad_sector", "company_count"]

    fig_sector = px.pie(
        sector_counts,
        names="broad_sector",
        values="company_count",
        title="Nifty 100 Companies by Sector",
        hole=0.35
    )

    st.plotly_chart(fig_sector, use_container_width=True)

else:
    st.warning(
        "Sector data not available. Upload sectors_cleaned.csv "
        "or ensure broad_sector exists in screener output."
    )


st.divider()


# ---------------------------------------------------------
# Quick Filters Preview
# ---------------------------------------------------------
st.subheader("🔎 Quick Company Lookup")

company_list = sorted(dashboard_data["company_id"].dropna().unique())

selected_company = st.selectbox(
    "Select a company",
    company_list
)

company_row = dashboard_data[
    dashboard_data["company_id"] == selected_company
].head(1)

if not company_row.empty:
    c = company_row.iloc[0]

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric("ROE", format_pct(c.get("return_on_equity_pct")))

    with c2:
        st.metric("ROCE", format_pct(c.get("return_on_capital_employed_pct")))

    with c3:
        st.metric("Debt / Equity", format_number(c.get("debt_to_equity")))

    with c4:
        st.metric("P/E", format_number(c.get("pe_ratio")))

    detail_cols = [
        "company_id",
        "company_name",
        "broad_sector",
        "sub_sector",
        "fiscal_year",
        "composite_score",
        "net_profit_margin_pct",
        "free_cash_flow_cr",
        "revenue_cagr_5y_pct",
        "pat_cagr_5y_pct",
        "capital_allocation_pattern",
    ]

    detail_cols = [col for col in detail_cols if col in company_row.columns]

    st.dataframe(
        company_row[detail_cols],
        use_container_width=True,
        hide_index=True
    )


# ---------------------------------------------------------
# Data Availability Section
# ---------------------------------------------------------
with st.expander("📁 Data files detected"):
    file_status = pd.DataFrame({
        "file": [
            "financial_ratios_generated.csv",
            "screener_full_ranked_universe.csv",
            "screener_presets_summary.csv",
            "sectors_cleaned.csv",
            "companies_cleaned.csv",
        ],
        "status": [
            RATIOS_PATH.exists(),
            SCREENER_PATH.exists(),
            PRESET_PATH.exists(),
            SECTORS_PATH.exists(),
            COMPANIES_PATH.exists(),
        ]
    })

    st.dataframe(file_status, use_container_width=True, hide_index=True)


# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------
st.caption(
    "Dashboard Home Screen · Built with Streamlit · "
    "Data source: Financial Ratio Engine + Investment Screener outputs"
)
