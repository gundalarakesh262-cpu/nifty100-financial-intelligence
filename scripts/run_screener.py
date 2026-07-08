"""Run a reproducible screener from generated CSV files and write outputs to the output/ folder.
This mirrors the logic in the notebook but as a standalone script so it runs reliably.
"""
import os
import sys
import pandas as pd
import yaml
import numpy as np

pd.set_option("display.max_columns", None)

# allow importing src modules from the scripts folder
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'src'))

from screener.peer import load_peer_groups, attach_peer_groups, compute_peer_percentiles
from analytics.peer import (
    compute_metric_percentiles,
    generate_peer_comparison_excel,
    generate_radar_charts,
    write_peer_percentiles_sqlite,
)

RATIOS = os.path.join(BASE, 'data', 'processed', 'financial_ratios_generated.csv')
PROFIT_LOSS = os.path.join(BASE, 'data', 'processed', 'profitandloss_cleaned.csv')
COMPANIES = os.path.join(BASE, 'data', 'processed', 'companies_cleaned.csv')
SECTORS = os.path.join(BASE, 'data', 'processed', 'sectors_cleaned.csv')
PEER_GROUPS = os.path.join(BASE, 'data', 'processed', 'peer_groups_cleaned.csv')
CONFIG = os.path.join(BASE, 'config', 'screener_config.yaml')
DB_PATH = os.path.join(BASE, 'nifty100.db')

print('Using ratios file:', RATIOS)

if not os.path.exists(RATIOS):
    print('Ratios file missing:', RATIOS)
    raise SystemExit(1)

ratios = pd.read_csv(RATIOS)

screener_data = ratios.copy()

if os.path.exists(COMPANIES):
    companies = pd.read_csv(COMPANIES)
    if 'id' in companies.columns and 'company_id' not in companies.columns:
        companies = companies.rename(columns={'id': 'company_id'})
    if 'company_id' in companies.columns and 'company_id' in screener_data.columns:
        companies['company_id'] = companies['company_id'].astype(str).str.strip().str.upper()
        screener_data['company_id'] = screener_data['company_id'].astype(str).str.strip().str.upper()
        keep = [c for c in ['company_id','company_name'] if c in companies.columns]
        screener_data = screener_data.merge(companies[keep], on='company_id', how='left')

if os.path.exists(SECTORS):
    sectors = pd.read_csv(SECTORS)
    if 'company_id' not in sectors.columns and 'id' in sectors.columns:
        sectors = sectors.rename(columns={'id': 'company_id'})
    if 'company_id' in sectors.columns and 'company_id' in screener_data.columns:
        sectors['company_id'] = sectors['company_id'].astype(str).str.strip().str.upper()
        screener_data['company_id'] = screener_data['company_id'].astype(str).str.strip().str.upper()
        keep = [c for c in ['company_id','broad_sector','sub_sector'] if c in sectors.columns]
        screener_data = screener_data.merge(sectors[keep], on='company_id', how='left')

# fiscal_year extraction
if 'fiscal_year' not in screener_data.columns and 'year' in screener_data.columns:
    screener_data['fiscal_year'] = screener_data['year'].astype(str).str.extract(r"(\d{4})")[0]

screener_data['fiscal_year'] = pd.to_numeric(screener_data.get('fiscal_year'), errors='coerce')

screener_data = screener_data.sort_values(['company_id', 'fiscal_year'])
screener_data['previous_debt_to_equity'] = screener_data.groupby('company_id')['debt_to_equity'].shift(1)
screener_data['de_ratio_declining'] = (
    pd.to_numeric(screener_data['debt_to_equity'], errors='coerce')
    < pd.to_numeric(screener_data['previous_debt_to_equity'], errors='coerce')
)
screener_data['de_ratio_declining'] = screener_data['de_ratio_declining'].fillna(False)

if 'revenue_cagr_3y_pct' not in screener_data.columns and os.path.exists(PROFIT_LOSS):
    pl = pd.read_csv(PROFIT_LOSS)
    pl['company_id'] = pl['company_id'].astype(str).str.strip().str.upper()
    pl['year_numeric'] = pd.to_numeric(pl['year'].astype(str).str.extract(r"(\d{4})")[0], errors='coerce')
    pl['sales'] = pd.to_numeric(pl['sales'], errors='coerce')
    pl = pl.sort_values(['company_id', 'year_numeric'])
    pl['sales_prior_3y'] = pl.groupby('company_id')['sales'].shift(3)
    pl['revenue_cagr_3y_pct'] = np.where(
        (pl['sales'] > 0) & (pl['sales_prior_3y'] > 0),
        ((pl['sales'] / pl['sales_prior_3y']) ** (1.0 / 3.0) - 1.0) * 100.0,
        np.nan,
    )
    screener_data = screener_data.merge(
        pl[['company_id', 'year_numeric', 'revenue_cagr_3y_pct']].rename(columns={'year_numeric': 'fiscal_year'}),
        on=['company_id', 'fiscal_year'],
        how='left',
    )

latest = (
    screener_data
    .dropna(subset=['fiscal_year'])
    .sort_values(['company_id','fiscal_year'])
    .groupby('company_id')
    .tail(1)
    .reset_index(drop=True)
)

# load presets from config
config = {}
if os.path.exists(CONFIG):
    with open(CONFIG, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f) or {}
    print('Loaded screener config from', CONFIG)
else:
    print('Config file not found:', CONFIG)

# attach peer group data before scoring
if os.path.exists(PEER_GROUPS):
    peer_groups = load_peer_groups(PEER_GROUPS)
    latest = attach_peer_groups(latest, peer_groups)
    print('Attached peer groups from', PEER_GROUPS)
else:
    print('Peer groups file not found:', PEER_GROUPS)

# scoring

def percentile_score(series, higher_is_better=True):
    s = pd.to_numeric(series, errors='coerce')
    if higher_is_better:
        return s.rank(pct=True) * 100
    else:
        return (1 - s.rank(pct=True)) * 100

scored = latest.copy()
if 'revenue_cagr_5yr' in scored.columns and 'revenue_cagr_5y_pct' not in scored.columns:
    scored = scored.rename(columns={'revenue_cagr_5yr': 'revenue_cagr_5y_pct'})
if 'pat_cagr_5yr' in scored.columns and 'pat_cagr_5y_pct' not in scored.columns:
    scored = scored.rename(columns={'pat_cagr_5yr': 'pat_cagr_5y_pct'})

score_columns = {
    'score_roe': ('return_on_equity_pct', True),
    'score_roce': ('return_on_capital_employed_pct', True),
    'score_margin': ('net_profit_margin_pct', True),
    'score_revenue_growth': ('revenue_cagr_5y_pct', True),
    'score_profit_growth': ('pat_cagr_5y_pct', True),
    'score_debt': ('debt_to_equity', False),
    'score_fcf': ('free_cash_flow_cr', True),
    'score_fcf_yield': ('fcf_yield_pct', True),
    'score_pe': ('pe_ratio', False),
    'score_pb': ('pb_ratio', False),
}

for sname, (col, higher) in score_columns.items():
    if col in scored.columns:
        scored[sname] = percentile_score(scored[col], higher)
    else:
        scored[sname] = 50

scored['composite_score'] = (
    scored['score_roe'].fillna(50) * 0.15 +
    scored['score_roce'].fillna(50) * 0.15 +
    scored['score_margin'].fillna(50) * 0.1 +
    scored['score_revenue_growth'].fillna(50) * 0.15 +
    scored['score_profit_growth'].fillna(50) * 0.15 +
    scored['score_debt'].fillna(50) * 0.1 +
    scored['score_fcf'].fillna(50) * 0.1 +
    scored['score_pe'].fillna(50) * 0.05 +
    scored['score_pb'].fillna(50) * 0.05
)

scored = scored.sort_values('composite_score', ascending=False).reset_index(drop=True)

# presets
preset_results = {}

# helper used by presets
scored['debt_free_flag'] = scored['interest_coverage'].astype(str).str.lower() == 'debt free'
scored['fcf_positive_flag'] = scored['free_cash_flow_cr'].fillna(0) >= 0

# function for preset filtering

def run_screener(
    data,
    sector=None,
    roe_min=None,
    roce_min=None,
    de_max=None,
    fcf_min=None,
    revenue_cagr_5y_min=None,
    pat_cagr_5y_min=None,
    pe_max=None,
    pb_max=None,
    dividend_yield_min=None,
    dividend_payout_ratio_pct_max=None,
    icr_min=None,
    market_cap_min=None,
    net_profit_min=None,
    eps_cagr_min=None,
    revenue_min=None,
    sales_min=None,
    revenue_cagr_3y_min=None,
    pat_cagr_3y_min=None,
    de_declining=False,
    debt_free_only=False,
    fcf_positive_only=False,
    top_n=50,
):
    result = data.copy()

    if sector is not None and 'broad_sector' in result.columns:
        result = result[result['broad_sector'] == sector]

    if roe_min is not None:
        result = result[result['return_on_equity_pct'] >= roe_min]

    if roce_min is not None and 'return_on_capital_employed_pct' in result.columns:
        result = result[result['return_on_capital_employed_pct'] >= roce_min]

    if de_max is not None:
        result = result[result['debt_to_equity'] <= de_max]

    if fcf_min is not None:
        result = result[result['free_cash_flow_cr'] >= fcf_min]

    if revenue_cagr_5y_min is not None and 'revenue_cagr_5y_pct' in result.columns:
        result = result[result['revenue_cagr_5y_pct'] >= revenue_cagr_5y_min]

    if pat_cagr_5y_min is not None and 'pat_cagr_5y_pct' in result.columns:
        result = result[result['pat_cagr_5y_pct'] >= pat_cagr_5y_min]

    if pe_max is not None and 'pe_ratio' in result.columns:
        result = result[result['pe_ratio'] <= pe_max]

    if pb_max is not None and 'pb_ratio' in result.columns:
        result = result[result['pb_ratio'] <= pb_max]

    if dividend_yield_min is not None and 'dividend_yield_pct' in result.columns:
        result = result[result['dividend_yield_pct'] >= dividend_yield_min]

    if dividend_payout_ratio_pct_max is not None and 'dividend_payout_ratio_pct' in result.columns:
        result = result[result['dividend_payout_ratio_pct'] <= dividend_payout_ratio_pct_max]

    if icr_min is not None and 'interest_coverage' in result.columns:
        result = result[result['interest_coverage'].fillna(-np.inf) >= icr_min]

    if market_cap_min is not None and 'market_cap_crore' in result.columns:
        result = result[result['market_cap_crore'] >= market_cap_min]

    if net_profit_min is not None and 'net_profit' in result.columns:
        result = result[result['net_profit'] >= net_profit_min]

    if eps_cagr_min is not None and 'eps_cagr_5y_pct' in result.columns:
        result = result[result['eps_cagr_5y_pct'] >= eps_cagr_min]

    if revenue_min is not None and 'revenue' in result.columns:
        result = result[result['revenue'] >= revenue_min]
    elif revenue_min is not None and 'sales' in result.columns:
        result = result[result['sales'] >= revenue_min]

    if sales_min is not None and 'sales' in result.columns:
        result = result[result['sales'] >= sales_min]
    elif sales_min is not None and 'revenue' in result.columns:
        result = result[result['revenue'] >= sales_min]

    if revenue_cagr_3y_min is not None and 'revenue_cagr_3y_pct' in result.columns:
        result = result[result['revenue_cagr_3y_pct'] >= revenue_cagr_3y_min]

    if pat_cagr_3y_min is not None and 'pat_cagr_3y_pct' in result.columns:
        result = result[result['pat_cagr_3y_pct'] >= pat_cagr_3y_min]

    if de_declining:
        result = result[result['de_ratio_declining'] == True]

    if debt_free_only:
        result = result[result['debt_free_flag'] == True]

    if fcf_positive_only:
        result = result[result['fcf_positive_flag'] == True]

    return result.sort_values('composite_score', ascending=False).head(top_n)

# compute peer percentile scoring if peer group membership is available
if 'peer_group_name' in scored.columns:
    scored = compute_peer_percentiles(scored)
    print('Computed peer percentile scores.')

# apply presets from config or default fallback
presets = config.get('presets', {}) if isinstance(config, dict) else {}
for preset_name, settings in presets.items():
    if isinstance(settings, dict):
        preset_results[preset_name] = run_screener(scored, **settings)

preset_summary = pd.DataFrame({
    'preset_name': list(preset_results.keys()),
    'company_count': [len(df) for df in preset_results.values()]
})

# save outputs
output_dir = os.path.join(BASE, 'output')
preset_dir = os.path.join(output_dir, 'preset_results')
os.makedirs(output_dir, exist_ok=True)
os.makedirs(preset_dir, exist_ok=True)

# Export peer percentile ranks and peer comparison reports when peer data is available.
if 'peer_group_name' in scored.columns and not scored['peer_group_name'].isna().all():
    metric_percentiles = compute_metric_percentiles(scored)
    write_peer_percentiles_sqlite(metric_percentiles, DB_PATH)
    print('Wrote peer percentiles to SQLite at', DB_PATH)

    generate_peer_comparison_excel(scored, peer_groups, os.path.join(output_dir, 'peer_comparison.xlsx'))
    print('Wrote peer comparison Excel to', os.path.join(output_dir, 'peer_comparison.xlsx'))

    generate_radar_charts(scored, peer_groups)
    print('Wrote radar charts to reports/radar_charts')
scored.to_csv(os.path.join(output_dir, 'screener_full_ranked_universe.csv'), index=False)
preset_summary.to_csv(os.path.join(output_dir, 'screener_presets_summary.csv'), index=False)
for preset_name, df in preset_results.items():
    preset_file = os.path.join(preset_dir, f"{preset_name.replace(' ', '_')}.csv")
    df.to_csv(preset_file, index=False)

# excel export
excel_path = os.path.join(output_dir, 'screener_output.xlsx')
with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
    scored.to_excel(writer, sheet_name='ranked_universe', index=False)
    for preset_name, df in preset_results.items():
        safe_name = preset_name[:31]
        df.to_excel(writer, sheet_name=safe_name, index=False)

print('Wrote output files to', os.path.join(BASE,'output'))
print('Wrote Excel export to', excel_path)
