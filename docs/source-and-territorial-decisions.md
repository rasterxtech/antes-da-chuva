# Fonte e Decisoes Territoriais

> **Disponibilidade no repositório consolidado:** o RAW citado neste documento
> é local e ignorado pelo Git. Os valores documentados são a baseline da origem;
> para inspecionar o RAW ou gerar uma nova GOLD, execute o pipeline com acesso à
> API do IBGE e armazenamento local.

## Fonte Primaria

- Fonte: API de Localidades v1, oficial do IBGE.
- Endpoint: `https://servicodados.ibge.gov.br/api/v1/localidades/municipios?orderBy=id`.
- Documentacao: `https://servicodados.ibge.gov.br/api/docs/localidades`.
- Data da consulta materializada: consultar `queried_at` em `data/raw/raw_ibge_municipalities_metadata.json` e o relatorio em `data-quality-report.md`.
- RAW imutavel da ultima execucao: `data/raw/raw_ibge_municipalities.json`.
- Integridade do RAW: SHA-256 do JSON e do payload de transporte registrados no manifesto ao lado do arquivo. A descompressao HTTP gzip, quando aplicada pelo servidor, nao altera o conteudo semantico preservado.

A API foi escolhida por ser oficial, publica, simples de automatizar e por entregar em uma unica resposta o geocodigo municipal, nome e hierarquias regional e estadual. A opcao `orderBy=id` torna a captura estavel para inspecao, mas a ordem nao integra a chave.

## Campos Originais

Os campos de primeiro nivel sao:

| Campo original | Tipo JSON | Uso |
|---|---|---|
| `id` | number | Geocodigo convertido para string. |
| `nome` | string | Nome oficial preservado. |
| `microrregiao` | object ou null | Hierarquia antiga preservada somente na SILVER. |
| `regiao-imediata` | object | Hierarquia vigente usada na SILVER e GOLD. |

As estruturas aninhadas usadas sao:

- `microrregiao.id`, `microrregiao.nome`, `microrregiao.mesorregiao.id` e `microrregiao.mesorregiao.nome` apenas na SILVER;
- `regiao-imediata.id` e `regiao-imediata.nome`;
- `regiao-imediata.regiao-intermediaria.id` e `.nome`;
- `regiao-imediata.regiao-intermediaria.UF.id`, `.sigla` e `.nome`;
- `regiao-imediata.regiao-intermediaria.UF.regiao.id` e `.nome`.

O manifesto RAW registra dinamicamente os campos de primeiro nivel efetivamente recebidos.

## Transformacoes

- Conversao de todos os codigos administrativos para string.
- Achatamento da hierarquia aninhada sem alterar os nomes oficiais.
- Criacao de `municipio_normalized` apenas para busca auxiliar.
- Classificacao por codigo de Brasilia como `distrito_federal` e Fernando de Noronha como `distrito_estadual`.
- Preservacao de meso/microrregioes na SILVER e exclusao dessas classificacoes antigas da GOLD.
- Ordenacao fisica da saida por `sigla_uf, municipio`, sem significado de chave.
- Adicao de linhagem (`source`, `source_url`, `source_updated_at`, `ingested_at`).

## Contagem e Escopo

Na consulta de 1 de setembro de 2026, a rota retornou 5.571 localidades no nivel municipal. A publicacao oficial mais recente disponivel, a Divisao Territorial Brasileira 2025, informa 5.569 municipios, aos quais se somam o Distrito Federal (Brasilia) e o distrito estadual de Fernando de Noronha. Assim, os 5.571 registros da API sao coerentes com o universo usado normalmente por bases estatisticas no nivel municipal.

A validacao automatica nao fixa 5.570 nem 5.571: compara a GOLD com a quantidade e com o conjunto de codigos recebidos na resposta oficial da execucao. A decomposicao por `tipo_unidade_territorial` torna a diferenca conceitual visivel.

Referencias oficiais complementares:

- DTB 2025: `https://geoftp.ibge.gov.br/organizacao_do_territorio/estrutura_territorial/divisao_territorial/2025/DTB_2025.zip`.
- Pagina da DTB: `https://www.ibge.gov.br/geociencias/organizacao-do-territorio/estrutura-territorial/23701-divisao-territorial-brasileira.html`.
- Divulgacao da DTB 2025, publicada em 30/03/2026: `https://agenciadenoticias.ibge.gov.br/agencia-noticias/2012-agencia-de-noticias/noticias/46255-ibge-atualiza-dados-geograficos-de-estados-e-municipios-brasileiros-para-o-ano-de-2025`.

## Casos Especiais

- Brasilia (`5300108`) permanece na dimensao como representante analitico do Distrito Federal. O DF nao e juridicamente um municipio e nao pode ser dividido em municipios.
- Fernando de Noronha (`2605459`) permanece porque a propria rota de municipios e as bases estatisticas do IBGE o tratam no nivel municipal. Juridicamente e um distrito estadual de Pernambuco.
- Boa Esperanca do Norte (`5101837`) e o municipio mais recente, incluido na DTB 2024 e instalado em 1 de janeiro de 2025. Possui regioes imediata e intermediaria, mas `microrregiao` nula na API, evidenciando por que a classificacao antiga nao deve compor a GOLD.
- Alteracoes de nome nao criam uma chave nova necessariamente. A dimensao sempre conserva o nome oficial vigente retornado pelo IBGE.

## Historico Futuro

Esta dimensao e de estado vigente, nao uma SCD nem uma tabela historica. Uma fonte historica pode conter codigo extinto, codigo alterado ou nome anterior e, portanto, nao deve receber join por nome.

Recomenda-se criar futuramente `bridge_municipality_ibge_history`, versionada por intervalo de vigencia, com pelo menos:

- `codigo_ibge_origem`;
- `codigo_ibge_vigente`;
- `valid_from` e `valid_to`;
- `relationship_type` (`renamed`, `split`, `merged`, `extinct`, `code_changed`);
- fator ou regra de correspondencia quando uma relacao nao for 1:1;
- ato legal e fonte oficial.

Codigos historicos sem correspondencia 1:1 devem permanecer em quarentena para decisao explicita; nunca devem ser associados somente por similaridade de nome.

## Limitacoes

- A API nao declara ano de referencia, versao, `Last-Modified` ou `ETag`; por isso `source_updated_at` fica nulo. O `ingested_at`, o RAW e seu SHA-256 garantem a rastreabilidade da captura.
- A API e uma visao vigente e nao fornece periodos de validade, codigos predecessores ou sucessores.
- A confirmacao com a DTB 2025 e documentada, mas a lista suplementar nao e uma segunda entrada do pipeline.
- Limites territoriais e geometrias nao pertencem ao escopo desta dimensao.
