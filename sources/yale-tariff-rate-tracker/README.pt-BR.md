# Yale Tariff Rate Tracker

[English](README.md) | [Português](README.pt-BR.md)

Módulo reutilizável para acessar os releases do [Tariff Rate Tracker](https://github.com/Budget-Lab-Yale/tariff-rate-tracker), do The Budget Lab at Yale. O projeto modela tarifas estatutárias dos Estados Unidos no nível **HTSUS10 × país de origem × intervalo de vigência**.

## O que este módulo entrega

- resolução automática do release mais recente pela API do GitHub;
- download auditável do ativo ZIP, com tag, data, URL e tamanho registrados;
- leitura somente do painel `actual`, sem misturar cenários contrafactuais;
- filtro por país antes da conversão do Parquet para pandas;
- saída compacta em CSV.GZ pronta para cruzamento com dados mensais do Census;
- exemplo Power Query para consultar os metadados do release sem baixar o arquivo de centenas de megabytes no Excel.

## Exemplos

| # | Exemplo | Uso |
|---|---|---|
| 01 | [Baixar o release mais recente](python/01_download_latest_release.py) | Resolve e baixa o ZIP oficial; grava um manifesto JSON |
| 02 | [Extrair o painel de um país](python/02_extract_country_rates.py) | Filtra `actual/snapshots` por código Census do país e gera CSV.GZ |
| 03 | [Construir a classificação mensal de sobretarifas](python/03_build_monthly_tariff_exposure.py) | Cruza o exemplo Census 07 com o Yale, remove probabilidades de utilização e leva incidências por conteúdo à maior faixa potencial |
| 01-M | [Metadados do release em Power Query](power-query/01_latest_release_metadata.m) | Retorna tag, data e URL do ativo oficial |

## Uso rápido

```bash
python -m pip install -r requirements.txt
python sources/yale-tariff-rate-tracker/python/01_download_latest_release.py
python sources/yale-tariff-rate-tracker/python/02_extract_country_rates.py --country 3510
python sources/yale-tariff-rate-tracker/python/03_build_monthly_tariff_exposure.py --census data/monthly_imports_country_htsus10.csv.gz --yale data/yale-tariff-rate-tracker/country_3510_rates.csv.gz
```

O código `3510` representa o Brasil na classificação de países do Census usada pelo tracker.

## Regra de cruzamento com o Census

O Census é mensal, enquanto o Yale registra intervalos diários. Para cada `mês × HTSUS10`:

1. fixe o dia 15 como data de referência mensal;
2. selecione o intervalo vigente nessa data para cada HTSUS10;
3. preserve `total_additional` como `yale_modeled_rate_reference`, somente para auditoria;
4. medidas iniciadas até o dia 15 entram no próprio mês; medidas posteriores entram no mês seguinte;
5. classifique aeronaves civis diretamente identificáveis em 0%, sob condição de cumprimento da General Note 6;
6. para outras exceções dependentes de uso, adote a alíquota cheia por padrão e registre a ressalva de elegibilidade;
7. classifique incidências dependentes de conteúdo pela maior alíquota estatutária potencial e marque `tariff_rate_qualifier=up_to`;
8. associe o tratamento ao valor mensal de importações para consumo (`CON_VAL_MO`).

Uma medida iniciada em 18 de agosto entra na classificação principal de setembro. O resultado é uma classificação analítica, não os direitos efetivamente arrecadados nem uma decisão aduaneira vinculante. O conceito não inclui tarifa-base, antidumping, direitos compensatórios ou medidas fora do tracker.

Referências normativas para a exceção de aeronaves civis: [Seção 301 Brasil](https://public-inspection.federalregister.gov/2026-14542.pdf), [Seção 301 trabalho forçado](https://public-inspection.federalregister.gov/2026-15274.pdf) e [HTSUS — General Note 6](https://hts.usitc.gov/).

## Limites

- O Yale modela parcelas de utilização e conteúdo em alguns programas. Probabilidades de utilização ficam fora da métrica principal; linhas dependentes de conteúdo usam um máximo potencial claramente qualificado, enquanto a estimativa Yale permanece nos campos auxiliares `yale_modeled_*`.
- A elegibilidade para exceções depende da documentação da entrada; o HTSUS10 isolado não substitui a análise do CBP.
- Releases podem conter intervalos futuros já incorporados ao cronograma do tracker; registre sempre tag e data de publicação.
- O ZIP é grande. A extração em Python/Parquet é a rota recomendada; o Power Query fica restrito à descoberta do release e ao consumo de extratos processados.

## Showcase relacionado

[![Monitor Brasil × tarifas dos EUA](../../docs/assets/us-brazil-tariff-monitor.png)](https://feliperamon123.github.io/us-brazil-tariff-monitor/)

O dashboard [Brasil × tarifas dos EUA](https://github.com/FelipeRamon123/us-brazil-tariff-monitor) aplica este módulo às importações mensais provenientes do Brasil.
