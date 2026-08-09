from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd
import requests

BASE_URL = "https://api.census.gov/data/timeseries/intltrade/imports/sitc"
VALUE_COLUMNS = [
    "GEN_VAL_YR",
    "CON_VAL_YR",
    "DUT_VAL_YR",
    "CAL_DUT_YR",
]

SITC_SECTIONS = {
    "0": "Food and live animals",
    "1": "Beverages and tobacco",
    "2": "Crude materials, inedible, except fuels",
    "3": "Mineral fuels, lubricants and related materials",
    "4": "Animal and vegetable oils, fats and waxes",
    "5": "Chemicals and related products",
    "6": "Manufactured goods classified chiefly by material",
    "7": "Machinery and transport equipment",
    "8": "Miscellaneous manufactured articles",
    "9": "Commodities and transactions not classified elsewhere",
}


def census_table(params: dict[str, str]) -> pd.DataFrame:
    response = requests.get(BASE_URL, params=params, timeout=120)
    response.raise_for_status()
    payload = response.json()
    return pd.DataFrame(payload[1:], columns=payload[0])


def query_year(year: int, country_code: str, api_key: str) -> pd.DataFrame:
    params = {
        "get": ",".join(["SITC", "CTY_NAME", *VALUE_COLUMNS]),
        "YEAR": str(year),
        "MONTH": "12",
        "CTY_CODE": country_code,
        "SUMMARY_LVL": "DET",
        "SUMMARY_LVL2": "SICY",
        "key": api_key,
    }

    df = census_table(params)
    df = df[["SITC", "CTY_NAME", *VALUE_COLUMNS]].copy()
    df = df[df["SITC"].astype(str).str.len() == 5]

    country_name = str(df["CTY_NAME"].iloc[0]) if not df.empty else ""

    for column in VALUE_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df["sitc_section"] = df["SITC"].astype(str).str[0]
    grouped = (
        df.groupby("sitc_section", as_index=False)[VALUE_COLUMNS]
        .sum(min_count=1)
        .rename(
            columns={
                "GEN_VAL_YR": "general_imports_usd",
                "CON_VAL_YR": "imports_for_consumption_usd",
                "DUT_VAL_YR": "dutiable_value_usd",
                "CAL_DUT_YR": "calculated_duties_usd",
            }
        )
    )

    grouped["sitc_section_name"] = grouped["sitc_section"].map(SITC_SECTIONS)
    grouped.insert(0, "country_name", country_name)
    grouped.insert(0, "country_code", str(country_code).zfill(4))
    grouped.insert(0, "year", year)

    ordered_columns = [
        "year",
        "country_code",
        "country_name",
        "sitc_section",
        "sitc_section_name",
        "general_imports_usd",
        "imports_for_consumption_usd",
        "dutiable_value_usd",
        "calculated_duties_usd",
    ]
    return grouped[ordered_columns]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download one country's U.S. import data and aggregate it to SITC sections."
    )
    parser.add_argument("--years", nargs="+", type=int, default=[2024, 2025])
    parser.add_argument(
        "--country-code",
        default="3510",
        help="Census Schedule C country code. Default: 3510 (Brazil).",
    )
    parser.add_argument("--output", default="data/country_sitc.csv")
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
