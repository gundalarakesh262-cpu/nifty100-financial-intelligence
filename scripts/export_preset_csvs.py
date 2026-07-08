import pandas as pd
from pathlib import Path

base = Path(__file__).resolve().parent.parent
xlsx = base / 'output' / 'screener_output.xlsx'
out_dir = base / 'output' / 'preset_csvs'

if not xlsx.exists():
    print('Missing workbook:', xlsx)
    raise SystemExit(1)

out_dir.mkdir(parents=True, exist_ok=True)

sheets = pd.read_excel(xlsx, sheet_name=None, engine='openpyxl')
for name, df in sheets.items():
    safe = name.replace(' ', '_')
    csv_path = out_dir / f"{safe}.csv"
    df.to_csv(csv_path, index=False)
    print('Wrote', csv_path)

print('Export complete. Directory:', out_dir)
