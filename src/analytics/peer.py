import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font
from openpyxl.utils import get_column_letter


def load_peer_groups(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    if 'company_id' not in df.columns and 'id' in df.columns:
        df = df.rename(columns={'id': 'company_id'})
    df['company_id'] = df['company_id'].astype(str).str.strip().str.upper()
    return df


def attach_peer_groups(df: pd.DataFrame, peer_groups: pd.DataFrame) -> pd.DataFrame:
    if 'company_id' not in df.columns:
        return df.copy()

    merged = df.copy()
    merged['company_id'] = merged['company_id'].astype(str).str.strip().str.upper()
    peer_subset = peer_groups[['company_id', 'peer_group_name', 'is_benchmark']].copy()
    peer_subset['company_id'] = peer_subset['company_id'].astype(str).str.strip().str.upper()

    if 'peer_group_name' in merged.columns or 'is_benchmark' in merged.columns:
        merged = merged.drop(columns=['peer_group_name', 'is_benchmark'], errors='ignore')

    merged = merged.merge(
        peer_subset,
        on='company_id',
        how='left',
    )
    return merged


def percentile_rank(series: pd.Series, higher_is_better: bool = True) -> pd.Series:
    values = pd.to_numeric(series, errors='coerce')
    if higher_is_better:
        return values.rank(pct=True, method='max').fillna(0) * 100
    return (1 - values.rank(pct=True, method='max')).fillna(0) * 100


def compute_metric_percentiles(df: pd.DataFrame, peer_group_col: str = 'peer_group_name') -> pd.DataFrame:
    metrics = {
        'ROE': ('return_on_equity_pct', True),
        'ROCE': ('return_on_capital_employed_pct', True),
        'Net Profit Margin': ('net_profit_margin_pct', True),
        'D/E': ('debt_to_equity', False),
        'FCF': ('free_cash_flow_cr', True),
        'PAT CAGR 5yr': ('pat_cagr_5y_pct', True),
        'Revenue CAGR 5yr': ('revenue_cagr_5y_pct', True),
        'EPS CAGR 5yr': ('eps_cagr_5y_pct', True),
        'Interest Coverage': ('interest_coverage', True),
        'Asset Turnover': ('asset_turnover', True),
    }

    out_rows: List[Dict[str, Optional[float]]] = []
    required_cols = [col for _, (col, _) in metrics.items()]
    if peer_group_col not in df.columns:
        return pd.DataFrame(out_rows)

    base = df.copy()
    base['peer_group_name'] = base[peer_group_col]

    for group_name, group in base.groupby('peer_group_name'):
        if pd.isna(group_name):
            continue
        for _, row in group.iterrows():
            for metric_name, (col, higher) in metrics.items():
                if col not in group.columns:
                    value = None
                    rank = None
                else:
                    value = row[col]
                    rank = percentile_rank(group[col], higher).loc[row.name]
                out_rows.append({
                    'company_id': row.get('company_id'),
                    'peer_group_name': group_name,
                    'metric': metric_name,
                    'value': value,
                    'percentile_rank': rank,
                    'year': row.get('year'),
                })

    return pd.DataFrame(out_rows)


def write_peer_percentiles_sqlite(df: pd.DataFrame, db_path: str = 'nifty100.db') -> None:
    if df.empty:
        return
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(path)) as conn:
        df.to_sql('peer_percentiles', conn, if_exists='replace', index=False)
def generate_peer_comparison_excel(
    df: pd.DataFrame,
    peer_groups: pd.DataFrame,
    output_path: str = 'output/peer_comparison.xlsx',
) -> None:
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if 'company_id' in df.columns:
        df['company_id'] = df['company_id'].astype(str).str.strip().str.upper()

    peer_groups = peer_groups.copy()
    peer_groups['company_id'] = peer_groups['company_id'].astype(str).str.strip().str.upper()

    merged = attach_peer_groups(df, peer_groups)

    # Day 20 requires 20 metric columns
    metrics = [
        'return_on_equity_pct',
        'return_on_capital_employed_pct',
        'return_on_assets_pct',
        'net_profit_margin_pct',
        'operating_profit_margin_pct',
        'debt_to_equity',
        'interest_coverage',
        'asset_turnover',
        'net_debt_cr',
        'free_cash_flow_cr',
        'capex_cr',
        'cash_from_operations_cr',
        'earnings_per_share',
        'book_value_per_share',
        'dividend_payout_ratio_pct',
        'revenue_cagr_5y_pct',
        'pat_cagr_5y_pct',
        'eps_cagr_5y_pct',
        'pe_ratio',
        'pb_ratio',
    ]

    lower_is_better_metrics = {
        'debt_to_equity',
        'net_debt_cr',
        'capex_cr',
        'pe_ratio',
        'pb_ratio',
    }

    # Ensure all 20 metric columns exist, even if some are blank
    for metric in metrics:
        if metric not in merged.columns:
            merged[metric] = np.nan

    if 'company_name' not in merged.columns:
        merged['company_name'] = merged['company_id']

    ranks = merged.copy()

    # Calculate percentile rank within each peer group
    for metric in metrics:
        higher_is_better = metric not in lower_is_better_metrics

        ranks[f'{metric}_percentile'] = (
            ranks
            .groupby('peer_group_name', dropna=False)[metric]
            .transform(lambda series: percentile_rank(series, higher_is_better=higher_is_better))
            .fillna(50)
        )

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        for group_name, group in ranks.groupby('peer_group_name'):
            if pd.isna(group_name):
                continue

            sheet_name = str(group_name)[:31]

            cols = (
                ['company_id', 'company_name']
                + metrics
                + [f'{metric}_percentile' for metric in metrics]
            )

            subset = group[cols].copy()

            # Add proper median row at bottom
            median_row = {col: '' for col in subset.columns}
            median_row['company_id'] = 'MEDIAN'
            median_row['company_name'] = 'Peer Group Median'

            for metric in metrics:
                median_row[metric] = pd.to_numeric(subset[metric], errors='coerce').median()

            subset = pd.concat(
                [subset, pd.DataFrame([median_row])],
                ignore_index=True
            )

            subset.to_excel(writer, sheet_name=sheet_name, index=False)

    # Apply conditional formatting and benchmark highlight
    workbook = load_workbook(output_file)

    green_fill = PatternFill(start_color='C6EFCE', end_color='C6EFCE', fill_type='solid')
    yellow_fill = PatternFill(start_color='FFEB9C', end_color='FFEB9C', fill_type='solid')
    red_fill = PatternFill(start_color='FFC7CE', end_color='FFC7CE', fill_type='solid')
    gold_fill = PatternFill(start_color='FFD966', end_color='FFD966', fill_type='solid')
    header_fill = PatternFill(start_color='1F4E78', end_color='1F4E78', fill_type='solid')
    median_fill = PatternFill(start_color='D9EAF7', end_color='D9EAF7', fill_type='solid')

    white_bold_font = Font(bold=True, color='FFFFFF')
    bold_font = Font(bold=True)

    for sheet_name in workbook.sheetnames:
        sheet = workbook[sheet_name]

        headers = [cell.value for cell in next(sheet.iter_rows(min_row=1, max_row=1))]

        percentile_cols = [
            i + 1
            for i, h in enumerate(headers)
            if isinstance(h, str) and h.endswith('_percentile')
        ]

        company_col = next(
            (i + 1 for i, h in enumerate(headers) if h == 'company_id'),
            None
        )

        # Header styling
        for cell in sheet[1]:
            cell.fill = header_fill
            cell.font = white_bold_font

        # Correct benchmark IDs only
        benchmark_ids = set(
            peer_groups.loc[
                (peer_groups['peer_group_name'].astype(str).str[:31] == sheet_name)
                & (
                    peer_groups['is_benchmark']
                    .astype(str)
                    .str.lower()
                    .isin(['true', '1', 'yes'])
                ),
                'company_id'
            ]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        for row_idx in range(2, sheet.max_row + 1):
            company_id = ''
            if company_col:
                company_id = str(sheet.cell(row=row_idx, column=company_col).value).strip().upper()

            # Median row styling
            if company_id == 'MEDIAN':
                for col_idx in range(1, sheet.max_column + 1):
                    sheet.cell(row=row_idx, column=col_idx).fill = median_fill
                    sheet.cell(row=row_idx, column=col_idx).font = bold_font
                continue

            # Percentile colouring
            for col_idx in percentile_cols:
                cell = sheet.cell(row=row_idx, column=col_idx)

                try:
                    pct = float(cell.value)
                except Exception:
                    continue

                if pct >= 75:
                    cell.fill = green_fill
                elif pct <= 25:
                    cell.fill = red_fill
                else:
                    cell.fill = yellow_fill

                cell.number_format = '0.0'

            # Highlight benchmark row
            if company_id in benchmark_ids:
                for col_idx in range(1, sheet.max_column + 1):
                    sheet.cell(row=row_idx, column=col_idx).fill = gold_fill
                    sheet.cell(row=row_idx, column=col_idx).font = bold_font

        # Formatting
        sheet.freeze_panes = 'C2'
        sheet.auto_filter.ref = sheet.dimensions

        for col_idx in range(1, sheet.max_column + 1):
            sheet.column_dimensions[get_column_letter(col_idx)].width = 18

        sheet.column_dimensions['A'].width = 16
        sheet.column_dimensions['B'].width = 32

    workbook.save(output_file)



def generate_radar_charts(
    df: pd.DataFrame,
    peer_groups: pd.DataFrame,
    output_dir: str = 'reports/radar_charts',
) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    radar_metrics = [
        ('ROE', 'return_on_equity_pct'),
        ('ROCE', 'return_on_capital_employed_pct'),
        ('NPM', 'net_profit_margin_pct'),
        ('D/E', 'debt_to_equity'),
        ('FCF', 'free_cash_flow_cr'),
        ('PAT CAGR 5yr', 'pat_cagr_5y_pct'),
        ('Revenue CAGR 5yr', 'revenue_cagr_5y_pct'),
        ('Composite Score', 'composite_quality_score'),
    ]

    merged = attach_peer_groups(df, peer_groups)
    merged['company_id'] = merged['company_id'].astype(str).str.strip().str.upper()

    gauges = len(radar_metrics)
    angles = [n / float(gauges) * 2 * np.pi for n in range(gauges)]
    angles += angles[:1]

    for group_name, group in merged.groupby('peer_group_name'):
        if pd.isna(group_name):
            continue
        peer_avg = {}
        for label, col in radar_metrics:
            if col in group.columns:
                if label == 'D/E':
                    peer_avg[label] = 100.0 - percentile_rank(group[col], False).mean()
                else:
                    peer_avg[label] = np.nanmean(pd.to_numeric(group[col], errors='coerce'))
            else:
                peer_avg[label] = 0.0

        peer_values = [peer_avg[label] for label, _ in radar_metrics]
        peer_values += peer_values[:1]

        for _, row in group.iterrows():
            company_values = []
            for label, col in radar_metrics:
                company_values.append(float(row[col]) if pd.notna(row.get(col)) else 0.0)
            company_values += company_values[:1]

            plt.figure(figsize=(8, 8))
            ax = plt.subplot(111, polar=True)
            plt.xticks(angles[:-1], [label for label, _ in radar_metrics], color='grey', size=8)
            ax.set_rlabel_position(30)
            ax.plot(angles, peer_values, linewidth=1, linestyle='dashed', label='Peer Avg')
            ax.fill(angles, peer_values, alpha=0.1)
            ax.plot(angles, company_values, linewidth=2, linestyle='solid', label=str(row.get('company_id', '')))
            ax.fill(angles, company_values, alpha=0.25)
            plt.title(f"{row.get('company_id', '')} — {group_name}", size=11, y=1.1)
            plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
            plt.tight_layout()
            filename = output_path / f"{row.get('company_id', '')}_radar.png"
            plt.savefig(filename, dpi=150)
            plt.close()

    if merged['peer_group_name'].isna().any():
        no_group = merged[merged['peer_group_name'].isna()]
        avg = merged[merged['peer_group_name'].notna()]
        if not avg.empty:
            nifty_avg = {}
            for label, col in radar_metrics:
                nifty_avg[label] = np.nanmean(pd.to_numeric(avg.get(col), errors='coerce'))
            values = [float(no_group.iloc[0].get(col, 0.0)) for _, col in radar_metrics]
            values += values[:1]
            avg_values = [float(nifty_avg[label]) for label, _ in radar_metrics]
            avg_values += avg_values[:1]
            plt.figure(figsize=(8, 8))
            ax = plt.subplot(111, polar=True)
            plt.xticks(angles[:-1], [label for label, _ in radar_metrics], color='grey', size=8)
            ax.plot(angles, avg_values, linewidth=1, linestyle='dashed', label='Nifty 100 Avg')
            ax.plot(angles, values, linewidth=2, linestyle='solid', label=str(no_group.iloc[0].get('company_id', '')))
            ax.fill(angles, values, alpha=0.25)
            plt.title(f"{no_group.iloc[0].get('company_id', '')} — No Peer Group", size=11, y=1.1)
            plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
            plt.tight_layout()
            filename = output_path / f"{no_group.iloc[0].get('company_id', '')}_radar.png"
            plt.savefig(filename, dpi=150)
            plt.close()
