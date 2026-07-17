import sqlite3
import pandas as pd
from pathlib import Path

# ==========================
# Paths
# ==========================
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "processed"
DB_PATH = ROOT / "nifty100.db"

print("=" * 60)
print("Loading processed CSVs into SQLite...")
print("=" * 60)

# Connect to SQLite
conn = sqlite3.connect(DB_PATH)

# CSV -> Table mapping
tables = {
    "companies_cleaned.csv": "companies",
    "profitandloss_cleaned.csv": "profitandloss",
    "balancesheet_cleaned.csv": "balancesheet",
    "cashflow_cleaned.csv": "cashflow",
    "stock_prices_cleaned.csv": "stock_prices",
    "sectors_cleaned.csv": "sectors",
    "peer_groups_cleaned.csv": "peer_groups",
    "documents_cleaned.csv": "documents",
    "analysis_cleaned.csv": "analysis",
    "financial_ratios_generated.csv": "financial_ratios"
}

loaded_tables = []

for csv_file, table_name in tables.items():

    file_path = DATA_DIR / csv_file

    if not file_path.exists():
        print(f"❌ Missing: {csv_file}")
        continue

    try:
        print(f"\nLoading {csv_file}...")

        df = pd.read_csv(file_path)

        print(f"Rows : {len(df)}")
        print(f"Columns : {len(df.columns)}")

        # Replace old table completely
        df.to_sql(
            table_name,
            conn,
            if_exists="replace",
            index=False
        )

        loaded_tables.append(table_name)

        print(f"✅ Loaded into table '{table_name}'")

    except Exception as e:
        print(f"❌ Error loading {csv_file}")
        print(e)

conn.commit()

print("\n" + "=" * 60)
print("DATABASE LOAD COMPLETE")
print("=" * 60)

cursor = conn.cursor()

for table in loaded_tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"{table:<20} {count:>8} rows")

conn.close()

print("\nDone!")