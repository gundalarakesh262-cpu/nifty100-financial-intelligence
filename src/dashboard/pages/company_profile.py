import streamlit as st
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = ROOT / "output" / "screener_full_ranked_universe.csv"

@st.cache_data
def load_screener_data() -> pd.DataFrame:
    if not DATA_PATH.exists():
        return pd.DataFrame()

    df = pd.read_csv(DATA_PATH)
    df['company_id'] = df['company_id'].astype(str).str.strip().str.upper()
    df['company_name'] = df['company_name'].astype(str).replace({'nan': pd.NA})
    df['company_name'] = df['company_name'].fillna(df['company_id'])
    df['broad_sector'] = df.get('broad_sector_y').fillna(df.get('broad_sector_x'))
    df['broad_sector'] = df['broad_sector'].fillna('Unknown')
    return df


def format_value(value):
    if pd.isna(value):
        return "N/A"
    if isinstance(value, float):
        return f"{value:,.2f}"
    return str(value)


def show() -> None:
    st.title("🏢 Company Profile")
    st.write("Explore company metrics from the latest screener universe.")

    df = load_screener_data()
    if df.empty:
        st.warning("Screener data is missing. Run the pipeline to generate output/screener_full_ranked_universe.csv.")
        return

    df['company_label'] = df['company_name'].fillna(df['company_id']).astype(str)
    companies = sorted(df['company_label'].unique())
    selected_company = st.selectbox("Select company", options=companies)

    company_rows = df[df['company_label'] == selected_company].sort_values(by='year', ascending=False)
    if company_rows.empty:
        st.warning("No records found for the selected company.")
        return

    latest = company_rows.iloc[0]
    st.subheader(f"{latest['company_name']} ({latest['company_id']})")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Broad Sector", latest.get('broad_sector', 'Unknown'))
        st.metric("Peer Group", latest.get('peer_group_name', 'Unassigned'))
        st.metric("Fiscal Year", latest.get('year', latest.get('fiscal_year', 'N/A')))

    with col2:
        st.metric("Composite Score", format_value(latest.get('composite_score')))
        st.metric("Peer Composite Score", format_value(latest.get('peer_composite_score')))
        st.metric("Peer Group Size", format_value(latest.get('peer_group_size')))

    st.markdown("---")
    st.subheader("Key metrics")

    metrics = [
        ("ROE (%)", latest.get('return_on_equity_pct')),
        ("Net Profit Margin (%)", latest.get('net_profit_margin_pct')),
        ("Debt / Equity", latest.get('debt_to_equity')),
        ("P/E Ratio", latest.get('pe_ratio')),
        ("P/B Ratio", latest.get('pb_ratio')),
        ("Free Cash Flow (Cr)", latest.get('free_cash_flow_cr')),
        ("Revenue 5Y CAGR (%)", latest.get('revenue_cagr_5y_pct')),
        ("PAT 5Y CAGR (%)", latest.get('pat_cagr_5y_pct')),
        ("Debt Free", latest.get('debt_free_flag')),
        ("FCF Positive", latest.get('fcf_positive_flag')),
    ]

    metric_df = pd.DataFrame([{"Metric": name, "Value": format_value(value)} for name, value in metrics])
    st.table(metric_df)

    st.markdown("---")
    st.subheader("Company history")
    history_cols = [
        'year',
        'return_on_equity_pct',
        'net_profit_margin_pct',
        'debt_to_equity',
        'pe_ratio',
        'pb_ratio',
        'free_cash_flow_cr',
        'revenue_cagr_5y_pct',
        'pat_cagr_5y_pct',
        'composite_score'
    ]
    history_cols = [c for c in history_cols if c in company_rows.columns]
    st.dataframe(company_rows[history_cols].reset_index(drop=True), use_container_width=True)

    if latest.get('peer_group_name') and latest.get('peer_group_name') != 'nan':
        peer_group = latest['peer_group_name']
        peer_df = df[df['peer_group_name'] == peer_group].sort_values(by='composite_score', ascending=False)
        st.markdown("---")
        st.subheader(f"Peer Group: {peer_group}")
        st.write(f"{len(peer_df)} companies in this peer group.")

        peer_display_cols = [
            'company_id',
            'company_name',
            'composite_score',
            'peer_composite_score',
            'return_on_equity_pct',
            'net_profit_margin_pct',
            'debt_to_equity',
            'pe_ratio'
        ]
        peer_display_cols = [c for c in peer_display_cols if c in peer_df.columns]
        st.dataframe(peer_df[peer_display_cols].reset_index(drop=True).head(10), use_container_width=True)
