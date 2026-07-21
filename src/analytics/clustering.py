"""KMeans clustering for Nifty universe archetype assignment.

This module builds a 5-cluster archetype model using key financial features,
handles missing values with sector-median imputation, and writes both the elbow
plot and final company cluster assignments.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


FEATURES: List[str] = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin_pct",
]


def _extract_year(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.extract(r"(\d{4})")[0], errors="coerce")


def _compute_fcf_cagr_5yr_from_history(ratios_path: Path) -> pd.DataFrame:
    history = pd.read_csv(ratios_path)
    if "company_id" not in history.columns:
        raise ValueError("financial_ratios_generated.csv is missing company_id")
    if "year" not in history.columns:
        raise ValueError("financial_ratios_generated.csv is missing year")
    if "free_cash_flow_cr" not in history.columns:
        raise ValueError("financial_ratios_generated.csv is missing free_cash_flow_cr")

    history = history.copy()
    history["company_id"] = history["company_id"].astype(str).str.strip().str.upper()
    history["year_num"] = _extract_year(history["year"])
    history["free_cash_flow_cr"] = pd.to_numeric(history["free_cash_flow_cr"], errors="coerce")

    history = history.sort_values(["company_id", "year_num"])
    history["fcf_5y_ago"] = history.groupby("company_id")["free_cash_flow_cr"].shift(5)

    history["fcf_cagr_5yr"] = np.where(
        (history["free_cash_flow_cr"] > 0) & (history["fcf_5y_ago"] > 0),
        ((history["free_cash_flow_cr"] / history["fcf_5y_ago"]) ** (1.0 / 5.0) - 1.0) * 100.0,
        np.nan,
    )

    latest = history.groupby("company_id", as_index=False).tail(1)
    return latest[["company_id", "fcf_cagr_5yr"]]


def _load_clustering_base(
    screener_path: Path,
    companies_path: Path,
    ratios_path: Path,
    sectors_path: Path,
) -> pd.DataFrame:
    base = pd.read_csv(screener_path)
    companies = pd.read_csv(companies_path)

    base = base.copy()
    base["company_id"] = base["company_id"].astype(str).str.strip().str.upper()

    company_id_col = "id" if "id" in companies.columns else "company_id"
    if company_id_col not in companies.columns:
        raise ValueError("companies_cleaned.csv must include id or company_id")

    target_ids = set(companies[company_id_col].astype(str).str.strip().str.upper())
    base = base[base["company_id"].isin(target_ids)].copy()

    if "revenue_cagr_5yr" not in base.columns and "revenue_cagr_5y_pct" in base.columns:
        base["revenue_cagr_5yr"] = pd.to_numeric(base["revenue_cagr_5y_pct"], errors="coerce")

    if "fcf_cagr_5yr" not in base.columns:
        fcf_cagr = _compute_fcf_cagr_5yr_from_history(ratios_path)
        base = base.merge(fcf_cagr, on="company_id", how="left")

    for col in FEATURES:
        if col not in base.columns:
            base[col] = np.nan
        base[col] = pd.to_numeric(base[col], errors="coerce")

    if "broad_sector" not in base.columns:
        base["broad_sector"] = np.nan

    if base["broad_sector"].isna().any() and sectors_path.exists():
        sectors = pd.read_csv(sectors_path)
        if "company_id" not in sectors.columns and "id" in sectors.columns:
            sectors = sectors.rename(columns={"id": "company_id"})
        if "company_id" in sectors.columns:
            sectors["company_id"] = sectors["company_id"].astype(str).str.strip().str.upper()
            keep_cols = [c for c in ["company_id", "broad_sector"] if c in sectors.columns]
            if keep_cols:
                base = base.drop(columns=["broad_sector"], errors="ignore").merge(
                    sectors[keep_cols].drop_duplicates(subset=["company_id"]),
                    on="company_id",
                    how="left",
                )

    base["broad_sector"] = base["broad_sector"].fillna("Unknown")

    return base


def _impute_with_sector_median(df: pd.DataFrame, features: List[str], sector_col: str = "broad_sector") -> pd.DataFrame:
    out = df.copy()
    out[sector_col] = out[sector_col].fillna("Unknown")

    for feature in features:
        sector_median = out.groupby(sector_col)[feature].transform("median")
        out[feature] = out[feature].fillna(sector_median)
        out[feature] = out[feature].fillna(out[feature].median())

    return out


def _save_elbow_plot(x_scaled: np.ndarray, output_path: Path) -> None:
    inertias: List[float] = []
    ks = list(range(2, 11))

    for k in ks:
        model = KMeans(n_clusters=k, random_state=42, n_init=10)
        model.fit(x_scaled)
        inertias.append(float(model.inertia_))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(8, 5))
    plt.plot(ks, inertias, marker="o")
    plt.title("KMeans Elbow Plot")
    plt.xlabel("Number of clusters (k)")
    plt.ylabel("Inertia")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def _build_cluster_name_map(centroids_unscaled: np.ndarray) -> Dict[int, str]:
    # Composite archetype score favors profitability and growth, penalizes leverage.
    cdf = pd.DataFrame(centroids_unscaled, columns=FEATURES)
    cdf["archetype_score"] = (
        cdf["return_on_equity_pct"].fillna(0)
        + cdf["operating_profit_margin_pct"].fillna(0)
        + cdf["revenue_cagr_5yr"].fillna(0)
        + cdf["fcf_cagr_5yr"].fillna(0)
        - cdf["debt_to_equity"].fillna(0) * 10.0
    )

    rank_order = cdf.sort_values("archetype_score", ascending=False).index.tolist()
    labels_by_rank = [
        "Quality Compounders",
        "Growth Leaders",
        "Balanced Performers",
        "Value Steadies",
        "Turnaround Watch",
    ]

    name_map: Dict[int, str] = {}
    for i, cluster_idx in enumerate(rank_order):
        name_map[int(cluster_idx)] = labels_by_rank[i]

    return name_map


def run_kmeans_clustering(
    screener_path: Path = Path("output/screener_full_ranked_universe.csv"),
    companies_path: Path = Path("data/processed/companies_cleaned.csv"),
    ratios_path: Path = Path("data/processed/financial_ratios_generated.csv"),
    sectors_path: Path = Path("data/processed/sectors_cleaned.csv"),
    elbow_plot_path: Path = Path("reports/elbow_plot.png"),
    output_csv_path: Path = Path("output/cluster_labels.csv"),
) -> pd.DataFrame:
    df = _load_clustering_base(screener_path, companies_path, ratios_path, sectors_path)
    df = _impute_with_sector_median(df, FEATURES, sector_col="broad_sector")

    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(df[FEATURES])

    _save_elbow_plot(x_scaled, elbow_plot_path)

    model = KMeans(n_clusters=5, random_state=42, n_init=10)
    cluster_ids = model.fit_predict(x_scaled)
    distances = np.linalg.norm(x_scaled - model.cluster_centers_[cluster_ids], axis=1)

    centroids_unscaled = scaler.inverse_transform(model.cluster_centers_)
    cluster_name_map = _build_cluster_name_map(centroids_unscaled)

    result = pd.DataFrame(
        {
            "company_id": df["company_id"].astype(str),
            "cluster_id": cluster_ids.astype(int),
            "cluster_name": [cluster_name_map[int(cid)] for cid in cluster_ids],
            "distance_from_centroid": np.round(distances, 6),
        }
    ).sort_values(["cluster_id", "distance_from_centroid", "company_id"]).reset_index(drop=True)

    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_csv_path, index=False)
    return result


def main() -> None:
    result = run_kmeans_clustering()
    print(f"Cluster assignments written: {len(result)} rows")
    print("Saved elbow plot to reports/elbow_plot.png")
    print("Saved cluster labels to output/cluster_labels.csv")


if __name__ == "__main__":
    main()
