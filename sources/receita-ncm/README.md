# Brazilian Federal Revenue — Portuguese NCM nomenclature

[English](README.md) | [Português](README.pt-BR.md) | [Back to toolkit](../../README.md)

Reusable connector for the public **Sistema Classif** JSON. It extracts the official Portuguese labels at the internationally shared HS2, HS4 and HS6 levels.

| Environment | File | Output |
|---|---|---|
| Python | [`python/01_download_ncm_hierarchy.py`](python/01_download_ncm_hierarchy.py) | JSON dictionaries for HS2, HS4 and HS6 |
| Power Query | [`power-query/01_ncm_hierarchy.m`](power-query/01_ncm_hierarchy.m) | `level × code × description` table |

Official source: `https://portalunico.siscomex.gov.br/classif/api/publico/nomenclatura/download/json`.

NCM8 and HTSUS10 share the international nomenclature only through HS6. U.S.-specific HTS8/HTSUS10 detail should therefore keep its official U.S. description; the Portuguese HS6 parent may be shown as context, but is not an official translation of the U.S. statistical suffix.
