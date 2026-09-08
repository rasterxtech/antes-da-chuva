# Índice — Sources restantes

1. `01_atlas_s2id.md` — Atlas/S2ID
2. `02_icm.md` — ICM
3. `03_transferegov.md` — Transferegov
4. `04_sinisa.md` — SINISA
5. `05_midr_prioritarios.md` — MIDR prioritários/Cadastro Nacional
6. `06_cemaden.md` — Cemaden
7. `07_sgb_suscetibilidade.md` — SGB
8. `08_populacao_areas_risco.md` — População em Áreas de Risco

## Ordem recomendada
Atlas → ICM → Transferegov → SINISA → MIDR → Cemaden → SGB → População em Áreas de Risco.

## Depois das fontes
Criar `municipality_source_coverage` (1 linha por `codigo_ibge`) apenas com flags de disponibilidade e referências mais recentes, sem indicadores.

Criar `source_freshness` (1 linha por fonte) com `last_checked_at`, `last_changed_at`, `latest_reference_period`, `latest_publication_date`, `days_since_check`, `days_since_change`, `status`.

## Orquestração
Após todas as fontes individuais, criar `python -m src.all_sources`. Uma fonte pode falhar sem corromper as demais; o run global deve reportar status por source.

## Frequências de checagem sugeridas
Atlas semanal; ICM mensal; Transferegov diário; SINISA mensal; MIDR semanal; Cemaden inventory diário; SGB mensal; Risk Population mensal. São frequências de checagem, não periodicidade oficial.
