import streamlit as st
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

SCREENER_PATH = ROOT / "output" / "screener_full_ranked_universe.csv"
PRESET_PATH = ROOT / "output" / "screener_presets_summary.csv"


@st.cache_data
def load_data():

    if not SCREENER_PATH.exists():
        return pd.DataFrame(), pd.DataFrame()

    screener = pd.read_csv(SCREENER_PATH)

    if PRESET_PATH.exists():
        presets = pd.read_csv(PRESET_PATH)
    else:
        presets = pd.DataFrame()

    return screener, presets


def show():

    st.title("📄 Reports & Downloads")

    screener, presets = load_data()

    if screener.empty:
        st.error("No screener output found.")
        return

    companies = screener["company_id"].nunique()

    sectors = (
        screener.get("broad_sector_y")
        .fillna(screener.get("broad_sector_x"))
        .nunique()
    )

    years = screener["year"].nunique()

    records = len(screener)

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Companies", companies)
    c2.metric("Sectors", sectors)
    c3.metric("Years", years)
    c4.metric("Records", records)

    st.divider()

    st.subheader("Preset Summary")

    if presets.empty:
        st.info("No preset summary found.")
    else:
        st.dataframe(
            presets,
            use_container_width=True,
            hide_index=True
        )

    st.divider()

    st.subheader("Download Reports")

    csv = screener.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇ Download Full Screener CSV",
        csv,
        "screener_full_ranked_universe.csv",
        "text/csv"
    )

    if not presets.empty:

        preset_csv = presets.to_csv(index=False).encode("utf-8")

        st.download_button(
            "⬇ Download Preset Summary",
            preset_csv,
            "screener_presets_summary.csv",
            "text/csv"
        )

    st.divider()

    st.subheader("Latest Top 25 Companies")

    cols = [
        "company_id",
        "company_name",
        "broad_sector_y",
        "return_on_equity_pct",
        "pe_ratio",
        "pb_ratio",
        "composite_score"
    ]

    cols = [c for c in cols if c in screener.columns]

    table = (
        screener
        .sort_values(
            "composite_score",
            ascending=False
        )
        .head(25)
    )

    st.dataframe(
        table[cols],
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    st.caption(
        "Nifty100 Financial Intelligence Platform • Reports Module"
    )


if __name__ == "__main__":
    show()