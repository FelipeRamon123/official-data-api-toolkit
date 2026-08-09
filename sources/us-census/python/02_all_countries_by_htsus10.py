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


def get_countries(year: int, api_key: str) -> pd.DataFrame:
    params = {
        "get": "CTY_CODE,CTY_NAME,GEN_VAL_YR",
        "YEAR": str(year),
        "MONTH": "12",
        "SUMMARY_LVL": "DET",
        "SUMMARY_LVL2": "CY",
        "key": api_key,
    }
    df = census_table(params)
    df["GEN_VAL_YR"] = pd.to_numeric(df["GEN_VAL_YR"], errors="coerce")
    df = df[
        df["CTY_CODE"].notna()
        & (df["CTY_CODE"].astype(str) != "")
        & (df["CTY_CODE"].astype(str) != "-")
        & df["CTY_NAME"].notna()
        & (df["GEN_VAL_YR"] > 0)
    ]
    return df[["CTY_CODE", "CTY_NAME"]].drop_duplicates("CTY_CODE")


def query_country(
    year: int,
    country_code: str,
    country_name: str,
    api_key: str,
) -> pd.DataFrame:
    params = {
        "get": ",".join(
            [
                "I_COMMODITY",
                "GEN_VAL_YR",
                "CON_VAL_YR",
                "DUT_VAL_YR",
                "CAL_DUT_YR",
            ]
        ),
        "YEAR": str(year),
        "MONTH": "12",
        "CTY_CODE": country_code,
        "COMM_LVL": "HS10",
        "SUMMARY_LVL": "DET",
        "SUMMARY_LVL2": "HSCY",
        "key": api_key,
    }

    df = census_table(params)
    df = df[["I_COMMODITY", *VALUE_COLUMNS]].copy()
    df = df[df["I_COMMODITY"].astype(str).str.len() == 10]
    df["I_COMMODITY"] = df["I_COMMODITY"].astype(str).str.zfill(10)

    for column in VALUE_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce").astype("Int64")

    df = df.rename(
        columns={
            "I_COMMODITY": "htsus10",
            "GEN_VAL_YR": "general_imports_usd",
            "CON_VAL_YR": "imports_for_consumption_usd",
            "DUT_VAL_YR": "dutiable_value_usd",
            "CAL_DUT_YR": "calculated_duties_usd",
        }
    )
    df.insert(0, "country_name", country_name)
    df.insert(0, "country_code", str(country_code).zfill(4))
    df.insert(0, "year", year)
    return df


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download annual U.S. imports for every country and HTS10 code."
    )
    parser.add_argument("--years", nargs="+", type=int, default=[2024, 2025])
    parser.add_argument("--output", default="data/country_htsus10.csv")
    args = parser.parse_args()

    api_key = os.environ.get("CENSUS_API_KEY")
    if not api_key:
        raise SystemExit("Set the CENSUS_API_KEY environment variable first.")

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()

    write_header = True
    total_rows = 0

    for year in args.years:
        countries = get_countries(year, api_key)
        for row in countries.itertuples(index=False):
            country_code = str(row.CTY_CODE)
            country_name = str(row.CTY_NAME)
            print(f"{year} | {country_code} | {country_name}")

            frame = query_country(year, country_code, country_name, api_key)
            frame.to_csv(
                output,
                mode="w" if write_header else "a",
                header=write_header,
                index=False,
            )
            write_header = False
            total_rows += len(frame)

    print(f"Saved {total_rows:,} rows to {output}")


if __name__ == "__main__":
    main()
