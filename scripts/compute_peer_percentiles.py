import sqlite3
from pathlib import Path
import pandas as pd
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.screener import peer as peer_mod

base = Path(__file__).resolve().parent.parent
ratios_path = base / 'data' / 'processed' / 'financial_ratios_generated.csv'
companies_path = base / 'data' / 'processed' / 'companies_cleaned.csv'
peer_groups_path = base / 'data' / 'processed' / 'peer_groups_cleaned.csv'

out_dir = base / 'output'
out_dir.mkdir(exist_ok=True)
sqlite_path = out_dir / 'peer_percentiles.sqlite'
excel_path = out_dir / 'peer_comparison.xlsx'

# Load data
ratios = pd.read_csv(ratios_path, dtype=str)
ratios = ratios.rename(columns={c: c.strip() for c in ratios.columns})
# coerce numeric where possible
for col in ratios.columns:
    try:
        ratios[col] = pd.to_numeric(ratios[col], errors='ignore')
    except Exception:
        pass

companies = pd.read_csv(companies_path, dtype=str)
companies = companies.rename(columns={c: c.strip() for c in companies.columns})

peer_groups = pd.read_csv(peer_groups_path, dtype=str)
peer_groups = peer_mod.load_peer_groups(str(peer_groups_path))

# attach company names
if 'company_id' in ratios.columns and 'id' in companies.columns:
    companies = companies.rename(columns={'id': 'company_id'})
ratios['company_id'] = ratios['company_id'].astype(str).str.strip().str.upper()
companies['company_id'] = companies['company_id'].astype(str).str.strip().str.upper()
# pick company name column
name_col = None
for candidate in ('company_name', 'name', 'company', 'companyTitle'):
    if candidate in companies.columns:
        name_col = candidate
        break
if name_col is None:
    companies['company_name'] = companies.get('company_name', companies.get('name', pd.NA))
    name_col = 'company_name'

merged = ratios.merge(companies[['company_id', name_col]], on='company_id', how='left')
merged = merged.rename(columns={name_col: 'company_name'})
merged = peer_mod.attach_peer_groups(merged, peer_groups)

# compute percentiles (local implementation to avoid transform/index issues)
metrics = {
    'peer_score_roe': {'col': 'return_on_equity_pct', 'higher_is_better': True, 'weight': 0.15},
    'peer_score_roce': {'col': 'return_on_capital_employed_pct', 'higher_is_better': True, 'weight': 0.15},
    'peer_score_margin': {'col': 'net_profit_margin_pct', 'higher_is_better': True, 'weight': 0.1},
    'peer_score_revenue_growth': {'col': 'revenue_cagr_5y_pct', 'higher_is_better': True, 'weight': 0.15},
    'peer_score_profit_growth': {'col': 'pat_cagr_5y_pct', 'higher_is_better': True, 'weight': 0.15},
    'peer_score_debt': {'col': 'debt_to_equity', 'higher_is_better': False, 'weight': 0.1},
    'peer_score_fcf': {'col': 'free_cash_flow_cr', 'higher_is_better': True, 'weight': 0.1},
    'peer_score_pe': {'col': 'pe_ratio', 'higher_is_better': False, 'weight': 0.05},
    'peer_score_pb': {'col': 'pb_ratio', 'higher_is_better': False, 'weight': 0.05},
}

computed = merged.copy()
used_metrics = {}
for score_name, spec in metrics.items():
    col = spec['col']
    higher = spec['higher_is_better']
    if col not in computed.columns:
        continue
    # compute percentile within each peer group using groupby.apply then reindex
    def _apply_rank(grp):
        vals = pd.to_numeric(grp, errors='coerce')
        if higher:
            return vals.rank(pct=True, method='max') * 100
        return (1 - vals.rank(pct=True, method='max')) * 100

    rank_series = computed.groupby('peer_group_name')[col].apply(_apply_rank)
    # rank_series has an index matching the original df; reindex to computed.index
    computed[score_name] = rank_series.reindex(computed.index).fillna(50)
    used_metrics[score_name] = spec

# composite score
if not used_metrics:
    computed['peer_composite_score'] = 50.0
else:
    weighted_scores = []
    total_weight = 0.0
    for score_name, spec in used_metrics.items():
        weight = spec.get('weight', 0.0)
        weighted_scores.append(computed[score_name].fillna(50) * weight)
        total_weight += weight
    if total_weight == 0:
        computed['peer_composite_score'] = 50.0
    else:
        computed['peer_composite_score'] = sum(weighted_scores) / total_weight

computed['peer_group_size'] = computed.groupby('peer_group_name')['peer_group_name'].transform('count')

# write to sqlite
conn = sqlite3.connect(str(sqlite_path))
computed.to_sql('peer_percentiles', conn, if_exists='replace', index=False)
conn.close()

# write to excel: one sheet 'all' and one per peer group
with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
    computed.to_excel(writer, sheet_name='all', index=False)
    if 'peer_group_name' in computed.columns:
        for grp, grp_df in computed.groupby('peer_group_name'):
            safe = str(grp)[:30] if pd.notna(grp) else 'ungrouped'
            safe = safe.replace('/', '_')
            grp_df.to_excel(writer, sheet_name=safe[:31], index=False)

print('Wrote sqlite:', sqlite_path)
print('Wrote excel:', excel_path)
print('Rows written:', len(computed))
print('Unique peer groups:', computed['peer_group_name'].nunique() if 'peer_group_name' in computed.columns else 0)
