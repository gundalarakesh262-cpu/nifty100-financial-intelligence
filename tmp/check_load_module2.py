import sys
from pathlib import Path
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from src.dashboard.pages import screener

df = screener.load_screener_data()
print('rows', len(df))
print('top broad_sector values sample:', df['broad_sector'].head(5).tolist())
print(df[['company_id','company_name','broad_sector','composite_score']].head(5).to_dict(orient='records'))
