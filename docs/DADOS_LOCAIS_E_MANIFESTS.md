# Dados Locais e Manifests

## Política de arquivos grandes

`data/raw/`, `data/silver/` e `data/gold/` são áreas locais. Elas podem conter
downloads, relatórios gerados e Parquets, mas o Git mantém somente seus arquivos
`.gitkeep`. Não adicione arquivos dessas camadas, mesmo quando um derivado for
compacto.

`data/processed/` permanece local para o pipeline legado temporário do frontend.
As amostras pequenas em `data/samples/` continuam versionadas para colaboração.

`app/public/data/v1/` e a saida publica do exportador: indice, metadata e shards
por UF derivados das GOLDs. JSONs desse diretorio podem ser versionados quando
forem o conjunto de apresentacao revisado para a aplicacao. Eles nao sao RAW,
SILVER ou GOLD e nao devem conter Parquets, credenciais ou dados pessoais. O
exportador recusa substituir uma saida que nao tenha seu marcador de geracao.

## Manifests versionados

`data/manifests/` aceita somente JSON de metadados de execução com até 1 MB por
arquivo. Eles registram versões, URLs, hashes, contagens e status, mas nunca
substituem os dados que descrevem. A verificação Python do CI rejeita artefatos
locais rastreados, formatos não JSON nesse diretório e manifests acima do limite.

Os manifests migrados são cópias compactas das execuções de origem. Eles são
evidência histórica, não confirmação de que RAW, SILVER ou GOLD existam neste
clone. Os hashes de saída neles registrados referem-se aos artefatos da execução
de origem.

## Execução local

Para materializar os dados, instale `requirements.txt` e execute, da raiz, em
ordem:

```bash
python -m src.pipeline
python -m src.mapbiomas
python -m src.atlas
python -m pytest -q
```

Essas etapas requerem acesso às fontes oficiais e espaço local. Até serem
concluídas, qualquer consulta a Parquets e os testes marcados como dependentes de
saídas materializadas permanecem bloqueados; os demais testes Python podem ser
executados offline.
