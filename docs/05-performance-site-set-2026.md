# Performance do site — 28 e 29/09/2026

Registro do que foi feito para acelerar o site, o que ficou de fora e o que cada colega precisa
saber antes de mexer. Feito por Renato com o Claude (Claude Code).

## Antes e depois (home, PageSpeed Insights)

| | Antes (28/09, manhã) | Depois (29/09) |
|---|---|---|
| Nota no celular | 55 | 65-68 (varia entre rodadas) |
| Nota no computador | 61 | 95 |
| Celular: tempo até aparecer algo (FCP) | 7,5 s | 1,5 s |
| Celular: tempo com a página congelada (TBT) | 200-1.000 ms | 190 ms |
| Computador: conteúdo principal (LCP) | 3,8 s | 1,2 s |

Os dados de **visitantes reais** do Google (Core Web Vitals, janela de 28 dias) estavam
reprovados em 28/09: LCP de 5,9 s no celular e 4,7 s no computador. O efeito das mudanças
aparece aos poucos até o fim de outubro.

## O que foi feito (tudo no ar)

| # | Mudança | Onde | Commit / versão |
|---|---|---|---|
| 1 | Removida a tela de carregamento do navio animado (Lottie) | 313 páginas, `js/main.js`, `css/main.css`, `scripts/build_pages.py` | `e8a24bd` |
| 2 | Banner de cookies AdOpt carregando com `async` | 315 páginas | `c8c7b46` |
| 3 | 4 CSS base unificados em `css/base.css` (gerado) | 313 páginas, `scripts/build_css.py`, `scripts/verificar.py` | `5ec7b62` |
| 4 | Foto principal da home sem animação de entrada | `css/main.css` | `acec10d` |
| 5 | Chat do Botmaker só na 1ª interação (rolar, tocar, clicar, mouse, tecla) | GTM-52WHRQN | versão 13 |
| 6 | Fontes Poppins e Nunito Sans servidas pelo próprio site (sai o Google Fonts) | `fonts/`, `css/fonts.css`, 315 páginas, `vercel.json` | `1d5999a` |

## Regras novas para quem mexe no site

- **Nunca edite `css/base.css`.** Ele é gerado a partir de `fonts.css`, `variables.css`,
  `reset.css`, `main.css` e `responsive.css`. Edite a origem e rode
  `python scripts/build_css.py`. O `scripts/verificar.py` reprova se ele estiver desatualizado.
- **Não adicione `<link>` do Google Fonts.** As fontes estão em `/fonts/`. Página que não usa o
  `base.css` carrega `<link rel="stylesheet" href="/css/fonts.css" />`.
- **Arquivo de fonte tem cache de 1 ano, imutável.** Para trocar uma fonte, mude o NOME do
  arquivo; sobrescrever com o mesmo nome não chega a quem já visitou.
- **O loader do navio foi desativado, não apagado.** Como reativar:
  `docs/04-loader-navio-desativado.md`.
- **O chat do Botmaker não aparece no navegador interno do Claude Code**, nem antes destas
  mudanças. Para conferir o chat, use um navegador de verdade.

## Testado e NÃO publicado

- **AdOpt carregado depois da abertura da página.** Funcionou, mas no Lighthouse (7 rodadas de
  cada versão) nota, FCP e LCP ficaram iguais; só o TBT caiu ~65 ms. E a tarefa pesada do AdOpt
  passaria a rodar na hora do primeiro toque. Descartado.
- **Hotjar:** já estava pausado no GTM; a WM usa só o Clarity.

## O que falta

| Prioridade | Item | Quem |
|---|---|---|
| Alta | O script do AdOpt ocupa o celular por ~1,5 s de uma vez; é o maior peso restante | Fornecedor (versão mais leve) |
| Média | Trocar o ícone do chat (PNG de 920 KB → 9 KB) e tirar as fontes Roboto/Mulish do CSS do Botmaker | Painel do Botmaker |
| Baixa | `utm-tracking.js` ainda trava a primeira exibição (cuidado: grava a origem do lead) | Site |
| Baixa | Imagens da home maiores que o tamanho exibido; logo de 1180 px exibido com 83 px | Site |
| A avaliar | Tag "Semrush" dispara em todas as páginas sem esperar o aceite de cookies | Quem souber para que serve |

## Como desfazer

- **Site:** `git revert <commit>` do item da tabela acima.
- **GTM (chat do Botmaker):** Versões → versão 12 → Publicar.
