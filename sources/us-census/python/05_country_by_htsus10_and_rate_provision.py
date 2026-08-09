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
    response = requests.get(BASE_URL, params=params, timeout=180)
    response.raise_for_status()
    payload = response.json()
    return pd.DataFrame(payload[1:], columns=payload[0])


def query_year(year: int, country_code: str, api_key: str) -> pd.DataFrame:
    params = {
        "get": ",".join(["I_COMMODITY", "RP", "CTY_NAME", *VALUE_COLUMNS]),
        "YEAR": str(year),
        "MONTH": "12",
        "CTY_CODE": country_code,
        "COMM_LVL": "HS10",
        "SUMMARY_LVL": "DET",
        "SUMMARY_LVL2": "HSCYRP",
        "key": api_key,
    }

    df = census_table(params)
    df = df[["I_COMMODITY", "RP", "CTY_NAME", *VALUE_COLUMNS]].copy()
    df = df[df["I_COMMODITY"].astype(str).str.len() == 10]

    df["I_COMMODITY"] = df["I_COMMODITY"].astype(str).str.zfill(10)
    df["RP"] = df["RP"].astype(str).str.zfill(2)
    for column in VALUE_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce").astype("Int64")

    df = df.rename(
        columns={
            "I_COMMODITY": "htsus10",
            "RP": "rate_provision_code",
            "CTY_NAME": "country_name",
            "GEN_VAL_YR": "general_imports_usd",
            "CON_VAL_YR": "imports_for_consumption_usd",
            "DUT_VAL_YR": "dutiable_value_usd",
            "CAL_DUT_YR": "calculated_duties_usd",
        }
    )
    df.insert(0, "country_code", str(country_code).zfill(4))
    df.insert(0, "year", year)
    return df


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download one country's U.S. imports by HTS10 and Rate Provision code."
    )
    parser.add_argument("--years", nargs="+", type=int, default=[2024, 2025])
    parser.add_argument(
        "--country-code",
        default="3510",
        help="Census Schedule C country code. Default: 3510 (Brazil).",
    )
    parser.add_argument("--output", default="data/country_hts_rate_provision.csv")
    args = parser.parse_args()

    api_key = os.environ.get("CENSUS_API_KEY")
    if not api_key:
        raise SystemExit("Set the CENSUS_API_KEY environment variable first.")

    result = pd.concat(
        [query_year(year, args.country_code, api_key) for year in args.years],
        ignore_index=True,
    )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output, index=False)
    print(f"Saved {len(result):,} rows to {output}")


if __name__ == "__main__":
    main()
