# WM Trading — Design de Landing Pages

> Diretrizes de **layout e composição** para landing pages de campanha.
> Herda 100% dos [Fundamentos da Marca](01-fundamentos-da-marca.md)
> (fontes, cores, tamanhos, bordas, sombras, botões), mas tem **diagramação
> e imagens próprias** — uma LP **não** replica o layout da home.

---

## Princípio

Uma LP é uma página de **conversão**, não institucional. Objetivo único:
gerar leads qualificados. Logo, a estrutura é diferente da home:

- **Foco em uma única oferta** e um único CTA repetido (ex.: "Solicitar Cotação").
- **Formulário acima da dobra** sempre que possível.
- **Caminho linear** de leitura: problema → solução → prova → ação.
- **Sem menu de navegação completo** do site (header enxuto, só âncoras + CTA).
- Layout, ritmo de seções e imagens são **exclusivos da LP**.

---

## O que herdar dos Fundamentos (obrigatório)

`variables.css` + `reset.css` + `foundations.css`. Disso vêm: Poppins/Nunito,
laranja `#FC5000`, escala de tamanhos, raios, sombras, `.btn`, `.field`,
`.eyebrow`, `.reveal`, `.container`, logotipos.

```html
<link rel="stylesheet" href="../css/variables.css" />
<link rel="stylesheet" href="../css/reset.css" />
<link rel="stylesheet" href="../css/foundations.css" />
<link rel="stylesheet" href="lp.css" />   <!-- layout próprio da LP -->
```

> ❌ **Não** importar `css/main.css` nem `css/responsive.css` — eles são a
> diagramação **da home**. A LP escreve seu próprio layout em `lp.css`.

---

## O que é próprio de cada LP

- **Diagramação** (grid das seções, hero, blocos de conversão).
- **Imagens**: geradas/escolhidas para o tema da campanha — **não** reutilizar
  as fotos da home (autopeças, aço, solar, prédio, CEO).
- **Textos** e CTAs específicos da oferta.

### Imagens on-brand
Quando não houver foto oficial do tema, usar **gráficos da identidade** (fundos
escuros `#1A1A1A` com glow laranja `#FC5000`, padrão zigzag "WM", grid sutil,
arcos/rotas). Exemplos versionados em `importacao-carne-suina/assets/`
(`hero-bg.jpg`, `mercados.jpg`, `produto.jpg`, `og-image.jpg`).

---

## Estrutura recomendada (ordem)

1. **Header enxuto** — logo + âncoras + CTA (sem mega-menu).
2. **Hero** — H1 (peso leve, realce laranja) + subtítulo + 3 benefícios + CTA
   primário/secundário. Fundo gráfico on-brand. (Opcional: formulário à direita.)
3. **Barra de confiança** — selos/dados (anos, filiais, ISO, canal verde).
4. **Problema/Desafios** — cards.
5. **Solução/Processo** — etapas numeradas.
6. **Sobre a oferta** — texto + visual on-brand.
7. **Benefícios** — grid de cards.
8. **Mercados/Alcance** — dado + visual.
9. **Diferenciais**.
10. **Prova social** — números + depoimentos.
11. **FAQ** — otimizado para SEO/GEO (acordeão + JSON-LD `FAQPage`).
12. **CTA final + Formulário** — campos: Nome, Empresa, Cargo, E-mail, Telefone,
    Volume, Mensagem.
13. **Footer enxuto**.

Flutuantes de CRO: **WhatsApp** fixo + **CTA sticky** no mobile.

---

## SEO / GEO / CRO

- **Meta** title/description, canonical, Open Graph + `og:image` (1200×630).
- **JSON-LD**: `Organization`, `Service`, `FAQPage`, `BreadcrumbList`.
- **GEO**: linguagem factual, perguntas/respostas objetivas, entidades nomeadas.
- **CRO**: um CTA dominante repetido; formulário curto; provas próximas do CTA.

---

## Ritmo visual

- Alternar superfícies `#FFFFFF` ↔ `#F5F5F5`; usar `#1A1A1A` ou `#FC5000` em
  1–2 seções de impacto (hero, KPIs, CTA final).
- Títulos de seção centralizados, peso leve, com realce laranja em 1 palavra.
- `--section-py` entre seções; `.reveal` para entrada suave.

---

## Convenção de pastas

```
site-wm-trading/
├── css/                         # Fundamentos (compartilhado)
│   ├── variables.css            # tokens
│   └── foundations.css          # primitivas de marca
├── docs/                        # Este design system
│   ├── 01-fundamentos-da-marca.md
│   └── 02-design-landing-pages.md
└── <slug-da-lp>/                # uma pasta por LP
    ├── index.html
    ├── lp.css                   # layout próprio da LP
    └── assets/                  # imagens próprias da LP
```
