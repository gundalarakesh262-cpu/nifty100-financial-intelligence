import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = ROOT / "output" / "screener_full_ranked_universe.csv"

@st.cache_data
def load_screener_data() -> pd.DataFrame:
    if not DATA_PATH.exists():
        return pd.DataFrame()

    df = pd.read_csv(DATA_PATH)
    df['broad_sector'] = df.get('broad_sector_y').fillna(df.get('broad_sector_x')).fillna('Unknown')
    df['sub_sector'] = df.get('sub_sector', 'Unknown')
    df['company_name'] = df['company_name'].astype(str).replace({'nan': pd.NA})
    df['company_name'] = df['company_name'].fillna(df['company_id'])
    return df


def show() -> None:
    st.title("📊 Sector Analysis")
    st.write("Analyze sector-level trends for the latest screener universe.")

    df = load_screener_data()
    if df.empty:
        st.warning("Screener data is not available. Run the pipeline to generate output/screener_full_ranked_universe.csv.")
        return

    sectors = sorted(df['broad_sector'].dropna().unique())
    selected_sector = st.selectbox("Select Sector:", options=['All'] + sectors)

    display_df = df if selected_sector == 'All' else df[df['broad_sector'] == selected_sector]
    if display_df.empty:
        st.warning("No data found for the selected sector.")
        return

    st.subheader(f"{selected_sector} Sector Overview")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Companies", f"{display_df['company_id'].nunique():,}")
    with col2:
        if 'return_on_equity_pct' in display_df.columns:
            st.metric("Avg ROE (%)", f"{display_df['return_on_equity_pct'].mean():.2f}")
        else:
            st.metric("Avg ROE (%)", "N/A")
    with col3:
        if 'pe_ratio' in display_df.columns:
            st.metric("Avg P/E", f"{display_df['pe_ratio'].mean():.2f}")
        else:
            st.metric("Avg P/E", "N/A")
    with col4:
        if 'composite_score' in display_df.columns:
            st.metric("Avg Composite Score", f"{display_df['composite_score'].mean():.2f}")
        else:
            st.metric("Avg Composite Score", "N/A")

    st.markdown("---")
    st.subheader("Sector score distribution")
    score_cols = [c for c in ['composite_score', 'peer_composite_score'] if c in display_df.columns]
    if score_cols:
        st.line_chart(display_df.sort_values('company_id')[score_cols].fillna(0))
    else:
        st.info("Score columns are not available in the dataset.")

    st.markdown("---")
    st.subheader("Peer group counts")
    if 'peer_group_name' in display_df.columns:
        group_counts = display_df['peer_group_name'].fillna('Unassigned').value_counts().head(20)
        st.bar_chart(group_counts)
    else:
        st.info("Peer group data is not available.")

    st.markdown("---")
    st.subheader("Top companies")
    top_cols = [
        'company_id',
        'company_name',
        'peer_group_name',
        'return_on_equity_pct',
        'net_profit_margin_pct',
        'debt_to_equity',
        'pe_ratio',
        'composite_score',
    ]
    top_cols = [c for c in top_cols if c in display_df.columns]
    st.dataframe(display_df.sort_values(by='composite_score' if 'composite_score' in display_df.columns else 'company_id', ascending=False).head(20)[top_cols].reset_index(drop=True), use_container_width=True)
