import pandas as pd
import os

def load_excel_file(filepath, header=1):
    """
    Load Excel file with proper settings
    
    Args:
        filepath: Path to Excel file
        header: Row number for headers (default 1 = row 2)
    
    Returns:
        DataFrame with data
    """
    try:
        df = pd.read_excel(filepath, header=header, engine='openpyxl')
        print(f"Loaded: {os.path.basename(filepath)} ({len(df)} rows)")
        return df
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None


def load_all_excel_files(data_path="data/raw"):
    """Load all Excel files from folder"""
    print(f"Loading all Excel files from {data_path}...\n")
    
    files = {}
    
    file_list = [
        'analysis',
        'balancesheet',
        'cashflow',
        'companies',
        'documents',
        'financial_ratios',
        'market_cap',
        'peer_groups',
        'profitandloss',
        'prosandcons',
        'sectors',
        'stock_prices'
    ]
    
    for filename in file_list:
        filepath = f"{data_path}/{filename}.xlsx"
        if os.path.exists(filepath):
            df = load_excel_file(filepath, header=0)
            if df is not None:
                files[filename] = df
        else:
            print(f"File not found: {filepath}")
    
    print(f"\nSuccessfully loaded {len(files)} files")
    return files


if __name__ == "__main__":
   
    data = load_all_excel_files("data/raw")
    
    
    print("\n" + "="*50)
    print("LOADED DATA SUMMARY")
    print("="*50)
    for name, df in data.items():
        print(f"{name}: {df.shape[0]} rows × {df.shape[1]} columns")