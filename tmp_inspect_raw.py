import pandas as pd
import os

files = ['companies', 'profitandloss', 'balancesheet', 'cashflow', 'sectors']
for f in files:
    path = os.path.join('data', 'raw', f + '.xlsx')
    print(f'=== {f} ===')
    if os.path.exists(path):
        df = pd.read_excel(path, nrows=0)
        print(df.columns.tolist())
    else:
        print('MISSING', path)
