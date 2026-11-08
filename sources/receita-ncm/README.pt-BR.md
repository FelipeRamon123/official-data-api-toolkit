# Receita Federal — nomenclatura NCM em português

[English](README.md) | [Voltar ao toolkit](../../README.pt-BR.md)

Conector para o JSON público do **Sistema Classif**, usado para obter as descrições oficiais em português que pertencem à base internacional compartilhada do Sistema Harmonizado.

## Exemplos

| Ambiente | Arquivo | Saída |
|---|---|---|
| Python | [`python/01_download_ncm_hierarchy.py`](python/01_download_ncm_hierarchy.py) | JSON com dicionários SH2, SH4 e SH6 |
| Power Query | [`power-query/01_ncm_hierarchy.m`](power-query/01_ncm_hierarchy.m) | Tabela `nível × código × descrição` |

Fonte oficial: `https://portalunico.siscomex.gov.br/classif/api/publico/nomenclatura/download/json`.

## Escopo da correspondência

NCM8 e HTSUS10 compartilham a estrutura internacional somente até o **SH6**. Por isso, o conector oferece descrições portuguesas seguras nos níveis SH2, SH4 e SH6. Para códigos HTS8/HTSUS10, uma aplicação pode exibir o SH6 em português como contexto e conservar a descrição americana do detalhe estatístico; não deve apresentar o desdobramento americano como se fosse uma tradução oficial da NCM.

Os metadados do JSON registram a data de atualização e o ato normativo informado pelo Sistema Classif.
