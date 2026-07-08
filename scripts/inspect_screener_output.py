import pandas as pd
from pathlib import Path

out = Path(__file__).resolve().parent.parent / 'output' / 'screener_output.xlsx'
if not out.exists():
    print('Missing', out)
    raise SystemExit(1)

sheets = pd.read_excel(out, sheet_name=None, engine='openpyxl')
summary = {}
for name, df in sheets.items():
    summary[name] = len(df)
    print('---', name, f'({len(df)} rows)')
    if df.empty:
        print('  <empty>')
        continue
    cols = ['company_id','company_name','composite_quality_score','pe_ratio','market_cap_crore']
    avail = [c for c in cols if c in df.columns]
    print(df[avail].head(5).to_string(index=False))
    print()

print('counts:', summary)
