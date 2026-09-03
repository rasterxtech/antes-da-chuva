# Contexto comum para todos os prompts

Você está contribuindo no projeto:

https://github.com/rasterxtech/antes-da-chuva

Antes de escrever código:

1. inspecione o repositório atual;
2. leia `README.md`;
3. leia `docs/como-consumir.md`;
4. leia `docs/schema.md`, `docs/mapbiomas.md` e `docs/atlas.md`;
5. inspecione as GOLDs existentes e seus schemas reais;
6. reutilize a arquitetura e convenções já existentes;
7. NÃO altere pipelines IBGE, MapBiomas ou Atlas apenas para facilitar o frontend.

O projeto atualmente é batch-oriented e materializa Parquets. Não existe uma API obrigatória.

Para a camada de apresentação, prefira uma arquitetura simples e compatível com hospedagem estática.

```text
Parquets GOLD
   ↓
script Python/DuckDB de preparação
   ↓
JSONs pequenos por município / assets estáticos
   ↓
frontend
```

Evite enviar Parquets gigantes para o navegador.

`codigo_ibge` continua sendo a chave interna.

As visualizações devem ser responsivas e funcionar bem em desktop e mobile.

Não criar:
- score de risco;
- previsão;
- probabilidade futura;
- relações causais;
- ranking sensacionalista.

Sempre diferenciar registro histórico, comparação e interpretação.

O objetivo da interface é permitir que uma pessoa entenda um município em poucos minutos.

Utilize dados reais existentes nas GOLDs, nunca mocks como resultado final.

Quando uma informação estiver ausente, a interface deve explicar a ausência em vez de mostrar zero automaticamente.

## Contrato de payload municipal

No primeiro bloco, crie uma estrutura reutilizável de payload municipal para a camada de apresentação.

```json
{
  "municipality": {},
  "summary": {},
  "disasters": {
    "history": [],
    "types": [],
    "months": [],
    "highlights": []
  },
  "land_cover": {
    "history": [],
    "change": {}
  },
  "benchmarks": {},
  "sources": {}
}
```

Os prompts seguintes devem estender essa mesma estrutura, não inventar novos contratos paralelos.
