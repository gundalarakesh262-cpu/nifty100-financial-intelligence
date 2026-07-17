import pandas as pd
import streamlit as st
import plotly.express as px
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = ROOT / "output" / "capital_allocation.csv"


@st.cache_data
def load_capital():

    if not DATA_PATH.exists():
        return pd.DataFrame()

    df = pd.read_csv(DATA_PATH)

    df["company_id"] = (
        df["company_id"]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce")

    return df


def show():

    st.title("💰 Capital Allocation Dashboard")
    st.write("Analyze how companies allocate operating, investing and financing cash flows.")

    df = load_capital()

    if df.empty:
        st.warning("capital_allocation.csv not found.")
        return

    companies = sorted(df["company_id"].dropna().unique())

    company = st.selectbox(
        "Select Company",
        companies
    )

    company_df = (
        df[df["company_id"] == company]
        .sort_values("year")
    )

    latest = company_df.iloc[-1]

    st.markdown("### Latest Capital Allocation")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Operating",
        latest["cfo_sign"]
    )

    c2.metric(
        "Investing",
        latest["cfi_sign"]
    )

    c3.metric(
        "Financing",
        latest["cff_sign"]
    )

    c4.metric(
        "Pattern",
        latest["pattern_label"]
    )

    st.markdown("---")

    st.subheader("Capital Allocation History")

    st.dataframe(
        company_df.reset_index(drop=True),
        use_container_width=True
    )

    st.markdown("---")

    st.subheader("Cash Flow Direction by Year")

    chart_df = company_df.copy()

    chart_df["CFO"] = chart_df["cfo_sign"].map({
        "+": 1,
        "-": -1
    })

    chart_df["CFI"] = chart_df["cfi_sign"].map({
        "+": 1,
        "-": -1
    })

    chart_df["CFF"] = chart_df["cff_sign"].map({
        "+": 1,
        "-": -1
    })

    fig = px.line(
        chart_df,
        x="year",
        y=["CFO", "CFI", "CFF"],
        markers=True,
        title="Cash Flow Sign Trend"
    )

    fig.update_layout(
        yaxis=dict(
            tickvals=[-1, 1],
            ticktext=["Negative", "Positive"]
        ),
        legend_title="Cash Flow"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.markdown("---")

    st.subheader("Pattern Distribution")

    pattern_counts = (
        df["pattern_label"]
        .value_counts()
        .reset_index()
    )

    pattern_counts.columns = [
        "Pattern",
        "Count"
    ]

    fig2 = px.bar(
        pattern_counts,
        x="Pattern",
        y="Count",
        text="Count",
        title="Capital Allocation Patterns Across Companies"
    )

    st.plotly_chart(
        fig2,
        use_container_width=True
    )


if __name__ == "__main__":
    show()