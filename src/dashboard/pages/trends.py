import pandas as pd
import streamlit as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = ROOT / "output" / "screener_full_ranked_universe.csv"

@st.cache_data
def load_screener_data() -> pd.DataFrame:
    if not DATA_PATH.exists():
        return pd.DataFrame()

    df = pd.read_csv(DATA_PATH)
    df['company_id'] = df['company_id'].astype(str).str.strip().str.upper()
    df['company_name'] = df.get('company_name', df['company_id']).astype(str).replace({'nan': pd.NA})
    df['company_name'] = df['company_name'].fillna(df['company_id']).astype(str).str.strip()
    df['broad_sector'] = df.get('broad_sector_y').fillna(df.get('broad_sector_x'))
    df['broad_sector'] = df['broad_sector'].replace({'nan': pd.NA}).fillna('Unknown').astype(str).str.strip()
    df['sub_sector'] = df.get('sub_sector', pd.NA)
    if 'year' in df.columns:
        year_numeric = df['year'].astype(str).str.extract(r"(\d{4})")[0]
        df['year_numeric'] = pd.to_numeric(year_numeric, errors='coerce')
    else:
        df['year_numeric'] = pd.NA
    for col in ['return_on_equity_pct', 'net_profit_margin_pct', 'debt_to_equity', 'pe_ratio', 'pb_ratio', 'composite_score', 'peer_composite_score']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df


def show() -> None:
    st.title("📈 Trends")
    st.write("Explore multi-year and sector trends for the latest screener universe.")

    df = load_screener_data()
    if df.empty:
        st.warning("Screener data is not available. Run the pipeline to generate output/screener_full_ranked_universe.csv.")
        return

    df = df.copy()
    years = sorted(df['year_numeric'].dropna().unique())
    if not years:
        st.warning("No year information was found in the screener dataset.")
        return

    sectors = ['All'] + sorted(df['broad_sector'].dropna().unique().astype(str).tolist())
    selected_sector = st.selectbox("Sector for trend analysis", options=sectors, index=0)
    metric_options = [
        ('Composite Score', 'composite_score'),
        ('Peer Composite Score', 'peer_composite_score'),
        ('Return on Equity (%)', 'return_on_equity_pct'),
        ('Net Profit Margin (%)', 'net_profit_margin_pct'),
        ('Debt to Equity', 'debt_to_equity'),
        ('P/E Ratio', 'pe_ratio'),
    ]
    metric_map = {label: key for label, key in metric_options if key in df.columns}
    selected_metric_label = st.selectbox("Metric to chart", options=list(metric_map.keys()))
    selected_metric = metric_map[selected_metric_label]

    filtered = df if selected_sector == 'All' else df[df['broad_sector'] == selected_sector]
    if filtered.empty:
        st.warning("No data found for the selected sector.")
        return

    st.markdown("---")
    latest_year = int(filtered['year_numeric'].dropna().max())
    current = filtered[filtered['year_numeric'] == latest_year]
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Latest year", str(latest_year))
    with col2:
        if selected_metric in filtered.columns:
            st.metric(
                f"Latest {selected_metric_label}",
                f"{current[selected_metric].mean():.2f}" if not current[selected_metric].dropna().empty else "N/A"
            )
        else:
            st.metric(f"Latest {selected_metric_label}", "N/A")
    with col3:
        st.metric("Companies in view", f"{filtered['company_id'].nunique():,}")

    st.markdown("---")
    st.subheader("Year-over-year trend")
    trend_df = (
        filtered
        .dropna(subset=[selected_metric, 'year_numeric'])
        .groupby('year_numeric', as_index=False)[selected_metric]
        .mean()
        .sort_values('year_numeric')
    )
    if trend_df.empty:
        st.info(f"No trend data for {selected_metric_label}.")
    else:
        st.line_chart(trend_df.rename(columns={'year_numeric': 'Year', selected_metric: selected_metric_label}).set_index('Year'))

    st.markdown("---")
    st.subheader("Trend metrics by sector")
    sector_metric = (
        df
        .dropna(subset=[selected_metric, 'year_numeric'])
        .groupby(['year_numeric', 'broad_sector'], as_index=False)[selected_metric]
        .mean()
        .sort_values(['year_numeric', 'broad_sector'])
    )
    if sector_metric.empty:
        st.info("Sector trend metrics are not available.")
    else:
        pivot = sector_metric.pivot(index='year_numeric', columns='broad_sector', values=selected_metric)
        st.area_chart(pivot.fillna(method='ffill').fillna(0))

    st.markdown("---")
    st.subheader("Top companies for latest year")
    top_cols = ['company_id', 'company_name', 'broad_sector', 'year', selected_metric]
    top_cols = [c for c in top_cols if c in filtered.columns]
    top_df = (
        current.sort_values(by=selected_metric, ascending=False)
        .head(20)
        .reset_index(drop=True)
        .fillna('Unknown')
    )
    st.dataframe(top_df[top_cols], use_container_width=True)

    st.markdown("---")
    st.caption("Trend metrics are based on the latest screener dataset in output/screener_full_ranked_universe.csv.")
