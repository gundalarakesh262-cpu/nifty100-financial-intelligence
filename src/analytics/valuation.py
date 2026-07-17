import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

INPUT = ROOT / "output" / "screener_full_ranked_universe.csv"

SUMMARY_OUTPUT = ROOT / "output" / "valuation_summary.xlsx"
FLAGS_OUTPUT = ROOT / "output" / "valuation_flags.csv"


def load_data():

    if not INPUT.exists():
        raise FileNotFoundError(INPUT)

    df = pd.read_csv(INPUT)

    df["company_id"] = (
        df["company_id"]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    if "company_name" not in df.columns:
        df["company_name"] = df["company_id"]

    df["company_name"] = (
        df["company_name"]
        .fillna(df["company_id"])
        .astype(str)
        .str.strip()
    )

    numeric = [
        "free_cash_flow_cr",
        "earnings_per_share",
        "book_value_per_share",
        "composite_score",
        "score_pe",
        "score_pb",
        "score_fcf_yield",
    ]

    for col in numeric:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def calculate(df):

    df = df.copy()

    if "score_fcf_yield" in df.columns:
        df["FCF Yield Score"] = df["score_fcf_yield"]
    else:
        df["FCF Yield Score"] = 0

    def pe_flag(score):

        if pd.isna(score):
            return "Unknown"

        if score >= 8:
            return "Cheap"

        if score >= 5:
            return "Fair"

        return "Expensive"

    df["PE Flag"] = df["score_pe"].apply(pe_flag)

    def valuation(score):

        if pd.isna(score):
            return "Unknown"

        if score >= 80:
            return "Undervalued"

        if score >= 60:
            return "Fair Value"

        return "Overvalued"

    df["Valuation"] = df["composite_score"].apply(valuation)

    return df


def export(df):

    summary = df[
        [
            "company_id",
            "company_name",
            "broad_sector_y",
            "free_cash_flow_cr",
            "earnings_per_share",
            "book_value_per_share",
            "FCF Yield Score",
            "PE Flag",
            "Valuation",
            "composite_score",
        ]
    ].copy()

    summary.columns = [
        "Company ID",
        "Company",
        "Sector",
        "Free Cash Flow",
        "EPS",
        "Book Value",
        "FCF Yield Score",
        "PE Flag",
        "Valuation",
        "Composite Score",
    ]

    summary.to_excel(SUMMARY_OUTPUT, index=False)

    flags = summary[
        summary["Valuation"].isin(
            [
                "Undervalued",
                "Overvalued",
            ]
        )
    ]

    flags.to_csv(
        FLAGS_OUTPUT,
        index=False,
    )

    print("Done!")
    print(f"Summary : {SUMMARY_OUTPUT}")
    print(f"Flags   : {FLAGS_OUTPUT}")


def main():

    df = load_data()

    df = calculate(df)

    export(df)


if __name__ == "__main__":
    main()