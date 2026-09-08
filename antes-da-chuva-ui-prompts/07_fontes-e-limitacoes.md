# Prompt 07 — Fontes e limitações

Implemente o bloco **De onde vêm estes dados?** e a subseção **Como interpretar**.

## Objetivo
Dar transparência ao usuário sem obrigá-lo a ler a documentação técnica no GitHub.

## Fontes atuais
### IBGE
Identidade territorial e hierarquia regional.

### MapBiomas Brasil
Cobertura e uso da terra.

### Atlas Digital/S2ID
Registros históricos oficiais de desastres e impactos.

## Estrutura por fonte
Mostrar:
- nome;
- órgão/projeto;
- período utilizado;
- versão/release/coleção;
- última atualização da carga;
- link oficial;
- link para metodologia interna.

## Metadata
Não hardcode coleção MapBiomas, série, release Atlas ou datas se os manifests já contêm esses valores. Gerar metadata da interface a partir dos manifests.

## Limitações curtas
IBGE: `A dimensão representa a territorialidade vigente.`

MapBiomas: `Área urbanizada é uma classe de cobertura e não mede diretamente impermeabilização.`

Atlas: `Ausência de registro não significa ausência de desastre.`

Atlas: `Sazonalidade histórica não é previsão futura.`

## UX
Usar cards/accordions e permitir expandir `Entenda a metodologia`. Evitar muro de texto.

## Data lineage
Opcionalmente incluir seção avançada com `source_release`, `collection`, `reference_year`, hash encurtado e `ingested_at`.

## Links
Links externos para fontes oficiais. Links internos para `docs/mapbiomas.md`, `docs/atlas.md`, `docs/schema.md` ou equivalentes publicados.

## Payload
Adicionar `sources`.

## Entregável
Componente, metadata automática, links, limitações, estado para manifest ausente e teste garantindo que versões exibidas refletem os manifests atuais.
