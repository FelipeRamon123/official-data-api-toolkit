# Query Options

The six code examples cover the main implementation patterns. The U.S. Census International Trade API supports many more dimensions and classifications, and most variations reuse these patterns.

## Main dimensions and classifications

| Analytical need | Dataset / variable | Typical use |
|---|---|---|
| Detailed import product | `imports/hs` + `I_COMMODITY` | HTSUS product analysis |
| Country of origin | `CTY_CODE` / `CTY_NAME` | Supplier-country comparison |
| Customs district of entry | `DISTRICT` / `DIST_NAME` | Entry geography |
| Port of entry | `imports/porths` + `PORT` | Port and logistics analysis |
| State of destination | `imports/statehs` + `STATE` | U.S. subnational destination analysis |
| SITC | `imports/sitc` + `SITC` | Internationally comparable commodity grouping |
| NAICS | `imports/naics` + `NAICS` | Industry-oriented classification |
| End-Use | `imports/enduse` + `I_ENDUSE` | Macroeconomic use categories |
| Advanced Technology | `imports/hitech` + `HITECH` | Technology-oriented trade analysis |
| USDA Ag / Non-Ag | `imports/usda` + `USDA` | Agricultural versus non-agricultural split |
| Rate Provision | `imports/hs` + `RP` | Customs treatment analysis |
| Country Subcode | `imports/hs` + `CTY_SUBCODE` | Special country/program treatment |
| Export commodity | `exports/hs` + `E_COMMODITY` | U.S. exports by Schedule B / HS |
| Domestic vs. re-export | `exports/hs` + `DF` | Separate U.S.-origin exports from foreign-merchandise re-exports |

## Geographic variations

The main HS endpoint can combine HTS, country, customs district, Rate Provision and Country Subcode in valid `SUMMARY_LVL2` combinations.

Dedicated geographic endpoints include:

```text
imports/statehs
imports/porths
```

Port and state HS datasets are limited to HS2, HS4 and HS6. HTSUS10 is not available there.

### Why the repository uses one country in the port example

Although the API can represent HS × Port × Country, a request covering every country, every port and every HS6 code can become extremely large. Example 03 therefore uses a selected `CountryCode` and demonstrates the geographic pattern without encouraging an unnecessarily large extraction.

## Transportation and logistics fields

The port endpoint includes measures such as:

```text
AIR_VAL_YR
AIR_WGT_YR
VES_VAL_YR
VES_WGT_YR
CNT_VAL_YR
CNT_WGT_YR
```

They support analysis of air, vessel and containerized vessel trade values and shipping weights.

Other import endpoints can expose charges and CIF measures, including fields such as:

```text
GEN_CHA_YR
GEN_CIF_YR
CON_CHA_YR
CON_CIF_YR
```

## Quantities

The main HS endpoint also includes statistical quantity and unit fields such as:

```text
GEN_QY1_YR
GEN_QY2_YR
CON_QY1_YR
CON_QY2_YR
UNIT_QY1
UNIT_QY2
```

Quantity units differ by HTS code, so they should be interpreted together with the corresponding unit fields.

## Country groupings

The API supports predefined country groupings and geographic regions. Use the official Census definitions and codes when a grouped result is preferable to individual partner-country records.

## Example SUMMARY_LVL2 combinations

```text
HSCY       HTS × Country
HSDT       HTS × District
HSCYDT     HTS × Country × District
HSPT       HS × Port
HSPTCY     HS × Port × Country
HSCYRP     HTS × Country × Rate Provision
HSCYDF     Schedule B × Country × Domestic/Foreign export type
SICY       SITC × Country
SICYDT     SITC × Country × District
EUCY       End-Use × Country
HTCY       Hi-Tech × Country
```

The complete list is maintained in the official International Trade API User Guide:
https://www.census.gov/foreign-trade/reference/guides/Guide_to_International_Trade_Datasets.pdf

## How the examples generalize

The six scripts cover the main implementation patterns:

1. simple aggregation;
2. iterative large extraction;
3. alternate geographic endpoint;
4. alternate classification with post-processing;
5. advanced dimensional combination.
6. export-specific logic, including the `DF` domestic/re-export dimension.

Most other queries are variations of endpoint, requested fields, commodity level and a valid `SUMMARY_LVL2` combination rather than a fundamentally different extraction architecture.
