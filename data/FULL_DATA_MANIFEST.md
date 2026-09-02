# Manifesto das bases completas

Este manifesto identifica as entradas completas usadas pelo pipeline do Antes da Chuva e o conjunto municipal produzido a partir delas. Os arquivos grandes são compartilhados de forma privada com os colaboradores e permanecem fora do Git.

## Fontes originais

| Arquivo | Tamanho | SHA-256 | Uso |
| --- | ---: | --- | --- |
| `atlas_1991_2025.xlsx` | 68,16 MB | `b7871f503d57887f5a77e7064cbf278cb8a34edfc46c9daddb241c465341cf7e` | Registros municipais das cinco tipologias ligadas à chuva |
| `censo_6805_percentual_rede.json` | 1,62 MB | `00e2cf4ec9841de2c5e6f6a30f331f83f4c5eddbc2189306138774b12741ed27` | Indicador municipal derivado da tabela 6805 do Censo 2022 |
| `siconv_programa.csv.zip` | 10,76 MB | `19c33fc8799e078b60aa2f74fadae5d0a90875dbf0a4946ec91f639041c4ec87` | Identificação dos programas selecionados |
| `siconv_programa_proposta.csv.zip` | 5,37 MB | `9ae6013728a3fb69b81cc75a69d162b501d5d8929d1dfdd0d6ecf170ecf31011` | Relação entre programas e propostas |
| `siconv_proposta.csv.zip` | 190,31 MB | `55c4dc8ff6fc85a9dc65b8f7e09176794dabf88362aa5143c68e22d7cc69e817` | Município e objeto das propostas |
| `siconv_convenio.csv.zip` | 15,75 MB | `7b4d1b9ab5c822184bffae77f993b6e3c8a705f22a2f3d86f7aa4faa5c3e4a34` | Situação, ano, número e valor dos convênios |

## Dado processado

| Arquivo | Tamanho | SHA-256 | Uso |
| --- | ---: | --- | --- |
| `municipios.json` | 2,01 MB | `d27d90d50175f506375785d05f68394c1b9f118f2b9d57077b8f000cfa4384bf` | Conjunto consolidado de 5.570 localidades consumido pelo frontend |

Tamanho total do pacote: aproximadamente 294 MB.

## Verificação após o download

No PowerShell:

```powershell
Get-FileHash -Algorithm SHA256 caminho-do-arquivo
```

No Linux ou WSL:

```bash
sha256sum caminho-do-arquivo
```

O valor calculado deve ser idêntico ao hash registrado neste manifesto.

## Uso no pipeline

Copie os seis arquivos de fontes originais para `data/raw/`, preservando os nomes. Em seguida, execute:

```bash
python scripts/build_data.py
```

A saída será gravada em `app/public/data/municipios.json`.

## Proveniência e limites

- Atlas Digital de Desastres no Brasil: `https://atlasdigital.mdr.gov.br/paginas/downloads.xhtml`
- Censo Demográfico 2022, tabela 6805: `https://sidra.ibge.gov.br/tabela/6805`
- Transferências e Parcerias da União: `https://dados.gov.br/dados/conjuntos-dados/transferencias-e-parcerias-da-uniao`

Os arquivos são dados públicos e continuam sujeitos aos termos de suas fontes. A auditoria metodológica e os limites de interpretação estão documentados em `docs/AUDITORIA_FONTES.md`.
