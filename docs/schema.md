# Schema de `dim_municipality`

> **Disponibilidade no repositório consolidado:** este é o contrato da GOLD.
> O arquivo `data/gold/dim_municipality.parquet` é materializado localmente e
> não está no Git; consultas a ele dependem de uma execução local do pipeline.

Granularidade: uma linha por unidade territorial retornada no nivel municipal pela API de Localidades do IBGE. A chave primaria logica e `codigo_ibge`.

| Nome | Tipo DuckDB/Parquet | Descricao | Origem |
|---|---|---|---|
| `codigo_ibge` | `VARCHAR` / `STRING` | Geocodigo IBGE de 7 digitos e chave canonica. | `id`, convertido de numero para string. |
| `municipio` | `VARCHAR` / `STRING` | Nome oficial, sem alteracao. | `nome`. |
| `municipio_normalized` | `VARCHAR` / `STRING` | Nome auxiliar sem acentos, em minusculas e com espacos normalizados. Nunca deve ser usado como chave principal. | Derivado de `nome` com Unicode NFKD, remocao de diacriticos, `casefold` e normalizacao de espacos. |
| `uf` | `VARCHAR` / `STRING` | Nome oficial da Unidade da Federacao. | `regiao-imediata.regiao-intermediaria.UF.nome`. |
| `sigla_uf` | `VARCHAR` / `STRING` | Sigla da Unidade da Federacao. | `regiao-imediata.regiao-intermediaria.UF.sigla`. |
| `codigo_uf_ibge` | `VARCHAR` / `STRING` | Codigo IBGE da UF, tratado como identificador. | `regiao-imediata.regiao-intermediaria.UF.id`, convertido para string. |
| `regiao` | `VARCHAR` / `STRING` | Nome da Grande Regiao. | `regiao-imediata.regiao-intermediaria.UF.regiao.nome`. |
| `codigo_regiao` | `VARCHAR` / `STRING` | Codigo IBGE da Grande Regiao, tratado como identificador. | `regiao-imediata.regiao-intermediaria.UF.regiao.id`, convertido para string. |
| `regiao_imediata` | `VARCHAR` / `STRING` | Regiao Geografica Imediata vigente. | `regiao-imediata.nome`. |
| `codigo_regiao_imediata` | `VARCHAR` / `STRING` | Codigo IBGE da Regiao Geografica Imediata. | `regiao-imediata.id`, convertido para string. |
| `regiao_intermediaria` | `VARCHAR` / `STRING` | Regiao Geografica Intermediaria vigente. | `regiao-imediata.regiao-intermediaria.nome`. |
| `codigo_regiao_intermediaria` | `VARCHAR` / `STRING` | Codigo IBGE da Regiao Geografica Intermediaria. | `regiao-imediata.regiao-intermediaria.id`, convertido para string. |
| `tipo_unidade_territorial` | `VARCHAR` / `STRING` | Distingue `municipio`, `distrito_federal` e `distrito_estadual`. | Regra explicita por `codigo_ibge`: `5300108` e Distrito Federal; `2605459` e distrito estadual; demais sao municipios. |
| `source` | `VARCHAR` / `STRING` | Identificacao da fonte oficial. | Constante `IBGE API de Localidades v1`. |
| `source_url` | `VARCHAR` / `STRING` | Endpoint exato consultado. | Configuracao do pipeline. |
| `source_updated_at` | `TIMESTAMPTZ` / timestamp UTC | Data de atualizacao declarada pela fonte, quando informada. | Header HTTP `Last-Modified`; nulo na consulta atual porque a API nao o fornece. |
| `ingested_at` | `TIMESTAMPTZ` / timestamp UTC | Instante de inicio da execucao do pipeline. | Gerado pelo pipeline em UTC. |

## Colunas Somente na SILVER

`mesorregiao`, `codigo_mesorregiao`, `microrregiao` e `codigo_microrregiao` sao preservadas em `data/silver/silver_ibge_municipalities.parquet` para rastreabilidade. Nao fazem parte da GOLD porque foram progressivamente substituidas pelas regioes imediatas e intermediarias ate 2023 e a classificacao antiga ja nao e completa: Boa Esperanca do Norte/MT aparece com `microrregiao = null` na API.
