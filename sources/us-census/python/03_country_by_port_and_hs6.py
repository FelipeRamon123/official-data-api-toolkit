from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd
import requests

BASE_URL = "https://api.census.gov/data/timeseries/intltrade/imports/porths"
VALUE_COLUMNS = ["GEN_VAL_YR", "AIR_VAL_YR", "VES_VAL_YR", "CNT_VAL_YR"]


def census_table(params: dict[str, str]) -> pd.DataFrame:
    response = requests.get(BASE_URL, params=params, timeout=180)
    response.raise_for_status()
    payload = response.json()
    return pd.DataFrame(payload[1:], columns=payload[0])


def query_year(year: int, api_key: str, country_code: str) -> pd.DataFrame:
    params = {
        # CTY_CODE is not repeated in `get` because it is already used
        # as a predicate below.
        "get": ",".join(
            [
                "I_COMMODITY",
                "I_COMMODITY_LDESC",
                "PORT",
                "PORT_NAME",
                "CTY_NAME",
                "GEN_VAL_YR",
                "AIR_VAL_YR",
                "VES_VAL_YR",
                "CNT_VAL_YR",
            ]
        ),
        "YEAR": str(year),
        "MONTH": "12",
        "CTY_CODE": str(country_code),
        "COMM_LVL": "HS6",
        "SUMMARY_LVL": "DET",
        "SUMMARY_LVL2": "HSPTCY",
        "key": api_key,
    }

    df = census_table(params)
    df = df[
        [
            "CTY_CODE",
            "CTY_NAME",
            "PORT",
            "PORT_NAME",
            "I_COMMODITY",
            "I_COMMODITY_LDESC",
            *VALUE_COLUMNS,
        ]
    ].copy()

    df = df[df["I_COMMODITY"].astype(str).str.len() == 6]

    df["CTY_CODE"] = df["CTY_CODE"].astype(str).str.zfill(4)
    df["PORT"] = df["PORT"].astype(str).str.zfill(4)
    df["I_COMMODITY"] = df["I_COMMODITY"].astype(str).str.zfill(6)

    for column in VALUE_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce").astype("Int64")

    df = df.rename(
        columns={
            "CTY_CODE": "country_code",
            "CTY_NAME": "country_name",
            "PORT": "port_code",
            "PORT_NAME": "port_name",
            "I_COMMODITY": "hs6",
            "I_COMMODITY_LDESC": "hs_description",
            "GEN_VAL_YR": "general_imports_usd",
            "AIR_VAL_YR": "air_value_usd",
            "VES_VAL_YR": "vessel_value_usd",
            "CNT_VAL_YR": "containerized_vessel_value_usd",
        }
    )

    df.insert(0, "year", year)
    return df


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Download U.S. imports by port and HS6 for one selected country. "
            "Brazil (3510) is the default example."
        )
    )
    parser.add_argument("--years", nargs="+", type=int, default=[2024, 2025])
    parser.add_argument(
        "--country-code",
        default="3510",
        help="Census Schedule C country code. Default: 3510 (Brazil).",
    )
    parser.add_argument("--output", default="data/country_port_hs6.csv")
    args = parser.parse_args()

    api_key = os.environ.get("CENSUS_API_KEY")
    if not api_key:
        raise SystemExit("Set the CENSUS_API_KEY environment variable first.")

    result = pd.concat(
        [
            query_year(
                year=year,
                api_key=api_key,
                country_code=args.country_code,
            )
            for year in args.years
        ],
        ignore_index=True,
    )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output, index=False)
    print(f"Saved {len(result):,} rows to {output}")


if __name__ == "__main__":
    main()
