import pandas as pd
import streamlit as st
import plotly.express as px
import re
from pathlib import Path

from src.etl.normaliser import normalize_year

ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = ROOT / "output" / "capital_allocation.csv"


def parse_year_date(value: str) -> pd.Timestamp:
    if pd.isna(value):
        return pd.NaT

    year_str = str(value).strip()
    if not year_str:
        return pd.NaT

    normalized = normalize_year(year_str)
    if normalized:
        try:
            year_part, month_part = normalized.split("-")
            return pd.Timestamp(year=int(year_part), month=int(month_part), day=1)
        except Exception:
            return pd.NaT

    month_map = {
        "JAN": 1,
        "FEB": 2,
        "MAR": 3,
        "APR": 4,
        "MAY": 5,
        "JUN": 6,
        "JUL": 7,
        "AUG": 8,
        "SEP": 9,
        "OCT": 10,
        "NOV": 11,
        "DEC": 12,
    }

    match = re.match(r"^([A-Z]{3})[\s-]+(\d{2,4})$", year_str.upper())
    if match:
        month_text, year_text = match.groups()
        month = month_map.get(month_text)
        if month is not None:
            year = int(year_text)
            if year < 100:
                year += 2000
            return pd.Timestamp(year=year, month=month, day=1)

    match = re.match(r"^(\d{4})$", year_str)
    if match:
        return pd.Timestamp(year=int(match.group(1)), month=3, day=1)

    return pd.NaT


def display_value(value, fallback: str = "N/A") -> str:
    if pd.isna(value):
        return fallback

    text = str(value).strip()
    return text if text else fallback


@st.cache_data
def load_capital(path: Path, modified: float):

    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    df["company_id"] = (
        df["company_id"]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    if "year" in df.columns:
        df["year"] = df["year"].astype(str).str.strip()
        df["year_date"] = df["year"].apply(parse_year_date)

    return df


def show():

    st.title("💰 Capital Allocation Dashboard")
    st.write("Analyze how companies allocate operating, investing and financing cash flows.")

    df = load_capital(
        DATA_PATH,
        DATA_PATH.stat().st_mtime if DATA_PATH.exists() else 0.0,
    )

    if df.empty:
        st.warning("capital_allocation.csv not found.")
        return

    companies = sorted(df["company_id"].dropna().unique())

    company = st.selectbox(
        "Select Company",
        companies
    )

    company_df = df[df["company_id"] == company].copy()
    if company_df.empty:
        st.warning("No capital allocation rows found for the selected company.")
        return

    if "year_date" in company_df.columns and not company_df["year_date"].isna().all():
        company_df = company_df.sort_values("year_date")
        latest = company_df.loc[company_df["year_date"].idxmax()]
    else:
        company_df = company_df.sort_values("year")
        latest = company_df.iloc[-1]

    st.markdown("### Latest Capital Allocation")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Operating",
        display_value(latest.get("cfo_sign"))
    )

    c2.metric(
        "Investing",
        display_value(latest.get("cfi_sign"))
    )

    c3.metric(
        "Financing",
        display_value(latest.get("cff_sign"))
    )

    c4.metric(
        "Pattern",
        display_value(latest.get("pattern_label"))
    )

    st.markdown("---")

    st.subheader("Capital Allocation History")

    history_df = company_df.drop(columns=["year_date"]) if "year_date" in company_df.columns else company_df
    st.dataframe(
        history_df.fillna("N/A").reset_index(drop=True),
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

    x_axis = "year_date" if "year_date" in chart_df.columns else "year"
    fig = px.line(
        chart_df,
        x=x_axis,
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