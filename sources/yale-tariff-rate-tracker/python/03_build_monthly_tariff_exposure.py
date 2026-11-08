from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

COMPONENTS = [
    "rate_232", "rate_301", "rate_s301br", "rate_s301fl", "rate_ieepa_recip",
    "rate_ieepa_fent", "rate_s122", "rate_section_201", "rate_other",
]
MONTHLY_REFERENCE_DAY = 15
STATUTORY_232_RATES = {0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 1.00}
STATUTORY_122_RATES = {0.10}
DIRECT_AIRCRAFT_PREFIXES = ("8801", "8802", "8805", "8806")


def is_one_of(value: float, allowed: set[float], tolerance: float = 1e-8) -> bool:
    return any(abs(float(value) - item) <= tolerance for item in allowed)


def apply_discrete_treatment(frame: pd.DataFrame) -> pd.DataFrame:
    """Remove Yale applicability-share assumptions from the primary rate."""
    out = frame.copy()
    for column in COMPONENTS:
        out[column] = pd.to_numeric(out[column], errors="coerce").astype(float)
    description_column = next((name for name in ["description_en", "hts10_description", "I_COMMODITY_LDESC"] if name in out), None)
    descriptions = out[description_column].fillna("").str.upper() if description_column else pd.Series("", index=out.index)
    prefixes = out["htsus10"].astype(str).str[:4]
    military_only = descriptions.str.contains("MILITARY", regex=False) & ~descriptions.str.contains("NON-MILITARY", regex=False)
    direct_aircraft = prefixes.isin(DIRECT_AIRCRAFT_PREFIXES) & ~military_only
    raw_components = {column: pd.to_numeric(out[column], errors="coerce").fillna(0).copy() for column in COMPONENTS}
    br = raw_components["rate_s301br"]
    fl = pd.to_numeric(out["rate_s301fl"], errors="coerce").fillna(0)
    use_conditioned = br.map(lambda value: is_one_of(value, {0.025, 0.125})) | fl.map(
        lambda value: is_one_of(value, {0.0125, 0.0625})
    )
    aircraft_exception = use_conditioned & direct_aircraft
    default_full = use_conditioned & ~direct_aircraft
    out.loc[aircraft_exception, ["rate_s301br", "rate_s301fl"]] = 0.0
    out.loc[default_full & (br > 0), "rate_s301br"] = 0.25
    out.loc[default_full & (fl > 0), "rate_s301fl"] = 0.125

    rate232 = pd.to_numeric(out["rate_232"], errors="coerce").fillna(0)
    rate122 = pd.to_numeric(out["rate_s122"], errors="coerce").fillna(0)
    modeled_232_content = (rate232 > 0) & ~rate232.map(lambda value: is_one_of(value, STATUTORY_232_RATES))
    modeled_122_scope = (rate122 > 0) & ~rate122.map(lambda value: is_one_of(value, STATUTORY_122_RATES))
    conditional_scope = modeled_232_content | modeled_122_scope
    reference_dates = pd.to_datetime(out["rate_reference_date"], errors="coerce")
    cap_232 = pd.Series(0.0, index=out.index)
    cap_232.loc[modeled_232_content & (reference_dates < pd.Timestamp("2025-06-04"))] = 0.25
    cap_232.loc[modeled_232_content & (reference_dates >= pd.Timestamp("2025-06-04"))] = 0.50
    cap_122 = pd.Series(0.0, index=out.index)
    cap_122.loc[modeled_122_scope] = 0.10
    potential_cap = pd.concat([cap_232, cap_122], axis=1).max(axis=1)
    out.loc[modeled_232_content, "rate_232"] = cap_232.loc[modeled_232_content]
    out.loc[modeled_122_scope, "rate_s122"] = cap_122.loc[modeled_122_scope]
    out["additional_rate_effective"] = pd.to_numeric(out["yale_modeled_rate_reference"], errors="coerce")
    out.loc[aircraft_exception, "additional_rate_effective"] = (
        out.loc[aircraft_exception, "additional_rate_effective"] - br.loc[aircraft_exception] - fl.loc[aircraft_exception]
    ).clip(lower=0)
    out.loc[default_full, "additional_rate_effective"] = (
        out.loc[default_full, "additional_rate_effective"] - br.loc[default_full] - fl.loc[default_full]
        + out.loc[default_full, "rate_s301br"] + out.loc[default_full, "rate_s301fl"]
    )
    out.loc[conditional_scope, "additional_rate_effective"] = pd.concat([
        pd.to_numeric(out.loc[conditional_scope, "additional_rate_effective"], errors="coerce"),
        potential_cap.loc[conditional_scope],
    ], axis=1).max(axis=1)
    out["additional_rate_effective"] = pd.to_numeric(out["additional_rate_effective"], errors="coerce").mask(
        pd.to_numeric(out["additional_rate_effective"], errors="coerce").abs() < 1e-9, 0.0
    )
    unmatched = pd.to_numeric(out["yale_modeled_rate_reference"], errors="coerce").isna()
    out.loc[unmatched, "additional_rate_effective"] = pd.NA
    out["tariff_rate_qualifier"] = "exact"
    out.loc[conditional_scope, "tariff_rate_qualifier"] = "up_to"
    out["tariff_treatment_status"] = "classified"
    out["tariff_treatment_note"] = ""
    out.loc[aircraft_exception, "tariff_treatment_status"] = "conditional_exemption"
    out.loc[aircraft_exception, "tariff_treatment_note"] = "Civil-aircraft exemption assumed; General Note 6 and entry evidence are required."
    out.loc[default_full, "tariff_treatment_status"] = "conditional_default_full"
    out.loc[default_full, "tariff_treatment_note"] = "Full headline rate used by default; a qualifying aircraft or pharmaceutical use may be exempt."
    out.loc[conditional_scope, "tariff_treatment_status"] = "conditional_scope"
    out.loc[modeled_232_content, "tariff_treatment_note"] = "Potential surcharge up to 50%; actual incidence depends on covered metal content declared at entry."
    out.loc[modeled_232_content & (reference_dates < pd.Timestamp("2025-06-04")), "tariff_treatment_note"] = "Potential surcharge up to 25%; actual incidence depends on covered metal content declared at entry."
    out.loc[modeled_122_scope & ~modeled_232_content, "tariff_treatment_note"] = "Potential surcharge up to 10%; actual incidence depends on eligible use or scope declared at entry."
    out.loc[unmatched, "tariff_treatment_status"] = "unmatched"
    out.loc[unmatched, "tariff_rate_qualifier"] = "unmatched"
    return out


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
        auxiliary["yale_modeled_rate_day_weighted"] = auxiliary["weighted_total_additional"].div(auxiliary["days"]).fillna(0)
        auxiliary = auxiliary[["hts10", "yale_modeled_rate_day_weighted"]]
        snapshot = rates[(rates.valid_from <= reference) & (rates.valid_until >= reference)].sort_values(["hts10", "valid_from"]).drop_duplicates("hts10", keep="last")
        snapshot = snapshot[["hts10", "total_additional", "valid_from", *COMPONENTS]].rename(columns={
            "total_additional": "yale_modeled_rate_reference", "valid_from": "rate_valid_from",
        })
        snapshot["rate_reference_date"] = reference
        eom = active[(active.valid_from <= end) & (active.valid_until >= end)].sort_values(["hts10", "valid_from"]).drop_duplicates("hts10", keep="last")
        eom = eom[["hts10", "total_additional"]].rename(columns={"total_additional": "yale_modeled_rate_eom"})
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
    result = apply_discrete_treatment(result)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    result.sort_values(["period", "htsus10"]).to_csv(output, index=False, compression="gzip" if output.suffix == ".gz" else None)
    matched = result["yale_modeled_rate_reference"].notna().mean()
    print(f"Saved {len(result):,} rows to {output}; HTSUS10 row coverage: {matched:.1%}")


if __name__ == "__main__":
    main()
