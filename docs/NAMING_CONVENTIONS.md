# Naming conventions

This repository distinguishes the international Harmonized System from U.S. national extensions.

| Context | English | Português |
|---|---|---|
| 2 digits | HS2 | SH2 |
| 4 digits | HS4 | SH4 |
| 6 digits | HS6 | SH6 |
| U.S. 10-digit statistical code | HTSUS10 | HTSUS10 |
| Brazil/Mercosur 8-digit code | NCM | NCM |

The Census API parameter is `COMM_LVL=HS10`, but the resulting 10-digit U.S. commodity code is described in this repository as **HTSUS10** to avoid confusing it with an international 10-digit HS level, which doesn't exist.

`Rate Provision` is kept in English because it is the Census field/dimension name used by the API.
