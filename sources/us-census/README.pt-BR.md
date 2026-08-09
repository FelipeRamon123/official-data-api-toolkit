# U.S. Census International Trade API

[English](README.md) | [Português](README.pt-BR.md) | [Voltar ao toolkit](../../README.pt-BR.md)

Exemplos reutilizáveis em Power Query M e Python para a **International Trade API do U.S. Census Bureau**.

A proposta é chegar rápido a uma consulta que funcione e depois adaptar para o produto, país, porto ou classificação que você precisa.

[![Abrir no Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/FelipeRamon123/official-data-api-toolkit/blob/main/notebooks/us-census-quickstart-colab.ipynb)

Execute o início rápido em Python diretamente no Google Colab, usando este repositório sem precisar editar a URL do GitHub.

## Showcase ao vivo

[![Navegue pela U.S. Census Imports API Showcase](https://raw.githubusercontent.com/FelipeRamon123/united-states-census-imports-api-showcase/main/assets/portfolio/dashboard-scroll.gif)](https://feliperamon123.github.io/united-states-census-imports-api-showcase/)

A **U.S. Census Imports API Showcase** transforma o dataset gerado pelo exemplo 02 em uma aplicação interativa e bilíngue cobrindo 2024 e 2025.

**[Abrir o dashboard ao vivo →](https://feliperamon123.github.io/united-states-census-imports-api-showcase/)** · [Ver o repositório da showcase](https://github.com/FelipeRamon123/united-states-census-imports-api-showcase) · [Baixar o dataset completo](https://github.com/FelipeRamon123/united-states-census-imports-api-showcase/releases/latest/download/us-imports-htsus10-country-2024-2025.csv.gz)

## O que está incluído

| # | Exemplo | Granularidade | Serve para |
|---|---|---|---|
| 01 | [Mundo por HTSUS10](power-query/01_world_by_htsus10.m) | Ano × HTSUS10 | Importações dos EUA por produto detalhado, com todas as origens agregadas |
| 02 | [Todos os países por HTSUS10](power-query/02_all_countries_by_htsus10.m) | Ano × País × HTSUS10 | Ranking de fornecedores e bases grandes |
| 03 | [Um país por porto e SH6](power-query/03_country_by_port_and_hs6.m) | Ano × País × Porto × SH6 | Porto de entrada e transporte |
| 04 | [Um país por seção SITC](power-query/04_country_by_sitc_section.m) | Ano × País × seção SITC | Visão setorial ampla |
| 05 | [Um país por HTSUS10 e Rate Provision](power-query/05_country_by_htsus10_and_rate_provision.m) | Ano × País × HTSUS10 × RP | Tratamento aduaneiro observado |
| 06 | [Exportações para um país por Schedule B10](power-query/06_exports_to_country_by_schedule_b10.m) | Ano × País de destino × Schedule B10 × tipo de exportação | Mercado de destino e separação entre exportações domésticas e reexportações |

Cada exemplo também tem uma versão em Python na pasta [`python/`](python/).

## Código por trás da showcase

A showcase pública usa o exemplo **02**, porque o dashboard precisa do detalhe de país fornecedor para cada HTSUS10.

- Power Query: [`02_all_countries_by_htsus10.m`](power-query/02_all_countries_by_htsus10.m)
- Python: [`02_all_countries_by_htsus10.py`](python/02_all_countries_by_htsus10.py)

## Início rápido: Power Query

1. Abra Excel ou Power BI.
2. Crie uma consulta em branco.
3. Abra o **Editor Avançado**.
4. Cole um dos arquivos de `power-query/`.
5. Substitua `YOUR_CENSUS_API_KEY`.

A maioria dos exemplos aceita vários anos:

```powerquery
Years = {2024, 2025}
```

ou:

```powerquery
Years = {2020..2025}
```

## Início rápido: Python

A partir da raiz do repositório:

```bash
python -m pip install -r requirements.txt
```

Defina a chave do Census:

```powershell
$env:CENSUS_API_KEY="YOUR_CENSUS_API_KEY"
```

No macOS/Linux:

```bash
export CENSUS_API_KEY="YOUR_CENSUS_API_KEY"
```

Depois execute, por exemplo:

```bash
python sources/us-census/python/02_all_countries_by_htsus10.py --years 2024 2025
```

Brasil por porto e SH6:

```bash
python sources/us-census/python/03_country_by_port_and_hs6.py \
  --years 2024 2025 \
  --country-code 3510 \
  --output data/brazil_port_hs6.csv
```

Exportações dos EUA para o Brasil por Schedule B10 e tipo de exportação:

```bash
python sources/us-census/python/06_exports_to_country_by_schedule_b10.py \
  --years 2024 2025 \
  --country-code 3510 \
  --output data/us_exports_to_brazil_schedule_b10.csv
```

## Dá para consultar outras coisas?

Sim. Os seis scripts mostram padrões de consulta, não tudo o que existe na API.

Também é possível trabalhar com dimensões como:

- distrito aduaneiro;
- estado de destino nos EUA;
- NAICS;
- End-Use;
- Advanced Technology;
- classificações USDA;
- country subcodes;
- medidas de transporte;
- quantidades e unidades.

Veja [`docs/query-options.md`](docs/query-options.md).

## Alguns conceitos importantes

### Dados anuais

Os exemplos usam `MONTH = 12` com campos terminados em `_YR`.

Ex.:

```text
GEN_VAL_YR
CON_VAL_YR
DUT_VAL_YR
CAL_DUT_YR
```

Eles são valores acumulados no ano. Em dezembro, representam o ano-calendário completo.

### Importações gerais x importações para consumo

Não são a mesma medida.

Uma mercadoria pode chegar aos EUA e entrar nas importações gerais antes de ser retirada de um armazém alfandegado ou Foreign Trade Zone para consumo.

Veja as explicações práticas em [`docs/data-dictionary.md`](docs/data-dictionary.md).

### HTSUS10 x SH6

O endpoint principal `imports/hs` aceita `COMM_LVL=HS10`. Neste toolkit, chamamos o código americano de 10 dígitos de **HTSUS10**.

Os endpoints por porto e por estado ficam limitados a SH2, SH4 e SH6.

### HTSUS10 x Schedule B10

As importações dos EUA usam códigos estatísticos HTSUS no nível de 10 dígitos. As exportações usam códigos Schedule B. Ambos compartilham a base internacional do Sistema Harmonizado até seis dígitos, mas suas extensões de 10 dígitos não são intercambiáveis.

O exemplo 06 usa `E_COMMODITY`, `ALL_VAL_YR` e `DF`. O campo `DF` separa exportações domésticas (`1`) de mercadorias estrangeiras exportadas pelos EUA (`2`), normalmente chamadas de reexportações.

### Consultas grandes

Tentar puxar todos os países e todos os produtos detalhados em uma única chamada pode gerar timeout.

O exemplo 02 usa um padrão mais seguro:

```text
obter a lista de países
→ consultar um país
→ repetir
→ combinar os resultados
```

## Documentação

- [`docs/api-guide.md`](docs/api-guide.md)
- [`docs/data-dictionary.md`](docs/data-dictionary.md)
- [`docs/query-options.md`](docs/query-options.md)
- [`examples/brazil-2024.md`](examples/brazil-2024.md)

## Fonte oficial

U.S. Census Bureau International Trade Data API.

Para tarifa jurídica, defesa comercial ou classificação legal, volte à fonte oficial correspondente. Calculated Duties e Rate Provision são campos úteis para análise, mas não substituem o HTS nem as regras aduaneiras aplicáveis.
