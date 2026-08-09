from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd
import requests

BASE_URL = "https://api.census.gov/data/timeseries/intltrade/exports/hs"


def census_table(params: dict[str, str]) -> pd.DataFrame:
    response = requests.get(BASE_URL, params=params, timeout=180)
    response.raise_for_status()
    payload = response.json()
    return pd.DataFrame(payload[1:], columns=payload[0])


def query_year(year: int, country_code: str, api_key: str) -> pd.DataFrame:
    params = {
        "get": ",".join(
            [
                "E_COMMODITY",
                "E_COMMODITY_LDESC",
                "DF",
                "CTY_NAME",
                "ALL_VAL_YR",
            ]
        ),
        "YEAR": str(year),
        "MONTH": "12",
        "CTY_CODE": str(country_code),
        "COMM_LVL": "HS10",
        "SUMMARY_LVL": "DET",
        "SUMMARY_LVL2": "HSCYDF",
        "key": api_key,
    }

    df = census_table(params)
    df = df[
        [
            "E_COMMODITY",
            "E_COMMODITY_LDESC",
            "DF",
            "CTY_NAME",
            "ALL_VAL_YR",
        ]
    ].copy()

    df = df[df["E_COMMODITY"].astype(str).str.len() == 10]
    df["E_COMMODITY"] = df["E_COMMODITY"].astype(str).str.zfill(10)
    df["DF"] = df["DF"].astype(str)
    df["ALL_VAL_YR"] = pd.to_numeric(df["ALL_VAL_YR"], errors="coerce").astype("Int64")

    df["export_type"] = df["DF"].map(
        {
            "1": "Domestic",
            "2": "Foreign (re-export)",
        }
    ).fillna("Other")

    df = df.rename(
        columns={
            "E_COMMODITY": "schedule_b10",
            "E_COMMODITY_LDESC": "schedule_b_description",
            "DF": "export_type_code",
            "CTY_NAME": "country_name",
            "ALL_VAL_YR": "export_value_usd",
        }
    )

    df.insert(0, "country_code", str(country_code).zfill(4))
    df.insert(0, "year", year)

    return df[
        [
            "year",
            "country_code",
            "country_name",
            "schedule_b10",
            "schedule_b_description",
            "export_type_code",
            "export_type",
            "export_value_usd",
        ]
    ]


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Download U.S. exports to one selected destination country by "
            "10-digit Schedule B code, separating domestic exports and re-exports."
        )
    )
    parser.add_argument("--years", nargs="+", type=int, default=[2024, 2025])
    parser.add_argument(
        "--country-code",
        default="3510",
        help="Census Schedule C destination-country code. Default: 3510 (Brazil).",
    )
    parser.add_argument(
        "--output",
        default="data/exports_to_country_by_schedule_b10.csv",
    )
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
