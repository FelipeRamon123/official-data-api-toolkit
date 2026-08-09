from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd
import requests

BASE_URL = "https://api.census.gov/data/timeseries/intltrade/imports/hs"
VALUE_COLUMNS = [
    "GEN_VAL_YR",
    "CON_VAL_YR",
    "DUT_VAL_YR",
    "CAL_DUT_YR",
]


def census_table(params: dict[str, str]) -> pd.DataFrame:
    response = requests.get(BASE_URL, params=params, timeout=120)
    response.raise_for_status()
    payload = response.json()
    return pd.DataFrame(payload[1:], columns=payload[0])


def query_year(year: int, api_key: str) -> pd.DataFrame:
    params = {
        "get": ",".join(
            [
                "I_COMMODITY",
                "I_COMMODITY_LDESC",
                "GEN_VAL_YR",
                "CON_VAL_YR",
                "DUT_VAL_YR",
                "CAL_DUT_YR",
            ]
        ),
        "YEAR": str(year),
        "MONTH": "12",
        "COMM_LVL": "HS10",
        "SUMMARY_LVL2": "HS",
        "key": api_key,
    }

    df = census_table(params)
    df = df[["I_COMMODITY", "I_COMMODITY_LDESC", *VALUE_COLUMNS]].copy()
    df = df[df["I_COMMODITY"].astype(str).str.len() == 10]

    df["I_COMMODITY"] = df["I_COMMODITY"].astype(str).str.zfill(10)
    for column in VALUE_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce").astype("Int64")

    df = df.rename(
        columns={
            "I_COMMODITY": "htsus10",
            "I_COMMODITY_LDESC": "hts_description",
            "GEN_VAL_YR": "general_imports_usd",
            "CON_VAL_YR": "imports_for_consumption_usd",
            "DUT_VAL_YR": "dutiable_value_usd",
            "CAL_DUT_YR": "calculated_duties_usd",
        }
    )
    df.insert(0, "origin_aggregation", "WORLD")
    df.insert(0, "year", year)
    return df


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download annual U.S. imports by HTS10 with all origins aggregated."
    )
    parser.add_argument("--years", nargs="+", type=int, default=[2024, 2025])
    parser.add_argument("--output", default="data/world_htsus10.csv")
    args = parser.parse_args()

    api_key = os.environ.get("CENSUS_API_KEY")
    if not api_key:
        raise SystemExit("Set the CENSUS_API_KEY environment variable first.")

    result = pd.concat(
        [query_year(year, api_key) for year in args.years],
        ignore_index=True,
    )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output, index=False)
    print(f"Saved {len(result):,} rows to {output}")


if __name__ == "__main__":
    main()
