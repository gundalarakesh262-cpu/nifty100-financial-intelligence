from pathlib import Path
import pandas as pd
import sys
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from src.dashboard.pages import screener

# load data
df = screener.load_screener_data()
# apply basic default filters as in screener.show()
filtered = df.copy()
roe_min = 0.0
npm_min = 0.0
de_max = 3.0
pe_max = 30.0
top_n = 50
if 'return_on_equity_pct' in filtered.columns:
    filtered = filtered[filtered['return_on_equity_pct'].fillna(-999) >= roe_min]
if 'net_profit_margin_pct' in filtered.columns:
    filtered = filtered[filtered['net_profit_margin_pct'].fillna(-999) >= npm_min]
if 'debt_to_equity' in filtered.columns:
    filtered = filtered[filtered['debt_to_equity'].fillna(999) <= de_max]
if 'pe_ratio' in filtered.columns:
    filtered = filtered[filtered['pe_ratio'].fillna(999) <= pe_max]

filtered = filtered.sort_values(by='composite_score', ascending=False).head(top_n)

# build display_df same as screener.show()
display_cols = [
    'company_id','company_name','broad_sector','sub_sector','peer_group_name','year',
    'return_on_equity_pct','net_profit_margin_pct','debt_to_equity','pe_ratio','pb_ratio',
    'free_cash_flow_cr','revenue_cagr_5y_pct','pat_cagr_5y_pct','composite_score','peer_composite_score'
]
visible_cols = [c for c in display_cols if c in filtered.columns]
display_df = filtered[visible_cols].reset_index(drop=True).fillna('Unknown')

csv = display_df.to_csv(index=False)
print('\n--- CSV preview ---\n')
print('\n'.join(csv.splitlines()[:10]))
