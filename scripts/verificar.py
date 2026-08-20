#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WM Trading — verificador pre-publicacao.

Confere, ANTES de dar push, as coisas que ja quebraram o site de verdade:
a integridade do <head> da index.html (molde de todo o site), a propagacao
do tracking/LGPD para as paginas geradas, links mortos, e a sanidade da
tabela de redirects do vercel.json.

    python scripts/verificar.py              # checagens locais (antes do push)
    python scripts/verificar.py --producao   # + confere o site no ar

Sai com codigo 1 se encontrar ERRO; 0 se estiver tudo certo (avisos nao
reprovam). Nao altera nenhum arquivo.

Contexto: criado apos o incidente de 24/07/2026, quando uma index.html vinda
de uma copia local antiga derrubou banner LGPD, GA4/Ads, atribuicao de leads
e o popup de WhatsApp — e o gerador espalhou o defeito para as paginas novas.
Ver ROTINA-ATUALIZACAO-SITE.md.
"""

import argparse
import glob
import json

SITE_URL = "https://www.wmtrading.com.br"
import os
import re
import subprocess
import sys
import unicodedata
import urllib.error
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL_PADRAO = "https://site-wm-trading.vercel.app"

# Paginas que legitimamente NAO tem tracking/consent (conferido em 24/07/2026):
# a pagina de pausa e os tres iframes do mapa, que sao embutidos em outras paginas.
SEM_TRACKING_OK = {
    "offline.html",
    os.path.join("mapa-brasil", "assets", "original_visitedplaces.html"),
    os.path.join("mapa-brasil", "mapa_colombia_panama.html"),
    os.path.join("mapa-brasil", "mapa_completo.html"),
}

# O <head> da index.html e o molde de head/menu/rodape das 254 paginas geradas.
# Cada item aqui foi perdido no incidente de 24/07 — a lista e a lista de sintomas.
#
# ATENCAO: tudo aqui e conferido com os comentarios HTML REMOVIDOS. A index.html
# tem um comentario que cita "js/consent.js" e "GTM-52WHRQN"; uma busca ingenua por
# texto acha o comentario e aprova uma home que perdeu o <script> de verdade.
SCRIPTS_DO_MOLDE = [
    ("js/consent.js", "Consent Mode default negado + wm_ambiente + carga do GTM"),
    ("js/utm-tracking.js", "atribuicao de origem dos leads (UTM/gclid -> Pipedrive)"),
    ("js/whatsapp-popup.js", "botao flutuante + popup de captura de WhatsApp"),
]

# CMP AdOpt: dono do consentimento de cookies desde a migracao do banner proprio.
# Sao DUAS tags e as duas importam — o injector sozinho nao sabe de qual site e, e
# a meta sozinha nao carrega nada. Se uma cair, o site fica sem banner de cookies
# em producao e ninguem percebe olhando a tela.
# tem_script() nao serve aqui: o src tem query string depois do .js, entao a
# checagem e por padrao de texto.
ADOPT_WEBSITE_ID = "e7ae093c-b92e-4ceb-9c53-ac44c0b811f8"

TAGS_DO_MOLDE = [
    (r'rel="canonical"', "URL canonica (evita conteudo duplicado)"),
    (r'property="og:', "Open Graph (previa ao compartilhar o link)"),
    (r'type="application/ld\+json"', "dados estruturados JSON-LD (Organization)"),
    (r"max-image-preview:large", "libera imagem grande em resultados/IA do Google"),
    (r'class="adopt-injector"', "CMP AdOpt: script do banner de cookies"),
    (r'name="adopt-website-id"', "CMP AdOpt: meta com o ID do site"),
    (r"website_code=" + re.escape(ADOPT_WEBSITE_ID), "CMP AdOpt: ID do site correto"),
    (r"tag\.goadopt\.io", "CMP AdOpt: dominio do injector"),
]

# Marcadores do CMP conferidos PAGINA POR PAGINA, nao so no molde: TAGS_DO_MOLDE
# olha apenas a index.html, e DUAS paginas do site nao saem do gerador
# (segmentos-aeronaves.html e importacao-carne-suina/index.html). Foi exatamente
# assim que elas entraram na migracao do AdOpt sem banner de cookies.
ADOPT_POR_PAGINA = [
    (r'class="adopt-injector"', "script do CMP AdOpt"),
    (r"website_code=" + re.escape(ADOPT_WEBSITE_ID), "ID do site no AdOpt"),
]

# O ID do container do GTM nao fica na index.html — mora dentro do consent.js.
# Conferido no arquivo, nao no HTML.
# GTM-52WHRQN e o container EXCLUSIVO do site novo. O GTM-K58GFND ficou com o
# WordPress: ele servia os dois sites, e por isso qualquer publicacao nele
# alterava o site que estava no ar.
GTM_ID = "GTM-52WHRQN"
GTM_ARQUIVO = os.path.join("js", "consent.js")

# Scripts que TODA pagina publica precisa ter (propagados pelo gerador).
SCRIPTS_OBRIGATORIOS = [nome for nome, _ in SCRIPTS_DO_MOLDE]

# Unico href="#" legitimo do site: acionado por JS, reabre o painel de cookies.
LINK_VAZIO_OK = "data-wm-consent-prefs"

# Amostra para o smoke test em producao: uma URL por classe de regra.
# A origem tem que ser testada NA FORMA QUE O WORDPRESS PUBLICAVA — com barra no fim.
# E a forma que o Google tem indexada, e com trailingSlash:true e a unica que casa com
# a tabela em um salto so. A forma sem barra funciona tambem, mas em dois saltos
# (/contato -> /contato/ -> /fale-conosco/), entao nao serve como amostra.
AMOSTRA_REDIRECTS = [
    ("/contato/", "/fale-conosco/"),
    ("/wm-cast/", "/podcast/"),
    ("/sobre/", "/about/"),
    ("/falcon-8x/", "/aeronaves/falcon-8x/"),
    ("/duimp/", "/ebooks/duimp/"),
    ("/blog/tag/importacao/", "/blog/"),
    ("/podcast/episodio-10/", "/podcast/"),
    ("/segmentos/aeronaves/", "/segmentos-aeronaves/"),
    ("/blog/ex-tarifario-energia-solar/", "/blog/ex-tarifario-importacoes-fotovoltaico/"),
]

# URLs antigas do WordPress que agora tem que responder 200 DIRETO, sem redirect —
# e a prova de que a mudanca de 14/08 preservou os enderecos que o Google indexou.
AMOSTRA_PARIDADE_WP = [
    "/",
    "/assessoria-aduaneira/",
    "/blog/aco-sucesso/",
    "/segmentos/maquinas/",
    "/aeronaves/falcon-8x/",
    "/ebooks/duimp/",
]

# Paginas que precisam responder 200 direto, sem redirect.
AMOSTRA_DIRETAS = ["/", "/segmentos/", "/blog/"]


class Relatorio:
    def __init__(self):
        self.erros = []
        self.avisos = []

    def erro(self, msg):
        self.erros.append(msg)
        print(f"  [ERRO]  {msg}")

    def aviso(self, msg):
        self.avisos.append(msg)
        print(f"  [aviso] {msg}")

    def ok(self, msg):
        print(f"  [ok]    {msg}")


def titulo(texto):
    print(f"\n{texto}")
    print("-" * len(texto))


def paginas_html():
    """Todos os .html do repo, como caminho relativo."""
    encontrados = []
    for pasta, subpastas, arquivos in os.walk(ROOT_DIR):
        subpastas[:] = [s for s in subpastas if s not in (".git", "node_modules", "__pycache__")]
        for a in arquivos:
            if a.endswith(".html"):
                completo = os.path.join(pasta, a)
                encontrados.append(os.path.relpath(completo, ROOT_DIR))
    return sorted(encontrados)


def ler(caminho_relativo):
    with open(os.path.join(ROOT_DIR, caminho_relativo), encoding="utf-8", errors="replace") as f:
        return f.read()


COMENTARIO_HTML = re.compile(r"<!--.*?-->", re.DOTALL)


def sem_comentarios(html):
    """Remove comentarios HTML antes de procurar tags.

    Sem isso, um comentario que apenas MENCIONA 'js/consent.js' faz o
    verificador aprovar uma pagina que perdeu o <script> de verdade.
    """
    return COMENTARIO_HTML.sub("", html)


def tem_script(html, arquivo):
    """True se existe uma tag <script src="...arquivo"> de fato (nao em comentario)."""
    padrao = r'<script\b[^>]*\bsrc\s*=\s*["\'][^"\']*' + re.escape(arquivo) + r'["\']'
    return re.search(padrao, html, re.IGNORECASE) is not None


def faltas_no_molde(html):
    """Lista de (marcador, descricao) ausentes de um HTML ja sem comentarios."""
    faltando = []
    for arquivo, descricao in SCRIPTS_DO_MOLDE:
        if not tem_script(html, arquivo):
            faltando.append((f"<script src={arquivo}>", descricao))
    for padrao, descricao in TAGS_DO_MOLDE:
        if not re.search(padrao, html, re.IGNORECASE):
            faltando.append((padrao.replace("\\", ""), descricao))
    return faltando


def git(*args):
    try:
        r = subprocess.run(["git"] + list(args), cwd=ROOT_DIR,
                           capture_output=True, text=True, timeout=30)
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None


# --------------------------------------------------------------------------
# A. Git — a regra de ouro numero 1 da rotina
# --------------------------------------------------------------------------
def checar_git(rel):
    titulo("A. Git (voce esta trabalhando em cima da versao mais recente?)")

    if git("rev-parse", "--git-dir") is None:
        rel.aviso("nao consegui ler o git aqui; pulando esta secao")
        return

    if git("fetch", "origin") is None:
        rel.aviso("nao consegui consultar o GitHub (sem rede?); a checagem de "
                  "divergencia abaixo pode estar desatualizada")

    contagem = git("rev-list", "--left-right", "--count", "HEAD...@{u}")
    if contagem and "\t" in contagem:
        a_frente, atras = (int(x) for x in contagem.split("\t"))
        if atras:
            rel.erro(f"sua copia esta {atras} commit(s) ATRAS do GitHub. "
                     f"Rode 'git pull' antes de continuar — publicar assim "
                     f"pode desfazer o trabalho da outra pessoa.")
        if a_frente:
            rel.ok(f"{a_frente} commit(s) seu(s) ainda nao publicado(s)")
        if not atras and not a_frente:
            rel.ok("em dia com o GitHub")
    else:
        rel.aviso("nao consegui comparar com o GitHub")

    sujo = git("status", "--porcelain")
    if sujo:
        rel.ok(f"{len(sujo.splitlines())} arquivo(s) alterado(s) para publicar")
    else:
        rel.ok("nada alterado desde o ultimo commit")


# --------------------------------------------------------------------------
# B. index.html — o molde do site inteiro
# --------------------------------------------------------------------------
def checar_molde(rel):
    titulo("B. index.html — o molde de head/menu/rodape das 254 paginas")

    try:
        home = ler("index.html")
    except FileNotFoundError:
        rel.erro("index.html nao encontrada")
        return

    faltando = faltas_no_molde(sem_comentarios(home))
    for marcador, descricao in faltando:
        rel.erro(f"a home perdeu '{marcador}' — {descricao}")

    # O container do GTM vive no consent.js, nao na home.
    try:
        if GTM_ID not in ler(GTM_ARQUIVO):
            faltando.append((GTM_ID, "container do GTM"))
            rel.erro(f"{GTM_ARQUIVO} nao contem o container {GTM_ID} — "
                     f"sem GA4 e sem Google Ads no site inteiro")
    except FileNotFoundError:
        faltando.append((GTM_ARQUIVO, "arquivo do consent"))
        rel.erro(f"{GTM_ARQUIVO} nao existe — sem banner LGPD e sem GTM")

    if faltando:
        rel.erro("NAO PUBLIQUE. Uma index.html incompleta contamina o site inteiro "
                 "na proxima geracao. Provavel causa: copia local antiga. "
                 "Ver ROTINA-ATUALIZACAO-SITE.md.")
    else:
        total = len(SCRIPTS_DO_MOLDE) + len(TAGS_DO_MOLDE) + 1
        rel.ok(f"os {total} elementos criticos do <head> estao presentes "
               f"(comentarios ignorados)")


# --------------------------------------------------------------------------
# C. Propagacao para as paginas geradas
# --------------------------------------------------------------------------
def checar_propagacao(rel):
    titulo("C. Propagacao do tracking/LGPD para as paginas geradas")

    todas = paginas_html()
    sem_scripts = []
    sem_adopt = []

    for pagina in todas:
        if pagina in SEM_TRACKING_OK:
            continue
        conteudo = sem_comentarios(ler(pagina))
        ausentes = [s for s in SCRIPTS_OBRIGATORIOS if not tem_script(conteudo, s)]
        if ausentes:
            sem_scripts.append((pagina, ausentes))
        # O CMP e conferido PAGINA POR PAGINA, e nao so na index.html: duas
        # paginas do site nao saem do gerador e ja ficaram sem banner de cookies
        # exatamente por isso.
        faltando_cmp = [d for p, d in ADOPT_POR_PAGINA if not re.search(p, conteudo)]
        if faltando_cmp:
            sem_adopt.append((pagina, faltando_cmp))

    if sem_scripts:
        for pagina, ausentes in sem_scripts[:15]:
            rel.erro(f"{pagina} sem: {', '.join(ausentes)}")
        if len(sem_scripts) > 15:
            rel.erro(f"...e mais {len(sem_scripts) - 15} pagina(s). "
                     f"Rode 'python scripts/build_pages.py' e verifique de novo.")
    else:
        rel.ok(f"{len(todas) - len(SEM_TRACKING_OK)} paginas com consent + UTM + "
               f"WhatsApp ({len(SEM_TRACKING_OK)} excecoes conhecidas)")

    if sem_adopt:
        for pagina, faltando in sem_adopt[:15]:
            rel.erro(f"{pagina} sem CMP: {', '.join(faltando)}")
        if len(sem_adopt) > 15:
            rel.erro(f"...e mais {len(sem_adopt) - 15} pagina(s) sem o AdOpt. "
                     f"Se for pagina fora do gerador, espelhe o <head> a mao.")
    else:
        rel.ok(f"{len(todas) - len(SEM_TRACKING_OK)} paginas com o CMP AdOpt "
               f"(conferido pagina por pagina, nao so no molde)")


# --------------------------------------------------------------------------
# D. Links mortos
# --------------------------------------------------------------------------
def checar_links_mortos(rel):
    titulo("D. Links mortos (href=\"#\")")

    padrao = re.compile(r'<a\b[^>]*href="#"[^>]*>', re.IGNORECASE)
    mortos = {}

    for pagina in paginas_html():
        achados = [t for t in padrao.findall(ler(pagina)) if LINK_VAZIO_OK not in t]
        if achados:
            mortos[pagina] = len(achados)

    if mortos:
        total = sum(mortos.values())
        rel.erro(f"{total} link(s) sem destino em {len(mortos)} pagina(s):")
        for pagina, n in sorted(mortos.items(), key=lambda x: -x[1])[:10]:
            rel.erro(f"    {pagina}: {n}")
        if "index.html" in mortos:
            rel.erro("    a home esta entre elas — sintoma classico de copia local antiga")
    else:
        rel.ok("nenhum link sem destino (fora o de preferencias de cookies, que e por JS)")


def checar_ingles(rel):
    """A arvore /en/ existe e esta pareada com o portugues?

    O build_pages reescreve as paginas PT e APAGA o hreflang que o build_en
    injetou nelas. Se alguem regenerar e esquecer de rodar o build_en, o par
    quebra e o Google volta a ignorar a versao em ingles — sem sintoma visivel.
    Este bloco existe para isso nao passar batido.
    """
    titulo("H. Arvore em ingles e hreflang")

    fonte = os.path.join(ROOT_DIR, "content", "en", "paginas.json")
    if not os.path.exists(fonte):
        rel.ok("sem arvore /en/ configurada")
        return

    with open(fonte, encoding="utf-8") as f:
        paginas = json.load(f)

    sem_arquivo, sem_par, sem_lang = [], [], []
    for p in paginas:
        rel_en = p["en"].strip("/")
        arq_en = "en/index.html" if rel_en == "en" else rel_en + ".html"
        caminho_en = os.path.join(ROOT_DIR, arq_en.replace("/", os.sep))
        if not os.path.exists(caminho_en):
            sem_arquivo.append(p["en"])
            continue
        html_en = ler(arq_en)
        if 'lang="en"' not in html_en:
            sem_lang.append(p["en"])
        if f'hreflang="pt-BR" href="{SITE_URL}{p["pt"]}"' not in html_en:
            sem_par.append(f'{p["en"]} (falta o par no lado EN)')

        # lado portugues
        alvo = _alvo(p["pt"])
        if alvo and f'hreflang="en" href="{SITE_URL}{p["en"]}"' not in ler(alvo):
            sem_par.append(f'{p["pt"]} (falta o par no lado PT — rode build_en.py)')

    if sem_arquivo:
        rel.erro(f"{len(sem_arquivo)} pagina(s) /en/ no conteudo mas sem arquivo gerado: "
                 f"{', '.join(sem_arquivo[:5])}")
    if sem_lang:
        rel.erro(f"{len(sem_lang)} pagina(s) /en/ sem lang=\"en\": {', '.join(sem_lang[:5])}")
    if sem_par:
        rel.erro(f"{len(sem_par)} hreflang incompleto — o Google so aceita o par nos DOIS "
                 f"sentidos:")
        for s in sem_par[:6]:
            rel.erro(f"    {s}")
    if not (sem_arquivo or sem_lang or sem_par):
        rel.ok(f"{len(paginas)} paginas /en/ com lang=en e hreflang pareado nos dois lados")

    # nenhum redirect pode interceptar uma pagina /en/ que existe
    cfg = json.loads(ler("vercel.json"))
    existentes = {p["en"] for p in paginas}
    capturadas = [r for r in cfg.get("redirects", [])
                  if r["source"] in existentes
                  or (r["source"].startswith("/en/:") or r["source"] == "/en/:path(.*)")]
    if capturadas:
        rel.erro(f"{len(capturadas)} redirect(s) interceptam paginas /en/ que existem — "
                 f"na Vercel o redirect vem ANTES do arquivo:")
        for r in capturadas[:5]:
            rel.erro(f"    {r['source']} -> {r['destination']}")
    else:
        rel.ok("nenhum redirect intercepta as paginas /en/")


EXT_ASSET = ("webp", "jpg", "jpeg", "png", "svg", "gif", "avif", "mp4",
              "webm", "json", "css", "js", "woff", "woff2", "ico", "pdf")

_ASSET_JS = re.compile(
    r"""['"`]([^'"`\n]*?/[^'"`\n]*?\.(?:""" + "|".join(EXT_ASSET) + r"""))(?:\?[^'"`\n]*)?['"`]""",
    re.IGNORECASE)


def _asset_em_js(codigo):
    """Caminhos de asset RELATIVOS escritos como string dentro de JavaScript.

    Exige a barra: 'images/x.webp' entra, 'main.js' solto nao — sem isso qualquer
    nome de arquivo usado como rotulo viraria falso positivo. Query string e
    ignorada. Template literal com ${} tambem e pego, porque o prefixo relativo
    quebra do mesmo jeito.
    """
    achados = []
    for alvo in _ASSET_JS.findall(codigo):
        if alvo.startswith(("/", "http", "data:", "blob:", "//")):
            continue
        if alvo not in achados:
            achados.append(alvo)
    return achados


def slugificar(texto):
    """Mesma regra que um CMS usa para virar titulo em endereco."""
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def checar_slug_dos_posts(rel):
    """Post criado no site novo cujo endereco nao e o que o titulo sugere.

    Post MIGRADO tem originalUrl no frontmatter: ali o slug veio do WordPress e e
    a URL que o Google indexou — divergir do titulo e normal e nao se mexe. O
    risco esta no post criado aqui: ninguem de fora sabe o slug encurtado, e quem
    deduz o endereco pelo titulo toma 404. Foi o caso de
    /blog/por-que-empresas-escolhem-a-wm-trading-para-importar/ em 20/08/2026.
    """
    titulo("I. Slug dos posts criados no site novo")

    fontes = sorted(glob.glob(os.path.join(ROOT_DIR, "content", "blog", "*.mdx")))
    if not fontes:
        rel.ok("nenhum post em content/blog — nada a conferir")
        return

    try:
        redirects = json.loads(ler("vercel.json")).get("redirects", [])
    except Exception:
        redirects = []
    origens = {r.get("source", "").rstrip("/") for r in redirects}

    novos = 0
    sem_rede = []
    for caminho in fontes:
        with open(caminho, encoding="utf-8", errors="replace") as fh:
            texto = fh.read()
        if re.search(r"^originalUrl:", texto, re.M):
            continue          # migrado: o slug do WordPress e o correto
        m_t = re.search(r'^title:\s*"(.*?)"\s*$', texto, re.M)
        m_s = re.search(r'^slug:\s*"(.*?)"\s*$', texto, re.M)
        if not (m_t and m_s):
            continue
        novos += 1
        esperado, real = slugificar(m_t.group(1)), m_s.group(1)
        if esperado == real:
            continue
        url = f"/blog/{esperado}"
        if url in origens:
            continue          # ja existe 301 cobrindo o endereco previsivel
        sem_rede.append((real, esperado))

    if sem_rede:
        rel.aviso(f"{len(sem_rede)} post(s) criado(s) aqui com slug diferente do "
                  f"titulo e SEM 301 do endereco que o titulo sugere:")
        for real, esperado in sem_rede:
            rel.aviso(f"    /blog/{real}/  <-  falta 301 de  /blog/{esperado}/")
        rel.aviso("    para resolver, em vercel.json:")
        real, esperado = sem_rede[0]
        rel.aviso(f'      {{"source": "/blog/{esperado}/", '
                  f'"destination": "/blog/{real}/", "permanent": true}}')
    else:
        rel.ok(f"{novos} post(s) criado(s) no site novo: endereco previsivel "
               f"pelo titulo, ou 301 ja existente")


def checar_caminhos_relativos(rel):
    """Com trailingSlash:true, /x.html e servida em /x/ — e isso muda a base dos
    caminhos relativos: 'images/a.webp' vira '/x/images/a.webp' e da 404.

    As paginas geradas sao imunes (make_paths_absolute). As MANUAIS nao, e ja
    custaram caro duas vezes em 17/08: a de aeronaves ficou 3 dias sem CSS pelos
    src/href, e depois as 4 imagens do hero continuaram quebradas porque a
    primeira correcao passou pelos src e nao pelos srcset — que sao os que o
    navegador de fato usa quando existem.
    """
    titulo("G. Caminhos relativos em pagina manual")

    cfg = json.loads(ler("vercel.json"))
    if cfg.get("trailingSlash") is not True:
        rel.ok("trailingSlash desligado — caminho relativo nao muda de base")
        return

    # So ASSET: e o que quebra o visual da pagina. href de <a> e link de conteudo,
    # tratado no bloco D e na varredura de content/**.
    padrao = re.compile(r'\b(src|srcset|imagesrcset)="([^"]+)"', re.IGNORECASE)
    padrao_link = re.compile(r'<link\b[^>]*href="([^"]+)"', re.IGNORECASE)
    achados = {}

    for pagina in paginas_html():
        # A home e a unica servida na raiz do dominio: nela relativo e absoluto
        # apontam para o mesmo lugar. Nas demais, /x.html vira /x/ e a base muda.
        if pagina == "index.html":
            continue

        html = sem_comentarios(ler(pagina))
        ruins = []

        def _relativo(alvo):
            return bool(alvo) and not alvo.startswith(
                ("/", "#", "http", "data:", "mailto:", "tel:", "javascript:", "?"))

        for atributo, valor in padrao.findall(html):
            for item in valor.split(","):
                alvo = item.strip().split(" ")[0]
                if _relativo(alvo):
                    ruins.append(f'{atributo}="{alvo}"')
        for alvo in padrao_link.findall(html):
            if _relativo(alvo):
                ruins.append(f'link href="{alvo}"')

        # Caminho relativo dentro de STRING JS tambem quebra, e nao aparece em
        # nenhum atributo: foi o defeito das 8 fotos da galeria de feiras em
        # 20/08/2026 ('images/aeronaves/feira-*.webp' num objeto JS inline).
        for trecho in re.findall(r"<script\b[^>]*>(.*?)</script>", html,
                                 re.IGNORECASE | re.DOTALL):
            for alvo in _asset_em_js(trecho):
                ruins.append(f'string JS "{alvo}"')

        if ruins:
            achados[pagina] = ruins

    # Arquivo .js externo e carregado por MUITAS paginas, e o caminho resolve
    # contra a URL DA PAGINA, nao contra a pasta do .js. Aqui nao ha excecao de
    # index.html: basta uma pagina fora da raiz para quebrar.
    for arquivo in sorted(glob.glob(os.path.join(ROOT_DIR, "js", "*.js"))):
        rel_js = os.path.relpath(arquivo, ROOT_DIR).replace(os.sep, "/")
        alvos = _asset_em_js(ler(rel_js))
        if alvos:
            achados[rel_js] = [f'string JS "{a}"' for a in alvos]

    if achados:
        total = sum(len(v) for v in achados.values())
        rel.erro(f"{total} caminho(s) relativo(s) em {len(achados)} arquivo(s) — "
                 f"com trailingSlash:true resolvem contra /pagina/ e dao 404:")
        for pagina, ruins in sorted(achados.items(), key=lambda x: -len(x[1]))[:8]:
            rel.erro(f"    {pagina}: {len(ruins)}x  ex.: {ruins[0][:70]}")
    else:
        rel.ok("nenhum caminho relativo (src, href, srcset, imagesrcset "
               "e string JS conferidos)")


# --------------------------------------------------------------------------
# E. vercel.json — tabela de redirects
# --------------------------------------------------------------------------
def _alvo(caminho_url):
    """Arquivo que a Vercel serve para uma URL, ou None se nao existe.

    Desde 14/08 o vercel.json usa cleanUrls:true + trailingSlash:true, entao a URL
    publica NAO tem .html: /about/ e servida por about.html e /segmentos/ por
    segmentos/index.html. Sem a tentativa com .html, os 52 redirects estaticos
    aparecem todos como 'destino nao existe'.
    """
    p = caminho_url.split("?")[0].split("#")[0].strip("/")
    if p == "":
        raiz = os.path.join(ROOT_DIR, "index.html")
        return raiz if os.path.isfile(raiz) else None
    base = os.path.join(ROOT_DIR, *p.split("/"))
    for tentativa in (base, base + ".html", os.path.join(base, "index.html")):
        if os.path.isfile(tentativa):
            return tentativa
    return None


def _resolve(caminho_url):
    return _alvo(caminho_url) is not None


def checar_vercel(rel):
    titulo("E. vercel.json — tabela de redirects")

    try:
        with open(os.path.join(ROOT_DIR, "vercel.json"), encoding="utf-8") as f:
            cfg = json.load(f)
    except FileNotFoundError:
        rel.erro("vercel.json nao encontrado")
        return
    except json.JSONDecodeError as e:
        rel.erro(f"vercel.json com JSON invalido (linha {e.lineno}): {e.msg} — "
                 f"a Vercel recusa o deploy assim")
        return

    if cfg.get("rewrites"):
        rel.aviso("existe 'rewrites' no vercel.json — se for o catch-all da pausa "
                  "para offline.html, o site inteiro fica offline ao publicar")

    redirects = cfg.get("redirects", [])
    if not redirects:
        rel.erro("nenhum redirect configurado — as 286 URLs antigas do WordPress "
                 "cairiam em 404 na virada (ver Fase 5 do plano)")
        return

    estaticas = [r for r in redirects if ":" not in r["source"] and ":" not in r["destination"]]
    dinamicas = [r for r in redirects if r not in estaticas]

    mortos = [r for r in estaticas if not _resolve(r["destination"])]
    for r in mortos:
        rel.erro(f"{r['source']} -> {r['destination']} (destino nao existe)")

    # Com trailingSlash:true a Vercel normaliza o caminho ANTES de consultar a tabela.
    # Consequencias que este bloco pega, ambas descobertas em 17/08:
    #   1) origem sem barra nunca casa com a URL antiga do WP (que tem barra) -> 404;
    #   2) se a origem ganhar barra e o destino for ela mesma, vira laco infinito.
    if cfg.get("trailingSlash") is True:
        lacos = [r for r in estaticas if r["source"] == r["destination"]]
        for r in lacos:
            rel.erro(f"{r['source']} -> {r['destination']} : origem igual ao destino, "
                     f"a Vercel entraria em laco infinito")

        # A regra da barra vale para PAGINA, nao para arquivo. Medido em producao
        # em 17/08: /x.pdf responde 200 direto, e /x.pdf/ leva 308 REMOVENDO a barra
        # (o inverso de /about, que ganha barra). Exigir barra em origem de arquivo
        # seria o erro contrario — por isso caminho com extensao fica de fora.
        def _e_arquivo(caminho):
            ultimo = caminho.rstrip("/").rsplit("/", 1)[-1]
            return "." in ultimo and not ultimo.startswith(".")

        sem_barra = [r for r in estaticas
                     if not r["source"].endswith("/") and not _e_arquivo(r["source"])]
        for r in sem_barra:
            rel.erro(f"{r['source']} -> {r['destination']} : com trailingSlash:true a "
                     f"origem precisa terminar em barra, senao a URL antiga do WordPress "
                     f"(/{r['source'].strip('/')}/) cai em 404")

        # Espelho da regra acima: origem de ARQUIVO nao pode ter barra.
        arquivo_com_barra = [r for r in estaticas
                             if r["source"].endswith("/") and _e_arquivo(r["source"])]
        for r in arquivo_com_barra:
            rel.erro(f"{r['source']} -> {r['destination']} : origem e arquivo e nao pode "
                     f"terminar em barra — a Vercel remove a barra antes de consultar a "
                     f"tabela, entao a regra nunca casaria")

        # :path* nao consome a barra final; :path(.*) consome.
        frageis = [r for r in dinamicas if ":path*" in r["source"] or ":path+" in r["source"]]
        for r in frageis:
            rel.erro(f"{r['source']} -> {r['destination']} : com trailingSlash:true use "
                     f":path(.*) — o :path*/:path+ nao casa com a barra final")

    # Sequestro = a origem JA e uma pagina real E aponta para OUTRO arquivo.
    # Com cleanUrls+trailingSlash, /about e /about/ resolvem para o mesmo about.html:
    # esse redirect e redundante (a Vercel ja faz), nao um sequestro. O caso real foi
    # /segmentos -> / em 06/08, que matava a pagina /segmentos criada em 15/07.
    sombras = [r for r in estaticas
               if r["source"] != "/"
               and _alvo(r["source"]) is not None
               and _alvo(r["source"]) != _alvo(r["destination"])]
    for r in sombras:
        rel.erro(f"{r['source']} -> {r['destination']} : '{r['source']}' JA e uma pagina "
                 f"real do site novo (serve {os.path.basename(_alvo(r['source']))}); "
                 f"este redirect a sequestraria")

    # Regra especifica precisa vir ANTES da dinamica que a cobriria (a Vercel usa a 1a que casar).
    ordem = [r["source"] for r in redirects]
    fora_de_ordem = []
    for i, fonte in enumerate(ordem):
        if ":" in fonte:
            continue
        for j, dinamica in enumerate(ordem):
            if ":" not in dinamica or j >= i:
                continue
            prefixo = dinamica.split("/:")[0]
            if prefixo and fonte.startswith(prefixo + "/"):
                fora_de_ordem.append((fonte, dinamica))
    for fonte, dinamica in fora_de_ordem:
        rel.erro(f"'{fonte}' esta DEPOIS de '{dinamica}' — a regra dinamica casa primeiro "
                 f"e a especifica nunca roda. Mova-a para cima.")

    if not (mortos or sombras or fora_de_ordem):
        rel.ok(f"{len(redirects)} regras ({len(estaticas)} estaticas + {len(dinamicas)} "
               f"dinamicas): destinos existem, nenhuma sequestra pagina real, ordem correta")


# --------------------------------------------------------------------------
# F. robots.txt — estado consciente
# --------------------------------------------------------------------------
def checar_robots(rel):
    titulo("F. robots.txt")

    try:
        robots = ler("robots.txt")
    except FileNotFoundError:
        rel.erro("robots.txt nao encontrado")
        return

    bloqueado = re.search(r"^\s*Disallow:\s*/\s*$", robots, re.MULTILINE)

    if bloqueado:
        rel.aviso("BLOQUEADO para buscadores ('Disallow: /'). Correto enquanto o site "
                  "vive no vercel.app. Na virada de dominio, liberar — e o item que, "
                  "se esquecido, tira o site do Google.")
    else:
        rel.aviso("LIBERADO para indexacao. So pode ficar assim quando o dominio "
                  "wmtrading.com.br ja apontar para a Vercel — senao o vercel.app "
                  "vira duplicata do site oficial e os dois competem no Google.")


# --------------------------------------------------------------------------
# G/H. Producao
# --------------------------------------------------------------------------
def _buscar(url, seguir=True):
    class SemRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None

    abridor = urllib.request.build_opener() if seguir else \
        urllib.request.build_opener(SemRedirect)
    req = urllib.request.Request(url, headers={"User-Agent": "wm-verificar/1.0"})
    try:
        with abridor.open(req, timeout=20) as r:
            return r.status, r.headers.get("Location"), r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Location"), ""
    except Exception as e:
        return None, str(e), ""


def checar_producao(rel, base):
    titulo(f"G. Site no ar — home ({base})")

    status, _, html = _buscar(base + "/")
    if status != 200:
        rel.erro(f"a home respondeu {status}")
    else:
        faltando = faltas_no_molde(sem_comentarios(html))
        if faltando:
            rel.erro(f"a home NO AR esta sem: {', '.join(m for m, _ in faltando)}")
        else:
            rel.ok("a home no ar tem o <head> completo (LGPD, GTM, UTM, WhatsApp, SEO)")

    # A prova da mudanca de 14/08: as URLs que o Google indexou no WordPress precisam
    # responder 200 DIRETO, sem redirect. Qualquer 301/308 aqui significa que o endereco
    # mudou e o Google vai ter que reprocessar aquela pagina.
    titulo("G2. Paridade com as URLs do WordPress (200 direto, sem redirect)")
    for caminho in AMOSTRA_PARIDADE_WP:
        status, destino, _ = _buscar(base + caminho, seguir=False)
        if status == 200:
            rel.ok(f"{caminho} -> 200 (endereco preservado)")
        elif status in (301, 302, 307, 308):
            rel.erro(f"{caminho} -> {status} {destino or ''} : o endereco que o Google "
                     f"indexou MUDOU; era para responder 200 direto")
        else:
            rel.erro(f"{caminho} -> {status} {destino or ''} (esperado 200 direto)")

    titulo("H. Site no ar — redirects e paginas diretas")

    for caminho in AMOSTRA_DIRETAS:
        status, destino, _ = _buscar(base + caminho, seguir=False)
        if status == 200:
            rel.ok(f"{caminho} -> 200 (direto, sem redirect)")
        else:
            rel.erro(f"{caminho} -> {status} {destino or ''} (esperado 200 direto)")

    for origem, esperado in AMOSTRA_REDIRECTS:
        status, destino, _ = _buscar(base + origem, seguir=False)
        if status in (301, 308) and destino and destino.endswith(esperado):
            rel.ok(f"{origem} -> {status} -> {esperado}")
        elif status in (301, 308):
            rel.erro(f"{origem} -> {status} -> {destino} (esperado {esperado})")
        else:
            rel.erro(f"{origem} -> {status} (esperado 301/308 para {esperado})")


# --------------------------------------------------------------------------
def main():
    p = argparse.ArgumentParser(description="Verificador pre-publicacao do site WM Trading.")
    p.add_argument("--producao", action="store_true",
                   help="tambem confere o site no ar (rode DEPOIS do push)")
    p.add_argument("--url", default=URL_PADRAO,
                   help=f"endereco do site publicado (padrao: {URL_PADRAO})")
    args = p.parse_args()

    print("=" * 70)
    print("WM Trading — verificacao pre-publicacao")
    print("=" * 70)

    rel = Relatorio()
    checar_git(rel)
    checar_molde(rel)
    checar_propagacao(rel)
    checar_links_mortos(rel)
    checar_vercel(rel)
    checar_robots(rel)
    checar_caminhos_relativos(rel)
    checar_slug_dos_posts(rel)
    checar_ingles(rel)
    if args.producao:
        checar_producao(rel, args.url.rstrip("/"))

    print("\n" + "=" * 70)
    if rel.erros:
        print(f"REPROVADO — {len(rel.erros)} erro(s), {len(rel.avisos)} aviso(s)")
        print("Nao publique antes de resolver os erros acima.")
        print("=" * 70)
        return 1

    print(f"APROVADO — 0 erros, {len(rel.avisos)} aviso(s)")
    if not args.producao:
        print("Depois do push, rode de novo com --producao para conferir o site no ar.")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
