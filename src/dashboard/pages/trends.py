import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = ROOT / "output" / "screener_full_ranked_universe.csv"


@st.cache_data
def load_data():

    if not DATA_PATH.exists():
        return pd.DataFrame()

    df = pd.read_csv(DATA_PATH)

    df["company_id"] = (
        df["company_id"]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    if "company_name" not in df.columns:
        df["company_name"] = df["company_id"]

    df["company_name"] = (
        df["company_name"]
        .fillna(df["company_id"])
        .astype(str)
    )

    df["broad_sector"] = (
        df.get("broad_sector_y")
        .fillna(df.get("broad_sector_x"))
        .fillna("Unknown")
    )

    if "year" in df.columns:
        df["year_numeric"] = (
            df["year"]
            .astype(str)
            .str.extract(r"(\d{4})")[0]
            .astype(float)
        )

    numeric_cols = [
        "return_on_equity_pct",
        "net_profit_margin_pct",
        "debt_to_equity",
        "pe_ratio",
        "pb_ratio",
        "free_cash_flow_cr",
        "composite_score"
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def show():

    st.title("📈 Financial Trends")

    df = load_data()

    if df.empty:
        st.error("No screener data found.")
        return

    sectors = ["All"] + sorted(df["broad_sector"].dropna().unique())

    sector = st.selectbox(
        "Sector",
        sectors
    )

    if sector == "All":
        filtered = df.copy()
    else:
        filtered = df[df["broad_sector"] == sector]

    companies = sorted(filtered["company_name"].unique())

    company = st.selectbox(
        "Company",
        companies
    )

    company_df = filtered[
        filtered["company_name"] == company
    ].sort_values("year_numeric")

    st.divider()

    c1, c2, c3, c4 = st.columns(4)

    latest = company_df.iloc[-1]

    c1.metric(
        "Latest Year",
        int(latest["year_numeric"])
    )

    if "return_on_equity_pct" in latest:
        c2.metric(
            "ROE",
            f"{latest['return_on_equity_pct']:.2f}%"
        )

    if "pe_ratio" in latest:
        c3.metric(
            "PE",
            f"{latest['pe_ratio']:.2f}"
        )

    if "composite_score" in latest:
        c4.metric(
            "Score",
            f"{latest['composite_score']:.2f}"
        )

    st.divider()

    metrics = {
        "ROE":"return_on_equity_pct",
        "Net Profit Margin":"net_profit_margin_pct",
        "Debt to Equity":"debt_to_equity",
        "PE Ratio":"pe_ratio",
        "PB Ratio":"pb_ratio",
        "Free Cash Flow":"free_cash_flow_cr",
        "Composite Score":"composite_score"
    }

    metric = st.selectbox(
        "Metric",
        list(metrics.keys())
    )

    column = metrics[metric]

    if column in company_df.columns:

        fig = px.line(
            company_df,
            x="year_numeric",
            y=column,
            markers=True,
            title=f"{metric} Trend"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    st.divider()

    st.subheader("Sector Average Trend")

    if column in filtered.columns:

        sector_avg = (
            filtered
            .groupby("year_numeric")[column]
            .mean()
            .reset_index()
        )

        fig = px.area(
            sector_avg,
            x="year_numeric",
            y=column,
            title=f"Average {metric}"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    st.divider()

    st.subheader("Company Financial History")

    cols = [
        "year",
        "return_on_equity_pct",
        "net_profit_margin_pct",
        "debt_to_equity",
        "pe_ratio",
        "pb_ratio",
        "free_cash_flow_cr",
        "composite_score"
    ]

    cols = [c for c in cols if c in company_df.columns]

    st.dataframe(
        company_df[cols],
        use_container_width=True,
        hide_index=True
    )

    csv = company_df.to_csv(index=False).encode()

    st.download_button(
        "⬇ Download Trend Data",
        csv,
        file_name=f"{company}_trend.csv",
        mime="text/csv"
    )