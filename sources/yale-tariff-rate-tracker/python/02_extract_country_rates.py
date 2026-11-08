from __future__ import annotations

import argparse
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pandas as pd
import pyarrow.parquet as pq

KEEP_COLUMNS = [
    "hts10", "country", "base_rate", "total_additional", "total_rate",
    "rate_232", "rate_301", "rate_s301br", "rate_s301fl",
    "rate_ieepa_recip", "rate_ieepa_fent", "rate_s122",
    "rate_section_201", "rate_other", "revision", "valid_from", "valid_until",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract one country from Yale actual-rate snapshots.")
    parser.add_argument("--country", default="3510", help="Census country code, for example 3510 for Brazil")
    parser.add_argument("--archive", default="data/yale-tariff-rate-tracker/latest-release.zip")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    country = str(args.country).zfill(4)
    output = Path(args.output or f"data/yale-tariff-rate-tracker/country_{country}_rates.csv.gz")
    frames: list[pd.DataFrame] = []

    with ZipFile(args.archive) as archive:
        members = sorted(
            name for name in archive.namelist()
            if "/actual/snapshots/valid_from=" in name and name.endswith("/rates.parquet")
        )
        if not members:
            raise SystemExit("No actual/snapshots/valid_from=*/rates.parquet members found.")
        for member in members:
            table = pq.read_table(
                BytesIO(archive.read(member)),
                columns=KEEP_COLUMNS,
                filters=[("country", "=", country)],
            )
            frame = table.to_pandas()
            if not frame.empty:
                frames.append(frame)

    if not frames:
        raise SystemExit(f"No rows found for country {country}.")
    result = pd.concat(frames, ignore_index=True)
    result["hts10"] = result["hts10"].astype(str).str.zfill(10)
    result = result.drop_duplicates(["hts10", "country", "valid_from", "valid_until"], keep="last")
    result = result.sort_values(["valid_from", "hts10"])
    output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output, index=False, compression="gzip")
    print(f"Saved {len(result):,} rows across {result['valid_from'].nunique()} intervals to {output}")


if __name__ == "__main__":
    main()
