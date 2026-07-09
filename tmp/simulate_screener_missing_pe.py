from pathlib import Path
import pandas as pd
import traceback

root = Path(__file__).resolve().parents[1]
path = root / 'output' / 'screener_full_ranked_universe.csv'
print('CSV path:', path)
print('exists:', path.exists())

if not path.exists():
    raise SystemExit('screener_full_ranked_universe.csv not found in output/')

df = pd.read_csv(path)
print('Loaded rows:', len(df))
print('Columns sample:', df.columns.tolist()[:40])

# Simulate deployed CSV missing 'pe_ratio'
if 'pe_ratio' in df.columns:
    df2 = df.drop(columns=['pe_ratio']).copy()
    print("Dropped 'pe_ratio' to simulate missing column.")
else:
    df2 = df.copy()
    print("'pe_ratio' not present; using original df")

# Vulnerable expression that caused KeyError in Streamlit
print('\n--- Vulnerable expression (will error if column missing) ---')
try:
    val = float(min(100.0, df2['pe_ratio'].dropna().max() or 100.0))
    print('vulnerable val:', val)
except Exception as e:
    print('Caught exception from vulnerable expression:')
    traceback.print_exc()

# Fixed helper
print('\n--- Fixed safe_stats and guarded filtering ---')

def safe_stats(df, col, min_default=0.0, max_default=100.0):
    import pandas as _pd
    if col in df.columns:
        s = _pd.to_numeric(df[col], errors='coerce').dropna()
        if not s.empty:
            return float(s.min()), float(s.quantile(0.25)), float(s.max())
    return float(min_default), float((min_default + max_default) / 4.0), float(max_default)

print("safe_stats(pe_ratio)", safe_stats(df2, 'pe_ratio', 0.0, 100.0))

# Apply guarded filter
filtered = df2.copy()
if 'pe_ratio' in filtered.columns:
    _,_,pe_max_default = safe_stats(filtered, 'pe_ratio', 0.0, 100.0)
    filtered = filtered[filtered['pe_ratio'].fillna(999) <= pe_max_default]
    print('Applied pe_ratio filter, remaining rows:', len(filtered))
else:
    print('Skipped pe_ratio filter; column missing. Rows unchanged:', len(filtered))

print('\nSample rows:')
print(filtered.head(5).to_dict(orient='records'))
