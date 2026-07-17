"""Build the financial_ratios dataset and write it to SQLite and output CSV."""

import os
import sys
import sqlite3
from typing import Dict, Optional

# Allow running this script directly from the repository root.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pandas as pd

from src.analytics.cagr import (
    eps_cagr,
    pat_cagr,
    revenue_cagr,
)
from src.analytics.cashflow_kpis import (
    capex_intensity,
    cfo_pat_ratio,
    free_cash_flow,
    generate_capital_allocation_rows,
    write_capital_allocation_csv,
)
from src.analytics.ratios import (
    asset_turnover,
    debt_to_equity,
    interest_coverage_ratio,
    net_profit_margin,
    operating_profit_margin,
    roe,
)
from src.etl.normaliser import normalize_year


def parse_year_date(year_value: Optional[str]) -> Optional[pd.Timestamp]:
    if pd.isna(year_value) or year_value is None:
        return None

    year_str = str(year_value).strip()
    if not year_str:
        return None

    normalized = normalize_year(year_str)
    if normalized:
        try:
            return pd.to_datetime(normalized, format='%Y-%m', errors='raise')
        except Exception:
            pass

    try:
        parsed = pd.to_datetime(year_str, errors='coerce')
        if pd.notna(parsed):
            return parsed
    except Exception:
        pass

    return None


def load_processed_data(data_path: str = 'data/processed') -> Dict[str, pd.DataFrame]:
    return {
        'profitandloss': pd.read_csv(os.path.join(data_path, 'profitandloss_cleaned.csv')),
        'balancesheet': pd.read_csv(os.path.join(data_path, 'balancesheet_cleaned.csv')),
        'cashflow': pd.read_csv(os.path.join(data_path, 'cashflow_cleaned.csv')),
        'companies': pd.read_csv(os.path.join(data_path, 'companies_cleaned.csv')),
        'sectors': pd.read_csv(os.path.join(data_path, 'sectors_cleaned.csv')),
    }


def build_ratio_dataframe(data_path: str = 'data/processed') -> pd.DataFrame:
    dfs = load_processed_data(data_path)
    pl = dfs['profitandloss'].copy()
    bs = dfs['balancesheet'].copy()
    cf = dfs['cashflow'].copy()
    companies = dfs['companies'].copy()
    sectors = dfs['sectors'].copy()

    for df in (pl, bs, cf, companies, sectors):
        if 'company_id' in df.columns:
            df['company_id'] = df['company_id'].astype(str)

    pl['year_parsed'] = pl['year'].apply(parse_year_date)
    bs['year_parsed'] = bs['year'].apply(parse_year_date)
    cf['year_parsed'] = cf['year'].apply(parse_year_date)

    pl = pl[pl['year_parsed'].notna()]
    bs = bs[bs['year_parsed'].notna()]
    cf = cf[cf['year_parsed'].notna()]

    merged = pl.merge(bs, on=['company_id', 'year_parsed'], how='outer', suffixes=('_pl', '_bs'))
    merged = merged.merge(cf, on=['company_id', 'year_parsed'], how='outer')

    merged['year'] = merged['year_pl'].fillna(merged.get('year_bs')).fillna(merged.get('year'))
    merged['year'] = merged['year'].astype(str)

    if 'company_id' in companies.columns:
        merged = merged.merge(companies[['company_id', 'book_value']], on='company_id', how='left')
    elif 'id' in companies.columns:
        merged = merged.merge(companies[['id', 'book_value']].rename(columns={'id': 'company_id'}), on='company_id', how='left')
    else:
        merged['book_value'] = None

    if 'company_id' in sectors.columns:
        merged = merged.merge(sectors[['company_id', 'broad_sector']], on='company_id', how='left')
    elif 'id' in sectors.columns:
        merged = merged.merge(sectors[['id', 'broad_sector']].rename(columns={'id': 'company_id'}), on='company_id', how='left')
    else:
        merged['broad_sector'] = None

    merged = merged.sort_values(['company_id', 'year_parsed']).reset_index(drop=True)

    merged.fillna({
        'total_assets': 0,
        'sales': 0,
        'net_profit': 0,
        'operating_profit': 0,
        'equity_capital': 0,
        'reserves': 0,
        'borrowings': 0,
        'other_income': 0,
        'interest': 0,
        'operating_activity': 0,
        'investing_activity': 0,
    }, inplace=True)

    ratio_rows = []
    for _, group in merged.groupby('company_id', sort=False):
        group = group.reset_index(drop=True)
        sales_history = group['sales'].tolist()
        net_profit_history = group['net_profit'].tolist()
        eps_history = group['eps'].tolist() if 'eps' in group.columns else [None] * len(group)

        for pos, row in group.iterrows():
            if pos >= 5:
                revenue_cagr_val, _ = revenue_cagr(sales_history[pos - 5], row['sales'], 5)
                pat_cagr_val, _ = pat_cagr(net_profit_history[pos - 5], row['net_profit'], 5)
                eps_cagr_val, _ = eps_cagr(eps_history[pos - 5], row['eps'], 5)
            else:
                revenue_cagr_val, pat_cagr_val, eps_cagr_val = None, None, None

            ratio_rows.append({
                'company_id': row['company_id'],
                'year': row['year'],
                'year_parsed': row['year_parsed'],
                'net_profit_margin_pct': net_profit_margin(row['net_profit'], row['sales']),
                'operating_profit_margin_pct': operating_profit_margin(row['operating_profit'], row['sales']),
                'return_on_equity_pct': roe(row['net_profit'], row['equity_capital'], row['reserves']),
                'debt_to_equity': debt_to_equity(row['borrowings'], row['equity_capital'], row['reserves']),
                'interest_coverage': interest_coverage_ratio(row['operating_profit'], row['other_income'], row['interest']),
                'asset_turnover': asset_turnover(row['sales'], row['total_assets']),
                'free_cash_flow_cr': free_cash_flow(row['operating_activity'], row['investing_activity']),
                'capex_cr': capex_intensity(row['sales'], row['investing_activity']),
                'earnings_per_share': row.get('eps'),
                'book_value_per_share': row.get('book_value'),
                'dividend_payout_ratio_pct': row.get('dividend_payout'),
                'total_debt_cr': row['borrowings'],
                'cash_from_operations_cr': row['operating_activity'],
                'revenue_cagr_5yr': revenue_cagr_val,
                'pat_cagr_5yr': pat_cagr_val,
                'eps_cagr_5yr': eps_cagr_val,
                'composite_quality_score': cfo_pat_ratio(row.get('operating_activity'), row.get('net_profit')),
                'broad_sector': row.get('broad_sector'),
            })

    return pd.DataFrame(ratio_rows)


def write_ratios_to_sqlite(df: pd.DataFrame, db_path: str = 'nifty100.db') -> None:
    os.makedirs(os.path.dirname(db_path) or '.', exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        df.to_sql('financial_ratios', conn, if_exists='replace', index=False)


def write_generated_ratios_csv(df: pd.DataFrame, data_path: str = 'data/processed') -> None:
    csv_path = os.path.join(data_path, 'financial_ratios_generated.csv')
    os.makedirs(data_path, exist_ok=True)
    output_df = df.drop(columns=['year_parsed']) if 'year_parsed' in df.columns else df
    output_df.to_csv(csv_path, index=False)


def export_capital_allocation(data_path: str = 'data/processed', output_path: str = 'output/capital_allocation.csv') -> None:
    cf = pd.read_csv(os.path.join(data_path, 'cashflow_cleaned.csv'))
    pl = pd.read_csv(os.path.join(data_path, 'profitandloss_cleaned.csv'))

    cf['company_id'] = cf['company_id'].astype(str)
    pl['company_id'] = pl['company_id'].astype(str)
    cf['year_parsed'] = cf['year'].apply(parse_year_date)
    pl['year_parsed'] = pl['year'].apply(parse_year_date)

    merged = cf.merge(pl[['company_id', 'year_parsed', 'net_profit']], on=['company_id', 'year_parsed'], how='left')
    
    # Rename columns to match expected keys: operating_activity -> cfo, investing_activity -> cfi, financing_activity -> cff
    merged['cfo'] = merged['operating_activity']
    merged['cfi'] = merged['investing_activity']
    merged['cff'] = merged['financing_activity']
    
    merged['cfo_pat_ratio'] = merged.apply(
        lambda row: cfo_pat_ratio(row.get('cfo'), row.get('net_profit')),
        axis=1,
    )

    rows = merged.to_dict(orient='records')
    allocation_rows = generate_capital_allocation_rows(rows)
    write_capital_allocation_csv(allocation_rows, output_path)
    write_capital_allocation_csv(allocation_rows, os.path.join(data_path, 'capital_allocation.csv'))


def run(data_path: str = 'data/processed', db_path: str = 'nifty100.db', output_path: str = 'output/capital_allocation.csv') -> None:
    ratios = build_ratio_dataframe(data_path)
    write_generated_ratios_csv(ratios, data_path)
    write_ratios_to_sqlite(ratios, db_path)
    export_capital_allocation(data_path, output_path)


if __name__ == '__main__':
    os.makedirs('output', exist_ok=True)
    run()
