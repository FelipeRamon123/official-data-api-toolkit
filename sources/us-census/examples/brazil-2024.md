# Example: Brazil, 2024

Brazil uses Census Schedule C country code `3510`.

This page shows how to configure the toolkit for a Brazil-focused analysis in 2024.

## Power Query M

For examples with a year list, use:

```powerquery
Years = {2024}
```

For the port example, set:

```powerquery
CountryCode = "3510"
```

The country-by-HTS10 example obtains the list of partner countries automatically and therefore does not require a single-country parameter.

## Python

Set the API key first:

```powershell
$env:CENSUS_API_KEY="YOUR_CENSUS_API_KEY"
```

### U.S. imports from all countries by HTSUS10

```bash
python sources/us-census/python/02_all_countries_by_htsus10.py \
  --years 2024 \
  --output data/all_countries_by_htsus10_2024.csv
```

### U.S. imports from Brazil by port and HS6

```bash
python sources/us-census/python/03_country_by_port_and_hs6.py \
  --years 2024 \
  --country-code 3510 \
  --output data/brazil_port_hs6_2024.csv
```

### Brazil sector profile using SITC sections

```bash
python sources/us-census/python/04_country_by_sitc_section.py \
  --years 2024 \
  --country-code 3510 \
  --output data/brazil_sitc_2024.csv
```

### Brazil by HTSUS10 and Rate Provision

```bash
python sources/us-census/python/05_country_by_htsus10_and_rate_provision.py \
  --years 2024 \
  --country-code 3510 \
  --output data/brazil_hts_rate_provision_2024.csv
```

### U.S. exports to Brazil by Schedule B10 and export type

```bash
python sources/us-census/python/06_exports_to_country_by_schedule_b10.py \
  --years 2024 \
  --country-code 3510 \
  --output data/us_exports_to_brazil_schedule_b10_2024.csv
```

The export example separates `DF = 1` domestic exports from `DF = 2` foreign exports (re-exports).

## Suggested validation

For annual extracts using `_YR` fields, compare aggregated values against an official Census total for the same year and trade definition. Keep general imports and imports for consumption separate because they measure different concepts.
