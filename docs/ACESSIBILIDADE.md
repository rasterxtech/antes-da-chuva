# Revisão de acessibilidade

## Escopo da revisão

Revisão estática do código da interface e dos testes em 3 de setembro de 2026.
Ela não substitui teste com pessoas usuárias, leitores de tela, diferentes
navegadores ou medição visual em uma implantação.

| Tema | Evidência no código | Estado |
|---|---|---|
| Idioma e estrutura | `lang="pt-BR"`, landmark `main`, cabeçalhos e seções nomeadas em `app/app/layout.tsx` e `app/app/page.tsx` | Revisado estaticamente |
| Teclado | Combobox aceita setas, Enter e Escape; resultados são botões | Coberto por `app/test/page.test.tsx` |
| Atalho de conteúdo | Link “Pular para o conteúdo principal” aponta ao conteúdo principal | Implementado e coberto por teste |
| Foco visível | `:focus-visible` aplica contorno consistente; controles existentes preservam seus anéis | Implementado; inspeção visual manual pendente |
| Estados assíncronos | Índice, shards e metadados mostram carregamento, erro ou alerta | Revisado estaticamente e parcialmente coberto por teste |
| ARIA | Busca usa `combobox`, `listbox`, opções e `aria-activedescendant`; atualizações municipais usam `aria-live` | Revisado estaticamente |
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
- [ ] Conferir zoom de 200%, largura de 320 px e orientação retrato.
- [ ] Conferir `prefers-reduced-motion: reduce` em navegador real.
- [ ] Registrar achados e correções antes de declarar conformidade.
