# Smoke test de produção

> **PENDENTE DE EXECUÇÃO.** Este arquivo é um checklist. Não registra resultado
> de produção, URL, data, navegador, release ou commit porque essas informações
> não foram confirmadas neste checkout.

## Identificação a preencher antes do teste

| Campo | Valor |
|---|---|
| URL autorizada | `[PENDENTE]` |
| Data e hora com fuso | `[PENDENTE]` |
| Pessoa responsável | `[PENDENTE]` |
| Navegador e versão | `[PENDENTE]` |
| Viewport ou dispositivo | `[PENDENTE]` |
| Commit ou release demonstrada | `[PENDENTE]` |

## Checklist

| Verificação | Resultado esperado | Estado | Evidência a anexar |
|---|---|---|---|
| Carregamento inicial | Página carrega sem erro bloqueador visível | `[ ] PENDENTE` | Captura ou registro de console sem dados sensíveis |
| Índice municipal | Busca aceita nome, UF e código IBGE de sete dígitos | `[ ] PENDENTE` | Município e código usados |
| Link compartilhável | `codigo_ibge` válido abre o município correspondente | `[ ] PENDENTE` | URL redigida se necessário e resultado |
| Fonte Atlas | Período e release são mostrados a partir da metadata publicada | `[ ] PENDENTE` | Captura da seção de fontes |
| Ausências | Estados não aparecem como zero ou conclusão indevida | `[ ] PENDENTE` | Município e estado observados |
| MapBiomas | Período, unidade em hectares e cautela metodológica aparecem | `[ ] PENDENTE` | Município e captura |
| Alertas | Links para IDAP e orientações oficiais abrem o destino esperado | `[ ] PENDENTE` | Destino confirmado sem registrar dados pessoais |
| Teclado e movimento | Foco visível, atalho de conteúdo e redução de movimento funcionam | `[ ] PENDENTE` | Navegador e cenário usados |
| Mobile | Fluxo principal permanece utilizável no viewport definido | `[ ] PENDENTE` | Viewport e captura |

## Encerramento

- [ ] Registrar defeitos bloqueadores e decisão de corrigir ou interromper a submissão.
- [ ] Guardar capturas aprovadas em `capturas/` com nomes sem dados pessoais.
- [ ] Atualizar este arquivo somente com fatos observados durante o teste.
