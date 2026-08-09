# API Guide

This note summarizes the API concepts used by the examples in this repository.

## Base pattern

U.S. imports endpoints follow this structure:

```text
https://api.census.gov/data/timeseries/intltrade/imports/{dataset}
```

Common datasets include:

- `hs`
- `porths`
- `statehs`
- `naics`
- `statenaics`
- `enduse`
- `sitc`
- `hitech`
- `usda`

Official overview:
https://www.census.gov/data/developers/data-sets/international-trade.html

## Time parameters

A request must specify either:

```text
time=YYYY-MM
```

or:

```text
YEAR=YYYY
MONTH=MM
```

This toolkit uses `YEAR` and `MONTH` because they are easier to parameterize in Power Query and Python.

## Year-to-date fields

Fields ending in `_YR` are year-to-date values. To obtain a complete calendar year, request December:

```text
YEAR=2024
MONTH=12
```

Examples:

```text
GEN_VAL_YR
CON_VAL_YR
DUT_VAL_YR
CAL_DUT_YR
```

For current-month values, use the `_MO` equivalents.

## Commodity level

For the import HS endpoint:

```text
COMM_LVL=HS2
COMM_LVL=HS4
COMM_LVL=HS6
COMM_LVL=HS10
```

HTSUS10 is available in the main `imports/hs` endpoint.

Port and state HS datasets are restricted to HS2, HS4 and HS6. The Census User Guide states that HS10 is not available in `porths` and `statehs` because of respondent confidentiality protection.

## SUMMARY_LVL

For individual countries, this toolkit uses:

```text
SUMMARY_LVL=DET
```

Country groupings use a different summary treatment. See the official guide for country grouping codes.

## SUMMARY_LVL2

`SUMMARY_LVL2` identifies the combination of dimensions being summarized.

Examples used here:

| Code | Meaning |
|---|---|
| `HS` | HTS commodity |
| `CY` | Country |
| `HSCY` | HTS × Country |
| `HSPTCY` | HS × Port × Country |
| `SICY` | SITC × Country |
| `HSCYRP` | HTS × Country × Rate Provision |
| `HSCYDF` | Schedule B × Country × Domestic/Foreign export type |

Other combinations exist, including district, state, country subcode and additional classifications. The official User Guide contains the complete list.

## Why the all-country HTS10 example loops by country

The Census User Guide warns that a single request for all countries and all HS commodities will almost always time out. It recommends breaking large extractions into smaller calls and recombining the results.

The `02_all_countries_by_htsus10` examples implement that pattern:

```text
1. Request the list of countries for the year
2. Request HTS10 records for one country
3. Repeat for every country
4. Append the results
```

## Why the port example uses one selected country

The `porths` endpoint supports HS × Port × Country combinations, but a world-scale Country × Port × HS6 extract can become very large. Example 03 is therefore country-specific. Change the `CountryCode` parameter (Power Query) or `--country-code` argument (Python) to analyze another partner.

## Imports versus exports at 10-digit detail

The import and export HS endpoints are parallel but not identical.

- Imports use `I_COMMODITY`; at 10 digits this is the U.S. import HTSUS statistical detail.
- Exports use `E_COMMODITY`; at 10 digits U.S. export reporting uses Schedule B.
- Export values use fields such as `ALL_VAL_YR`.
- Export queries can use `DF` to distinguish domestic exports (`1`) from foreign merchandise / re-exports (`2`).

Example 06 uses `SUMMARY_LVL2 = HSCYDF`, combining export commodity, destination country and Domestic/Foreign status.

## API key

All Census Data API queries currently require an API key.

Request a key at:
https://api.census.gov/data/key_signup.html

Do not commit a real key to GitHub.

## Query Builder

The Census also provides an International Trade API Query Builder, useful for checking valid combinations before coding them.

The Query Builder is linked from the official International Trade API page:
https://www.census.gov/data/developers/data-sets/international-trade.html
