import pandas as pd
from typing import Dict, List, Any


def load_peer_groups(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    if 'company_id' not in df.columns and 'id' in df.columns:
        df = df.rename(columns={'id': 'company_id'})
    df['company_id'] = df['company_id'].astype(str).str.strip().str.upper()
    return df


def attach_peer_groups(df: pd.DataFrame, peer_groups: pd.DataFrame) -> pd.DataFrame:
    merged = df.copy()
    if 'company_id' in merged.columns and 'company_id' in peer_groups.columns:
        merged['company_id'] = merged['company_id'].astype(str).str.strip().str.upper()
        merged = merged.merge(
            peer_groups[['company_id', 'peer_group_name', 'is_benchmark']],
            on='company_id',
            how='left'
        )
    return merged


def percentile_rank(series: pd.Series, higher_is_better: bool = True) -> pd.Series:
    values = pd.to_numeric(series, errors='coerce')
    if higher_is_better:
        return values.rank(pct=True, method='max') * 100
    return (1 - values.rank(pct=True, method='max')) * 100


def compute_peer_percentiles(
    df: pd.DataFrame,
    peer_group_col: str = 'peer_group_name',
    metrics: Dict[str, Dict[str, Any]] = None,
) -> pd.DataFrame:
    if metrics is None:
        metrics = {
            'peer_score_roe': {'col': 'return_on_equity_pct', 'higher_is_better': True, 'weight': 0.15},
            'peer_score_roce': {'col': 'return_on_capital_employed_pct', 'higher_is_better': True, 'weight': 0.15},
            'peer_score_margin': {'col': 'net_profit_margin_pct', 'higher_is_better': True, 'weight': 0.1},
            'peer_score_revenue_growth': {'col': 'revenue_cagr_5y_pct', 'higher_is_better': True, 'weight': 0.15},
            'peer_score_profit_growth': {'col': 'pat_cagr_5y_pct', 'higher_is_better': True, 'weight': 0.15},
            'peer_score_debt': {'col': 'debt_to_equity', 'higher_is_better': False, 'weight': 0.1},
            'peer_score_fcf': {'col': 'free_cash_flow_cr', 'higher_is_better': True, 'weight': 0.1},
            'peer_score_pe': {'col': 'pe_ratio', 'higher_is_better': False, 'weight': 0.05},
            'peer_score_pb': {'col': 'pb_ratio', 'higher_is_better': False, 'weight': 0.05},
        }

    df = df.copy()
    if peer_group_col not in df.columns:
        return df

    used_metrics = {}
    for score_name, spec in metrics.items():
        col = spec['col']
        higher = spec['higher_is_better']
        if col not in df.columns:
            continue

        percentile_values = (
            df.groupby(peer_group_col)[col]
            .apply(lambda series: percentile_rank(series, higher))
            .reset_index(level=0, drop=True)
        )
        df[score_name] = percentile_values.reindex(df.index).fillna(50)
        used_metrics[score_name] = spec

    if not used_metrics:
        df['peer_composite_score'] = 50.0
        return df

    # composite score within peer groups
    weighted_scores = []
    total_weight = 0.0
    for score_name, spec in used_metrics.items():
        weight = spec.get('weight', 0.0)
        weighted_scores.append(df[score_name].fillna(50) * weight)
        total_weight += weight
    if total_weight == 0:
        df['peer_composite_score'] = 50.0
    else:
        df['peer_composite_score'] = sum(weighted_scores) / total_weight

    # count peers in group
    df['peer_group_size'] = df.groupby(peer_group_col)[peer_group_col].transform('count')
    return df
