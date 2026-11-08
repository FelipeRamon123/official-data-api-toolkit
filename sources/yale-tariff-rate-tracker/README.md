# Yale Tariff Rate Tracker

[English](README.md) | [Português](README.pt-BR.md)

Reusable access module for The Budget Lab at Yale's [Tariff Rate Tracker](https://github.com/Budget-Lab-Yale/tariff-rate-tracker). The project models U.S. statutory tariffs at the **HTSUS10 × origin country × validity interval** level.

## What this module provides

- latest-release resolution through the GitHub API;
- auditable ZIP download with tag, date, URL and size metadata;
- extraction from the `actual` panel only, excluding counterfactual scenarios;
- country filtering before Parquet-to-pandas conversion;
- compact CSV.GZ output ready to join to monthly Census trade data;
- a Power Query example that retrieves release metadata without loading the large archive into Excel.

## Examples

| # | Example | Use |
|---|---|---|
| 01 | [Download latest release](python/01_download_latest_release.py) | Resolves and downloads the official ZIP; writes a JSON manifest |
| 02 | [Extract one country panel](python/02_extract_country_rates.py) | Filters `actual/snapshots` by Census country code and writes CSV.GZ |
| 03 | [Build monthly surcharge classification](python/03_build_monthly_tariff_exposure.py) | Joins Census example 07 to Yale, removes utilization-share assumptions and assigns content-dependent lines to the highest potential band |
| 01-M | [Release metadata in Power Query](power-query/01_latest_release_metadata.m) | Returns the official tag, date and asset URL |

## Quick start

```bash
python -m pip install -r requirements.txt
python sources/yale-tariff-rate-tracker/python/01_download_latest_release.py
python sources/yale-tariff-rate-tracker/python/02_extract_country_rates.py --country 3510
```

Country code `3510` identifies Brazil in the Census country classification used by the tracker.

## Joining to Census data

Census trade data are monthly; Yale rates are interval-based. The script snapshots day 15, preserves Yale's original output in `yale_modeled_*` audit fields, and builds a discrete primary classification. Identifiable civil aircraft are assigned 0% subject to General Note 6; other use-conditioned lines default to the full headline rate; content-dependent cases are assigned the highest potentially applicable statutory rate and marked with `tariff_rate_qualifier=up_to`. Measures beginning after day 15 enter the following month.

Primary references for the civil-aircraft exception: [Section 301 Brazil](https://public-inspection.federalregister.gov/2026-14542.pdf), [Section 301 forced labor](https://public-inspection.federalregister.gov/2026-15274.pdf), and [HTSUS General Note 6](https://hts.usitc.gov/).

## Limitations

- Yale models utilization and content shares for some programs; utilization probabilities are excluded from the primary output, while content-dependent lines use a clearly qualified potential maximum rather than the modeled share.
- Exception eligibility depends on entry documentation; HTSUS10 alone does not replace a CBP determination.
- Releases may include future intervals already encoded in the tracker schedule; always retain the release tag and publication date.
- The ZIP is large. Python/Parquet is the recommended extraction path; Power Query is intended for release discovery and processed extracts.

## Related showcase

[![Brazil × U.S. tariffs monitor](../../docs/assets/us-brazil-tariff-monitor.png)](https://feliperamon123.github.io/us-brazil-tariff-monitor/)

The [Brazil × U.S. tariffs dashboard](https://github.com/FelipeRamon123/us-brazil-tariff-monitor) applies this module to monthly imports from Brazil.
