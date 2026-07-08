import yaml
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional


def load_config(path: str) -> Dict[str, Any]:
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def _to_numeric(series: pd.Series, fillna: Optional[float] = None) -> pd.Series:
    values = pd.to_numeric(series, errors='coerce')
    if fillna is not None:
        values = values.fillna(fillna)
    return values


def _winsorize_scale(series: pd.Series, lower_pct: float = 0.10, upper_pct: float = 0.90) -> pd.Series:
    values = pd.to_numeric(series, errors='coerce')
    if values.empty:
        return pd.Series(np.nan, index=series.index)
    lower = values.quantile(lower_pct)
    upper = values.quantile(upper_pct)
    clipped = values.clip(lower=lower, upper=upper)
    denom = upper - lower
    if denom == 0 or np.isnan(denom):
        return pd.Series(50.0, index=series.index)
    scaled = 100.0 * (clipped - lower) / denom
    return scaled.clip(0, 100)


def _normalize_within_sector(df: pd.DataFrame, column: str, higher_is_better: bool = True) -> pd.Series:
    if column not in df.columns:
        return pd.Series(np.nan, index=df.index)

    normalized = pd.Series(index=df.index, dtype=float)
    sectors = df['broad_sector'].fillna('') if 'broad_sector' in df.columns else pd.Series('', index=df.index)
    for sector, group in df.groupby(sectors):
        normalized.loc[group.index] = _winsorize_scale(group[column])
    normalized = normalized.fillna(50.0)
    if not higher_is_better:
        normalized = 100.0 - normalized
    return normalized


def _safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    num = pd.to_numeric(numerator, errors='coerce')
    den = pd.to_numeric(denominator, errors='coerce').replace({0: np.nan})
    return (num / den).replace([np.inf, -np.inf], np.nan)


def compute_composite_quality_score(df: pd.DataFrame) -> pd.Series:
    df = df.copy()
    df['return_on_equity_pct'] = _to_numeric(df.get('return_on_equity_pct'))
    df['return_on_capital_employed_pct'] = _to_numeric(df.get('return_on_capital_employed_pct'))
    df['net_profit_margin_pct'] = _to_numeric(df.get('net_profit_margin_pct'))
    df['free_cash_flow_cr'] = _to_numeric(df.get('free_cash_flow_cr'))
    df['cash_from_operations_cr'] = _to_numeric(df.get('cash_from_operations_cr'))
    df['net_profit'] = _to_numeric(df.get('net_profit'))
    if 'revenue_cagr_5y_pct' not in df.columns and 'revenue_cagr_5yr' in df.columns:
        df['revenue_cagr_5y_pct'] = _to_numeric(df['revenue_cagr_5yr'])
    else:
        df['revenue_cagr_5y_pct'] = _to_numeric(df.get('revenue_cagr_5y_pct'))
    if 'pat_cagr_5y_pct' not in df.columns and 'pat_cagr_5yr' in df.columns:
        df['pat_cagr_5y_pct'] = _to_numeric(df['pat_cagr_5yr'])
    else:
        df['pat_cagr_5y_pct'] = _to_numeric(df.get('pat_cagr_5y_pct'))
    if 'eps_cagr_5y_pct' not in df.columns and 'eps_cagr_5yr' in df.columns:
        df['eps_cagr_5y_pct'] = _to_numeric(df['eps_cagr_5yr'])
    else:
        df['eps_cagr_5y_pct'] = _to_numeric(df.get('eps_cagr_5y_pct'))
    df['debt_to_equity'] = _to_numeric(df.get('debt_to_equity'))
    df['interest_coverage'] = df.get('interest_coverage')

    df['interest_coverage'] = df['interest_coverage'].replace('Debt Free', np.inf)
    df['interest_coverage'] = _to_numeric(df['interest_coverage'])
    df['cfo_to_pat'] = _safe_divide(df['cash_from_operations_cr'], df['net_profit'])
    df['fcf_positive_flag'] = df['free_cash_flow_cr'].fillna(0) >= 0

    keys = {
        'roe': ('return_on_equity_pct', True),
        'roce': ('return_on_capital_employed_pct', True),
        'npm': ('net_profit_margin_pct', True),
        'fcf_cagr': ('free_cash_flow_cr', True),
        'cfo_to_pat': ('cfo_to_pat', True),
        'fcf_positive': ('fcf_positive_flag', True),
        'rev_cagr': ('revenue_cagr_5y_pct', True),
        'pat_cagr': ('pat_cagr_5y_pct', True),
        'de': ('debt_to_equity', False),
        'icr': ('interest_coverage', True),
    }

    score = pd.Series(0.0, index=df.index)
    weights = {
        'roe': 0.15,
        'roce': 0.10,
        'npm': 0.10,
        'fcf_cagr': 0.15,
        'cfo_to_pat': 0.10,
        'fcf_positive': 0.05,
        'rev_cagr': 0.10,
        'pat_cagr': 0.10,
        'de': 0.10,
        'icr': 0.05,
    }

    for name, (column, higher_is_better) in keys.items():
        if name == 'fcf_cagr':
            target = 'fcf_cagr_5y_pct' if 'fcf_cagr_5y_pct' in df.columns else 'free_cash_flow_cr'
            normalized = _normalize_within_sector(df, target, True)
        elif name == 'fcf_positive':
            normalized = df['fcf_positive_flag'].astype(float) * 100.0
        else:
            normalized = _normalize_within_sector(df, column, higher_is_better)
        score += normalized.fillna(50.0) * weights[name]

    total_weight = sum(weights.values())
    if total_weight > 0:
        score = score / total_weight
    return score.clip(0, 100).fillna(0.0)


def mark_latest_rows_with_trend(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    if 'company_id' not in result.columns or 'year' not in result.columns:
        return result

    result['year'] = pd.to_numeric(result['year'], errors='coerce')
    result = result.sort_values(['company_id', 'year'])
    result['debt_to_equity'] = _to_numeric(result.get('debt_to_equity'))
    result['previous_de_ratio'] = result.groupby('company_id')['debt_to_equity'].shift(1)
    result['de_ratio_declining'] = result['debt_to_equity'] < result['previous_de_ratio']
    latest = result.groupby('company_id', as_index=False).last()
    latest['de_ratio_declining'] = latest['de_ratio_declining'].fillna(False)
    return latest


def apply_filters(df: pd.DataFrame, thresholds: Dict[str, Any]) -> pd.DataFrame:
    df = df.copy()
    for col in [
        'return_on_equity_pct', 'return_on_capital_employed_pct', 'net_profit_margin_pct',
        'free_cash_flow_cr', 'cash_from_operations_cr', 'net_profit', 'revenue_cagr_5y_pct',
        'pat_cagr_5y_pct', 'eps_cagr_5y_pct', 'operating_profit_margin_pct', 'debt_to_equity',
        'pe_ratio', 'pb_ratio', 'dividend_yield_pct', 'dividend_payout_ratio_pct',
        'interest_coverage', 'market_cap_crore', 'asset_turnover', 'revenue', 'sales',
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    if 'interest_coverage' in df.columns:
        df['debt_free_flag'] = df['interest_coverage'].astype(object).fillna('').astype(str).str.lower() == 'debt free'
        df['interest_coverage'] = df['interest_coverage'].replace('Debt Free', np.inf)
        df['interest_coverage'] = pd.to_numeric(df['interest_coverage'], errors='coerce')
    else:
        df['debt_free_flag'] = False

    df['fcf_positive_flag'] = df.get('free_cash_flow_cr', pd.Series(np.nan, index=df.index)).fillna(-np.inf) >= 0
    df['de_ratio_declining'] = df.get('de_ratio_declining', False).astype(bool)

    passes = pd.Series(True, index=df.index)

    if thresholds.get('roe_min') is not None:
        passes &= df['return_on_equity_pct'].fillna(-np.inf) >= float(thresholds['roe_min'])
    if thresholds.get('de_max') is not None:
        max_de = float(thresholds['de_max'])
        is_financial = df.get('broad_sector') == 'Financials'
        de_ok = df['debt_to_equity'].fillna(np.inf) <= max_de
        passes &= de_ok | is_financial.fillna(False)
    if thresholds.get('fcf_min') is not None:
        passes &= df['free_cash_flow_cr'].fillna(-np.inf) >= float(thresholds['fcf_min'])
    if thresholds.get('revenue_cagr_5y_min') is not None:
        passes &= df['revenue_cagr_5y_pct'].fillna(-np.inf) >= float(thresholds['revenue_cagr_5y_min'])
    if thresholds.get('pat_cagr_5y_min') is not None:
        passes &= df['pat_cagr_5y_pct'].fillna(-np.inf) >= float(thresholds['pat_cagr_5y_min'])
    if thresholds.get('opm_min') is not None:
        passes &= df['operating_profit_margin_pct'].fillna(-np.inf) >= float(thresholds['opm_min'])
    if thresholds.get('pe_max') is not None and 'pe_ratio' in df.columns:
        passes &= df['pe_ratio'].fillna(np.inf) <= float(thresholds['pe_max'])
    if thresholds.get('pb_max') is not None and 'pb_ratio' in df.columns:
        passes &= df['pb_ratio'].fillna(np.inf) <= float(thresholds['pb_max'])
    if thresholds.get('dividend_yield_min') is not None and 'dividend_yield_pct' in df.columns:
        passes &= df['dividend_yield_pct'].fillna(-np.inf) >= float(thresholds['dividend_yield_min'])
    if thresholds.get('dividend_payout_ratio_pct_max') is not None and 'dividend_payout_ratio_pct' in df.columns:
        passes &= df['dividend_payout_ratio_pct'].fillna(np.inf) <= float(thresholds['dividend_payout_ratio_pct_max'])
    if thresholds.get('icr_min') is not None and 'interest_coverage' in df.columns:
        min_icr = float(thresholds['icr_min'])
        icr_ok = df['debt_free_flag'] | df['interest_coverage'].fillna(-np.inf) >= min_icr
        passes &= icr_ok
    if thresholds.get('market_cap_min') is not None and 'market_cap_crore' in df.columns:
        passes &= df['market_cap_crore'].fillna(-np.inf) >= float(thresholds['market_cap_min'])
    if thresholds.get('net_profit_min') is not None and 'net_profit' in df.columns:
        passes &= df['net_profit'].fillna(-np.inf) >= float(thresholds['net_profit_min'])
    if thresholds.get('eps_cagr_min') is not None and 'eps_cagr_5y_pct' in df.columns:
        passes &= df['eps_cagr_5y_pct'].fillna(-np.inf) >= float(thresholds['eps_cagr_min'])
    if thresholds.get('asset_turnover_min') is not None and 'asset_turnover' in df.columns:
        passes &= df['asset_turnover'].fillna(-np.inf) >= float(thresholds['asset_turnover_min'])
    if thresholds.get('sales_min') is not None and ('revenue' in df.columns or 'sales' in df.columns):
        sales_value = df['revenue'].fillna(df.get('sales', pd.Series(np.nan, index=df.index)))
        passes &= sales_value.fillna(-np.inf) >= float(thresholds['sales_min'])
    if thresholds.get('revenue_min') is not None and ('revenue' in df.columns or 'sales' in df.columns):
        revenue_value = df['revenue'].fillna(df.get('sales', pd.Series(np.nan, index=df.index)))
        passes &= revenue_value.fillna(-np.inf) >= float(thresholds['revenue_min'])
    if thresholds.get('revenue_cagr_3y_min') is not None and 'revenue_cagr_3y_pct' in df.columns:
        passes &= df['revenue_cagr_3y_pct'].fillna(-np.inf) >= float(thresholds['revenue_cagr_3y_min'])
    if thresholds.get('pat_cagr_3y_min') is not None and 'pat_cagr_3y_pct' in df.columns:
        passes &= df['pat_cagr_3y_pct'].fillna(-np.inf) >= float(thresholds['pat_cagr_3y_min'])
    if thresholds.get('de_declining'):
        passes &= df['de_ratio_declining']
    if thresholds.get('debt_free_only'):
        passes &= df['debt_free_flag']
    if thresholds.get('fcf_positive_only'):
        passes &= df['fcf_positive_flag']

    if 'composite_quality_score' not in df.columns:
        df['composite_quality_score'] = compute_composite_quality_score(df)

    df['_passes_thresholds'] = passes
    out = df[df['_passes_thresholds']].sort_values('composite_quality_score', ascending=False)
    return out.drop(columns=['_passes_thresholds'])


if __name__ == '__main__':
    print('screener.engine module — import and call load_config/apply_filters from scripts')
