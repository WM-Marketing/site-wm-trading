# -*- coding: utf-8 -*-
"""
Gráficos editoriais da WM Trading, desenhados em SVG no build.

Até 14/10/2026 esses gráficos eram um <canvas> do Chart.js. Os números só
existiam dentro do <script> e, na tela, viravam pixels. Quem não executa
JavaScript — GPTBot, ClaudeBot, PerplexityBot — encontrava uma figura vazia; o
Googlebot, que executa, indexava uma imagem sem texto. O dado próprio de cada
pauta, a série do Comex Stat, ficava invisível para busca e para resposta de IA.

Agora o SVG sai escrito no HTML final: meses e valores em <text>, um <desc> que
lê o gráfico em palavras e uma tabela com a série inteira. Nada depende do
navegador. A validação é `curl <url> | grep <valor>`: se o número não estiver
lá, o gráfico voltou a ser imagem.

Uma série nova entra só aqui, no dicionário GRAFICOS. O build_pages.py expande
{{wm-chart:chave}} chamando grafico_svg(chave).
"""
import math
from html import escape

LARANJA = "#ff5a1f"
AZUL = "#133b5c"
CINZA = "#8b8b8b"
COR_GRADE = "#e5e5e5"
COR_EIXO = "#6b6b6b"
COR_VALOR = "#1f1f1f"

FONTE_PADRAO = "Fonte: MDIC/Comex Stat"
MILHOES_USD = {"prefixo": "US$ ", "sufixo": " mi", "casas": 1, "casas_eixo": 0}
PERCENTUAL = {"prefixo": "", "sufixo": "%", "casas": 1, "casas_eixo": 0}


# ---------------------------------------------------------------------------
# Séries. Os números vêm do Comex Stat e são a matéria-prima do post: mudar um
# valor aqui muda o gráfico, a tabela, a leitura em <desc> e o que o robô lê.
# ---------------------------------------------------------------------------
MESES_24 = ["set./24", "out./24", "nov./24", "dez./24", "jan./25", "fev./25", "mar./25", "abr./25",
            "mai./25", "jun./25", "jul./25", "ago./25", "set./25", "out./25", "nov./25", "dez./25",
            "jan./26", "fev./26", "mar./26", "abr./26", "mai./26", "jun./26", "jul./26", "ago./26"]
MESES_AGO25_JUL26 = ["ago./25", "set./25", "out./25", "nov./25", "dez./25", "jan./26",
                     "fev./26", "mar./26", "abr./26", "mai./26", "jun./26", "jul./26"]

GRAFICOS = {
    "aco-set-2026": {
        "tipo": "linha",
        "titulo": "Importação mensal de produtos siderúrgicos e obras de ferro ou aço",
        "fonte": "Fonte: MDIC/Comex Stat.",
        "unidade": MILHOES_USD,
        "rotulo_x": "Mês",
        "labels": MESES_24,
        "series": [
            {"label": "Produtos siderúrgicos", "cor": LARANJA,
             "data": [494.61, 476.94, 338.01, 291, 462.05, 377.24, 483.02, 409.98, 502.47, 471.28,
                      471.05, 368.37, 334.47, 362.31, 351.42, 293.75, 407.25, 421.95, 415.49,
                      302.03, 251.27, 365.99, 316.96, 317.1]},
            {"label": "Obras de ferro ou aço", "cor": AZUL,
             "data": [373.68, 395.51, 321.19, 359.93, 397.01, 410.1, 342.17, 353.41, 347.54, 353.98,
                      415.09, 378.17, 409.91, 394.07, 309.19, 344.37, 385.81, 328.79, 506.52,
                      379.05, 366.15, 488.39, 402.18, 473.3]},
        ],
    },
    "maquinas-aditivas-set-2026": {
        "tipo": "linha",
        "titulo": "Importação mensal de máquinas para fabricação aditiva por depósito de plástico ou borracha",
        "fonte": "Fonte: MDIC/Comex Stat.",
        "unidade": MILHOES_USD,
        "rotulo_x": "Mês",
        "labels": MESES_24,
        "series": [
            {"label": "Máquinas por depósito de plástico ou borracha", "cor": LARANJA, "area": True,
             "data": [2.92, 1.82, 1.6, 1.89, 2.5, 1.26, 1.71, 1.9, 2.08, 2.9, 1.83, 3.97, 5.82,
                      6.82, 4.48, 3.69, 3.22, 4.76, 6.46, 5.55, 10.62, 13.21, 11.8, 21.58]},
        ],
    },
    "ciclos-eletricos-set-2026": {
        "tipo": "linha",
        "titulo": "Importação mensal de ciclos com motor elétrico para propulsão",
        "fonte": "Fonte: MDIC/Comex Stat.",
        "unidade": MILHOES_USD,
        "rotulo_x": "Mês",
        "labels": MESES_24,
        "series": [
            {"label": "Ciclos com motor elétrico para propulsão", "cor": LARANJA, "area": True,
             "destaque": [22, 23],
             "data": [3.83, 5.75, 6.09, 6.03, 6.19, 6.11, 5.7, 4.25, 4.65, 7.46, 9.41, 12.37,
                      11.13, 11.48, 14.24, 19.58, 14.02, 10.49, 16.69, 14.01, 14.89, 14.74,
                      25.39, 25.87]},
        ],
    },
    "instrumentos-analise-set-2026": {
        "tipo": "linha",
        "titulo": "Importação mensal de instrumentos e aparelhos para análises físicas ou químicas",
        "fonte": "Fonte: MDIC/Comex Stat.",
        "unidade": MILHOES_USD,
        "rotulo_x": "Mês",
        "labels": MESES_24,
        "series": [
            {"label": "Instrumentos e aparelhos para análises físicas ou químicas", "cor": LARANJA,
             "area": True,
             "data": [82.87, 71.63, 66.88, 78.12, 63.27, 78.58, 69.6, 78.82, 78.6, 81.9, 87.52,
                      80.02, 94.01, 85.03, 76.23, 88.52, 83.25, 81.51, 88.31, 87.24, 86.14,
                      97.12, 99.13, 100.58]},
        ],
    },
    "autos-8703": {
        "tipo": "linha",
        "titulo": "Importação mensal de automóveis de passageiros",
        "fonte": "Valores FOB em US$ milhões. Fonte: MDIC/Comex Stat.",
        "unidade": {"prefixo": "US$ ", "sufixo": " mi", "casas": 2, "casas_eixo": 0},
        "rotulo_x": "Mês",
        "zero": True,
        "labels": ["jul./25", "ago./25", "set./25", "out./25", "nov./25", "dez./25",
                   "jan./26", "fev./26", "mar./26", "abr./26", "mai./26", "jun./26"],
        "series": [
            {"label": "Valor FOB (US$ milhões)", "cor": LARANJA, "area": True,
             "data": [321.38, 405.49, 484.00, 601.14, 785.16, 678.75, 564.20, 559.68,
                      1125.77, 1249.62, 1873.87, 2416.53]},
        ],
    },
    "camisetas-mensal": {
        "tipo": "linha",
        "titulo": "Importação mensal de T-shirts e camisetas de malha",
        "fonte": FONTE_PADRAO,
        "unidade": MILHOES_USD,
        "rotulo_x": "Mês",
        "labels": MESES_AGO25_JUL26,
        "series": [
            {"label": "Valor FOB (US$ milhões)", "cor": LARANJA, "area": True,
             "data": [21.1, 19.8, 28.1, 22.5, 20.6, 29.6, 21.0, 22.1, 21.9, 19.1, 22.6, 25.1]},
        ],
    },
    "baterias-mensal": {
        "tipo": "linha",
        "titulo": "Importação mensal de baterias e acumuladores elétricos",
        "fonte": FONTE_PADRAO,
        "unidade": MILHOES_USD,
        "rotulo_x": "Mês",
        "labels": MESES_AGO25_JUL26,
        "series": [
            {"label": "Valor FOB (US$ milhões)", "cor": LARANJA, "area": True,
             "data": [71.4, 83.8, 75.9, 76.7, 67.6, 87.4, 76.7, 97.6, 97.2, 128.2, 97.0, 99.7]},
        ],
    },
    "platina-mensal": {
        "tipo": "linha",
        "titulo": "Importação mensal de platina bruta",
        "fonte": FONTE_PADRAO,
        "unidade": MILHOES_USD,
        "rotulo_x": "Mês",
        "labels": MESES_AGO25_JUL26,
        "series": [
            {"label": "Valor FOB (US$ milhões)", "cor": LARANJA, "area": True,
             "data": [12.4, 25.8, 11.2, 10.9, 22.8, 28.5, 35.9, 22.7, 18.1, 30.9, 33.1, 44.9]},
        ],
    },
    "ginastica-mensal": {
        "tipo": "linha",
        "titulo": "Importação mensal de equipamentos para cultura física e ginástica",
        "fonte": FONTE_PADRAO,
        "unidade": MILHOES_USD,
        "rotulo_x": "Mês",
        "labels": MESES_AGO25_JUL26,
        "series": [
            {"label": "Valor FOB (US$ milhões)", "cor": LARANJA, "area": True,
             "data": [21.3, 20.2, 29.8, 30.3, 34.4, 31.3, 21.9, 31.4, 30.1, 24.6, 29.9, 35.1]},
        ],
    },
    "platina-origens": {
        "tipo": "barra",
        "titulo": "Principais origens da platina bruta importada pelo Brasil",
        "fonte": FONTE_PADRAO,
        "unidade": PERCENTUAL,
        "rotulo_x": "Origem",
        "maximo": 100,
        "labels": ["África do Sul", "Bélgica", "Estados Unidos"],
        "series": [
            {"label": "Participação no valor importado",
             "cores": [LARANJA, "#6e6e6e", AZUL],
             "data": [69.7, 17.7, 7.7]},
        ],
    },
    "camisetas-origens": {
        "tipo": "composicao",
        "titulo": "Composição por fibra e valor médio por quilo, por origem",
        "fonte": FONTE_PADRAO,
        "unidade": {"prefixo": "", "sufixo": "%", "casas": 0, "casas_eixo": 0},
        "rotulo_x": "Origem",
        "labels": ["China", "Peru", "Bangladesh"],
        "series": [
            {"label": "Algodão (%)", "cor": LARANJA, "data": [29, 99, 85]},
            {"label": "Outras fibras (%)", "cor": CINZA, "data": [71, 1, 15]},
        ],
        "linha": {"label": "Valor médio (US$/kg)", "cor": AZUL, "data": [11.3, 27.7, 16.9],
                  "unidade": {"prefixo": "US$ ", "sufixo": "/kg", "casas": 1, "casas_eixo": 0}},
    },
}


# ---------------------------------------------------------------------------
# Números e escala
# ---------------------------------------------------------------------------
def numero(valor, casas):
    """1234.5 -> '1.234,5'. O separador do leitor, não o do Python."""
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def formata(valor, unidade, eixo=False):
    casas = unidade["casas_eixo"] if eixo else unidade["casas"]
    return f'{unidade["prefixo"]}{numero(valor, casas)}{unidade["sufixo"]}'


def escala(valores, do_zero=False, maximo=None):
    """Mínimo, máximo e marcas do eixo Y em passos redondos."""
    menor, maior = min(valores), max(valores)
    if do_zero or menor > 0 and menor / maior < 0.35:
        menor = 0
    if maximo is not None:
        return 0, maximo, [maximo * i / 5 for i in range(6)]
    vao = maior - menor or abs(maior) or 1
    bruto = vao / 6
    magnitude = 10 ** math.floor(math.log10(bruto))
    passo = next(m * magnitude for m in (1, 2, 2.5, 5, 10) if m * magnitude >= bruto)
    base = math.floor(menor / passo) * passo
    topo = math.ceil(maior / passo) * passo
    marcas = [base + i * passo for i in range(int(round((topo - base) / passo)) + 1)]
    return base, topo, marcas


def caminho_suave(pontos, tensao=0.32):
    """Catmull-Rom convertido em bézier, para manter a curva que o Chart.js desenhava."""
    if len(pontos) < 2:
        return ""
    partes = [f"M {pontos[0][0]:.1f} {pontos[0][1]:.1f}"]
    for i in range(len(pontos) - 1):
        p0 = pontos[i - 1] if i else pontos[i]
        p1, p2 = pontos[i], pontos[i + 1]
        p3 = pontos[i + 2] if i + 2 < len(pontos) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) * tensao / 2, p1[1] + (p2[1] - p0[1]) * tensao / 2)
        c2 = (p2[0] - (p3[0] - p1[0]) * tensao / 2, p2[1] - (p3[1] - p1[1]) * tensao / 2)
        partes.append(f"C {c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}")
    return " ".join(partes)


# ---------------------------------------------------------------------------
# Leitura em palavras e tabela: é o que o robô sem JavaScript encontra
# ---------------------------------------------------------------------------
def descricao_numerica(spec):
    unidade = spec["unidade"]
    labels = spec["labels"]
    frases = []
    if spec["tipo"] in ("barra", "composicao"):
        for serie in spec["series"]:
            itens = ", ".join(f"{labels[i]} {formata(v, unidade)}" for i, v in enumerate(serie["data"]))
            prefixo = f'{serie["label"]}: ' if len(spec["series"]) > 1 else ""
            frases.append(f"{prefixo}{itens}")
        if spec.get("linha"):
            linha = spec["linha"]
            itens = ", ".join(f"{labels[i]} {formata(v, linha['unidade'])}"
                              for i, v in enumerate(linha["data"]))
            frases.append(f'{linha["label"]}: {itens}')
        return ". ".join(frases) + "."
    for serie in spec["series"]:
        dados = serie["data"]
        i_max = dados.index(max(dados))
        i_min = dados.index(min(dados))
        rumo = "subiu de" if dados[-1] >= dados[0] else "caiu de"
        prefixo = f'{serie["label"]}: ' if len(spec["series"]) > 1 else ""
        frases.append(
            f'{prefixo}{rumo} {formata(dados[0], unidade)} em {labels[0]} '
            f'para {formata(dados[-1], unidade)} em {labels[-1]}; '
            f'maior mês {labels[i_max]} ({formata(dados[i_max], unidade)}), '
            f'menor mês {labels[i_min]} ({formata(dados[i_min], unidade)})'
        )
    texto = ". ".join(frases) + "."
    return texto[0].upper() + texto[1:]


def tabela_dados(spec):
    unidade = spec["unidade"]
    colunas = [serie["label"] for serie in spec["series"]]
    if spec.get("linha"):
        colunas.append(spec["linha"]["label"])
    cabecalho = "".join(f"<th scope=\"col\">{escape(c)}</th>" for c in colunas)
    linhas = []
    for i, rotulo in enumerate(spec["labels"]):
        celulas = "".join(f"<td>{escape(formata(s['data'][i], unidade))}</td>" for s in spec["series"])
        if spec.get("linha"):
            celulas += f"<td>{escape(formata(spec['linha']['data'][i], spec['linha']['unidade']))}</td>"
        linhas.append(f'<tr><th scope="row">{escape(rotulo)}</th>{celulas}</tr>')
    return (
        '<details class="wm-chart-dados"><summary>Ver os dados em tabela</summary>'
        f'<table><caption>{escape(spec["titulo"])}</caption>'
        f'<thead><tr><th scope="col">{escape(spec.get("rotulo_x", "Período"))}</th>{cabecalho}</tr></thead>'
        f'<tbody>{"".join(linhas)}</tbody></table></details>'
    )


# ---------------------------------------------------------------------------
# Desenho
# ---------------------------------------------------------------------------
ALTURA = 340
MARGEM_SUP = 22
MARGEM_DIR = 22
MARGEM_INF = 50


def _moldura(spec):
    n = len(spec["labels"])
    largura = 980 if n > 12 else 760
    fonte = 15 if largura > 800 else 12
    tem_legenda = len(spec["series"]) > 1 or bool(spec.get("linha"))
    valores = [v for serie in spec["series"] for v in serie["data"]]
    base, topo, marcas = escala(valores, spec.get("zero", False), spec.get("maximo"))
    casas = 1 if any(abs(mk - round(mk)) > 1e-9 for mk in marcas) else 0
    maior_rotulo = max(len(formata(mk, dict(spec["unidade"], casas_eixo=casas), eixo=True))
                       for mk in marcas)
    margem_esq = int(maior_rotulo * fonte * 0.58) + 16
    margem_dir = 92 if spec.get("linha") else MARGEM_DIR
    inferior = MARGEM_INF + (24 if tem_legenda else 0)
    return {
        "largura": largura, "altura": ALTURA, "fonte": fonte,
        "x0": margem_esq, "x1": largura - margem_dir,
        "y0": MARGEM_SUP, "y1": ALTURA - inferior,
        "legenda": tem_legenda,
    }


def _grade(m, base, topo, marcas, unidade, clip_id):
    if any(abs(marca - round(marca)) > 1e-9 for marca in marcas):
        unidade = dict(unidade, casas_eixo=1)
    partes = [f'<clipPath id="{clip_id}"><rect x="{m["x0"]}" y="{m["y0"] - 6}" '
              f'width="{m["x1"] - m["x0"]}" height="{m["y1"] - m["y0"] + 6}"/></clipPath>']
    for marca in marcas:
        y = m["y1"] - (marca - base) / (topo - base) * (m["y1"] - m["y0"])
        partes.append(f'<line x1="{m["x0"]}" y1="{y:.1f}" x2="{m["x1"]}" y2="{y:.1f}" '
                      f'stroke="{COR_GRADE}" stroke-width="1"/>')
        partes.append(f'<text x="{m["x0"] - 10}" y="{y + 4:.1f}" text-anchor="end" '
                      f'font-size="{m["fonte"]}" fill="{COR_EIXO}">{escape(formata(marca, unidade, eixo=True))}</text>')
    return partes


def _rotulos_x(m, labels, xs):
    largura_rotulo = max(len(r) for r in labels) * m["fonte"] * 0.58
    cabem = max(2, int((m["x1"] - m["x0"]) / (largura_rotulo * 1.25)))
    passo = max(1, math.ceil(len(labels) / cabem))
    ultimo = len(labels) - 1
    visiveis = [i for i in range(0, ultimo + 1, passo)]
    if visiveis[-1] != ultimo:
        if ultimo - visiveis[-1] < passo:
            visiveis.pop()
        visiveis.append(ultimo)
    partes = []
    for i, rotulo in enumerate(labels):
        if i not in visiveis:
            continue
        ancora = "start" if i == 0 else ("end" if i == ultimo else "middle")
        partes.append(f'<text x="{xs[i]:.1f}" y="{m["y1"] + 22}" text-anchor="{ancora}" '
                      f'font-size="{m["fonte"]}" fill="{COR_EIXO}">{escape(rotulo)}</text>')
    return partes


def _legenda(m, itens):
    partes = []
    x = m["x0"]
    y = m["y1"] + 46
    for rotulo, cor in itens:
        partes.append(f'<circle cx="{x + 5}" cy="{y - 4}" r="5" fill="{cor}"/>')
        partes.append(f'<text x="{x + 16}" y="{y}" font-size="{m["fonte"]}" fill="{COR_EIXO}">{escape(rotulo)}</text>')
        x += 26 + len(rotulo) * (m["fonte"] * 0.55)
    return partes


def _grafico_linha(spec, m, clip_id):
    unidade = spec["unidade"]
    labels = spec["labels"]
    todos = [v for s in spec["series"] for v in s["data"]]
    base, topo, marcas = escala(todos, do_zero=spec.get("zero", False))
    n = len(labels)
    xs = [m["x0"] + i * (m["x1"] - m["x0"]) / (n - 1) for i in range(n)]

    def y_de(v):
        return m["y1"] - (v - base) / (topo - base) * (m["y1"] - m["y0"])

    partes = _grade(m, base, topo, marcas, unidade, clip_id)
    partes += _rotulos_x(m, labels, xs)
    partes.append(f'<line x1="{m["x0"]}" y1="{m["y1"]}" x2="{m["x1"]}" y2="{m["y1"]}" '
                  f'stroke="#cfcfcf" stroke-width="1"/>')

    for serie in spec["series"]:
        pontos = [(xs[i], y_de(v)) for i, v in enumerate(serie["data"])]
        caminho = caminho_suave(pontos)
        if serie.get("area"):
            fechado = f'{caminho} L {pontos[-1][0]:.1f} {m["y1"]} L {pontos[0][0]:.1f} {m["y1"]} Z'
            partes.append(f'<path d="{fechado}" fill="{serie["cor"]}" fill-opacity="0.16" '
                          f'clip-path="url(#{clip_id})"/>')
        partes.append(f'<path d="{caminho}" fill="none" stroke="{serie["cor"]}" stroke-width="3" '
                      f'stroke-linecap="round" stroke-linejoin="round" clip-path="url(#{clip_id})"/>')
        destaque = set(serie.get("destaque", []))
        for i, (px, py) in enumerate(pontos):
            raio = 6 if i in destaque else 4
            cor = AZUL if i in destaque else serie["cor"]
            rotulo = f'{labels[i]}: {formata(serie["data"][i], unidade)}'
            if len(spec["series"]) > 1:
                rotulo = f'{serie["label"]} — {rotulo}'
            partes.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{raio}" fill="{cor}" '
                          f'stroke="#fff" stroke-width="1.5"><title>{escape(rotulo)}</title></circle>')

    escritos = []
    for serie in spec["series"]:
        dados = serie["data"]
        chaves = {len(dados) - 1}
        if len(spec["series"]) == 1:
            chaves |= {0, dados.index(max(dados)), dados.index(min(dados))}
        for i in sorted(chaves, key=lambda k: (k not in (0, len(dados) - 1), k)):
            px, py = xs[i], y_de(dados[i])
            acima = py - m["y0"] > 26
            if any(abs(px - ex) < 78 and abs(py - ey) < 18 for ex, ey in escritos):
                continue
            escritos.append((px, py))
            ancora = "start" if i == 0 else ("end" if i == len(dados) - 1 else "middle")
            dx = 4 if i == 0 else (-4 if i == len(dados) - 1 else 0)
            partes.append(
                f'<text x="{px + dx:.1f}" y="{py + (-12 if acima else 20):.1f}" text-anchor="{ancora}" '
                f'font-size="{m["fonte"] + 1}" font-weight="700" fill="{COR_VALOR}" paint-order="stroke" '
                f'stroke="#fff" stroke-width="3">{escape(formata(dados[i], unidade))}</text>'
            )

    if m["legenda"]:
        partes += _legenda(m, [(s["label"], s["cor"]) for s in spec["series"]])
    return partes


def _grafico_barra(spec, m, clip_id):
    unidade = spec["unidade"]
    labels = spec["labels"]
    serie = spec["series"][0]
    base, topo, marcas = escala(serie["data"], do_zero=True, maximo=spec.get("maximo"))
    n = len(labels)
    faixa = (m["x1"] - m["x0"]) / n
    xs = [m["x0"] + faixa * (i + 0.5) for i in range(n)]
    largura_barra = min(96, faixa * 0.46)

    partes = _grade(m, base, topo, marcas, unidade, clip_id)
    partes += _rotulos_x(m, labels, xs)
    for i, valor in enumerate(serie["data"]):
        altura = (valor - base) / (topo - base) * (m["y1"] - m["y0"])
        y = m["y1"] - altura
        cor = serie.get("cores", [serie.get("cor", LARANJA)] * n)[i]
        partes.append(f'<rect x="{xs[i] - largura_barra / 2:.1f}" y="{y:.1f}" width="{largura_barra:.1f}" '
                      f'height="{altura:.1f}" rx="5" fill="{cor}">'
                      f'<title>{escape(f"{labels[i]}: {formata(valor, unidade)}")}</title></rect>')
        partes.append(f'<text x="{xs[i]:.1f}" y="{y - 10:.1f}" text-anchor="middle" font-size="13" '
                      f'font-weight="700" fill="{COR_VALOR}">{escape(formata(valor, unidade))}</text>')
    partes.append(f'<line x1="{m["x0"]}" y1="{m["y1"]}" x2="{m["x1"]}" y2="{m["y1"]}" '
                  f'stroke="#cfcfcf" stroke-width="1"/>')
    return partes


def _grafico_composicao(spec, m, clip_id):
    """Barras empilhadas em 100% com uma linha de preço no eixo da direita."""
    unidade = spec["unidade"]
    labels = spec["labels"]
    linha = spec["linha"]
    base, topo, marcas = escala([0, 100], do_zero=True, maximo=100)
    n = len(labels)
    faixa = (m["x1"] - m["x0"]) / n
    xs = [m["x0"] + faixa * (i + 0.5) for i in range(n)]
    largura_barra = min(110, faixa * 0.5)

    partes = _grade(m, base, topo, marcas, unidade, clip_id)
    partes += _rotulos_x(m, labels, xs)

    # Eixo da direita, o do valor por quilo.
    teto_preco = math.ceil(max(linha["data"]) / 10) * 10
    for k in range(5):
        valor = teto_preco * k / 4
        y = m["y1"] - (valor / teto_preco) * (m["y1"] - m["y0"])
        partes.append(f'<text x="{m["x1"] + 10}" y="{y + 4:.1f}" font-size="12" fill="{COR_EIXO}">'
                      f'{escape(formata(valor, linha["unidade"], eixo=True))}</text>')

    for i in range(n):
        acumulado = 0.0
        for serie in spec["series"]:
            valor = serie["data"][i]
            rotulo = f'{labels[i]} — {serie["label"]}: {formata(valor, unidade)}'
            altura = valor / 100 * (m["y1"] - m["y0"])
            y = m["y1"] - (acumulado / 100 * (m["y1"] - m["y0"])) - altura
            partes.append(f'<rect x="{xs[i] - largura_barra / 2:.1f}" y="{y:.1f}" '
                          f'width="{largura_barra:.1f}" height="{altura:.1f}" fill="{serie["cor"]}">'
                          f'<title>{escape(rotulo)}</title></rect>')
            if altura > 22:
                partes.append(f'<text x="{xs[i]:.1f}" y="{y + altura / 2 + 5:.1f}" text-anchor="middle" '
                              f'font-size="13" font-weight="700" fill="#fff">'
                              f'{escape(formata(valor, unidade))}</text>')
            acumulado += valor

    pontos = [(xs[i], m["y1"] - linha["data"][i] / teto_preco * (m["y1"] - m["y0"])) for i in range(n)]
    partes.append(f'<path d="{caminho_suave(pontos, 0.25)}" fill="none" stroke="{linha["cor"]}" '
                  f'stroke-width="3" stroke-linecap="round"/>')
    for i, (px, py) in enumerate(pontos):
        texto = formata(linha["data"][i], linha["unidade"])
        rotulo_linha = f'{labels[i]} — {linha["label"]}: {texto}'
        partes.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="5" fill="{linha["cor"]}" stroke="#fff" '
                      f'stroke-width="1.5"><title>{escape(rotulo_linha)}</title></circle>')
        partes.append(f'<text x="{px:.1f}" y="{py - 13:.1f}" text-anchor="middle" font-size="12" '
                      f'font-weight="700" fill="{COR_VALOR}" paint-order="stroke" stroke="#fff" '
                      f'stroke-width="3">{escape(texto)}</text>')

    partes.append(f'<line x1="{m["x0"]}" y1="{m["y1"]}" x2="{m["x1"]}" y2="{m["y1"]}" '
                  f'stroke="#cfcfcf" stroke-width="1"/>')
    partes += _legenda(m, [(s["label"], s["cor"]) for s in spec["series"]] + [(linha["label"], linha["cor"])])
    return partes


DESENHOS = {"linha": _grafico_linha, "barra": _grafico_barra, "composicao": _grafico_composicao}


def grafico_svg(chave):
    """O gráfico inteiro — SVG, leitura em <desc> e tabela — pronto para o HTML."""
    spec = GRAFICOS[chave]
    m = _moldura(spec)
    id_titulo, id_desc, id_clip = f"g-{chave}-t", f"g-{chave}-d", f"g-{chave}-c"
    corpo = DESENHOS[spec["tipo"]](spec, m, id_clip)
    descricao = descricao_numerica(spec)
    svg = (
        f'<svg class="wm-chart-svg{" wm-chart-svg--largo" if m["largura"] > 800 else ""}" '
        f'viewBox="0 0 {m["largura"]} {m["altura"]}" '
        f'role="img" aria-labelledby="{id_titulo} {id_desc}" '
        f'font-family="\'Nunito Sans\', Arial, sans-serif">'
        f'<title id="{id_titulo}">{escape(spec["titulo"])}</title>'
        f'<desc id="{id_desc}">{escape(descricao)}</desc>'
        + "".join(corpo) + "</svg>"
    )
    return (
        '<figure class="wm-interactive-chart">\n'
        f'  <figcaption>{escape(spec["titulo"])}</figcaption>\n'
        f'  <div class="wm-interactive-chart__canvas">{svg}</div>\n'
        f'  <p class="wm-interactive-chart__source">{escape(spec["fonte"])}</p>\n'
        f'  {tabela_dados(spec)}\n'
        '</figure>'
    )
