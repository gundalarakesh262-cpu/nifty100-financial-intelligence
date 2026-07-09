import pandas as pd
import sys

path = r'c:\Users\gunda\OneDrive\Document.2\Desktop\nifty100-financial-intelligence\output\screener_output.xlsx'
try:
    xls = pd.ExcelFile(path, engine='openpyxl')
except Exception as e:
    print("ERROR loading", path)
    print("Hint: ensure openpyxl is installed in the active Python environment.")
    print("Install with: python -m pip install openpyxl")
    print(e)
    sys.exit(1)

print("sheets:", xls.sheet_names)
for s in xls.sheet_names:
    try:
        df = pd.read_excel(path, sheet_name=s, engine='openpyxl')
        print(f"{s}: {len(df)} rows")
    except Exception as e:
        print(f"ERROR reading sheet {s}: {e}")
