from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

COMPONENTS = [
    "rate_232", "rate_301", "rate_s301br", "rate_s301fl", "rate_ieepa_recip",
    "rate_ieepa_fent", "rate_s122", "rate_section_201", "rate_other",
]
MONTHLY_REFERENCE_DAY = 15


def normalize_census(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype={"htsus10": str, "hts10": str, "country_code": str})
    frame = frame.rename(columns={"hts10": "htsus10", "CON_VAL_MO": "consumption_value_usd"})
    required = {"period", "htsus10", "consumption_value_usd"}
    if missing := required - set(frame.columns):
        raise ValueError(f"Census file is missing columns: {sorted(missing)}")
    frame["htsus10"] = frame["htsus10"].astype(str).str.zfill(10)
    frame["consumption_value_usd"] = pd.to_numeric(frame["consumption_value_usd"], errors="coerce").fillna(0)
    return frame


def monthly_rates(rates: pd.DataFrame, periods: list[str]) -> pd.DataFrame:
    rates["hts10"] = rates["hts10"].astype(str).str.zfill(10)
    rates["valid_from"] = pd.to_datetime(rates["valid_from"], errors="raise")
    rates["valid_until"] = pd.to_datetime(rates["valid_until"], errors="coerce").fillna(pd.Timestamp("2099-12-31"))
    for column in ["total_additional", *COMPONENTS]:
        if column not in rates:
            rates[column] = 0
        rates[column] = pd.to_numeric(rates[column], errors="coerce").fillna(0)
    rates = rates.sort_values(["hts10", "valid_from", "valid_until"]).reset_index(drop=True)
    out = []
    for period in periods:
        start, end = pd.Period(period, "M").start_time.normalize(), pd.Period(period, "M").end_time.normalize()
        reference = start + pd.Timedelta(days=MONTHLY_REFERENCE_DAY - 1)
        active = rates[(rates.valid_from <= end) & (rates.valid_until >= start)].copy()
        active["days_in_force"] = ((active.valid_until.clip(upper=end) - active.valid_from.clip(lower=start)).dt.days + 1).clip(lower=0)
        active["weighted_total_additional"] = active["total_additional"] * active["days_in_force"]
        auxiliary = active.groupby("hts10", as_index=False).agg(
            days=("days_in_force", "sum"),
            weighted_total_additional=("weighted_total_additional", "sum"),
        )
        auxiliary["additional_rate_day_weighted"] = auxiliary["weighted_total_additional"].div(auxiliary["days"]).fillna(0)
        auxiliary = auxiliary[["hts10", "additional_rate_day_weighted"]]
        snapshot = rates[(rates.valid_from <= reference) & (rates.valid_until >= reference)].sort_values(["hts10", "valid_from"]).drop_duplicates("hts10", keep="last")
        snapshot = snapshot[["hts10", "total_additional", "valid_from", *COMPONENTS]].rename(columns={
            "total_additional": "additional_rate_effective", "valid_from": "rate_valid_from",
        })
        snapshot["rate_reference_date"] = reference
        eom = active[(active.valid_from <= end) & (active.valid_until >= end)].sort_values(["hts10", "valid_from"]).drop_duplicates("hts10", keep="last")
        eom = eom[["hts10", "total_additional"]].rename(columns={"total_additional": "additional_rate_eom"})
        monthly = snapshot.merge(auxiliary, on="hts10", how="outer").merge(eom, on="hts10", how="outer")
        monthly.insert(0, "period", period)
        out.append(monthly)
    return pd.concat(out, ignore_index=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Join monthly Census imports to Yale statutory surcharges using a day-15 monthly reference.")
    parser.add_argument("--census", required=True, help="CSV/CSV.GZ from Census example 07")
    parser.add_argument("--yale", required=True, help="Country-rate CSV.GZ from Yale example 02")
    parser.add_argument("--output", default="data/monthly_tariff_exposure.csv.gz")
    args = parser.parse_args()
    census = normalize_census(Path(args.census))
    rates = pd.read_csv(args.yale, dtype={"hts10": str, "country": str})
    lookup = monthly_rates(rates, sorted(census["period"].astype(str).unique()))
    result = census.merge(lookup, left_on=["period", "htsus10"], right_on=["period", "hts10"], how="left").drop(columns=["hts10"])
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    result.sort_values(["period", "htsus10"]).to_csv(output, index=False, compression="gzip" if output.suffix == ".gz" else None)
    matched = result["additional_rate_effective"].notna().mean()
    print(f"Saved {len(result):,} rows to {output}; HTSUS10 row coverage: {matched:.1%}")


if __name__ == "__main__":
    main()
