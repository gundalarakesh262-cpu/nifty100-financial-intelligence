import streamlit as st
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = ROOT / "output" / "screener_full_ranked_universe.csv"


@st.cache_data
def load_data():

    if not DATA_PATH.exists():
        return pd.DataFrame()

    df = pd.read_csv(DATA_PATH)

    df["company_id"] = df["company_id"].astype(str).str.upper().str.strip()

    if "company_name" not in df.columns:
        df["company_name"] = df["company_id"]

    return df


def show():

    st.title("👥 Peer Comparison")

    df = load_data()

    if df.empty:
        st.warning("No screener data found.")
        return

    peer_groups = sorted(df["peer_group_name"].dropna().unique())

    if len(peer_groups) == 0:
        st.warning("No peer groups available.")
        return

    selected_group = st.selectbox(
        "Peer Group",
        peer_groups
    )

    peer_df = df[df["peer_group_name"] == selected_group]

    company = st.selectbox(
        "Company",
        sorted(peer_df["company_name"].unique())
    )

    company_row = peer_df[
        peer_df["company_name"] == company
    ].iloc[0]

    st.success(f"Comparing {company} with its peers")

    st.markdown("---")

    metrics = [
        "return_on_equity_pct",
        "net_profit_margin_pct",
        "debt_to_equity",
        "pe_ratio",
        "pb_ratio",
        "composite_score"
    ]

    metrics = [m for m in metrics if m in peer_df.columns]

    comparison = peer_df[
        ["company_name"] + metrics
    ].copy()

    st.subheader("Peer Comparison Table")

    st.dataframe(
        comparison.sort_values(
            "composite_score",
            ascending=False
        ),
        width="stretch"
    )

    st.markdown("---")

    st.subheader("Selected Company")

    col1, col2, col3 = st.columns(3)

    if "return_on_equity_pct" in company_row:
        col1.metric(
            "ROE %",
            round(float(company_row["return_on_equity_pct"]),2)
        )

    if "debt_to_equity" in company_row:
        col2.metric(
            "Debt / Equity",
            round(float(company_row["debt_to_equity"]),2)
        )

    if "composite_score" in company_row:
        col3.metric(
            "Composite Score",
            round(float(company_row["composite_score"]),2)
        )

    st.markdown("---")

    st.subheader("Top Peer Rankings")

    ranking = peer_df.sort_values(
        "composite_score",
        ascending=False
    )

    st.bar_chart(
        ranking.set_index("company_name")["composite_score"]
    )