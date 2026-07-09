from pathlib import Path
import pandas as pd
root = Path(__file__).resolve().parents[1]
path = root / 'output' / 'screener_full_ranked_universe.csv'
df = pd.read_csv(path)
print('columns:', list(df.columns))
print('year unique count:', df['year'].nunique())
print('year sample:', sorted(df['year'].dropna().unique())[:20])
print('company_id unique:', df['company_id'].nunique())
print('has peer_group_name:', 'peer_group_name' in df.columns)
print('has composite_quality_score:', 'composite_quality_score' in df.columns)
print('has peer_composite_score:', 'peer_composite_score' in df.columns)
print('has broad_sector_y:', 'broad_sector_y' in df.columns)
print('has broad_sector_x:', 'broad_sector_x' in df.columns)
print('has sub_sector:', 'sub_sector' in df.columns)
print('first 5 rows:')
print(df[['company_id','year','broad_sector_x','broad_sector_y','sub_sector','composite_score','composite_quality_score']].head(5).to_dict(orient='records'))
path2 = root / 'output' / 'screener_presets_summary.csv'
print('preset summary exists', path2.exists())
if path2.exists():
    p = pd.read_csv(path2)
    print('preset summary columns', list(p.columns))
    print('preset summary sample', p.head(10).to_dict(orient='records'))
