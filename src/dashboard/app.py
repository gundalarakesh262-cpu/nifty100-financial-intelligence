import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# ---------------------------------------------------
# PAGE CONFIG (Must be first Streamlit command)
# ---------------------------------------------------
st.set_page_config(
    page_title="Nifty 100 Financial Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Hide default Streamlit page navigation
st.markdown(
    """
    <style>
    [data-testid="stSidebarNav"] {
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------
# PATHS
# ---------------------------------------------------
PAGE_ROOT = Path(__file__).resolve().parent

if str(PAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PAGE_ROOT))

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "output"

SCREENER_FILE = OUTPUT_DIR / "screener_full_ranked_universe.csv"
PRESETS_FILE = OUTPUT_DIR / "screener_presets_summary.csv"
EXCEL_FILE = OUTPUT_DIR / "screener_output.xlsx"


# ---------------------------------------------------
# HELPERS
# ---------------------------------------------------
def file_info(path: Path):
    if path.exists():
        t = pd.to_datetime(path.stat().st_mtime, unit="s")
        return f"{path.name} • {t:%d-%b-%Y %H:%M}"
    return f"{path.name} (Missing)"


@st.cache_data
def load_home_data():
    screener = pd.DataFrame()
    presets = pd.DataFrame()

    if SCREENER_FILE.exists():
        try:
            screener = pd.read_csv(SCREENER_FILE)
        except Exception:
            pass

    if EXCEL_FILE.exists():
        try:
            xl = pd.ExcelFile(EXCEL_FILE)
            rows = []

            for sheet in xl.sheet_names:
                try:
                    df_sheet = pd.read_excel(xl, sheet_name=sheet)
                    rows.append(
                        {
                            "Preset": sheet,
                            "Companies": len(df_sheet),
                        }
                    )
                except Exception:
                    rows.append(
                        {
                            "Preset": sheet,
                            "Companies": 0,
                        }
                    )

            presets = pd.DataFrame(rows)

        except Exception:
            pass

    elif PRESETS_FILE.exists():
        try:
            presets = pd.read_csv(PRESETS_FILE)
            if len(presets.columns) >= 2:
                presets.columns = ["Preset", "Companies"]
        except Exception:
            pass

    return screener, presets


# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------
st.sidebar.title("📈 Nifty 100 Dashboard")

page = st.sidebar.radio(
    "Navigate",
    [
        "Home",
        "Company Profile",
        "Screener",
        "Peer Comparison",
        "Sector Analysis",
        "Trends",
        "Capital Allocation",
        "Reports",
        "Valuation",
    ],
)

# ---------------------------------------------------
# HOME
# ---------------------------------------------------
if page == "Home":
    st.title("📊 Nifty 100 Financial Intelligence Platform")

    screener, presets = load_home_data()

    if st.button("🔄 Refresh"):
        load_home_data.clear()
        st.rerun()

    if screener.empty:
        st.warning(
            "Run scripts/run_screener.py first to generate the screener."
        )
    else:
        screener = screener.copy()

        screener["company_id"] = (
            screener.get("company_id", "")
            .astype(str)
            .str.strip()
            .str.upper()
        )

        screener["company_name"] = (
            screener.get("company_name", screener["company_id"])
            .fillna(screener["company_id"])
            .astype(str)
            .str.strip()
        )

        screener["broad_sector"] = (
            screener.get("broad_sector_y")
            .fillna(screener.get("broad_sector_x"))
            .fillna("Unknown")
        )

        screener["peer_group_name"] = screener.get(
            "peer_group_name", pd.NA
        )

        screener["return_on_equity_pct"] = pd.to_numeric(
            screener.get("return_on_equity_pct"), errors="coerce"
        )

        screener["debt_to_equity"] = pd.to_numeric(
            screener.get("debt_to_equity"), errors="coerce"
        )

        screener["composite_score"] = pd.to_numeric(
            screener.get("composite_score"), errors="coerce"
        )

        company_count = screener["company_id"].nunique()

        year_series = (
            screener["year"].astype(str).str.extract(r"(\d{4})")[0]
            if "year" in screener.columns
            else pd.Series(dtype="object")
        )

        latest_year = (
            year_series.dropna().max()
            if not year_series.dropna().empty
            else "N/A"
        )

        sector_count = screener["broad_sector"].nunique()

        top_preset = "N/A"
        top_preset_size = "N/A"

        if not presets.empty:
            preset_row = presets.sort_values(
                "Companies", ascending=False
            ).head(1)

            if not preset_row.empty:
                top_preset = preset_row.iloc[0]["Preset"]
                top_preset_size = int(preset_row.iloc[0]["Companies"])

        col1, col2, col3 = st.columns(3)
        col1.metric("Companies", f"{company_count:,}")
        col2.metric("Latest Year", latest_year)
        col3.metric("Sectors", f"{sector_count:,}")

        col4, col5, col6 = st.columns(3)
        col4.metric("Preset Definitions", len(presets))
        col5.metric("Largest Preset", top_preset)
        col6.metric("Preset Size", str(top_preset_size))

        st.caption(file_info(SCREENER_FILE))

        if not presets.empty:
            st.markdown("---")
            st.subheader("Preset Coverage")
            st.dataframe(
                presets.head(10),
                use_container_width=True,
                hide_index=True,
            )

        st.markdown("---")
        st.subheader("Quick Screener")

        sector_choices = ["All"] + sorted(
            screener["broad_sector"].dropna().astype(str).unique().tolist()
        )

        peer_choices = ["All"] + sorted(
            screener["peer_group_name"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        with st.expander("Filters", expanded=True):
            c1, c2, c3 = st.columns(3)

            with c1:
                selected_sector = st.selectbox(
                    "Sector", sector_choices
                )
                roe_min = st.slider(
                    "Min ROE (%)", 0.0, 50.0, 10.0
                )

            with c2:
                selected_peer = st.selectbox(
                    "Peer Group", peer_choices
                )
                de_max = st.slider(
                    "Max Debt/Equity", 0.0, 10.0, 3.0
                )

            with c3:
                top_n = st.slider("Top N", 5, 20, 10)
                search = st.text_input(
                    "Search company or ticker"
                )

        filtered = screener.copy()

        if selected_sector != "All":
            filtered = filtered[
                filtered["broad_sector"] == selected_sector
            ]

        if selected_peer != "All":
            filtered = filtered[
                filtered["peer_group_name"] == selected_peer
            ]

        filtered = filtered[
            filtered["return_on_equity_pct"].fillna(-999)
            >= roe_min
        ]

        filtered = filtered[
            filtered["debt_to_equity"].fillna(999)
            <= de_max
        ]

        if search:
            needle = search.strip().lower()

            filtered = filtered[
                filtered[["company_id", "company_name"]]
                .astype(str)
                .apply(
                    lambda row: row.str.lower().str.contains(
                        needle, na=False
                    )
                )
                .any(axis=1)
            ]

        filtered = filtered.sort_values(
            by="composite_score", ascending=False
        ).head(top_n)

        st.write(
            f"Showing {len(filtered)} companies from the screener universe."
        )

        display_cols = [
            "company_id",
            "company_name",
            "broad_sector",
            "peer_group_name",
            "return_on_equity_pct",
            "debt_to_equity",
            "composite_score",
        ]

        display_cols = [
            c for c in display_cols if c in filtered.columns
        ]

        display_df = filtered[display_cols].copy()

        for col in display_df.select_dtypes(
            include=["object", "string"]
        ).columns:
            display_df[col] = display_df[col].fillna("Unknown")

        st.dataframe(
            display_df.reset_index(drop=True),
            use_container_width=True,
            hide_index=True,
        )

        st.caption(file_info(EXCEL_FILE))


# ---------------------------------------------------
# COMPANY PROFILE
# ---------------------------------------------------
elif page == "Company Profile":
    from pages import company_profile

    company_profile.show()


# ---------------------------------------------------
# SCREENER
# ---------------------------------------------------
elif page == "Screener":
    from pages import screener

    screener.show()


# ---------------------------------------------------
# PEER COMPARISON
# ---------------------------------------------------
elif page == "Peer Comparison":
    from pages import peers

    peers.show()


# ---------------------------------------------------
# SECTOR ANALYSIS
# ---------------------------------------------------
elif page == "Sector Analysis":
    from pages import sector_analysis

    sector_analysis.show()


# ---------------------------------------------------
# TRENDS
# ---------------------------------------------------
elif page == "Trends":
    from pages import trends

    trends.show()


# ---------------------------------------------------
# CAPITAL ALLOCATION
# ---------------------------------------------------
elif page == "Capital Allocation":
    from pages import capital

    capital.show()


# ---------------------------------------------------
# REPORTS
# ---------------------------------------------------
elif page == "Reports":
    from pages import reports

    reports.show()


# ---------------------------------------------------
# VALUATION
# ---------------------------------------------------
elif page == "Valuation":
    from pages import valuation

    valuation.show()


# ---------------------------------------------------
st.markdown("---")
st.caption("© 2026 | Nifty 100 Financial Intelligence Platform")