import pandas as pd
import streamlit as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCREENER_PATH = ROOT / "output" / "screener_full_ranked_universe.csv"
PRESETS_SUMMARY_PATH = ROOT / "output" / "screener_presets_summary.csv"
PRESET_RESULTS_DIR = ROOT / "output" / "preset_results"

@st.cache_data
def load_screener_data() -> pd.DataFrame:
    if not SCREENER_PATH.exists():
        return pd.DataFrame()
    df = pd.read_csv(SCREENER_PATH)
    df['company_id'] = df['company_id'].astype(str).str.strip().str.upper()
    df['company_name'] = df.get('company_name', df['company_id']).astype(str).replace({'nan': pd.NA}).fillna(df['company_id']).astype(str).str.strip()
    df['broad_sector'] = df.get('broad_sector_y').fillna(df.get('broad_sector_x')).replace({'nan': pd.NA}).fillna('Unknown').astype(str).str.strip()
    return df

@st.cache_data
def load_preset_summary() -> pd.DataFrame:
    if not PRESETS_SUMMARY_PATH.exists():
        return pd.DataFrame()
    df = pd.read_csv(PRESETS_SUMMARY_PATH)
    if 'preset_name' in df.columns and 'company_count' in df.columns:
        df = df.rename(columns={'preset_name': 'Preset', 'company_count': 'Count'})
    return df


def load_preset_results(preset_name: str) -> pd.DataFrame:
    preset_file = PRESET_RESULTS_DIR / f"{preset_name.replace(' ', '_')}.csv"
    if not preset_file.exists():
        return pd.DataFrame()
    df = pd.read_csv(preset_file)
    df['company_id'] = df['company_id'].astype(str).str.strip().str.upper()
    return df


def show() -> None:
    st.title("📑 Reports")
    st.write("Download preset reports and inspect preset coverage for the latest universe.")

    screener_df = load_screener_data()
    presets_df = load_preset_summary()

    if screener_df.empty:
        st.warning("Screener data is missing. Run the pipeline to generate output/screener_full_ranked_universe.csv.")
        return

    st.subheader("Preset coverage summary")
    if presets_df.empty:
        st.info("No preset summary is available. Run `scripts/run_screener.py` to regenerate outputs.")
    else:
        st.dataframe(presets_df, use_container_width=True)

    st.markdown("---")
    st.subheader("Preset result download")
    presets = presets_df['Preset'].tolist() if 'Preset' in presets_df.columns else []
    preset_choice = st.selectbox("Select a preset", options=['All'] + presets)

    if preset_choice != 'All' and preset_choice:
        preset_results = load_preset_results(preset_choice)
        if preset_results.empty:
            st.warning(f"No result CSV found for preset '{preset_choice}'.")
        else:
            display_cols = [c for c in ['company_id', 'company_name', 'broad_sector', 'sub_sector', 'composite_score'] if c in preset_results.columns]
            st.write(f"Preset '{preset_choice}' includes {len(preset_results):,} companies.")
            st.dataframe(preset_results[display_cols].fillna('Unknown').head(200), use_container_width=True)
            csv_bytes = preset_results[display_cols].to_csv(index=False).encode('utf-8')
            st.download_button(
                label=f"Download {preset_choice} result CSV",
                data=csv_bytes,
                file_name=f"{preset_choice.replace(' ', '_')}_results.csv",
                mime="text/csv"
            )

    st.markdown("---")
    st.subheader("Export full datasets")
    left, right = st.columns(2)
    with left:
        if not screener_df.empty:
            csv_bytes = screener_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Download full screener universe CSV",
                data=csv_bytes,
                file_name="screener_full_ranked_universe.csv",
                mime="text/csv"
            )
    with right:
        if not presets_df.empty:
            csv_bytes = presets_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Download preset summary CSV",
                data=csv_bytes,
                file_name="screener_presets_summary.csv",
                mime="text/csv"
            )

    st.markdown("---")
    st.caption("Reports are sourced from output/screener_full_ranked_universe.csv and preset result files in output/preset_results.")


if __name__ == "__main__":
    show()
