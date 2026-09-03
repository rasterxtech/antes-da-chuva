# Amostras de dados para colaboração

Esta pasta oferece um recorte pequeno e legível do conjunto consolidado do Antes da Chuva. Ela existe para exploração, testes, protótipos e integração local sem exigir o download das bases brutas, que somam aproximadamente 1,5 GB.

## Conteúdo

| Arquivo | Grão | Uso recomendado |
| --- | --- | --- |
| `municipios.sample.json` | Um objeto por município | Testes que precisam do mesmo formato consumido pelo frontend |
| `censo.sample.csv` | Uma linha por município | Exploração do indicador derivado do Censo 2022 |
| `atlas.sample.csv` | Uma linha por município com histórico | Exploração dos registros agregados de desastres ligados à chuva |
| `transferegov.sample.csv` | Uma linha por município com evidência selecionada | Exploração dos convênios e da evidência mais recente |

Todos os arquivos usam `codigo_ibge` ou `code` como chave de integração municipal.

## Cobertura da amostra

O recorte contém 31 municípios:

- uma capital de cada unidade federativa;
- Blumenau, usado como caso demonstrador do produto;
- Acrelândia, caso sem histórico nem transferência no conjunto consolidado;
- Bom Jesus da Serra, caso com transferência e sem histórico;
- Milagres do Maranhão, caso em que o indicador censitário está ausente.

Essa composição testa presença e ausência de informações nas três dimensões do produto. Ela é intencional e não constitui uma amostra estatística da população brasileira.

## Regeneração

O payload legado normalizado `app/public/data/municipios.json` permanece
versionado para a transicao de Censo e Transferegov e para regenerar estas
amostras. A aplicacao atual consome o contrato v1 em `app/public/data/v1/`, nao
esse payload diretamente. Para reconstruir as amostras a partir do payload
legado:

```bash
python scripts/build_samples.py
```

O script valida a existência dos municípios, duplicatas e a cobertura das 27 unidades federativas antes de gravar os arquivos.

## Limitações

- As linhas são agregações municipais, não cópias integrais dos registros originais.
- A ausência de linha no Atlas ou no Transferegov representa ausência no recorte processado, não inexistência de desastre ou política pública.
- O campo `reconhecidos` é um subconjunto dos registros administrativos conhecidos.
- A amostra não deve ser usada para estimativas, rankings ou conclusões nacionais.
- As fontes oficiais e suas limitações estão documentadas em `docs/AUDITORIA_FONTES.md`.

## Bases originais

As fontes brutas permanecem fora do Git por tamanho e podem ser obtidas nos portais oficiais indicados em `docs/FONTES_DE_DADOS.md`. Os dados continuam sujeitos aos termos e às condições de suas fontes de origem.

Os colaboradores autorizados também podem solicitar aos mantenedores acesso ao pacote privado das bases completas e conferir sua integridade em `data/FULL_DATA_MANIFEST.md`.
