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
import json
import os
import re
import subprocess
import sys
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
# tem um comentario que cita "js/consent.js" e "GTM-K58GFND"; uma busca ingenua por
# texto acha o comentario e aprova uma home que perdeu o <script> de verdade.
SCRIPTS_DO_MOLDE = [
    ("js/consent.js", "banner LGPD + Consent Mode + carregamento do GTM"),
    ("js/utm-tracking.js", "atribuicao de origem dos leads (UTM/gclid -> Pipedrive)"),
    ("js/whatsapp-popup.js", "botao flutuante + popup de captura de WhatsApp"),
]

TAGS_DO_MOLDE = [
    (r'rel="canonical"', "URL canonica (evita conteudo duplicado)"),
    (r'property="og:', "Open Graph (previa ao compartilhar o link)"),
    (r'type="application/ld\+json"', "dados estruturados JSON-LD (Organization)"),
    (r"max-image-preview:large", "libera imagem grande em resultados/IA do Google"),
]

# O ID do container do GTM nao fica na index.html — mora dentro do consent.js,
# que so o dispara apos o aceite do banner. Conferido no arquivo, nao no HTML.
GTM_ID = "GTM-K58GFND"
GTM_ARQUIVO = os.path.join("js", "consent.js")

# Scripts que TODA pagina publica precisa ter (propagados pelo gerador).
SCRIPTS_OBRIGATORIOS = [nome for nome, _ in SCRIPTS_DO_MOLDE]

# Unico href="#" legitimo do site: acionado por JS, reabre o painel de cookies.
LINK_VAZIO_OK = "data-wm-consent-prefs"

# Amostra para o smoke test em producao: uma URL por classe de regra.
AMOSTRA_REDIRECTS = [
    ("/about", "/about.html"),
    ("/contato", "/fale-conosco.html"),
    ("/wm-cast", "/podcast.html"),
    ("/blog/tag/importacao", "/blog/index.html"),
    ("/segmentos/aeronaves", "/segmentos-aeronaves.html"),
    ("/blog/ex-tarifario-energia-solar", "/blog/ex-tarifario-importacoes-fotovoltaico.html"),
]

# Paginas que precisam responder 200 direto, sem redirect.
AMOSTRA_DIRETAS = ["/", "/segmentos", "/blog"]


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

    for pagina in todas:
        if pagina in SEM_TRACKING_OK:
            continue
        conteudo = sem_comentarios(ler(pagina))
        ausentes = [s for s in SCRIPTS_OBRIGATORIOS if not tem_script(conteudo, s)]
        if ausentes:
            sem_scripts.append((pagina, ausentes))

    if sem_scripts:
        for pagina, ausentes in sem_scripts[:15]:
            rel.erro(f"{pagina} sem: {', '.join(ausentes)}")
        if len(sem_scripts) > 15:
            rel.erro(f"...e mais {len(sem_scripts) - 15} pagina(s). "
                     f"Rode 'python scripts/build_pages.py' e verifique de novo.")
    else:
        rel.ok(f"{len(todas) - len(SEM_TRACKING_OK)} paginas com consent + UTM + "
               f"WhatsApp ({len(SEM_TRACKING_OK)} excecoes conhecidas)")


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


# --------------------------------------------------------------------------
# E. vercel.json — tabela de redirects
# --------------------------------------------------------------------------
def _resolve(caminho_url):
    p = caminho_url.split("?")[0].split("#")[0].strip("/")
    if p == "":
        return os.path.isfile(os.path.join(ROOT_DIR, "index.html"))
    alvo = os.path.join(ROOT_DIR, *p.split("/"))
    return os.path.isfile(alvo) or os.path.isfile(os.path.join(alvo, "index.html"))


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

    sombras = [r for r in estaticas if r["source"] != "/" and _resolve(r["source"])]
    for r in sombras:
        rel.erro(f"{r['source']} -> {r['destination']} : '{r['source']}' JA e uma pagina "
                 f"real do site novo; este redirect a sequestraria")

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
