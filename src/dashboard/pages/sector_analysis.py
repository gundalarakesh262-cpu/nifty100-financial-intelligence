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

    df["broad_sector"] = (
        df.get("broad_sector_y")
        .fillna(df.get("broad_sector_x"))
        .fillna("Unknown")
    )

    if "company_name" not in df.columns:
        df["company_name"] = df["company_id"]

    numeric_cols = [
        "return_on_equity_pct",
        "pe_ratio",
        "pb_ratio",
        "composite_score",
        "market_cap_crore",
        "free_cash_flow_cr"
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def show():

    st.title("🏭 Sector Analysis")

    st.write("Sector-wise financial analysis across the Nifty 100 universe.")

    df = load_data()

    if df.empty:
        st.error("Screener data not found.")
        return

    sectors = sorted(df["broad_sector"].dropna().unique())

    selected_sector = st.selectbox(
        "Select Sector",
        ["All"] + sectors
    )

    if selected_sector == "All":
        sector_df = df.copy()
    else:
        sector_df = df[df["broad_sector"] == selected_sector]

    st.divider()

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Companies",
        sector_df["company_id"].nunique()
    )

    if "return_on_equity_pct" in sector_df.columns:
        c2.metric(
            "Average ROE",
            f"{sector_df['return_on_equity_pct'].mean():.2f}%"
        )

    if "pe_ratio" in sector_df.columns:
        c3.metric(
            "Average PE",
            f"{sector_df['pe_ratio'].mean():.2f}"
        )

    if "composite_score" in sector_df.columns:
        c4.metric(
            "Average Score",
            f"{sector_df['composite_score'].mean():.2f}"
        )

    st.divider()

    left, right = st.columns(2)

    with left:

        st.subheader("Companies by Sector")

        sector_count = (
            df.groupby("broad_sector")["company_id"]
            .nunique()
            .reset_index(name="Companies")
            .sort_values("Companies", ascending=False)
        )

        fig = px.bar(
            sector_count,
            x="broad_sector",
            y="Companies",
            text="Companies"
        )

        fig.update_layout(height=450)

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with right:

        st.subheader("Sector Distribution")

        fig = px.pie(
            sector_count,
            names="broad_sector",
            values="Companies",
            hole=0.45
        )

        fig.update_layout(height=450)

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    st.divider()

    st.subheader("Average ROE by Sector")

    if "return_on_equity_pct" in df.columns:

        roe = (
            df.groupby("broad_sector")["return_on_equity_pct"]
            .mean()
            .reset_index()
            .sort_values("return_on_equity_pct", ascending=False)
        )

        fig = px.bar(
            roe,
            x="broad_sector",
            y="return_on_equity_pct",
            color="return_on_equity_pct",
            text_auto=".2f"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    st.divider()

    st.subheader("Average PE by Sector")

    if "pe_ratio" in df.columns:

        pe = (
            df.groupby("broad_sector")["pe_ratio"]
            .mean()
            .reset_index()
            .sort_values("pe_ratio")
        )

        fig = px.bar(
            pe,
            x="broad_sector",
            y="pe_ratio",
            color="pe_ratio",
            text_auto=".1f"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    st.divider()

    st.subheader("Top Companies")

    sort_column = (
        "composite_score"
        if "composite_score" in sector_df.columns
        else "company_name"
    )

    table = sector_df.sort_values(
        sort_column,
        ascending=False
    )

    display_cols = [
        "company_id",
        "company_name",
        "broad_sector",
        "peer_group_name",
        "return_on_equity_pct",
        "pe_ratio",
        "pb_ratio",
        "composite_score"
    ]

    display_cols = [
        c for c in display_cols
        if c in table.columns
    ]

    st.dataframe(
        table[display_cols],
        use_container_width=True,
        hide_index=True
    )

    csv = table.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇ Download Sector Data",
        csv,
        file_name="sector_analysis.csv",
        mime="text/csv"
    )