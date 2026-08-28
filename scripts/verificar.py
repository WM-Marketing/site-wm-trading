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

O processo de publicacao esta no CLAUDE.md, secao "PROCESSO DE PUBLICACAO VIA
GITHUB". Ate 28/08 estas duas mencoes apontavam para ROTINA-ATUALIZACAO-SITE.md,
um arquivo que NUNCA existiu no repositorio — o guarda mandava o operador
consultar um documento inexistente justamente no momento mais critico.
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

# ══════════════════════════════════════════════════════════════════════════
# FORMULARIOS — a regra, fixada em 27/08/2026
# ══════════════════════════════════════════════════════════════════════════
# Os campos que existem hoje e a mecanica de hoje sao PRE-REQUISITO:
#
#   1) campo novo pode ser criado, sempre;
#   2) campo existente pode ser OCULTADO — menos os dois de aceite;
#   3) mas a informacao TEM que continuar sendo enviada, ainda que oculta.
#
# Por que ocultar e permitido e desaparecer nao e: api/contato.js e LISTA FIXA
# de campos — ela enumera um por um em vez de repassar ...data. Campo que para
# de ser enviado nao volta a aparecer no Zapier sozinho: ele chega vazio para
# sempre, e os 5 Zaps que o mapeiam passam a receber string vazia sem ninguem
# perceber. Nao ha erro, nao ha alerta — so um campo do Pipedrive que seca.
#
# Por que os DOIS aceites nao podem ser ocultados: consentimento oculto nao e
# consentimento (LGPD art. 8). O checkbox tem que estar visivel e o ato tem que
# ser do visitante. Por isso aqui eles sao conferidos como VISIVEIS, e nao
# apenas presentes — e o aceite_privacidade tambem como required, porque sem
# 'sim' a funcao devolve 400 e o lead morre.

# Piso de informacao por tipo de formulario. Medido do site em 27/08/2026:
# e o que os formularios coletam HOJE, e por decisao e o minimo de amanha.
PISO_POR_TIPO = {
    "contato":     {"nome", "email", "telefone", "empresa", "estado",
                    "segmento", "forma_resposta", "mensagem"},
    "segmentos":   {"nome", "email", "telefone", "empresa", "estado",
                    "segmento", "forma_resposta", "mensagem"},
    "ebook":       {"nome", "email", "empresa"},
    "whatsapp":    {"nome", "email", "telefone"},
    "carne-suina": {"nome", "empresa", "cargo", "email", "telefone",
                    "volume", "mensagem"},
}

# Informacao que o HANDLER injeta no payload em vez de coletar num campo do
# formulario. Conta como enviada — e a regra 3 levada ao extremo: nao ha campo
# nenhum, e a informacao chega. Ex.: o handler inline da carne-suina faz
# payload.segmento = 'Carne suina', porque a LP e de um segmento so.
# Campo do piso que uma ARVORE de idioma legitimamente NAO coleta.
#
# Medido em 28/08/2026: por um <input type="hidden" name="estado" value=""> ou
# por nao ter o campo nenhum, o payload que chega no Zapier e IDENTICO — 42
# campos, estado:'' nos dois casos. O api/contato.js e lista fixa e ja preenche
# vazio o que nao vem. Ou seja, exigir o campo oculto na arvore /en/ era no-op
# puro: mais markup para nenhum efeito.
#
# Entao a arvore /en/ fica sem o campo, como o build_en.py escreve, e o piso
# reconhece a isencao. NAO confundir com a regra 3 (ocultar pode, desaparecer
# nao): ela vale para campo que o site COLETA de alguem. Visitante de fora nao
# tem UF brasileira para informar — nao ha dado sendo perdido aqui.
PISO_ISENTO_POR_ARVORE = {
    "en": {"estado"},
}


def _isencao_da_arvore(pagina):
    """Campos do piso dispensados pela arvore em que a pagina vive."""
    primeira = pagina.replace("\\", "/").split("/")[0]
    return PISO_ISENTO_POR_ARVORE.get(primeira, set())


INJETADO_PELO_HANDLER = {
    "carne-suina": {"segmento"},
}

# Formularios com handler proprio, fora do js/contact-form.js. Sao legitimos e
# existem por motivo (a carne-suina preserva a tela de sucesso da LP), mas
# precisam ser DECLARADOS aqui — senao um <form> novo sem a classe
# contact-form-js passaria como se tivesse handler, e nao envia nada.
# Chave: (arquivo, id do form)  ->  tipo do formulario.
HANDLERS_PROPRIOS = {
    (os.path.join("importacao-carne-suina", "index.html"), "leadForm"): "carne-suina",
}

# O formulario de WhatsApp e montado em JS, nao existe em HTML nenhum.
FORM_EM_JS = {"whatsapp": os.path.join("js", "whatsapp-popup.js")}

# ══════════════════════════════════════════════════════════════════════════
# VERSAO EM INGLES E IDIOMA — a regra, fixada em 27/08/2026
# ══════════════════════════════════════════════════════════════════════════
# Decisao do Giovanni. Vale para pagina E para post de blog:
#
#   1) Quem for criar uma pagina PERGUNTA se ela vai ter versao em ingles.
#      A pergunta e obrigatoria — nao se assume nem que sim nem que nao.
#   2) Se sim, a versao em ingles e criada na mesma leva. A traducao e feita
#      pela IA da propria maquina de quem esta trabalhando — nao por servico
#      externo, e nao depois "quando der".
#   3) Depois de pronta, a PESSOA valida a traducao. Enquanto nao validou, a
#      traducao esta marcada como pendente e o guarda REPROVA a publicacao.
#   4) Post de blog carrega uma TAG VISIVEL do idioma da pagina.
#
# O item 1 e de processo: nenhum script sabe se a pergunta foi feita. O que da
# para cobrar aqui e o resultado — e e o que esta cobrado abaixo.
#
# Por que o item 4 existe (medido em 27/08/2026): ha 6 posts em ingles em
# /blog/, na MESMA listagem dos 207 em portugues, ordenados so por data. O card
# mostrava categoria e data e nada mais — o leitor brasileiro clicava e caia num
# texto em ingles sem aviso nenhum.

# A marca de "traducao ainda nao validada por uma pessoa".
# Em pagina: a chave no content/en/paginas.json. Em post: no frontmatter do .mdx.
# Ausente = traducao antiga, de antes desta regra (nao reprova, so e contada).
# Explicitamente false = criada sob esta regra e AINDA NAO VALIDADA -> reprova.
# A decisao do item 1 da regra, REGISTRADA na fonte.
#
# "Perguntou se vai ter versao em ingles?" nenhum script sabe. Mas a RESPOSTA da
# para exigir: toda fonte NOVA em content/ declara versao_en: true|false. Assim
# a pergunta deixa de ser honra e passa a ser um campo que falta.
#
# Quem e "nova": o git decide (ver _fontes_novas). Arquivo ainda nao commitado,
# ou acrescentado depois de DATA_DA_REGRA. As 295 fontes que ja existiam ficam
# isentas — nao ha como afirmar retroativamente que alguem foi perguntado.
CHAVE_VERSAO_EN = "versao_en"
DATA_DA_REGRA = "2026-08-27"

# Pastas de content/ que produzem pagina publica. content/en/ fica de fora: e o
# LADO ingles, nao uma pagina que precisa decidir se tera versao em ingles.
PASTAS_DE_PAGINA = ("pages", "segments", "services", "blog", "ebooks", "aircraft")

CHAVE_REVISADA = "traducao_revisada"

# Idioma do site. Post em outro idioma precisa da tag visivel.
IDIOMA_PADRAO = "pt-BR"
CLASSE_TAG_POST = "post-meta__idioma"
# Uma listagem por idioma, desde 28/08 (gerar_listagens_do_blog no gerador).
# A EN sai como en/blog.html, e nao en/blog/index.html: e a convencao da arvore
# /en/ e o caminho que o build_en.py deriva de "/en/blog/".
LISTAGENS_POR_IDIOMA = {
    "pt-BR": os.path.join("blog", "index.html"),
    "en": os.path.join("en", "blog.html"),
}

ACEITE_OBRIGATORIO = "aceite_privacidade"
ACEITE_OPCIONAL = "aceite_marketing"


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
                 "Ver o processo no CLAUDE.md, secao PROCESSO DE PUBLICACAO.")
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

    # ---------------------------------------------------------------- trava
    # Vazamento de idioma: pagina /en/ mandando o visitante para o portugues
    # quando a versao em ingles EXISTE. O menu ja era tratado desde 18/08, mas o
    # CORPO da home nao: 24 links (os 15 cards do carrossel, o "ver todos", as 4
    # modalidades, o solucoes-wm) nasciam apontando para PT, porque o corpo dela e
    # uma copia da home em portugues. Ninguem viu por 3 dias — nada checava.
    # Link para pagina SEM versao em ingles nao e erro: e o fallback honesto.
    # o mesmo mapa que o build_en usa, incluindo os destinos das paginas PT sem
    # irma em ingles (DESTINO_SEM_PAR) — senao a trava aprovaria justo o link que
    # foi corrigido a mao. Import tardio: os dois geradores so definem coisas, o
    # main() de ambos esta atras de __main__.
    sys.path.insert(0, os.path.join(ROOT_DIR, "scripts"))
    import build_en  # noqa: E402  (import tardio de proposito, ver acima)
    pares = {q["pt"]: q["en"] for q in paginas}
    pares.update(build_en.DESTINO_SEM_PAR)
    vazando = []
    for p in paginas:
        rel_en = p["en"].strip("/")
        arq_en = "en/index.html" if rel_en == "en" else rel_en + ".html"
        if not os.path.exists(os.path.join(ROOT_DIR, arq_en.replace("/", os.sep))):
            continue
        html_en = ler(arq_en)
        for pt, en in pares.items():
            if pt == "/":
                continue
            for forma in (pt, pt.rstrip("/")):
                if 'href="%s"' % forma in html_en:
                    vazando.append("%s -> %s (existe %s)" % (p["en"], forma, en))
                    break

    if vazando:
        rel.erro("%d link(s) em paginas /en/ levando ao portugues, tendo versao em "
                 "ingles:" % len(vazando))
        for v in vazando[:8]:
            rel.erro("    %s" % v)
        if len(vazando) > 8:
            rel.erro("    ... e mais %d" % (len(vazando) - 8))
    else:
        rel.ok("nenhuma pagina /en/ manda o visitante para o portugues a toa")


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
# J. Formularios
# --------------------------------------------------------------------------
FORM_RE = re.compile(r"<form\b.*?</form>", re.S | re.I)
CAMPO_RE = re.compile(r'name="([^"]+)"')


def _tag_do_campo(form_html, nome):
    """A tag <input>/<select>/<textarea> daquele name, ou None."""
    m = re.search(
        r'<(?:input|select|textarea)\b[^>]*\bname="%s"[^>]*>' % re.escape(nome),
        form_html, re.I)
    return m.group(0) if m else None


def _rotulo_que_envolve(form_html, nome):
    """O <label> que contem o campo.

    Um aceite escondido pelo label conta como escondido, mesmo que o <input>
    pareca normal — e o jeito mais facil de esconder um checkbox sem parecer.
    """
    for m in re.finditer(r"<label\b[^>]*>.*?</label>", form_html, re.S | re.I):
        if ('name="%s"' % nome) in m.group(0):
            return m.group(0)
    return None


OCULTO_RE = re.compile(
    r'type="hidden"'
    r'|display\s*:\s*none'
    r'|visibility\s*:\s*hidden'
    r'|class="[^"]*\bhidden\b',
    re.I)


def _esta_oculto(form_html, nome):
    """True quando o campo — ou o label que o envolve — esta escondido.

    Confere a MARCACAO, nao o CSS calculado: uma classe de projeto que esconda
    o campo por arquivo .css passa por aqui. E o limite honesto de um
    verificador estatico, e esta escrito de proposito para ninguem confundir
    "passou no verificador" com "esta visivel no navegador".
    """
    tag = _tag_do_campo(form_html, nome)
    if tag and OCULTO_RE.search(tag):
        return True
    rotulo = _rotulo_que_envolve(form_html, nome)
    if rotulo:
        abertura = rotulo[:rotulo.find(">") + 1]
        if OCULTO_RE.search(abertura):
            return True
    return False


def _tipo_do_form(pagina, form_html):
    """(tipo, tem_handler) — de onde sai o tipo, e se alguem escuta o submit."""
    m = re.search(r'data-form-type="([^"]*)"', form_html)
    if m:
        return m.group(1), "contact-form-js" in form_html
    m_id = re.search(r'\bid="([^"]+)"', form_html)
    chave = (pagina, m_id.group(1) if m_id else "")
    if chave in HANDLERS_PROPRIOS:
        return HANDLERS_PROPRIOS[chave], True
    return None, "contact-form-js" in form_html


def checar_formularios(rel):
    titulo("J. Formularios — piso de informacao e mecanica de envio")

    # Agrupa por problema: 28 paginas com a mesma falta viram uma linha, senao
    # o relatorio vira uma parede e ninguem le.
    grupos = {}

    def anotar(chave, pagina):
        grupos.setdefault(chave, []).append(pagina)

    total = 0
    for pagina in paginas_html():
        html = sem_comentarios(ler(pagina))
        for form_html in FORM_RE.findall(html):
            total += 1
            tipo, tem_handler = _tipo_do_form(pagina, form_html)

            if tipo is None:
                anotar("form sem data-form-type e sem handler declarado em "
                       "HANDLERS_PROPRIOS — nao envia para /api/contato", pagina)
                continue
            if tipo not in PISO_POR_TIPO:
                env = tipo.replace("-", "_").upper()
                anotar("data-form-type=%r desconhecido — sem ZAPIER_WEBHOOK_%s "
                       "a funcao devolve 503" % (tipo, env), pagina)
                continue
            if not tem_handler:
                anotar("[%s] sem a classe contact-form-js — o handler ignora o "
                       "form (contact-form.js:55) e o submit recarrega a pagina"
                       % tipo, pagina)
                continue

            campos = set(CAMPO_RE.findall(form_html))

            # 1) honeypot
            if "_gotcha" not in campos:
                anotar("[%s] sem o honeypot _gotcha — perde a barreira anti-spam "
                       "do cliente e do servidor" % tipo, pagina)

            # 2) os dois aceites, e VISIVEIS
            if ACEITE_OBRIGATORIO not in campos:
                anotar("[%s] sem %s — a funcao devolve 400 e NENHUM lead entra"
                       % (tipo, ACEITE_OBRIGATORIO), pagina)
            else:
                tag = _tag_do_campo(form_html, ACEITE_OBRIGATORIO) or ""
                if "required" not in tag.lower():
                    anotar("[%s] %s sem required — deixa enviar e a funcao "
                           "recusa com 400" % (tipo, ACEITE_OBRIGATORIO), pagina)
                if 'value="sim"' not in tag:
                    anotar("[%s] %s sem value=\"sim\" — a funcao compara com "
                           "'sim' e recusa qualquer outro valor"
                           % (tipo, ACEITE_OBRIGATORIO), pagina)
                if _esta_oculto(form_html, ACEITE_OBRIGATORIO):
                    anotar("[%s] %s OCULTO — consentimento oculto nao e "
                           "consentimento (LGPD art. 8)"
                           % (tipo, ACEITE_OBRIGATORIO), pagina)

            if ACEITE_OPCIONAL not in campos:
                anotar("[%s] sem %s" % (tipo, ACEITE_OPCIONAL), pagina)
            else:
                tag = _tag_do_campo(form_html, ACEITE_OPCIONAL) or ""
                if "required" in tag.lower():
                    anotar("[%s] %s com required — marketing e base legal "
                           "separada e nao pode ser condicao de envio"
                           % (tipo, ACEITE_OPCIONAL), pagina)
                if _esta_oculto(form_html, ACEITE_OPCIONAL):
                    anotar("[%s] %s OCULTO — consentimento oculto nao e "
                           "consentimento (LGPD art. 8)"
                           % (tipo, ACEITE_OPCIONAL), pagina)

            # 3) o texto do aceite, que vai para o CRM como prova do QUE
            # O atributo EXATO. Um "data-wm-aceite" solto casa tambem com
            # "data-wm-aceite-marketing", e um formulario que perdesse o texto
            # do aceite de privacidade mas mantivesse o de marketing passaria
            # batido — foi o unico caso que escapou no teste negativo.
            if not re.search(r"data-wm-aceite(?=[\s>=/])", form_html):
                anotar("[%s] sem [data-wm-aceite] — o texto aceito nao e "
                       "capturado e o registro de consentimento fica sem o QUE"
                       % tipo, pagina)

            # 4) o piso de informacao — regra 3: oculto pode, ausente nao
            injetado = INJETADO_PELO_HANDLER.get(tipo, set())
            isento = _isencao_da_arvore(pagina)
            faltando = sorted(PISO_POR_TIPO[tipo] - campos - injetado - isento)
            if faltando:
                anotar("[%s] abaixo do piso, nao envia: %s — pode ficar oculto, "
                       "mas tem que ser enviado" % (tipo, ", ".join(faltando)),
                       pagina)

    # ── o formulario de WhatsApp e montado em JS: nao existe em HTML nenhum ──
    for tipo, arquivo in sorted(FORM_EM_JS.items()):
        try:
            js = ler(arquivo)
        except FileNotFoundError:
            rel.erro("%s nao existe — o formulario de %s desapareceu"
                     % (arquivo, tipo))
            continue
        total += 1
        campos = set(CAMPO_RE.findall(js))
        faltando = sorted(PISO_POR_TIPO[tipo] - campos)
        if faltando:
            rel.erro("%s [%s] abaixo do piso: %s"
                     % (arquivo, tipo, ", ".join(faltando)))
        if "_gotcha" not in campos:
            rel.erro("%s [%s] sem o honeypot _gotcha" % (arquivo, tipo))
        for aceite in (ACEITE_OBRIGATORIO, ACEITE_OPCIONAL):
            if aceite not in campos:
                rel.erro("%s [%s] sem %s" % (arquivo, tipo, aceite))

    for chave, paginas in sorted(grupos.items()):
        exemplos = ", ".join(paginas[:3])
        resto = " (+%d)" % (len(paginas) - 3) if len(paginas) > 3 else ""
        rel.erro("%d form(s): %s" % (len(paginas), chave))
        rel.erro("    em: %s%s" % (exemplos, resto))

    if not grupos:
        rel.ok("%d formulario(s): piso de informacao completo, honeypot, aceites "
               "visiveis e handler declarado" % total)


# --------------------------------------------------------------------------
# K. Idioma: versao em ingles e tag no blog
# --------------------------------------------------------------------------
def _posts_e_idiomas():
    """[(slug, lang, revisada, arquivo)] de cada post em content/blog.

    revisada: True, False, ou None quando a chave nao existe (post antigo).
    """
    saida = []
    for caminho in sorted(glob.glob(os.path.join(ROOT_DIR, "content", "blog", "*.mdx"))):
        with open(caminho, encoding="utf-8", errors="replace") as fh:
            texto = fh.read()
        m_s = re.search(r'^slug:\s*"(.*?)"\s*$', texto, re.M)
        if not m_s:
            continue
        m_l = re.search(r'^lang:\s*"?([\w-]+)"?\s*$', texto, re.M)
        lang = m_l.group(1) if m_l else None
        if not lang:
            m_o = re.search(r'^originalUrl:\s*"(.*?)"\s*$', texto, re.M)
            lang = "en" if (m_o and "/en/" in m_o.group(1)) else IDIOMA_PADRAO
        m_r = re.search(r"^%s:\s*(true|false)\s*$" % CHAVE_REVISADA, texto, re.M)
        revisada = None if not m_r else (m_r.group(1) == "true")
        saida.append((m_s.group(1), lang, revisada, os.path.basename(caminho)))
    return saida


def _esta_na_listagem(listagem_html, slug):
    """True se a listagem tem um card apontando para aquele post.

    Casa o href com a fronteira do slug (o ponto do .html ou a barra final),
    senao 'aco-sucesso' seria encontrado dentro de 'aco-sucesso-parte-2'.
    """
    return bool(re.search(
        r'href="/blog/%s(?:\.html|/)"' % re.escape(slug), listagem_html))


def _fontes_novas():
    """Fontes de content/ que sao NOVAS: ainda nao commitadas, ou acrescentadas
    depois de DATA_DA_REGRA.

    Duas chamadas de git, nao uma por arquivo — sao ~295 fontes.
    Se o git nao responder (copia sem .git), devolve None e a checagem e
    ANUNCIADA como nao feita, em vez de passar calada.
    """
    nao_commitadas = git("ls-files", "--others", "--exclude-standard", "content")
    desde_a_regra = git("log", "--diff-filter=A", "--since", DATA_DA_REGRA,
                        "--name-only", "--format=", "--", "content")
    if nao_commitadas is None and desde_a_regra is None:
        return None
    novas = set()
    for bloco in (nao_commitadas, desde_a_regra):
        for linha in (bloco or "").splitlines():
            linha = linha.strip().replace("\\", "/")
            if linha:
                novas.add(linha)
    return novas


def _e_fonte_de_pagina(rel_git):
    partes = rel_git.split("/")
    if len(partes) < 2 or partes[0] != "content":
        return False
    return partes[1] in PASTAS_DE_PAGINA and rel_git.endswith((".json", ".mdx"))


def _declaracao_versao_en(rel_git):
    """True/False conforme declarado; None quando nao declara; "ilegivel" quando
    o JSON nao abre.

    A diferenca importa: dizer "sem declarar versao_en" para um arquivo com erro
    de sintaxe manda a pessoa procurar um campo faltando quando o problema e uma
    virgula. Foi o que o testar-idioma.py pegou em 27/08 — o fixture do teste
    gerava JSON invalido e a mensagem culpava o campo.
    """
    try:
        texto = ler(rel_git.replace("/", os.sep))
    except (FileNotFoundError, OSError):
        return None
    if rel_git.endswith(".json"):
        try:
            dados = json.loads(texto)
        except ValueError:
            return "ilegivel"
        if isinstance(dados, dict) and isinstance(dados.get(CHAVE_VERSAO_EN), bool):
            return dados[CHAVE_VERSAO_EN]
        return None
    m = re.search(r"^%s:\s*(true|false)\s*$" % CHAVE_VERSAO_EN, texto, re.M)
    return None if not m else (m.group(1) == "true")


def _marca_revisada(rel_git):
    """A marca traducao_revisada da fonte: True, False, ou None se ausente."""
    try:
        texto = ler(rel_git.replace("/", os.sep))
    except (FileNotFoundError, OSError):
        return None
    if rel_git.endswith(".json"):
        try:
            dados = json.loads(texto)
        except ValueError:
            return None
        v = dados.get(CHAVE_REVISADA) if isinstance(dados, dict) else None
        return v if isinstance(v, bool) else None
    m = re.search(r"^%s:\s*(true|false)\s*$" % CHAVE_REVISADA, texto, re.M)
    return None if not m else (m.group(1) == "true")


def checar_idioma(rel):
    titulo("K. Idioma — versao em ingles e tag no blog")

    # ── 1. tag de idioma nos posts que nao estao em portugues ──────────────
    posts = _posts_e_idiomas()
    fora_do_padrao = [(s, l, f) for s, l, _, f in posts if l != IDIOMA_PADRAO]

    # As listagens, uma por idioma. Lidas uma vez.
    listagens = {}
    for lang, rel_lst in LISTAGENS_POR_IDIOMA.items():
        try:
            listagens[lang] = ler(rel_lst)
        except FileNotFoundError:
            rel.erro("%s nao existe — rode 'python scripts/build_pages.py'" % rel_lst)

    sem_tag_post, sem_lang_html = [], []
    for slug, lang, _arq in fora_do_padrao:
        rel_html = os.path.join("blog", slug + ".html")
        try:
            html = ler(rel_html)
        except FileNotFoundError:
            rel.erro("%s declara lang=%s mas blog/%s.html nao existe"
                     % (slug, lang, slug))
            continue
        if CLASSE_TAG_POST not in html:
            sem_tag_post.append(slug)
        if ('<html lang="%s"' % lang) not in html:
            sem_lang_html.append(slug)

    if sem_tag_post:
        rel.erro("%d post(s) em outro idioma SEM a tag visivel no cabecalho: %s"
                 % (len(sem_tag_post), ", ".join(sem_tag_post[:5])))
        rel.erro("    rode 'python scripts/build_pages.py' — a tag sai de "
                 "tag_de_idioma() no gerador")
    if sem_lang_html:
        rel.erro("%d post(s) com <html lang> diferente do frontmatter: %s"
                 % (len(sem_lang_html), ", ".join(sem_lang_html[:5])))
    if not (sem_tag_post or sem_lang_html):
        if fora_do_padrao:
            idiomas = sorted(set(l for _, l, _ in fora_do_padrao))
            rel.ok("%d post(s) fora do portugues (%s) com tag visivel no "
                   "cabecalho e <html lang> correto"
                   % (len(fora_do_padrao), ", ".join(idiomas)))
        else:
            rel.ok("todos os posts estao em portugues — nenhuma tag necessaria")

    # ── 1b. cada post na listagem do SEU idioma, e em nenhuma outra ────────
    #
    # Isto substituiu a checagem da tag no card. Com uma listagem por idioma a
    # tag no card nao informa nada (em /blog/ nunca apareceria; em /en/blog/
    # apareceria em todos), mas a SEPARACAO em si passou a ser a coisa que pode
    # regredir — e ja esteve errada: ate 27/08 a listagem unica trazia os 6
    # posts em ingles no meio dos 207 em portugues.
    faltando_na_sua, vazando_na_outra, sem_listagem = [], [], set()
    for slug, lang, _r, _arq in posts:
        if lang not in listagens:
            sem_listagem.add(lang)
            continue
        if not _esta_na_listagem(listagens[lang], slug):
            faltando_na_sua.append("%s (%s)" % (slug, lang))
        for outro, html_outro in listagens.items():
            if outro != lang and _esta_na_listagem(html_outro, slug):
                vazando_na_outra.append("%s (%s) aparece na listagem %s"
                                        % (slug, lang, outro))

    if faltando_na_sua:
        rel.erro("%d post(s) fora da listagem do proprio idioma: %s"
                 % (len(faltando_na_sua), ", ".join(faltando_na_sua[:5])))
    if vazando_na_outra:
        rel.erro("%d post(s) na listagem do idioma ERRADO: %s"
                 % (len(vazando_na_outra), ", ".join(vazando_na_outra[:5])))
        rel.erro("    era o defeito de ate 27/08 — leitor de um idioma "
                 "encontrando artigo do outro no meio da grade")
    if sem_listagem:
        rel.aviso("idioma(s) sem listagem propria: %s — acrescente em "
                  "LISTAGENS_POR_IDIOMA" % ", ".join(sorted(sem_listagem)))
    if not (faltando_na_sua or vazando_na_outra):
        resumo = ", ".join("%s=%d" % (l, sum(1 for _s, ll, _r, _a in posts if ll == l))
                           for l in sorted(listagens))
        rel.ok("%d post(s) cada um so na listagem do seu idioma (%s)"
               % (len(posts), resumo))

    # ── 2. traducao aguardando validacao de uma pessoa ─────────────────────
    pendentes = ["blog/%s" % s for s, _, r, _ in posts if r is False]
    antigos_sem_marca = 0

    fonte = os.path.join(ROOT_DIR, "content", "en", "paginas.json")
    if os.path.exists(fonte):
        with open(fonte, encoding="utf-8") as f:
            try:
                paginas = json.load(f)
            except ValueError as e:
                rel.erro("content/en/paginas.json ilegivel: %s" % e)
                paginas = []
        for entrada in paginas:
            if CHAVE_REVISADA not in entrada:
                antigos_sem_marca += 1
            elif entrada.get(CHAVE_REVISADA) is False:
                pendentes.append(entrada.get("en", "?"))

    if pendentes:
        rel.erro("%d traducao(oes) AGUARDANDO VALIDACAO de uma pessoa "
                 "(%s: false):" % (len(pendentes), CHAVE_REVISADA))
        for alvo in pendentes[:10]:
            rel.erro("    %s" % alvo)
        if len(pendentes) > 10:
            rel.erro("    ...e mais %d" % (len(pendentes) - 10))
        rel.erro("    a pessoa confere a traducao e troca para "
                 "%s: true. Nao publique traducao que ninguem leu." % CHAVE_REVISADA)
    else:
        rel.ok("nenhuma traducao pendente de validacao")

    if antigos_sem_marca:
        rel.aviso("%d pagina(s) /en/ sem a marca %s — traducao anterior a esta "
                  "regra (27/08/2026). Nao reprova; ao revisar uma delas, "
                  "acrescente a marca." % (antigos_sem_marca, CHAVE_REVISADA))

    # ── 3. a decisao "vai ter versao em ingles?" registrada na fonte ────────
    novas = _fontes_novas()
    if novas is None:
        rel.aviso("git nao respondeu — NAO foi possivel conferir se as fontes "
                  "novas declaram %s. A checagem foi PULADA, nao aprovada."
                  % CHAVE_VERSAO_EN)
        return

    fontes = sorted(f for f in novas if _e_fonte_de_pagina(f))
    if not fontes:
        rel.ok("nenhuma fonte de pagina nova desde %s — nada a declarar"
               % DATA_DA_REGRA)
        return

    sem_declaracao, com_en_sem_marca, ilegiveis = [], [], []
    com_en = 0
    for fonte in fontes:
        decisao = _declaracao_versao_en(fonte)
        if decisao == "ilegivel":
            ilegiveis.append(fonte)
            continue
        if decisao is None:
            sem_declaracao.append(fonte)
            continue
        if decisao:
            com_en += 1
            # Declarou que TEM versao em ingles: a marca de validacao humana
            # passa a ser obrigatoria. Enquanto ela for false, o bloco 2 acima
            # ja reprova; aqui o que se cobra e ela EXISTIR.
            if _marca_revisada(fonte) is None:
                com_en_sem_marca.append(fonte)

    if ilegiveis:
        rel.erro("%d fonte(s) nova(s) com JSON ILEGIVEL (nao e campo faltando, "
                 "e erro de sintaxe — o build_pages.py tambem vai falhar):"
                 % len(ilegiveis))
        for f in ilegiveis:
            rel.erro("    %s" % f)

    if sem_declaracao:
        rel.erro("%d fonte(s) nova(s) sem declarar %s:"
                 % (len(sem_declaracao), CHAVE_VERSAO_EN))
        for f in sem_declaracao[:10]:
            rel.erro("    %s" % f)
        if len(sem_declaracao) > 10:
            rel.erro("    ...e mais %d" % (len(sem_declaracao) - 10))
        rel.erro("    PERGUNTE a quem pediu a pagina se ela vai ter versao em "
                 "ingles e registre a resposta na fonte:")
        rel.erro('      .json  ->  "%s": true   (ou false)' % CHAVE_VERSAO_EN)
        rel.erro("      .mdx   ->  %s: true     (ou false), no frontmatter"
                 % CHAVE_VERSAO_EN)

    if com_en_sem_marca:
        rel.erro("%d fonte(s) com %s: true e SEM a marca %s:"
                 % (len(com_en_sem_marca), CHAVE_VERSAO_EN, CHAVE_REVISADA))
        for f in com_en_sem_marca:
            rel.erro("    %s" % f)
        rel.erro("    quem cria a traducao escreve %s: false; a PESSOA confere "
                 "e troca para true." % CHAVE_REVISADA)

    if not (sem_declaracao or com_en_sem_marca or ilegiveis):
        rel.ok("%d fonte(s) de pagina nova(s) declaram %s (%d com versao em "
               "ingles)" % (len(fontes), CHAVE_VERSAO_EN, com_en))


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
    checar_formularios(rel)
    checar_idioma(rel)
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
