import streamlit as st
import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path('output')
SCREENER_CSV = OUTPUT_DIR / 'screener_full_ranked_universe.csv'
PRESETS_CSV = OUTPUT_DIR / 'screener_presets_summary.csv'
PRESET_RESULTS_DIR = OUTPUT_DIR / 'preset_results'


def load_data():
    df = None
    presets = None
    if SCREENER_CSV.exists():
        df = pd.read_csv(SCREENER_CSV)
    if PRESETS_CSV.exists():
        presets = pd.read_csv(PRESETS_CSV)
    return df, presets


def load_preset_results(preset_name: str) -> pd.DataFrame:
    preset_file = PRESET_RESULTS_DIR / f"{preset_name.replace(' ', '_')}.csv"
    if preset_file.exists():
        return pd.read_csv(preset_file)
    return pd.DataFrame()


def format_presets(presets: pd.DataFrame) -> pd.DataFrame:
    if presets is None:
        return pd.DataFrame()
    if 'preset_name' in presets.columns and 'company_count' in presets.columns:
        return presets.rename(columns={'preset_name': 'preset', 'company_count': 'count'})
    return presets


def main():
    st.set_page_config(page_title='Screener Viewer', layout='wide')
    st.title('Screener — Ranked Universe')

    df, presets = load_data()
    if df is None:
        st.error(f'No screener CSV found at {SCREENER_CSV}. Run `py -3 scripts/run_screener.py` first.')
        return

    st.sidebar.header('Filters')
    sectors = sorted(df['broad_sector'].dropna().unique()) if 'broad_sector' in df.columns else []
    sel_sector = st.sidebar.selectbox('Broad Sector', options=['All'] + sectors)
    peer_groups = sorted(df['peer_group_name'].dropna().unique()) if 'peer_group_name' in df.columns else []
    sel_peer_group = st.sidebar.selectbox('Peer Group', options=['All'] + peer_groups) if peer_groups else 'All'
    min_score = st.sidebar.slider('Min composite_quality_score', 0.0, 100.0, 50.0)
    top_n = st.sidebar.number_input('Top N rows', min_value=10, max_value=1000, value=200)

    presets_display = format_presets(presets)
    if not presets_display.empty:
        selected_preset = st.sidebar.selectbox('Preset summary', options=['All'] + presets_display['preset'].tolist())
    else:
        selected_preset = 'All'

    q = df.copy()
    if sel_sector != 'All':
        q = q[q['broad_sector'] == sel_sector]
    if sel_peer_group != 'All':
        q = q[q['peer_group_name'] == sel_peer_group]
    if 'composite_quality_score' in q.columns:
        q = q[q['composite_quality_score'] >= min_score]

    sort_columns = [c for c in ['peer_composite_score', 'composite_score', 'composite_quality_score', 'company_id'] if c in q.columns]
    sort_by = st.sidebar.selectbox('Sort by', options=sort_columns, index=0) if sort_columns else None
    ascending = st.sidebar.checkbox('Ascending sort', value=False)
    if sort_by:
        q = q.sort_values(by=sort_by, ascending=ascending)

    display_columns = [
        'company_id',
        'company_name',
        'broad_sector',
        'sub_sector',
        'peer_group_name',
        'peer_composite_score',
        'composite_score',
        'composite_quality_score',
    ]
    display_columns = [c for c in display_columns if c in q.columns]
    if not display_columns:
        display_columns = q.columns.tolist()

    st.metric('Universe size', f'{len(df):,}')
    st.metric('Filtered size', f'{len(q):,}')
    if 'peer_group_name' in q.columns:
        st.metric('Peer groups represented', f'{q["peer_group_name"].nunique():,}')
    if 'peer_composite_score' in q.columns:
        st.metric('Top peer score', f'{q["peer_composite_score"].max():.1f}')

    left, right = st.columns(2)
    with left:
        if 'peer_composite_score' in q.columns:
            st.subheader('Peer score distribution')
            score_data = q['peer_composite_score'].dropna().reset_index(drop=True)
            st.line_chart(score_data)
        elif 'composite_score' in q.columns:
            st.subheader('Composite score distribution')
            score_data = q['composite_score'].dropna().reset_index(drop=True)
            st.line_chart(score_data)

    with right:
        if 'peer_group_name' in q.columns:
            st.subheader('Peer group counts')
            group_counts = q['peer_group_name'].value_counts().head(30)
            st.bar_chart(group_counts)

    st.subheader('Presets Summary')
    if not presets_display.empty:
        st.dataframe(presets_display)
        if selected_preset != 'All':
            preset_count = presets_display.loc[presets_display['preset'] == selected_preset, 'count'].squeeze()
            st.write(f'Selected preset: **{selected_preset}** — {preset_count:,} companies')
    else:
        st.write('No preset summary file found or it has an unexpected format.')
    st.subheader('Preset results')
    if selected_preset != 'All':
        preset_df = load_preset_results(selected_preset)
        if not preset_df.empty:
            st.write(f'Preset company list for **{selected_preset}**')
            st.dataframe(preset_df.head(top_n))
            csv_bytes = preset_df.head(top_n).to_csv(index=False).encode('utf-8')
            st.download_button('Download preset company list', csv_bytes, file_name=f'{selected_preset.replace(" ", "_")}_companies.csv')
        else:
            st.warning(f'No preset result CSV found for {selected_preset}. Run `py -3 scripts/run_screener.py` to regenerate outputs.')
    st.subheader('Top results')
    st.dataframe(q[display_columns].head(top_n))

    csv_bytes = q[display_columns].to_csv(index=False).encode('utf-8')
    st.download_button('Download filtered CSV', csv_bytes, file_name='screener_filtered.csv')


if __name__ == '__main__':
    main()
