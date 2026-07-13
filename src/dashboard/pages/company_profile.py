import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = ROOT / "output" / "screener_full_ranked_universe.csv"
COMPANIES_PATH = ROOT / "data" / "processed" / "companies_cleaned.csv"
PROSCONS_PATH = ROOT / "data" / "processed" / "prosandcons_cleaned.csv"
PROFITLOSS_PATH = ROOT / "data" / "processed" / "profitandloss_cleaned.csv"


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
    df['year'] = pd.to_numeric(df['year'], errors='coerce')
    return df


@st.cache_data
def load_company_metadata() -> pd.DataFrame:
    if not COMPANIES_PATH.exists():
        return pd.DataFrame()

    df = pd.read_csv(COMPANIES_PATH)
    df['company_id'] = df['id'].astype(str).str.strip().str.upper()
    df['company_name'] = df['company_name'].astype(str).replace({'nan': pd.NA})
    return df.set_index('company_id')


@st.cache_data
def load_proscons_data() -> pd.DataFrame:
    if not PROSCONS_PATH.exists():
        return pd.DataFrame()

    df = pd.read_csv(PROSCONS_PATH)
    df['company_id'] = df['company_id'].astype(str).str.strip().str.upper()
    df['pros'] = df['pros'].astype(str).replace({'nan': ''})
    df['cons'] = df['cons'].astype(str).replace({'nan': ''})
    return df


@st.cache_data
def load_profit_loss_data() -> pd.DataFrame:
    if not PROFITLOSS_PATH.exists():
        return pd.DataFrame()

    df = pd.read_csv(PROFITLOSS_PATH)
    df['company_id'] = df['company_id'].astype(str).str.strip().str.upper()
    df['year'] = pd.to_numeric(df['year'], errors='coerce')
    df['sales'] = pd.to_numeric(df['sales'], errors='coerce')
    df['net_profit'] = pd.to_numeric(df['net_profit'], errors='coerce')
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
    metadata = load_company_metadata()
    proscons = load_proscons_data()
    profit_loss = load_profit_loss_data()

    if df.empty:
        st.warning("Screener data is missing. Run the pipeline to generate output/screener_full_ranked_universe.csv.")
        return

    df['company_label'] = df['company_name'].fillna(df['company_id']).astype(str)
    company_labels = sorted(df['company_label'].unique())

    search_text = st.text_input("Search by company name or ticker", "")
    matches = [label for label in company_labels if search_text.strip().lower() in label.lower()]
    if search_text and not matches:
        st.warning(f"No matching company found for '{search_text.strip()}'. Try another ticker or name.")
        return

    selected_company = st.selectbox("Select company", options=matches if search_text else company_labels)

    company_rows = df[df['company_label'] == selected_company].sort_values(by='year', ascending=False)
    if company_rows.empty:
        st.warning("No records found for the selected company.")
        return

    latest = company_rows.iloc[0]
    company_id = latest['company_id']
    company_name = latest['company_name']
    company_meta = metadata.loc[company_id] if company_id in metadata.index else pd.Series(dtype='object')

    st.subheader(f"{company_name} ({company_id})")
    card_col1, card_col2 = st.columns([1, 3])
    with card_col1:
        logo_url = company_meta.get('company_logo') if 'company_logo' in company_meta else None
        if logo_url and pd.notna(logo_url):
            st.image(logo_url, width=120)
        else:
            st.write("No logo available")
    with card_col2:
        about = company_meta.get('about_company') if 'about_company' in company_meta else None
        website = company_meta.get('website') if 'website' in company_meta else None
        if about and pd.notna(about):
            st.markdown(f"**About:** {about}")
        if website and pd.notna(website):
            st.markdown(f"**Website:** [{website}]({website})")
        st.markdown(f"**Sector:** {latest.get('broad_sector', 'Unknown')}  ")
        st.markdown(f"**Peer Group:** {latest.get('peer_group_name', 'Unassigned')}  ")
        st.markdown(f"**Latest fiscal year:** {int(latest['year']) if pd.notna(latest['year']) else latest.get('fiscal_year', 'N/A')}")

    st.markdown("---")
    st.subheader("Key performance tiles")
    tiles = [
        ("ROE (%)", latest.get('return_on_equity_pct')),
        ("ROCE (%)", latest.get('return_on_capital_employed_pct')),
        ("Net Profit Margin (%)", latest.get('net_profit_margin_pct')),
        ("Debt / Equity", latest.get('debt_to_equity')),
        ("P/E Ratio", latest.get('pe_ratio')),
        ("P/B Ratio", latest.get('pb_ratio')),
    ]
    cols = st.columns(6)
    for col, (label, metric) in zip(cols, tiles):
        col.metric(label, format_value(metric))

    st.markdown("---")
    st.subheader("10-year Revenue and Net Profit")
    profit_rows = profit_loss[profit_loss['company_id'] == company_id].sort_values(by='year')
    if not profit_rows.empty:
        plot_rows = profit_rows.dropna(subset=['year'])
        fig = px.bar(
            plot_rows,
            x='year',
            y=['sales', 'net_profit'],
            barmode='group',
            labels={'value': 'Amount', 'year': 'Year', 'variable': 'Metric'},
            title=f"Revenue and Net Profit - {company_id}"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Revenue and net profit history is unavailable for this company.")

    st.markdown("---")
    st.subheader("ROE vs ROCE history")
    trend_rows = company_rows[['year', 'return_on_equity_pct', 'return_on_capital_employed_pct']].dropna(subset=['year'])
    if not trend_rows.empty:
        trend_rows = trend_rows.sort_values(by='year')
        fig = px.line(
            trend_rows,
            x='year',
            y=['return_on_equity_pct', 'return_on_capital_employed_pct'],
            labels={
                'value': 'Percentage',
                'variable': 'Metric',
                'year': 'Year'
            },
            title=f"ROE and ROCE trend - {company_id}"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("ROE/ROCE trend data is unavailable for this company.")

    company_proscons = proscons[proscons['company_id'] == company_id]
    pros = [item for item in company_proscons['pros'].dropna().astype(str).str.strip().tolist() if item]
    cons = [item for item in company_proscons['cons'].dropna().astype(str).str.strip().tolist() if item]

    st.markdown("---")
    st.subheader("Pros and Cons")
    if pros:
        st.markdown("**Pros**")
        for item in pros:
            st.markdown(f":white_check_mark: {item}")
    else:
        st.write("No pros data available.")

    if cons:
        st.markdown("**Cons**")
        for item in cons:
            st.markdown(f":x: {item}")
    else:
        st.write("No cons data available.")

    st.markdown("---")
    st.subheader("Historical screener metrics")
    history_cols = [
        'year',
        'return_on_equity_pct',
        'return_on_capital_employed_pct',
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
