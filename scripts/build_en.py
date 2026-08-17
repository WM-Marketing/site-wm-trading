# -*- coding: utf-8 -*-
"""Gera a arvore /en/ com o conteudo em ingles ja revisado do site antigo.

POR QUE UM SCRIPT SEPARADO
O build_pages.py gera as 254 paginas do site. Mexer nele para emitir /en/ faria
um erro no molde contaminar tudo — foi assim que, em 24/07, a home perdeu o
tracking e levou junto a vitrine do blog. Aqui o estrago possivel fica dentro de
/en/. O molde (head, menu, rodape) e reaproveitado do build_pages, entao o visual
e identico, mas nada existente e reescrito.

DE ONDE VEM O TEXTO
Das paginas /en/ do WordPress, que segundo o Thiago eram traduzidas a mao (mesmo
com apoio de IA, alguem entrava e revisava). Nao e traducao automatica: e
conteudo revisado sendo trazido, igual aos PDFs e aos posts.

ORDEM DE EXECUCAO — IMPORTA
    python scripts/build_pages.py     # primeiro, gera o site em PT
    python scripts/build_en.py        # depois, gera /en/ e injeta o hreflang
O hreflang precisa existir NOS DOIS LADOS para o Google aceitar o par; como as
paginas PT sao reescritas pelo build_pages, este script injeta o hreflang nelas
depois. Se alguem regenerar e esquecer de rodar este, o verificar.py acusa.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_pages as bp  # noqa: E402
import html as html_mod  # noqa: E402

ROOT = bp.ROOT_DIR
CONTEUDO = os.path.join(ROOT, "content", "en", "paginas.json")
SITE = "https://www.wmtrading.com.br"


def caminho_saida(url_en):
    """/en/segments/steel/ -> en/segments/steel.html"""
    rel = url_en.strip("/")
    if rel == "en":
        return os.path.join(ROOT, "en", "index.html")
    return os.path.join(ROOT, rel.replace("/", os.sep) + ".html")


def corpo_html(pagina):
    """Monta o miolo com as mesmas classes do site, para o visual bater."""
    blocos = pagina["blocos"]
    if not blocos:
        return ""

    # hero: primeiro cabecalho + primeiro paragrafo depois dele
    titulo_hero = pagina["h1"]
    sub_hero = pagina["sub"]

    partes = [f"""
    <section class="dynamic-hero">
      <div class="container">
        <h1 class="dynamic-hero__title">{html_mod.escape(titulo_hero)}</h1>
        {f'<p class="dynamic-hero__subtitle">{html_mod.escape(sub_hero)}</p>' if sub_hero else ''}
      </div>
    </section>"""]

    idx = 0
    for sec in pagina["secoes"]:
        alterna = "page-section--alternate" if idx % 2 == 1 else ""
        itens = ""
        if sec.get("lista"):
            itens = "<ul class='card-desc' style='margin-top:14px; padding-left:20px;'>" + \
                    "".join(f"<li>{html_mod.escape(i)}</li>" for i in sec["lista"]) + "</ul>"
        texto = "".join(
            f'<p class="card-desc" style="font-size: var(--fs-base); line-height: 1.7; '
            f'margin-bottom: 14px;">{html_mod.escape(p)}</p>' for p in sec["paragrafos"])
        cabecalho = (f'<h2 class="card-title" style="font-size: var(--fs-lg); '
                     f'font-weight: var(--fw-semibold); color: var(--color-primary); '
                     f'margin-bottom: 18px;">{html_mod.escape(sec["titulo"])}</h2>'
                     if sec.get("titulo") else "")
        partes.append(f"""
    <section class="page-section {alterna}">
      <div class="container intro-container">
        {cabecalho}
        {texto}
        {itens}
      </div>
    </section>""")
        idx += 1

    # CTA final, apontando para o formulario em portugues (unico que existe)
    partes.append("""
    <section class="page-section page-section--alternate">
      <div class="container intro-container" style="text-align:center;">
        <h2 class="card-title" style="font-size: var(--fs-lg); font-weight: var(--fw-semibold); margin-bottom: 18px;">Talk to our specialists</h2>
        <p class="card-desc" style="margin-bottom: 22px;">Tell us about your operation and our team will get back to you.</p>
        <a href="/fale-conosco/" class="btn btn-primary">Get in touch</a>
      </div>
    </section>""")
    return "\n".join(partes)


def injeta_hreflang(caminho_arquivo, url_pt, url_en):
    """Coloca o par hreflang no <head>. Idempotente."""
    if not os.path.exists(caminho_arquivo):
        return False
    with open(caminho_arquivo, encoding="utf-8") as f:
        html = f.read()
    if 'hreflang="en"' in html:
        html = re.sub(r'\s*<link rel="alternate" hreflang="[^"]*"[^>]*>', "", html)
    tags = (f'\n  <link rel="alternate" hreflang="pt-BR" href="{SITE}{url_pt}" />'
            f'\n  <link rel="alternate" hreflang="en" href="{SITE}{url_en}" />'
            f'\n  <link rel="alternate" hreflang="x-default" href="{SITE}{url_pt}" />')
    if "</head>" not in html:
        return False
    html = html.replace("</head>", tags + "\n</head>", 1)
    with open(caminho_arquivo, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    return True


def main():
    if not os.path.exists(CONTEUDO):
        sys.exit(f"ERRO: {CONTEUDO} nao existe. Rode antes o raspador de conteudo.")

    paginas = json.load(open(CONTEUDO, encoding="utf-8"))
    head_tpl, header_tpl, footer_tpl = bp.load_template_elements()

    gerados, com_par = 0, 0
    print(f"gerando {len(paginas)} paginas em /en/\n")

    for p in paginas:
        saida = caminho_saida(p["en"])
        os.makedirs(os.path.dirname(saida), exist_ok=True)
        corpo = corpo_html(p)
        if not corpo:
            print(f"  pulada (sem conteudo): {p['en']}")
            continue

        bp.render_html_page(
            saida, p["titulo"], p["description"], corpo,
            head_tpl, header_tpl, footer_tpl, lang="en")

        # hreflang dos dois lados
        injeta_hreflang(saida, p["pt"], p["en"])
        alvo_pt = bp._caminho_arquivo_pt(p["pt"]) if hasattr(bp, "_caminho_arquivo_pt") else None
        if alvo_pt is None:
            rel = p["pt"].strip("/")
            for tentativa in ([f"{rel}.html", f"{rel}/index.html"] if rel else ["index.html"]):
                cand = os.path.join(ROOT, tentativa.replace("/", os.sep))
                if os.path.exists(cand):
                    alvo_pt = cand
                    break
        if alvo_pt and injeta_hreflang(alvo_pt, p["pt"], p["en"]):
            com_par += 1

        gerados += 1
        print(f"  {p['en']:<56} <- {p['pt']}")

    n_sitemap = atualiza_sitemap(paginas)

    print(f"\n{'=' * 70}")
    print(f"paginas /en/ geradas      : {gerados}")
    print(f"pares hreflang completos  : {com_par}")
    print(f"URLs /en/ no sitemap      : {n_sitemap}")
    print("lembrete: rode SEMPRE depois do build_pages.py")


def atualiza_sitemap(paginas):
    """Acrescenta as URLs /en/ ao sitemap que o build_pages acabou de escrever.

    Sem isso o Google demora muito mais para reencontrar a arvore em ingles —
    justamente o que estamos tentando evitar na virada.
    """
    caminho = os.path.join(ROOT, "sitemap.xml")
    if not os.path.exists(caminho):
        return 0
    with open(caminho, encoding="utf-8") as f:
        xml = f.read()

    # tira entradas /en/ antigas para nao duplicar em regeneracoes seguidas
    xml = re.sub(r"\s*<url>\s*<loc>[^<]*/en/[^<]*</loc>.*?</url>", "", xml, flags=re.S)

    hoje = re.search(r"<lastmod>([^<]+)</lastmod>", xml)
    data = hoje.group(1) if hoje else ""
    novas = "".join(
        f"\n  <url>\n    <loc>{SITE}{p['en']}</loc>"
        f"{f'{chr(10)}    <lastmod>{data}</lastmod>' if data else ''}\n  </url>"
        for p in paginas)

    xml = xml.replace("</urlset>", novas + "\n</urlset>")
    with open(caminho, "w", encoding="utf-8", newline="\n") as f:
        f.write(xml)
    return len(paginas)


if __name__ == "__main__":
    main()
