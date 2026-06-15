# WM Trading — Fundamentos da Marca (Brandbook)

> Camada **reutilizável** do design system: tudo que é constante em qualquer
> página (home, landing pages, e-mails). **Não** define diagramação, seções
> nem imagens — isso é responsabilidade de cada página/documento de layout.

**Arquivos:** `css/variables.css` (tokens) + `css/foundations.css` (primitivas)
**Slogan:** *We Make it better* · **No ar desde:** 2004

---

## 1. Logotipo

| Variação | Arquivo | Uso |
|---|---|---|
| Logo laranja | `images/logo/fechado_logo_wm_trading_ajustada_logo_laranja.png` | Header, fundos claros |
| Logo + slogan colorido | `images/logo/fechado_logo_wm_trading_ajustada_logo_slogan_colorido.png` | Footer, materiais |
| WM (símbolo) | `images/logo/WM.svg` | Favicon, decoração, padrões |
| WM Letras | `images/logo/WM Letras.svg` | Marca-d'água, decoração |

**Regras:** altura mínima 44px · sempre manter área de respiro · nunca distorcer,
recolorir fora da paleta ou aplicar sombra. Em fundo escuro/laranja, usar a versão
branca; em fundo claro, a laranja.

---

## 2. Cores

| Token | Hex | Uso |
|---|---|---|
| `--color-primary` | `#FC5000` | Laranja WM — CTAs, destaques, links, ícones |
| (hover) | `#E04700` | Estado hover dos botões/links |
| `--color-primary-light` | `#FFEBE0` | Fundo suave laranja |
| `--color-text-dark` | `#3A3A3A` | Texto principal |
| `--color-text-muted` | `#888888` | Texto secundário |
| `--color-text-white` | `#FFFFFF` | Texto sobre fundo escuro/laranja |
| `--color-bg-white` | `#FFFFFF` | Fundo padrão |
| `--color-bg-light` | `#F5F5F5` | Fundo alternado de seção |
| `--color-bg-dark` | `#1A1A1A` | Fundos escuros (hero, faixas) |

Laranja é a cor de ação e deve aparecer com parcimônia (CTAs, destaques de título,
ícones). Fundos escuros usam `#1A1A1A`; nunca preto puro.

---

## 3. Tipografia

| Família | Uso | Pesos |
|---|---|---|
| **Poppins** | Tudo (corpo, títulos, UI, botões) | 300 / 400 / 500 / 600 / 700 |
| **Nunito Sans** | Destaques especiais pontuais | 800 |

```html
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&family=Nunito+Sans:wght@800&display=swap" rel="stylesheet" />
```

**Assinatura tipográfica:** títulos grandes em **peso leve (300)**. Reforço/realce
no título via `<span class="text-primary">` (laranja).

| Token | px | Uso típico | Classe utilitária |
|---|---|---|---|
| `--fs-xs` | 12 | labels, eyebrow, captions | — |
| `--fs-sm` | 14 | texto corrido, UI | `.t-body` |
| `--fs-base` | 16 | corpo | — |
| `--fs-md` | 18 | lead/destaque | `.t-lead` |
| `--fs-lg` | 27 | subtítulos | `.t-h3` (semibold) |
| `--fs-xl` | 32 | títulos de seção | `.t-h2` (light) |
| `--fs-2xl` | 56 | título hero (desktop) | `.t-display` (light) |
| `--fs-3xl` | 72 | números/KPIs | — |

No mobile (≤768px) o sistema reduz: `--fs-2xl` 34 · `--fs-xl` 26 · `--fs-lg` 22.

---

## 4. Bordas e raios

| Token | Valor | Uso |
|---|---|---|
| `--radius-sm` | 4px | tags, detalhes |
| `--radius-md` | 10px | inputs, ícones-selo |
| `--radius-lg` | 16px | cards |
| `--radius-xl` | 24px | painéis/medias grandes |
| `--radius-full` | 9999px | pílulas |
| Botões | 8px | padrão `.btn` |

Bordas sutis de divisão: `1px solid #efefef` (cards) e `#e8e8e8` (divisores).

---

## 5. Sombras e elevação

| Token | Valor | Uso |
|---|---|---|
| `--shadow-card` | `0 2px 16px rgba(0,0,0,0.07)` | cards e elevação leve |
| Foco de input | `0 0 0 3px rgba(252,80,0,0.12)` | estado :focus |

---

## 6. Espaçamento

| Token | Valor |
|---|---|
| `--container-width` | 1200px |
| `--container-px` | 80px (desktop) → 40px (≤1024) → 20px (mobile) |
| `--section-py` | 80px (desktop) → 56px (mobile) |
| `--transition` | 0.2s ease |

---

## 7. Botões (primitivas — `foundations.css`)

| Classe | Aparência |
|---|---|
| `.btn` | sólido laranja, texto branco, raio 8px (hover `#E04700`) |
| `.btn-outline` | contorno laranja, preenche no hover |
| `.btn-white` | fundo branco, texto laranja (para fundos escuros/laranja) |
| `.btn-ghost-light` | contorno branco translúcido (sobre fundo escuro) |
| `.btn-lg` | variação maior |
| `.link-arrow` | link laranja com seta |

---

## 8. Ícones

Estilo **linha (stroke 2)**, cantos arredondados (família Lucide/Feather), 24×24.
Em destaque: dentro de **selo quadrado laranja** com glifo branco (`.ico-badge`).

---

## 9. Componentes utilitários reutilizáveis

`.eyebrow` (rótulo laranja em caixa-alta) · `.reveal` (entrada com blur ao rolar)
· `.field` (campo de formulário) · `.container` · superfícies `.surface`,
`.surface-light`, `.surface-dark`, `.surface-primary`.

---

> **Diagramação, seções e imagens não pertencem a este documento.**
> Cada página define seu próprio layout consumindo estes fundamentos.
> Guia de LPs: [`02-design-landing-pages.md`](02-design-landing-pages.md).
