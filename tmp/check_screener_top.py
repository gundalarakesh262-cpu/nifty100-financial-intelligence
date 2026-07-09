from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / 'output' / 'screener_full_ranked_universe.csv'
print('exists', PATH.exists())
df = pd.read_csv(PATH)
df['company_id'] = df['company_id'].astype(str).str.strip().str.upper()
if 'company_name' in df.columns:
    df['company_name'] = df['company_name'].replace({'nan': pd.NA}).fillna(df['company_id'])
else:
    df['company_name'] = df['company_id']

# safe numeric
for col in ['return_on_equity_pct','net_profit_margin_pct','debt_to_equity','pe_ratio','composite_score','peer_composite_score','fcf_positive_flag','debt_free_flag']:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

# default filters from UI
roe_min = 0.0
npm_min = 0.0
de_max = 3.0 # derived from code: min(3.0, max(1.0, de_q25)) but we use 3
pe_max = 30.0
top_n = 50
sector = 'All'
peer_group = 'All'
fcf_positive_only = False
debt_free_only = False
text_search = ''

filtered = df.copy()
if 'return_on_equity_pct' in filtered.columns:
    filtered = filtered[filtered['return_on_equity_pct'].fillna(-999) >= roe_min]
if 'net_profit_margin_pct' in filtered.columns:
    filtered = filtered[filtered['net_profit_margin_pct'].fillna(-999) >= npm_min]
if 'debt_to_equity' in filtered.columns:
    filtered = filtered[filtered['debt_to_equity'].fillna(999) <= de_max]
if 'pe_ratio' in filtered.columns:
    filtered = filtered[filtered['pe_ratio'].fillna(999) <= pe_max]

filtered = filtered.sort_values(by='composite_score', ascending=False).head(top_n)
print('filtered len', len(filtered))
print('visible cols sample')
cols = ['company_id','company_name','broad_sector','sub_sector','peer_group_name','year','return_on_equity_pct','net_profit_margin_pct','debt_to_equity','pe_ratio','pb_ratio','free_cash_flow_cr','revenue_cagr_5y_pct','pat_cagr_5y_pct','composite_score','peer_composite_score']
visible_cols = [c for c in cols if c in filtered.columns]
print(visible_cols)
print(filtered[visible_cols].head(5).to_dict(orient='records'))

# show NaNs in key display fields for top row
if len(filtered)>0:
    top = filtered.iloc[0]
    for k in ['company_name','company_id','composite_score','broad_sector']:
        print(k, 'isnull?', pd.isna(top.get(k)))
    print('top values:')
    print(top[visible_cols].to_dict())
else:
    print('No rows after filtering')
