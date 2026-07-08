import pandas as pd
import streamlit as st
from pathlib import Path
from io import BytesIO

ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = ROOT / "output" / "screener_full_ranked_universe.csv"

@st.cache_data
def load_screener_data() -> pd.DataFrame:
    if not DATA_PATH.exists():
        return pd.DataFrame()

    df = pd.read_csv(DATA_PATH)
    df['company_id'] = df['company_id'].astype(str).str.strip().str.upper()

    if 'company_name' in df.columns:
        df['company_name'] = df['company_name'].replace({'nan': pd.NA}).fillna(df['company_id'])
    else:
        df['company_name'] = df['company_id']

    df['broad_sector'] = df.get('broad_sector_y').fillna(df.get('broad_sector_x'))
    df['broad_sector'] = df['broad_sector'].replace({'nan': pd.NA})
    df['sub_sector'] = df.get('sub_sector', pd.NA)

    numeric_cols = [
        'return_on_equity_pct',
        'net_profit_margin_pct',
        'operating_profit_margin_pct',
        'debt_to_equity',
        'pe_ratio',
        'pb_ratio',
        'free_cash_flow_cr',
        'revenue_cagr_5y_pct',
        'pat_cagr_5y_pct',
        'composite_score',
        'peer_composite_score',
        'fcf_positive_flag',
        'debt_free_flag'
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Filtered Screener')
    return buffer.getvalue()


def show() -> None:
    st.title("🔍 Live Investment Screener")
    st.write("Filter the Day 16 screener universe and download selected results.")

    df = load_screener_data()
    if df.empty:
        st.warning("Screener data is not available. Run the Day 16 pipeline to generate output/screener_full_ranked_universe.csv.")
        return

    sector_candidates = ['All'] + sorted(df['broad_sector'].dropna().unique().astype(str).tolist())
    peer_candidates = ['All'] + sorted(df['peer_group_name'].dropna().unique().astype(str).tolist())

    st.markdown("---")
    with st.expander("Filter settings", expanded=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            roe_min = st.slider(
                "Min ROE (%)",
                float(df['return_on_equity_pct'].min(skipna=True)),
                float(df['return_on_equity_pct'].max(skipna=True)),
                float(max(0.0, df['return_on_equity_pct'].quantile(0.25)))
            )
            npm_min = st.slider(
                "Min Net Profit Margin (%)",
                float(df['net_profit_margin_pct'].min(skipna=True)),
                float(df['net_profit_margin_pct'].max(skipna=True)),
                float(max(0.0, df['net_profit_margin_pct'].quantile(0.25)))
            )
            sector = st.selectbox("Sector", sector_candidates, index=0)

        with col2:
            de_max = st.slider(
                "Max Debt/Equity",
                0.0,
                float(min(10.0, df['debt_to_equity'].dropna().max() or 10.0)),
                float(min(3.0, df['debt_to_equity'].dropna().quantile(0.75) or 3.0))
            )
            pe_max = st.slider(
                "Max P/E",
                0.0,
                float(min(100.0, df['pe_ratio'].dropna().max() or 100.0)),
                float(min(30.0, df['pe_ratio'].dropna().quantile(0.75) or 30.0))
            )
            peer_group = st.selectbox("Peer Group", peer_candidates, index=0)

        with col3:
            fcf_positive_only = st.checkbox("Free Cash Flow Positive Only", value=False)
            debt_free_only = st.checkbox("Debt Free Only", value=False)
            top_n = st.slider("Top N Results", 10, 100, 50, step=5)
            text_search = st.text_input("Search by company name or ticker")

    filtered = df.copy()
    filtered = filtered[filtered['return_on_equity_pct'].fillna(-999) >= roe_min]
    filtered = filtered[filtered['net_profit_margin_pct'].fillna(-999) >= npm_min]
    filtered = filtered[filtered['debt_to_equity'].fillna(999) <= de_max]
    filtered = filtered[filtered['pe_ratio'].fillna(999) <= pe_max]

    if sector != 'All':
        filtered = filtered[filtered['broad_sector'] == sector]
    if peer_group != 'All':
        filtered = filtered[filtered['peer_group_name'] == peer_group]
    if fcf_positive_only and 'fcf_positive_flag' in filtered.columns:
        filtered = filtered[filtered['fcf_positive_flag'] == True]
    if debt_free_only and 'debt_free_flag' in filtered.columns:
        filtered = filtered[filtered['debt_free_flag'] == True]
    if text_search:
        needle = text_search.strip().lower()
        filtered = filtered[filtered[['company_name', 'company_id']].astype(str).apply(
            lambda row: row.str.lower().str.contains(needle, na=False)
        ).any(axis=1)]

    filtered = filtered.sort_values(by='composite_score', ascending=False).head(top_n)

    st.markdown("---")
    st.subheader("Screener Results")

    st.write(
        f"Showing {len(filtered)} companies from the Day 16 screener universe. "
        "Download the filtered subset below."
    )

    display_cols = [
        'company_id',
        'company_name',
        'broad_sector',
        'sub_sector',
        'peer_group_name',
        'year',
        'return_on_equity_pct',
        'net_profit_margin_pct',
        'debt_to_equity',
        'pe_ratio',
        'pb_ratio',
        'free_cash_flow_cr',
        'revenue_cagr_5y_pct',
        'pat_cagr_5y_pct',
        'composite_score',
        'peer_composite_score'
    ]
    visible_cols = [c for c in display_cols if c in filtered.columns]

    st.dataframe(filtered[visible_cols].reset_index(drop=True), use_container_width=True)

    csv_data = filtered.to_csv(index=False).encode('utf-8')
    excel_data = to_excel_bytes(filtered[visible_cols])

    col1, col2 = st.columns(2)
    col1.download_button(
        label="Download filtered CSV",
        data=csv_data,
        file_name="screener_filtered.csv",
        mime="text/csv"
    )
    col2.download_button(
        label="Download filtered Excel",
        data=excel_data,
        file_name="screener_filtered.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.markdown("---")
    st.caption("Data loaded from output/screener_full_ranked_universe.csv | Day 16 live screener")
