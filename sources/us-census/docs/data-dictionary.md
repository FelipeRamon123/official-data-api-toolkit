# Practical Data Dictionary

This dictionary focuses on the fields used by the examples in this repository.

| API field | Repository field | Practical meaning |
|---|---|---|
| `YEAR` | `year` | Reference year. In annual examples, December is requested and `_YR` fields represent the cumulative year-to-date value. |
| `I_COMMODITY` | `htsus10` / `hs6` | U.S. import Harmonized System / HTS commodity code. HTSUS10 is the most detailed level available in the main HS endpoint. |
| `I_COMMODITY_LDESC` | `hts_description` / `hs_description` | Long description of the HS/HTS commodity code. |
| `CTY_CODE` | `country_code` | Census trade country code. |
| `CTY_NAME` | `country_name` | Country name. |
| `GEN_VAL_YR` | `general_imports_usd` | Year-to-date general imports. Broad measure of merchandise entering U.S. territory. |
| `CON_VAL_YR` | `imports_for_consumption_usd` | Year-to-date imports for consumption. Merchandise entering U.S. consumption channels. |
| `DUT_VAL_YR` | `dutiable_value_usd` | Year-to-date portion of imports for consumption classified as dutiable. This is a value base, not the duty amount. |
| `CAL_DUT_YR` | `calculated_duties_usd` | Year-to-date calculated customs duties, in U.S. dollars. |
| `PORT` | `port_code` | Four-character port-of-entry code. The first two characters identify the district and the last two identify the port. |
| `PORT_NAME` | `port_name` | Port-of-entry name. |
| `AIR_VAL_YR` | `air_value_usd` | Year-to-date import value associated with air transportation. |
| `VES_VAL_YR` | `vessel_value_usd` | Year-to-date import value associated with vessel transportation. |
| `CNT_VAL_YR` | `containerized_vessel_value_usd` | Year-to-date value moved by containerized vessel. |
| `SITC` | `sitc_section` after aggregation | Five-character Standard International Trade Classification code in the API. The example groups the first digit into broad SITC sections. |
| `RP` | `rate_provision_code` | Two-character Rate Provision code indicating the free/dutiable or special customs provision under which merchandise entered. |

## Export fields used by example 06

| API field | Repository field | Practical meaning |
|---|---|---|
| `E_COMMODITY` | `schedule_b10` | Ten-digit U.S. export commodity code. Export reporting uses Schedule B rather than the import HTSUS statistical nomenclature. |
| `E_COMMODITY_LDESC` | `schedule_b_description` | Long description of the export commodity code. |
| `DF` | `export_type_code` | Domestic/Foreign indicator. `1` means domestic merchandise; `2` means foreign merchandise, commonly described as re-exports. |
| derived from `DF` | `export_type` | Friendly label created by the scripts. |
| `ALL_VAL_YR` | `export_value_usd` | Year-to-date export value in U.S. dollars. With `MONTH = 12`, this is the full-year value. |

## Common analytical ratios

### Observed effective duty on dutiable value

```text
calculated_duties_usd / dutiable_value_usd
```

Useful for describing the duty burden observed in the trade records, but it is not necessarily the legal nominal HTS tariff rate.

### Duty burden on all imports for consumption

```text
calculated_duties_usd / imports_for_consumption_usd
```

Shows calculated duties relative to the full value entering U.S. consumption channels.

### Dutiable share

```text
dutiable_value_usd / imports_for_consumption_usd
```

Shows the share of consumption imports classified as dutiable.

## Monthly equivalents

For monthly rather than year-to-date analysis, replace `_YR` fields with `_MO` fields, for example:

```text
GEN_VAL_YR -> GEN_VAL_MO
CON_VAL_YR -> CON_VAL_MO
DUT_VAL_YR -> DUT_VAL_MO
CAL_DUT_YR -> CAL_DUT_MO
```

## Interpretation caution

Calculated duty data and Rate Provision codes describe observed customs treatment in the trade statistics. They should not be used alone as a substitute for the legal HTS tariff schedule, Chapter 99 measures, exclusions, preferences or other applicable customs rules.

Official references:

- https://api.census.gov/data/timeseries/intltrade/imports/hs/variables.html
- https://api.census.gov/data/timeseries/intltrade/imports/porths/variables.html
- https://api.census.gov/data/timeseries/intltrade/imports/sitc/variables.html
- https://api.census.gov/data/timeseries/intltrade/exports/hs/variables.html
- https://www.census.gov/foreign-trade/reference/rpcodes.html
