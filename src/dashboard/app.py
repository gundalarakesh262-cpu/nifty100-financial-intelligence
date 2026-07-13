import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# MUST be the first Streamlit command
st.set_page_config(
    page_title="Nifty 100 Dashboard",
    page_icon="📈",
    layout="wide"
)

PAGE_ROOT = Path(__file__).resolve().parent
if str(PAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PAGE_ROOT))

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "output" / "screener_full_ranked_universe.csv"
PRESETS_PATH = ROOT / "output" / "screener_presets_summary.csv"


def format_file_info(path: Path) -> str:
    if path.exists():
        mtime = pd.to_datetime(path.stat().st_mtime, unit='s')
        return f"{path.name} updated {mtime:%Y-%m-%d %H:%M:%S}"
    return f"{path.name} missing"


@st.cache_data
def load_home_data():
    screener = pd.DataFrame()
    presets = pd.DataFrame()
    preset_source = "None"
    data_info = format_file_info(DATA_PATH)
    excel_path = ROOT / "output" / "screener_output.xlsx"
    excel_info = format_file_info(excel_path)

    if DATA_PATH.exists():
        try:
            screener = pd.read_csv(DATA_PATH)
        except Exception:
            screener = pd.DataFrame()

    if excel_path.exists():
        try:
            xls = pd.ExcelFile(excel_path)
            rows = []
            for name in xls.sheet_names:
                try:
                    df_sheet = pd.read_excel(xls, sheet_name=name)
                    rows.append({
                        'preset_name': name,
                        'company_count': len(df_sheet)
                    })
                except Exception:
                    rows.append({'preset_name': name, 'company_count': 0})
            presets = pd.DataFrame(rows)
            preset_source = f"Excel: {excel_path.name}"
        except Exception:
            presets = pd.DataFrame()
    else:
        if PRESETS_PATH.exists():
            try:
                presets = pd.read_csv(PRESETS_PATH)
                preset_source = f"CSV: {PRESETS_PATH.name}"
            except Exception:
                presets = pd.DataFrame()

    return screener, presets, preset_source, data_info, excel_info

# Sidebar
st.sidebar.title("📈 Nifty 100 Platform")

page = st.sidebar.radio(
    "Navigate:",
    [
        "Home",
        "Company Profile",
        "Screener",
        "Sector Analysis",
        "Trends",
        "Reports"
    ]
)

# ---------------- HOME ----------------
if page == "Home":
    st.title("📊 Nifty 100 Financial Intelligence Platform")
    st.write("Welcome to the Nifty 100 Dashboard!")

    screener_df, presets_df, preset_source, data_info, excel_info = load_home_data()
    if st.button("Refresh home data"):
        load_home_data.clear()
        st.experimental_rerun()

    if screener_df.empty:
        st.warning("Screener output is missing. Run `scripts/run_screener.py` to generate output/screener_full_ranked_universe.csv.")
        st.markdown("---")
        st.write("Use the sidebar to navigate to Company Profile, Screener, Sector Analysis, Trends, or Reports once the data is available.")
    else:
        screener_df = screener_df.copy()
        screener_df['year_only'] = screener_df['year'].astype(str).str.extract(r"(\d{4})")[0].astype(str)
        year_choices = [str(y) for y in range(2019, 2025)]
        latest_year = screener_df['year_only'].dropna().max() if not screener_df['year_only'].dropna().empty else "2024"
        selected_year = st.selectbox(
            "Select year",
            year_choices,
            index=year_choices.index(latest_year) if latest_year in year_choices else len(year_choices) - 1,
        )

        year_df = screener_df[screener_df['year_only'] == selected_year].copy()
        if year_df.empty:
            st.warning(f"No screener data available for {selected_year}. Try another year.")

        year_df['broad_sector'] = year_df.get('broad_sector_y').fillna(year_df.get('broad_sector_x')).fillna('Unknown')
        year_df['peer_group_name'] = year_df.get('peer_group_name', pd.NA)
        year_df['return_on_equity_pct'] = pd.to_numeric(year_df.get('return_on_equity_pct'), errors='coerce')
        year_df['net_profit_margin_pct'] = pd.to_numeric(year_df.get('net_profit_margin_pct'), errors='coerce')
        year_df['composite_score'] = pd.to_numeric(year_df.get('composite_score'), errors='coerce')

        total_companies = year_df['company_id'].astype(str).str.strip().str.upper().nunique() if not year_df.empty else 0
        total_sectors = year_df['broad_sector'].dropna().nunique() if not year_df.empty else 0
        avg_roe = year_df['return_on_equity_pct'].mean() if 'return_on_equity_pct' in year_df.columns else None
        avg_npm = year_df['net_profit_margin_pct'].mean() if 'net_profit_margin_pct' in year_df.columns else None
        avg_composite = year_df['composite_score'].mean() if 'composite_score' in year_df.columns else None
        top_sector = year_df['broad_sector'].value_counts().idxmax() if not year_df.empty else "N/A"

        st.subheader(f"Year snapshot: {selected_year}")
        row1, row2 = st.columns(2)
        with row1:
            col1, col2, col3 = st.columns(3)
            col1.metric("Total companies", f"{total_companies:,}")
            col2.metric("Sectors", f"{total_sectors:,}")
            col3.metric("Top sector", top_sector)
        with row2:
            col4, col5, col6 = st.columns(3)
            col4.metric("Avg ROE (%)", f"{avg_roe:.2f}" if avg_roe is not None and not pd.isna(avg_roe) else "N/A")
            col5.metric("Avg NPM (%)", f"{avg_npm:.2f}" if avg_npm is not None and not pd.isna(avg_npm) else "N/A")
            col6.metric("Avg Composite Score", f"{avg_composite:.2f}" if avg_composite is not None and not pd.isna(avg_composite) else "N/A")

        if not year_df.empty:
            st.markdown("---")
            st.subheader("Sector distribution")
            sector_counts = (
                year_df['broad_sector'].fillna('Unknown').value_counts().reset_index()
                    .rename(columns={'index': 'broad_sector', 'broad_sector': 'count'})
            )
            fig = px.pie(
                sector_counts,
                names='broad_sector',
                values='count',
                hole=0.45,
                title=f"Sector share in {selected_year}",
            )
            fig.update_traces(textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")
            st.subheader("Top 5 companies by composite score")
            top_quality_cols = [
                'company_id',
                'company_name',
                'broad_sector',
                'composite_score',
                'return_on_equity_pct',
                'net_profit_margin_pct',
                'revenue_cagr_5y_pct',
            ]
            top_quality_cols = [c for c in top_quality_cols if c in year_df.columns]
            if top_quality_cols:
                top_quality_df = year_df.sort_values(by='composite_score', ascending=False).head(5)[top_quality_cols]
                st.dataframe(top_quality_df.reset_index(drop=True), use_container_width=True)
            else:
                st.info("Composite score data is unavailable for the selected year.")

        st.markdown("---")
        st.subheader("Quick screener model")

        screener_df['broad_sector'] = screener_df.get('broad_sector_y').fillna(screener_df.get('broad_sector_x')).fillna('Unknown')
        screener_df['peer_group_name'] = screener_df.get('peer_group_name', pd.NA)
        screener_df['return_on_equity_pct'] = pd.to_numeric(screener_df.get('return_on_equity_pct'), errors='coerce')
        screener_df['debt_to_equity'] = pd.to_numeric(screener_df.get('debt_to_equity'), errors='coerce')

        sector_choices = ['All'] + sorted(screener_df['broad_sector'].dropna().unique().astype(str).tolist())
        peer_choices = ['All'] + sorted(screener_df['peer_group_name'].dropna().unique().astype(str).tolist())

        with st.expander("Screener filters", expanded=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                selected_sector = st.selectbox("Sector", sector_choices, index=0)
                roe_min = st.slider("Min ROE (%)", 0.0, 50.0, 10.0)
            with col2:
                selected_peer = st.selectbox("Peer Group", peer_choices, index=0)
                de_max = st.slider("Max Debt/Equity", 0.0, 10.0, 3.0)
            with col3:
                top_n = st.slider("Top N", 5, 20, 10)
                search = st.text_input("Search company or ticker")

        filtered = screener_df
        if selected_sector != 'All':
            filtered = filtered[filtered['broad_sector'] == selected_sector]
        if selected_peer != 'All':
            filtered = filtered[filtered['peer_group_name'] == selected_peer]
        filtered = filtered[filtered['return_on_equity_pct'].fillna(-999) >= roe_min]
        filtered = filtered[filtered['debt_to_equity'].fillna(999) <= de_max]
        if search:
            needle = search.strip().lower()
            filtered = filtered[filtered[['company_id', 'company_name']].astype(str).apply(
                lambda row: row.str.lower().str.contains(needle, na=False)
            ).any(axis=1)]

        filtered = filtered.sort_values(by='composite_score', ascending=False).head(top_n)

        st.markdown("---")
        st.write(f"Showing {len(filtered)} results from the latest screener universe.")

        home_display_cols = [
            'company_id',
            'company_name',
            'broad_sector',
            'peer_group_name',
            'composite_score',
            'return_on_equity_pct',
            'debt_to_equity',
            'pe_ratio'
        ]
        home_display_cols = [c for c in home_display_cols if c in filtered.columns]
        if home_display_cols:
            display_df = filtered[home_display_cols].copy()
            for c in display_df.select_dtypes(include=['object']).columns:
                display_df[c] = display_df[c].fillna('Unknown')
            st.dataframe(display_df.reset_index(drop=True), use_container_width=True)
        else:
            st.info("The screener model columns are missing from the dataset.")

# ---------------- COMPANY PROFILE ----------------
elif page == "Company Profile":
    from pages import company_profile as company_profile_page
    company_profile_page.show()

# ---------------- SCREENER ----------------
elif page == "Screener":
    from pages import screener as screener_page
    screener_page.show()

# ---------------- SECTOR ANALYSIS ----------------
elif page == "Sector Analysis":
    from pages import sector_analysis as sector_analysis_page
    sector_analysis_page.show()

# ---------------- TRENDS ----------------
elif page == "Trends":
    from pages import trends as trends_page
    trends_page.show()

# ---------------- REPORTS ----------------
elif page == "Reports":
    from pages import reports as reports_page
    reports_page.show()

st.markdown("---")
st.caption("© 2026 | Nifty 100 Financial Intelligence Platform v1.0")
