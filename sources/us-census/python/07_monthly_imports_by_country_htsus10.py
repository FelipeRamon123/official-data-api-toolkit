from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd
import requests

BASE_URL = "https://api.census.gov/data/timeseries/intltrade/imports/hs"
FIELDS = [
    "I_COMMODITY", "I_COMMODITY_LDESC", "CTY_NAME", "GEN_VAL_MO", "CON_VAL_MO",
    "DUT_VAL_MO", "CAL_DUT_MO", "GEN_QY1_MO", "GEN_QY2_MO", "CON_QY1_MO",
    "CON_QY2_MO", "UNIT_QY1", "UNIT_QY2",
]


def months(start: str, end: str):
    current, final = pd.Period(start, "M"), pd.Period(end, "M")
    while current <= final:
        yield current
        current += 1


def query_month(period: pd.Period, api_key: str, country_code: str) -> pd.DataFrame:
    params = {
        "get": ",".join(FIELDS), "YEAR": str(period.year), "MONTH": f"{period.month:02d}",
        "CTY_CODE": str(country_code).zfill(4), "COMM_LVL": "HS10", "SUMMARY_LVL": "DET",
        "SUMMARY_LVL2": "HSCY", "key": api_key,
    }
    response = requests.get(BASE_URL, params=params, timeout=240)
    response.raise_for_status()
    payload = response.json()
    frame = pd.DataFrame(payload[1:], columns=payload[0])
    frame = frame[frame["I_COMMODITY"].astype(str).str.fullmatch(r"\d{10}")].copy()
    frame.insert(0, "period", str(period))
    frame.insert(1, "country_code", str(country_code).zfill(4))
    renames = {
        "I_COMMODITY": "htsus10", "I_COMMODITY_LDESC": "description_en", "CTY_NAME": "country_name",
        "GEN_VAL_MO": "general_value_usd", "CON_VAL_MO": "consumption_value_usd",
        "DUT_VAL_MO": "dutiable_value_usd", "CAL_DUT_MO": "calculated_duties_usd",
        "GEN_QY1_MO": "general_qty1", "GEN_QY2_MO": "general_qty2",
        "CON_QY1_MO": "consumption_qty1", "CON_QY2_MO": "consumption_qty2",
        "UNIT_QY1": "unit_qty1", "UNIT_QY2": "unit_qty2",
    }
    frame = frame.rename(columns=renames)
    frame["htsus10"] = frame["htsus10"].astype(str).str.zfill(10)
    for column in [name for name in frame if name.endswith("_usd") or "qty" in name and not name.startswith("unit_")]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(0).astype("Int64")
    return frame


def main() -> None:
    parser = argparse.ArgumentParser(description="Download monthly U.S. imports from one country at HTSUS10 level.")
    parser.add_argument("--start", default="2025-01")
    parser.add_argument("--end", default=str(pd.Period(pd.Timestamp.today(), freq="M") - 1))
    parser.add_argument("--country-code", default="3510", help="Census Schedule C code; 3510 = Brazil")
    parser.add_argument("--output", default="data/monthly_imports_country_htsus10.csv.gz")
    args = parser.parse_args()
    api_key = os.environ.get("CENSUS_API_KEY")
    if not api_key:
        raise SystemExit("Set the CENSUS_API_KEY environment variable first.")
    result = pd.concat([query_month(period, api_key, args.country_code) for period in months(args.start, args.end)], ignore_index=True)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    result.sort_values(["period", "htsus10"]).to_csv(output, index=False, compression="gzip" if output.suffix == ".gz" else None)
    print(f"Saved {len(result):,} rows from {args.start} through {args.end} to {output}")


if __name__ == "__main__":
    main()
