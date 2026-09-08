# Revisão de acessibilidade

## Escopo da revisão

Revisão de código atualizada em 8 de setembro de 2026, complementada por inspeção visual e interativa do candidato editorial em navegador local. Veja as capturas e os cenários no [registro de homologação](HOMOLOGACAO_DESIGN_STAGING.md).

Ela não substitui testes com pessoas usuárias, leitores de tela, dispositivos físicos ou auditoria completa em uma implantação.

| Tema | Evidência no código | Estado |
|---|---|---|
| Idioma e estrutura | `lang="pt-BR"`, landmark `main`, cabeçalhos e seções nomeadas em `app/app/layout.tsx` e `app/app/page.tsx` | Revisado estaticamente |
| Teclado | Busca aceita setas, Enter e Escape; opção ativa rola à vista; seleção encaminha foco ao resultado; menu móvel fecha com Escape | Coberto por testes e inspeção de fluxos no navegador |
| Atalho de conteúdo | Link “Pular para o conteúdo principal” aponta ao conteúdo principal | Implementado e coberto por teste |
| Foco visível | `:focus-visible` aplica contorno consistente; controles existentes preservam seus anéis | Inspecionado nos fluxos principais; percurso completo ainda pendente |
| Estados assíncronos | Índice, shards e metadados mostram carregamento, erro ou alerta | Revisado estaticamente e parcialmente coberto por teste |
| ARIA | Busca usa `combobox`, `listbox`, opções e `aria-activedescendant` somente com lista aberta; `role="status"` anuncia carregamento/município sem repetir todos os gráficos | Revisado estaticamente; leitor de tela pendente |
| Gráficos | Séries diferenciadas por traçado além da cor; histórico e território oferecem tabelas expansíveis com cabeçalhos e unidades | Código e composição visual conferidos |
| Movimento | Animações decorativas ficam condicionadas a `prefers-reduced-motion`; cartões não se deslocam nesse modo | Revisado estaticamente |
| Links externos | Links gerados pela função de fonte anunciam abertura em nova aba | Revisado estaticamente |
| Contraste | Há combinações com transparência, gradientes e imagens | Pendente de medição no navegador, por estado e viewport |

`npm test` verifica comportamentos selecionados. Não há varredura automatizada
completa de WCAG configurada neste checkout.

## Checklist manual pendente

- [ ] Percorrer a página inteira apenas com Tab, Shift+Tab, Enter, Espaço e setas.
- [ ] Confirmar que o atalho de conteúdo aparece ao receber foco e leva ao alvo correto.
- [ ] Testar busca, seleção e mensagens de erro com leitor de tela.
- [ ] Medir contraste de texto, foco, alertas e links sobre todos os fundos reais.
- [x] Conferir reflow dos estados principais a 320 px em viewport de navegador.
- [ ] Complementar com zoom de 200%, orientação paisagem e dispositivo físico.
- [ ] Conferir `prefers-reduced-motion: reduce` em navegador real.
- [ ] Registrar achados e correções antes de declarar conformidade.
