import streamlit as st
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = ROOT / "output" / "screener_full_ranked_universe.csv"
OUTPUT_PATH = ROOT / "output" / "valuation_summary.xlsx"


# ---------------------------------------------------------
# Load Data
# ---------------------------------------------------------
@st.cache_data
def load_data():

    if not DATA_PATH.exists():
        return pd.DataFrame()

    df = pd.read_csv(DATA_PATH)

    # Company ID
    if "company_id" in df.columns:
        df["company_id"] = (
            df["company_id"]
            .astype(str)
            .str.upper()
            .str.strip()
        )

    # Company Name
    if "company_name" not in df.columns:
        df["company_name"] = df["company_id"]

    df["company_name"] = (
        df["company_name"]
        .fillna(df["company_id"])
        .astype(str)
        .str.strip()
    )

    numeric_cols = [
        "free_cash_flow_cr",
        "earnings_per_share",
        "book_value_per_share",
        "composite_score",
        "score_fcf",
        "score_fcf_yield",
        "score_pe",
        "score_pb"
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


# ---------------------------------------------------------
# Calculate Valuation
# ---------------------------------------------------------
def calculate_valuation(df):

    df = df.copy()

    # FCF Yield Score
    if "score_fcf_yield" in df.columns:
        df["FCF Yield Score"] = df["score_fcf_yield"]
    else:
        df["FCF Yield Score"] = 0

    # PE Flag
    def pe_flag(score):

        if pd.isna(score):
            return "Unknown"

        if score >= 8:
            return "Cheap"

        elif score >= 5:
            return "Fair"

        else:
            return "Expensive"

    if "score_pe" in df.columns:
        df["PE Flag"] = df["score_pe"].apply(pe_flag)
    else:
        df["PE Flag"] = "Unknown"

    # Overall Valuation
    def valuation(score):

        if pd.isna(score):
            return "Unknown"

        if score >= 80:
            return "Undervalued"

        elif score >= 60:
            return "Fair Value"

        else:
            return "Overvalued"

    df["Valuation"] = df["composite_score"].apply(valuation)

    return df


# ---------------------------------------------------------
# Dashboard
# ---------------------------------------------------------
def show():

    st.title("💰 Valuation Dashboard")

    df = load_data()

    if df.empty:
        st.error("No screener dataset found.")
        return

    valuation_df = calculate_valuation(df)

    valuation_df["company_name"] = (
        valuation_df["company_name"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    valuation_df = valuation_df[
        valuation_df["company_name"] != ""
    ]

    companies = sorted(
        valuation_df["company_name"].dropna().astype(str).unique(),
        key=str.lower
    )

    company = st.selectbox(
        "Select Company",
        companies
    )

    row = valuation_df[
        valuation_df["company_name"] == company
    ].iloc[0]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Composite Score",
        f"{row.get('composite_score',0):.2f}"
    )

    c2.metric(
        "EPS",
        f"{row.get('earnings_per_share',0):.2f}"
    )

    c3.metric(
        "Book Value",
        f"{row.get('book_value_per_share',0):.2f}"
    )

    c4.metric(
        "Free Cash Flow",
        f"{row.get('free_cash_flow_cr',0):,.2f}"
    )

    st.divider()

    left, right = st.columns(2)

    with left:
        st.success(f"PE Flag : **{row['PE Flag']}**")

    with right:
        st.info(f"Valuation : **{row['Valuation']}**")

    st.divider()

    display_cols = [
        "company_id",
        "company_name",
        "free_cash_flow_cr",
        "earnings_per_share",
        "book_value_per_share",
        "FCF Yield Score",
        "PE Flag",
        "Valuation",
        "composite_score"
    ]

    display_cols = [
        c for c in display_cols
        if c in valuation_df.columns
    ]

    display = valuation_df[display_cols].copy()

    st.subheader("Valuation Summary")

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True
    )

    # CSV Download
    csv = display.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇ Download CSV",
        csv,
        "valuation_summary.csv",
        "text/csv"
    )

    # Excel Export
    try:
        display.to_excel(
            OUTPUT_PATH,
            index=False
        )

        st.success(
            f"Excel exported successfully:\n{OUTPUT_PATH}"
        )

    except Exception as e:
        st.error(str(e))


if __name__ == "__main__":
    show()