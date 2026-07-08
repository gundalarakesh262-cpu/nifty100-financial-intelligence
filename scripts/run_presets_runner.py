from pathlib import Path
import sys

# Ensure project root is on sys.path so `src` package can be imported when
# running this script from the `scripts/` directory.
base = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(base))

from src.screener.run_presets import run_and_export
config = base / 'config' / 'screener_config.yaml'
ratios = base / 'data' / 'processed' / 'financial_ratios_generated.csv'
companies = base / 'data' / 'processed' / 'companies_cleaned.csv'
out = base / 'output' / 'screener_output.xlsx'

res = run_and_export(str(config), str(ratios), str(companies), str(out))
print(res)
