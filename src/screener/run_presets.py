import os
import pandas as pd
from pathlib import Path

from src.screener import engine


def load_latest_ratios(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    # normalize column names that engine expects
    if 'revenue_cagr_5yr' in df.columns:
        df['revenue_cagr_5y_pct'] = df['revenue_cagr_5yr']
    if 'pat_cagr_5yr' in df.columns:
        df['pat_cagr_5y_pct'] = df['pat_cagr_5yr']
    if 'eps_cagr_5yr' in df.columns:
        df['eps_cagr_5y_pct'] = df['eps_cagr_5yr']
    latest = engine.mark_latest_rows_with_trend(df)
    return latest


def enrich_with_company_names(df: pd.DataFrame, companies_path: str) -> pd.DataFrame:
    if not os.path.exists(companies_path):
        return df
    comp = pd.read_csv(companies_path)
    if 'id' in comp.columns and 'company_name' in comp.columns:
        comp = comp.rename(columns={'id': 'company_id'})
    comp['company_id'] = comp['company_id'].astype(str)
    merged = df.merge(comp[['company_id', 'company_name']], on='company_id', how='left')
    return merged


def run_and_export(config_path: str,
                   ratios_path: str,
                   companies_path: str,
                   out_path: str):
    cfg = engine.load_config(config_path)
    defaults = cfg.get('defaults', {})
    presets = cfg.get('presets', {})

    latest = load_latest_ratios(ratios_path)
    latest = enrich_with_company_names(latest, companies_path)
    # ensure expected columns exist to avoid KeyErrors in apply_filters
    expected_cols = [
        'return_on_equity_pct', 'return_on_capital_employed_pct', 'net_profit_margin_pct',
        'free_cash_flow_cr', 'cash_from_operations_cr', 'net_profit', 'revenue_cagr_5y_pct',
        'pat_cagr_5y_pct', 'eps_cagr_5y_pct', 'operating_profit_margin_pct', 'debt_to_equity',
        'pe_ratio', 'pb_ratio', 'dividend_yield_pct', 'dividend_payout_ratio_pct', 'interest_coverage',
        'market_cap_crore', 'asset_turnover', 'revenue', 'sales'
    ]
    for c in expected_cols:
        if c not in latest.columns:
            latest[c] = pd.NA
    # merge latest market metrics if available (pe,pb,market cap, dividend yield)
    base = Path(config_path).resolve().parents[1]
    market_path = base / 'data' / 'processed' / 'market_cap_cleaned.csv'
    if market_path.exists():
        m = pd.read_csv(market_path)
        # pick last available row per company
        m_latest = m.sort_values(['company_id', 'year']).groupby('company_id', as_index=False).last()
        latest = latest.merge(m_latest[['company_id', 'pe_ratio', 'pb_ratio', 'market_cap_crore', 'dividend_yield_pct']], on='company_id', how='left')

    writer = pd.ExcelWriter(out_path, engine='openpyxl')
    summary = {}

    for preset_name, thresholds in presets.items():
        merged_thresholds = dict(defaults)
        merged_thresholds.update(thresholds or {})
        df_out = engine.apply_filters(latest, merged_thresholds)
        top_n = int(merged_thresholds.get('top_n', defaults.get('top_n', 50)))
        df_out = df_out.head(top_n)

        # ensure key KPI columns exist
        kpis = [
            'company_id', 'company_name', 'broad_sector', 'composite_quality_score',
            'return_on_equity_pct', 'return_on_capital_employed_pct', 'net_profit_margin_pct',
            'free_cash_flow_cr', 'cash_from_operations_cr', 'cfo_to_pat',
            'revenue_cagr_5y_pct', 'pat_cagr_5y_pct', 'eps_cagr_5y_pct',
            'debt_to_equity', 'interest_coverage', 'pe_ratio', 'pb_ratio',
            'dividend_yield_pct', 'dividend_payout_ratio_pct', 'market_cap_crore', 'revenue'
        ]

        for col in kpis:
            if col not in df_out.columns:
                df_out[col] = pd.NA

        # compute cfo_to_pat if missing
        if 'cfo_to_pat' not in df_out.columns or df_out['cfo_to_pat'].isnull().all():
            if df_out.empty:
                df_out['cfo_to_pat'] = pd.Series(dtype=float)
            else:
                if 'cash_from_operations_cr' in df_out.columns and 'net_profit' in df_out.columns:
                    num = pd.to_numeric(df_out['cash_from_operations_cr'], errors='coerce')
                    den = pd.to_numeric(df_out['net_profit'], errors='coerce')
                    den = den.replace({0: pd.NA})
                    df_out['cfo_to_pat'] = (num / den).replace([pd.NA, pd.NA], pd.NA)
                else:
                    df_out['cfo_to_pat'] = pd.NA

        # select 20 KPI columns
        cols = [c for c in kpis]
        # sort by composite score desc
        if 'composite_quality_score' in df_out.columns:
            df_out = df_out.sort_values('composite_quality_score', ascending=False)

        df_out[cols].to_excel(writer, sheet_name=preset_name[:31], index=False)
        summary[preset_name] = len(df_out)

    # pandas openpyxl writer no longer exposes `save()`; close the writer instead
    writer.close()
    return summary


if __name__ == '__main__':
    base = Path(__file__).resolve().parents[2]
    cfg = base / 'config' / 'screener_config.yaml'
    ratios = base / 'data' / 'processed' / 'financial_ratios_generated.csv'
    companies = base / 'data' / 'processed' / 'companies_cleaned.csv'
    out = base / 'output' / 'screener_output.xlsx'
    out.parent.mkdir(parents=True, exist_ok=True)
    print('Running presets and exporting to', out)
    res = run_and_export(str(cfg), str(ratios), str(companies), str(out))
    for k, v in res.items():
        print(f"Preset {k}: {v} rows")
