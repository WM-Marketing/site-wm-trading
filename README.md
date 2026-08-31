# WM Trading 2.0 — Site Institucional

Site institucional da **WM Trading**, empresa especializada em soluções tributárias, logísticas e aduaneiras para importações.

**Live:** [www.wmtrading.com.br](https://www.wmtrading.com.br) — no ar desde 20/08/2026  
**Preview:** [site-wm-trading.vercel.app](https://site-wm-trading.vercel.app) — mesmo conteúdo, com `canonical` para o domínio  
**Repo:** [github.com/WM-Marketing/site-wm-trading](https://github.com/WM-Marketing/site-wm-trading)

---

## Stack

- **HTML5** / **CSS3** / **JavaScript** puro (sem frameworks)
- **Lottie Web** — animação do loader (cargo ship)
- **Google Fonts** — Poppins + Nunito Sans
- **Hosting** — Vercel, com deploy **automático pela integração com o GitHub**
- **Versionamento** — GitHub. **Push em `main` publica em produção** (`www.wmtrading.com.br`); branch gera preview

---

## Estrutura de arquivos

```
site-wm-trading/
├── index.html              # Página principal (home)
├── css/
│   ├── variables.css       # Design tokens (cores, tipografia, espaçamentos)
│   ├── reset.css           # CSS reset
│   ├── main.css            # Estilos principais (desktop-first)
│   └── responsive.css      # Breakpoints mobile (≤1024px, ≤768px, ≤480px)
├── js/
│   ├── main.js             # Lógica principal (loader, scroll reveal, hamburger, tabs)
│   └── i18n.js             # Tradutor PT/EN (96 elementos via data-i18n)
├── images/
│   ├── assets/             # Fotos de seções e ícones
│   ├── logo/               # Logotipos WM Trading (PNG + SVG)
│   ├── icons/              # Ícones de segmento
│   └── sections/           # Imagens específicas de seções
├── vercel.json             # Configuração Vercel (outputDirectory: ".")
├── .vercelignore           # Exclui vídeos e arquivos grandes do deploy
└── .gitignore
```

---

## Design System

O design system está documentado em [`docs/`](docs/), separado em duas camadas:

- **[Fundamentos da Marca](docs/01-fundamentos-da-marca.md)** — camada reutilizável
  (fontes, logo, cores, tamanhos, bordas, sombras, botões). Arquivos:
  `css/variables.css` (tokens) + `css/foundations.css` (primitivas).
- **[Design de Landing Pages](docs/02-design-landing-pages.md)** — diretrizes de
  layout/composição para LPs de campanha, que **herdam** os fundamentos mas têm
  diagramação e imagens próprias (não replicam a home).

> A home usa `css/main.css` + `css/responsive.css` (sua diagramação específica).
> As LPs **não** importam esses arquivos — só os fundamentos + um `lp.css` próprio.
> Exemplo: [`importacao-carne-suina/`](importacao-carne-suina/).

## Design Tokens

### Cores

| Token | Valor | Uso |
|---|---|---|
| `--color-primary` | `#FC5000` | Laranja WM — CTAs, destaques, links |
| `--color-primary-light` | `#FFEBE0` | Fundo suave laranja |
| `--color-text-dark` | `#3A3A3A` | Texto principal |
| `--color-text-muted` | `#888888` | Texto secundário |
| `--color-bg-dark` | `#1A1A1A` | Hero, seção números, CTA |
| `--color-bg-white` | `#FFFFFF` | Fundo padrão |
| `--color-bg-light` | `#F5F5F5` | Fundo alternado |

### Tipografia

| Font | Uso | Pesos |
|---|---|---|
| **Poppins** | Corpo, UI, botões | 300 / 400 / 500 / 600 / 700 |
| **Nunito Sans** | Destaques especiais | 800 |

| Token | Valor | Uso |
|---|---|---|
| `--fs-sm` | 14px | Labels, captions |
| `--fs-base` | 16px | Texto corrido |
| `--fs-lg` | 27px | Títulos de seção |
| `--fs-xl` | 32px | Subtítulos grandes |
| `--fs-2xl` | 56px | Hero title (desktop) |

### Espaçamentos

| Token | Valor |
|---|---|
| `--container-width` | 1200px |
| `--container-px` | 80px (desktop) → 20px (mobile) |
| `--section-py` | 80px (desktop) → 56px (mobile) |

---

## Seções da página

| # | Seção | Classe CSS | Descrição |
|---|---|---|---|
| 1 | **Hero** | `.hero` | Fundo fotovoltaico, título animado, CTA |
| 2 | **Cards de Segmento** | `.section-cards` | 3 cards sobrepostos ao hero (autopeças, aço, solar) |
| 3 | **Por que a WM** | `.section-motivo` | Grid de 5 cards com efeito glow no hover |
| 4 | **Números** | `.section-numeros` | 4 KPIs animados (15 filiais, 7 benefícios, 20 anos, 98%) |
| 5 | **Benefícios** | `.section-beneficios` | Texto + mapa do Brasil |
| 6 | **Experiência** | `.section-experiencia` | Foto CEO + texto institucional |
| 7 | **Segmentos** | `.section-segmentos` | Grid de cards por setor |
| 8 | **Modalidades** | `.section-modalidade` | Tabs: Encomenda / Conta e Ordem / Assessoria / Global Sourcing |
| 9 | **CTA Final** | `.section-cta` | Fundo laranja com chamada para ação |
| — | **Footer** | `.footer-links` / `.footer-social` | Links, redes sociais, selos LGPD |

---

## Funcionalidades JavaScript

### Loader (`main.js`)
- Animação Lottie (cargo ship) enquanto a página carrega
- Ao concluir: adiciona `.loaded` ao `<body>` e dispara animações do hero

### Animações de entrada
- **Hero**: `heroFadeUp`, `heroFadeIn`, `heroZoomIn` via `@keyframes` CSS + classe `.loaded`
- **Seções 3–9**: `IntersectionObserver` com blur + translateY, delay escalonado por elemento (`--reveal-delay`)

### Efeito Magic Card (Seção 3)
- `mousemove` atualiza `--mouse-x` e `--mouse-y` no card
- CSS `::before` cria glow radial de 700px; `::after` cria borda luminosa de 400px

### Hamburger menu (mobile)
- Botão `#menu-toggle` com 3 spans → animação X ao abrir
- Classe `.open` no `<nav class="header-nav">` controla visibilidade

### Tradutor PT/EN (`i18n.js`)
- 96 elementos com `data-i18n` (texto) ou `data-i18n-html` (HTML)
- Persiste idioma em `localStorage`
- Botão `#lang-toggle` com bandeira no header

### Tabs (Seção 8)
- Radio inputs controlam `.tab-panel.active` via JS
- Scroll horizontal no mobile com `overflow-x: auto`

---

## Responsividade

| Breakpoint | Comportamento |
|---|---|
| Desktop (> 1024px) | Layout padrão, container 1200px |
| Tablet (≤ 1024px) | Grid de motivos 2 col., footer 3 col. |
| Mobile (≤ 768px) | Hamburger menu, hero altura auto, grids 1 col., flex-direction column nas seções 5/6/8 |
| Small (≤ 480px) | Font sizes menores, footer 1 col. |

---

## Deploy

O deploy é feito via **Vercel API** diretamente (o webhook do GitHub está com instabilidade).

### Script de deploy (via terminal)

```bash
# No diretório do projeto
python3 deploy.py
```

Ou manualmente pelo painel Vercel:
1. [vercel.com](https://vercel.com) → projeto `site-wm-trading`
2. **Deployments** → deployment mais recente com status **Ready** → `...` → **Redeploy**

### Variáveis relevantes

| Item | Valor |
|---|---|
| Team ID | `team_N6WpTE1iUJs2iEGSaJDGd4qL` |
| Project ID | `prj_fGGQyZwgwW2eQWIK9Rm4DirhNuaa` |
| Produção | `https://site-wm-trading.vercel.app` |

---

## Notas importantes

- **Vídeos** estão excluídos do git e do deploy (`.gitignore` / `.vercelignore`) — arquivos `.mov` e `.mp4` são muito grandes
- **Nomes de arquivo** devem usar apenas caracteres ASCII (sem acentos, sem espaços) para funcionar corretamente no Vercel
- **Imagens do hero e segmentos** estão em `images/assets/`
