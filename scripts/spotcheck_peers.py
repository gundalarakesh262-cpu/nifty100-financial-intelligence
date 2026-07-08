import sqlite3
from pathlib import Path
import pandas as pd

base = Path(__file__).resolve().parent.parent
sqlite_path = base / 'output' / 'peer_percentiles.sqlite'
out_dir = base / 'reports' / 'spotchecks'
out_dir.mkdir(parents=True, exist_ok=True)

if not sqlite_path.exists():
    print('Missing', sqlite_path)
    raise SystemExit(1)

conn = sqlite3.connect(str(sqlite_path))
df = pd.read_sql('SELECT * FROM peer_percentiles', conn)
conn.close()

# normalize peer_group_name
df['peer_group_name'] = df['peer_group_name'].fillna('ungrouped')

for grp in ['IT Services', 'FMCG']:
    grp_df = df[df['peer_group_name'].str.lower() == grp.lower()].copy()
    if grp_df.empty:
        print(f'No rows for peer group: {grp}')
        continue
    grp_df['peer_composite_score'] = pd.to_numeric(grp_df['peer_composite_score'], errors='coerce').fillna(0)
    # deduplicate by company_id, keep the record with the highest peer_composite_score
    if 'company_id' in grp_df.columns:
        grp_df = grp_df.sort_values(by='peer_composite_score', ascending=False).drop_duplicates(subset=['company_id'], keep='first')
    top = grp_df.sort_values(by='peer_composite_score', ascending=False).head(10)
    print('\n===', grp, 'top companies (by peer_composite_score) ===')
    cols = ['company_id', 'company_name', 'peer_composite_score', 'peer_group_size']
    avail = [c for c in cols if c in top.columns]
    print(top[avail].to_string(index=False))
    csv_path = out_dir / f"spotcheck_{grp.replace(' ', '_')}.csv"
    top.to_csv(csv_path, index=False)
    print('Wrote', csv_path)

print('Spot-checks completed. Directory:', out_dir)
