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


# Capa para paginas /en/ cuja irma PT tem hero de DESENHO PROPRIO, de onde
# capa_da_pagina_pt() nao consegue extrair nada. Hoje e so a de aeronaves: a
# /segmentos-aeronaves/ usa um mosaico de fotos em fundo branco (.aero-hero), e nao
# um hero escuro com imagem de fundo, entao nao ha "a mesma imagem" para reusar.
# Paginas PT sem versao PROPRIA em ingles, mas cujo assunto ja existe em /en/.
# Nao entram no paginas.json de proposito: la cada par vira pagina gerada MAIS
# hreflang, e /en/segments/fuels/ ja e o par declarado da
# /segmentos/derivados-petroleo/. Uma URL nao pode ser o par canonico de duas.
# Aqui e so DESTINO DE LINK, que e outra coisa: o card "Fuel" do carrossel da
# home em ingles apontava para portugues porque /segmentos/combustivel/ nao tem
# irma em ingles. Mas o site em ingles resolve combustivel e derivados de
# petroleo na MESMA pagina, entao mandar o visitante para la e o certo — em vez
# de joga-lo no portugues por falta de destino.
DESTINO_SEM_PAR = {
    "/segmentos/combustivel/": "/en/segments/fuels/",
}

CAPAS_PROPRIAS_EN = {
    "/en/segments/aircraft-import/": "/images/heros/jato-executivo.webp",
    # Mesmo caso desde 26/08/2026: a /segmentos/equipamentos-fotovoltaicos/
    # trocou o hero escuro pelo mosaico .fv-hero, entao nao tem mais
    # .dynamic-hero__bg para a capa_da_pagina_pt() ler. Sem esta linha a
    # pagina em ingles saia do build sem imagem de capa. O arquivo e o que a
    # versao PT usava ate a virada.
    "/en/segments/photovoltaic-equipment/": "/wp-content/uploads/2024/06/banner-fotovolaticos.webp",
    # Mesmo caso desde 27/08/2026: a /segmentos/maquinas/ tambem trocou o hero
    # generico pelo mosaico .mq-hero. Sem esta linha a versao em ingles sai do
    # build sem imagem de capa.
    "/en/segments/machines/": "/images/maquinas/faixa-tratores.jpg",
}


def capa_da_pagina_pt(url_pt):
    """Le a imagem de hero que a pagina em portugues ja usa.

    Reaproveitar em vez de escolher outra mantem as duas versoes visualmente
    iguais e nao adiciona peso: o arquivo ja esta no site e no cache de quem
    navegou pela versao PT.
    """
    rel = url_pt.strip("/")
    for tentativa in ([f"{rel}.html", f"{rel}/index.html"] if rel else ["index.html"]):
        caminho = os.path.join(ROOT, tentativa.replace("/", os.sep))
        if not os.path.exists(caminho):
            continue
        with open(caminho, encoding="utf-8") as f:
            html = f.read()
        m = re.search(r'<img[^>]+class="dynamic-hero__bg"[^>]*src="([^"]+)"', html)
        if not m:
            m = re.search(r'class="dynamic-hero__bg"[^>]*src="([^"]+)"', html)
        if not m:
            m = re.search(r'<img[^>]+src="([^"]+)"[^>]*class="dynamic-hero__bg"', html)
        if m:
            return m.group(1)
    return ""


def corpo_html(pagina):
    """Monta o miolo com as mesmas classes do site, para o visual bater."""
    # `blocos` e o conteudo BRUTO raspado do site antigo, guardado so para conferencia:
    # quem vira HTML e `secoes`. A guarda olhava o campo errado, entao uma pagina escrita
    # a mao (a de contato em ingles) era descartada por "falta de conteudo" mesmo tendo
    # secoes preenchidas. Agora olha o que de fato e renderizado.
    if not pagina.get("secoes"):
        return ""

    # hero: primeiro cabecalho + primeiro paragrafo depois dele
    titulo_hero = pagina["h1"]
    sub_hero = pagina["sub"]

    # A capa vem da pagina PT equivalente: e a mesma imagem que o site ja usa
    # para aquele assunto, entao a versao em ingles nao fica com hero vazio.
    capa = CAPAS_PROPRIAS_EN.get(pagina["en"]) or capa_da_pagina_pt(pagina["pt"])
    img = (f'<img src="{capa}" alt="{html_mod.escape(titulo_hero)}" '
           f'class="dynamic-hero__bg" />' if capa else "")

    partes = [f"""
    <section class="dynamic-hero">
      {img}
      <div class="container dynamic-hero__container">
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

    partes.append(formulario_en(pagina))
    return "\n".join(partes)


# Segmentos como aparecem no formulario PT — o Zap espera exatamente estes
# valores, entao o rotulo em ingles e so visual: o value enviado continua o
# mesmo. Trocar o value quebraria a classificacao do lead no Pipedrive.
# Segmentos do formulario em ingles: (value, rotulo).
#
# O VALUE E O QUE O ZAPIER LE — ele casa o lead por string exata numa lookup
# table e manda o que nao casa para o default. Por isso o value e o texto em
# PORTUGUES da tabela, e so o rotulo e traduzido.
#
# Ate 27/08/2026 esta lista trazia a taxonomia das paginas de segmento do site
# (Aco, Varejo, Vinho, Drone, Rebocadores...), que nao existe na tabela do
# Zapier: 11 dos 14 valores nao casavam e o lead chegava sem segmento. Agora sao
# os mesmos 16 do SEGMENTS_LIST do build_pages, na mesma ordem.
#
# "Parte e Peças Geral" sem o S nao e erro de digitacao: e como esta cadastrado
# no Zapier. Ver SEGMENTO_VALUE_ZAPIER no build_pages.py.
SEGMENTOS_EN = [
    ("Aeronaves", "Aircraft"),
    ("Energia Renovável", "Renewable Energy"),
    ("Alimentos e Bebidas", "Food and Beverages"),
    ("Vestuário/Têxtil", "Apparel/Textiles"),
    ("Informática e Eletrônicos", "IT and Electronics"),
    ("Metais & Derivados", "Metals & Derivatives"),
    ("Partes e Peças Automotivas", "Automotive Parts and Components"),
    ("Produtos Químicos", "Chemicals"),
    ("Parte e Peças Geral", "General Parts and Components"),
    ("Cosméticos e Healthcare", "Cosmetics and Healthcare"),
    ("Insumos e Matéria Prima", "Inputs and Raw Material"),
    ("Medicamentos", "Pharmaceuticals"),
    ("Combustível", "Fuel"),
    ("Máquinas e Equipamentos", "Machines and Equipment"),
    ("Setor Automotivo", "Automotive Sector"),
    ("Outros", "Others"),
]


def formulario_en(pagina):
    """Formulario em ingles para as paginas /en/.

    Tres diferencas em relacao ao formulario PT, todas de proposito:
      - telefone aceita formato internacional, nao a mascara (DDD) brasileira;
      - o campo Estado sai: quem chega pelo ingles em geral nao e do Brasil, e
        um obrigatorio impossivel de responder derruba a conversao;
      - o VALUE do segmento continua em portugues, porque e o que o Zap espera
        para classificar o lead no Pipedrive. So o rotulo e traduzido.

    data-form-type="contato" DE PROPOSITO, e nao "contato-en".

    O handler encontra a URL do webhook por qualquer um dos dois (sem uma variavel
    ZAPIER_WEBHOOK_CONTATO_EN ele cai no padrao), entao ate ai tanto faz. O risco
    esta DENTRO do Zap: os 4 ramos em ingles estao adormecidos desde 09/07, e um
    envio que nao casa com ramo nenhum e descartado em silencio — o lead some sem
    erro na tela. Como a pagina /en/contact-us/ e o destino de contato de toda a
    arvore em ingles, o custo de errar aqui e perder o lead justamente de quem veio
    de fora. "contato" cai no ramo validado em producao desde 09/07.

    O que se perde: a etiqueta especifica de ingles no Pipedrive. Quando os ramos EN
    forem reativados (BLOCO C), voltar para "contato-en" e uma linha.
    """
    opcoes = "".join(
        f'\n            <option value="{valor}">{rotulo}</option>'
        for valor, rotulo in SEGMENTOS_EN)

    return f"""
    <section class="page-section page-section--alternate" id="contact">
      <div class="container intro-container">
        <h2 class="card-title" style="font-size: var(--fs-lg); font-weight: var(--fw-semibold); margin-bottom: 10px;">Talk to our specialists</h2>
        <p class="card-desc" style="margin-bottom: 26px;">Tell us about your operation and our team will get back to you shortly.</p>
        <form class="contact-form-js grid gap-4 form-grid-wm form-grid-wm--2col" data-form-type="contato">
          <input type="text" name="_gotcha" tabindex="-1" autocomplete="off" class="hidden" aria-hidden="true" style="display:none;" />

          <input name="nome" required placeholder="Full name *" class="input-wm sm-col-span-2" />
          <input name="email" type="email" required placeholder="E-mail *" class="input-wm" />
          <input name="telefone" type="tel" required placeholder="Phone (with country code) *" pattern="[0-9\\s\\(\\)\\+\\-\\.]+" class="input-wm" />
          <input name="empresa" placeholder="Company" class="input-wm sm-col-span-2" />

          <select name="segmento" required class="input-wm sm-col-span-2">
            <option value="" disabled selected>Segment *</option>{opcoes}
          </select>

          <select name="forma_resposta" required class="input-wm sm-col-span-2">
            <option value="" disabled selected>How would you like to be contacted? *</option>
            <option value="E-mail">E-mail</option>
            <option value="WhatsApp">WhatsApp</option>
            <option value="Telefone">Phone</option>
          </select>

          <textarea name="mensagem" required rows="4" placeholder="How can we help? *" class="input-wm sm-col-span-2 resize-y"></textarea>

          <label class="sm-col-span-2 form-checkbox-label">
            <input type="checkbox" name="aceite_privacidade" required value="sim" />
            <span>I have read and agree to the <a href="/en/privacy-policy/" class="text-primary underline">Privacy Policy</a> and authorise WM Trading to process my data in order to respond to this request.</span>
          </label>

          <label class="sm-col-span-2 form-checkbox-label">
            <input type="checkbox" name="aceite_marketing" value="sim" />
            <span>I would also like to receive content, materials and commercial communications from WM Trading (optional).</span>
          </label>

          <button type="submit" class="btn btn-block sm-col-span-2 btn-lg">Send</button>
        </form>
      </div>
    </section>"""


# Rotulos do menu em ingles. Sao os que o SITE ATUAL ja publica em /en/ — copiados
# de la, nao traduzidos por mim: e paridade, e evita inventar termo comercial.
# Os itens de primeiro nivel (Segmentos, Solucoes...) nao entram aqui: ja tem
# data-i18n e o i18n.js os traduz. Nome de aeronave e nome proprio, nao se traduz.
ROTULOS_MENU_EN = {
    # rotulos de categoria do mega-menu
    "Aeronaves": "Aircraft",
    "Energia &amp; Ind\u00fastria": "Energy &amp; Industry",
    "Consumo &amp; Tech": "Consumer &amp; Tech",
    # segmentos
    "Importa\u00e7\u00e3o de Aeronaves": "Aircraft Import",
    "Equipamentos Fotovoltaicos": "Photovoltaic Equipment Import",
    "Cases de Usinas Fotovoltaicas": "Photovoltaic Plant Cases",
    "Produtos Qu\u00edmicos": "Chemicals Import",
    "Combust\u00edveis e Derivados": "Fuels Import",
    "M\u00e1quinas e Equipamentos": "Machines Import",
    "A\u00e7o": "Steel Import",
    "Rebocadores": "Aircraft Tugs Import",
    "Cosm\u00e9ticos": "Cosmetics Import",
    "Inform\u00e1tica e Telecom.": "IT and Telecom Import",
    "Autope\u00e7as": "Auto Parts Import",
    "Varejo": "Retail Import",
    "Vinho": "Wines Import",
    "Drone": "Drone Import",
    "Ver todos os segmentos \u2192": "View all segments \u2192",
    # solucoes
    "Solu\u00e7\u00f5es WM": "WM Solutions",
    "Solu\u00e7\u00f5es Log\u00edsticas 4PL": "4PL Logistics Solutions",
    "Importa\u00e7\u00e3o por Encomenda": "Custom Import",
    "Importa\u00e7\u00e3o por Conta e Ordem": "Import by Account and Order",
    "Assessoria Aduaneira": "Customs Advisory",
    # conteudo
    "E-Books": "E-Books",
    "Materiais e Infogr\u00e1ficos": "Materials and Infographics",
    # quem somos / contato
    "Sobre n\u00f3s": "About Us",
    "Trabalhe conosco": "Careers",
    "Fale conosco": "Contact Us",
    "Unidades": "Units",
    "Ouvidoria \u2197": "Ombudsman \u2197",
}


# Itens que somem do menu das paginas /en/ porque nao existem em ingles.
#
# A REGRA, e por que ela nao e "esconder tudo que nao tem ingles":
# esconder um item so faz sentido quando existe OUTRO caminho para aquele assunto.
# Os 8 modelos de aeronave sao detalhe da pagina "Aircraft Import", que continua no
# menu; o 4PL e detalhe de "Solutions". Ja Blog, WM Cast, E-Books e Unidades sao a
# UNICA porta para aquele conteudo — esconde-los deixaria a coluna "Content" vazia e
# cortaria conteudo que existe. Melhor levar a conteudo real em outra lingua do que
# a lugar nenhum. E o mesmo criterio do site atual, que tambem esconde as aeronaves
# e o 4PL e mantem Blog, Podcast, E-Books e Units.
#
# Efeito medido: zero cliques vindos do ingles para as paginas de aeronave em 16 meses.
OCULTAR_NO_MENU_EN = [
    "/aeronaves/citation-jet/",
    "/aeronaves/pilatus-24/",
    "/aeronaves/phenom-300/",
    "/aeronaves/phenom-100/",
    "/aeronaves/m500/",
    "/aeronaves/falcon-6x/",
    "/aeronaves/falcon-8x/",
    "/aeronaves/falcon-900lx/",
    "/solucoes-4pl/",
]


def oculta_sem_ingles(bloco):
    """Remove do bloco os <a> cujo destino nao tem versao em ingles.

    Sem isto o menu em ingles promete o que nao entrega: o visitante clica em
    "Citation Jet", cai numa pagina em portugues e o menu muda embaixo dele.
    """
    removidos = 0
    for destino in OCULTAR_NO_MENU_EN:
        for forma in (destino, destino.rstrip("/")):
            padrao = re.compile(
                r'\s*<a\b[^>]*href="' + re.escape(forma) + r'"[^>]*>.*?</a>', re.S)
            bloco, n = padrao.subn("", bloco)
            removidos += n
    return bloco, removidos


def rotulos_em_ingles(bloco):
    """Troca o TEXTO dos itens de menu que nao tem data-i18n.

    Sao 43 dos 48 itens do menu: os 5 de primeiro nivel foram marcados em 17/08,
    o resto nunca foi. Sem isto, uma pagina /en/ mostra "Segments" no topo e
    "Importacao de Aeronaves" ao passar o mouse.

    Trocado AQUI, na geracao, e nao no navegador: assim o ingles fica escrito no
    arquivo e o Google le o menu em ingles junto com a pagina.
    """
    trocados = 0
    for pt, en in ROTULOS_MENU_EN.items():
        for abre, fecha in ((">", "<"),):
            antes = bloco
            bloco = bloco.replace(abre + pt + fecha, abre + en + fecha)
            if bloco != antes:
                trocados += 1
    return bloco, trocados


_CACHE_EN = {}


def traducoes_en():
    """Le o dicionario ingles de js/i18n.js.

    FONTE UNICA de proposito: as 115 frases da home ja estao traduzidas la, e sao
    as mesmas que o botao de idioma usa desde sempre. Copiar para um JSON criaria
    duas verdades que divergem na primeira vez que alguem editar so uma.

    Le os dois formatos que o arquivo usa: valor entre aspas simples e, quando o
    texto tem apostrofo (company's), entre aspas duplas.
    """
    if _CACHE_EN:
        return _CACHE_EN
    js = open(os.path.join(ROOT, "js", "i18n.js"), encoding="utf-8").read()
    ini = js.find("  en: {")
    fim = js.find("\n  }\n};", ini)
    if ini == -1 or fim == -1:
        return {}
    d = {}
    for linha in js[ini:fim].split("\n"):
        m = re.match(r"\s*'([^']+)':\s*'(.*)'\s*,?\s*$", linha)
        if not m:
            m = re.match(r"\s*'([^']+)':\s*\"(.*)\"\s*,?\s*$", linha)
        if m:
            d[m.group(1)] = m.group(2)
    _CACHE_EN.update(d)
    return d


def home_em_ingles(pagina):
    """Gera /en/ com o DESENHO da home em portugues e o texto em ingles.

    POR QUE NAO USAR O MOLDE GENERICO
    A home tem 9 secoes proprias (hero com navio, cards, numeros, o carrossel dos
    15 segmentos, modalidades, CTA). Gerada pelo molde de pagina de texto — hero +
    paragrafos + formulario — /en/ virava OUTRA pagina, com 8 secoes genericas e
    sem carrossel. E ela e a 3a pagina mais clicada do site inteiro: 1.262 cliques
    em 16 meses. O site atual serve a home em ingles com o mesmo desenho da em
    portugues, entao isto e paridade, nao novidade.

    POR QUE TRADUZIR AQUI E NAO NO NAVEGADOR
    Se o ingles so aparecesse depois de o JS rodar, o arquivo entregue ao Google
    estaria em portugues — e /en/ seria lida como copia da home PT. Traduzido na
    geracao, o ingles fica escrito no arquivo.

    Cobertura conferida: 134 de 134 elementos marcados, 0 sem traducao.
    """
    tr = traducoes_en()
    if not tr:
        print("  AVISO: dicionario ingles vazio — /en/ nao foi gerada")
        return None

    html = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    faltando = []

    def troca(m):
        tag, attrs, _ehhtml, chave, inner = m.groups()
        # elemento com filho do mesmo tipo quebraria o casamento nao-guloso
        if re.search(r"<" + tag + r"[\s>]", inner):
            return m.group(0)
        if chave not in tr:
            faltando.append(chave)
            return m.group(0)
        return "<%s%s>%s</%s>" % (tag, attrs, tr[chave], tag)

    html = re.sub(r"<(\w+)([^>]*\bdata-i18n(-html)?=\"([^\"]+)\"[^>]*)>(.*?)</\1>",
                  troca, html, flags=re.S)
    if faltando:
        print("  AVISO: sem traducao em ingles: %s" % sorted(set(faltando)))

    # cabecalho: o que e especifico da home em portugues
    titulo = "WM Trading \u2014 %s" % pagina["titulo"]
    html = re.sub(r"<title>.*?</title>", "<title>%s</title>" % titulo, html, flags=re.S)
    html = re.sub(r'(<meta\s+name="description"\s+content=")[^"]*(")',
                  lambda m: m.group(1) + pagina["description"] + m.group(2), html)
    html = re.sub(r'(<link\s+rel="canonical"\s+href=")[^"]*(")',
                  lambda m: m.group(1) + SITE + "/en/" + m.group(2), html)
    html = re.sub(r'(<meta\s+property="og:url"\s+content=")[^"]*(")',
                  lambda m: m.group(1) + SITE + "/en/" + m.group(2), html)
    html = re.sub(r'(<meta\s+property="og:title"\s+content=")[^"]*(")',
                  lambda m: m.group(1) + titulo + m.group(2), html)
    html = re.sub(r'(<meta\s+property="og:description"\s+content=")[^"]*(")',
                  lambda m: m.group(1) + pagina["description"] + m.group(2), html)
    html = re.sub(r'<html[^>]*\blang="[^"]*"', '<html lang="en"', html, count=1)

    # CAMINHO ABSOLUTO — obrigatorio. A home e servida na raiz, onde relativo e
    # absoluto coincidem, entao ela pode ter src="images/...". Copiada para /en/,
    # o mesmo caminho passa a resolver contra /en/ e da 404 em tudo: CSS, logo,
    # imagens. Foi o que deixou a pagina de aeronaves sem CSS de 14 a 17/08, e a
    # secao G do verificar.py pegou de novo aqui, antes de publicar.
    html = bp.make_paths_absolute(html)

    saida = os.path.join(ROOT, "en", "index.html")
    os.makedirs(os.path.dirname(saida), exist_ok=True)
    with open(saida, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    return saida



# Textos que NAO sao conteudo de elemento e por isso escapam do data-i18n: alt de
# imagem, aria-label e title de iframe. Um alt em portugues numa pagina lang="en" e
# um defeito de acessibilidade silencioso — o leitor de tela troca de voz no meio.
ATRIBUTOS_QS_EN = [
    ("Fachada da sede da WM Trading em Vitória", "WM Trading headquarters in Vitória, Brazil"),
    ("Time da WM Trading no escritório em open space da matriz", "WM Trading team at the headquarters open space"),
    ("Time da WM Trading trabalhando no escritório em open space", "WM Trading team working in the open space office"),
    ("Área de convivência da sede da WM Trading", "Lounge area at the WM Trading headquarters"),
    ("Dois executivos frente a frente durante uma reunião de negócios",
     "Two executives face to face during a business meeting"),
    ("Corredor de um armazém logístico com prateleiras cheias de mercadorias",
     "Aisle of a logistics warehouse with shelves full of goods"),
    ("Profissional conferindo planilhas com calculadora e laptop",
     "Professional reviewing spreadsheets with a calculator and a laptop"),
    ("Navio porta-contêineres atracado ao lado de um caminhão no pátio do porto",
     "Container ship docked next to a truck in the port yard"),
    ("Certificação ISO 9001 emitida pela Bureau Veritas", "ISO 9001 certification issued by Bureau Veritas"),
    ("Equipe da WM Trading reunida na confraternização de fim de ano",
     "WM Trading team together at the end-of-year celebration"),
    ("Vídeo institucional da WM Trading", "WM Trading institutional video"),
    ("Marcas do grupo WM", "WM group brands"),
    ("A WM em números", "WM in numbers"),
    ("% de satisfação no primeiro semestre de", "% satisfaction in the first half of"),
    ("% de satisfação no segundo semestre de", "% satisfaction in the second half of"),
]


# Texto do CORPO da /segmentos/maquinas/, em pares (portugues, ingles).
#
# POR QUE UMA TABELA E NAO O data-i18n
# A /about/ e a home carregam data-i18n em cada elemento, e a traducao vem do
# dicionario do js/i18n.js. A pagina de maquinas nao: os 28 data-i18n dela sao
# do cabecalho e do rodape compartilhados; o corpo e prosa escrita a mao. Em vez
# de instrumentar a pagina inteira so para gerar a irma, trocamos os textos
# literalmente — mesmo mecanismo do ATRIBUTOS_QS_EN.
#
# A ORDEM DA LISTA NAO IMPORTA: a maquinas_em_ingles() aplica as trocas da mais
# longa para a mais curta, senao "Maquinas agricolas" traduziria o prefixo de
# "Maquinas agricolas prontas para embarque" e a entrada longa nunca casaria.
# Agrupamos por secao aqui so para dar para ler.
#
# Se uma entrada nao casar, o build AVISA em vez de seguir quieto: texto em
# portugues sobrando na pagina em ingles e exatamente o que ninguem percebe.
TEXTOS_MAQUINAS_EN = [
    # ── S1 hero ──
    ("Importe máquinas e", "Import machinery and"),
    ("equipamentos com", "equipment with"),
    ("agilidade e segurança</span>", "speed and security</span>"),
    ("Planejamento tributário, licenciamento e logística para tornar sua operação\n          mais eficiente, da compra no exterior à entrega na sua planta.",
     "Tax planning, licensing and logistics to make your operation more efficient,\n          from the purchase abroad to delivery at your plant."),
    ("Falar com um<br>especialista", "Talk to a<br>specialist"),

    # ── S3 intro ──
    ("Importação de <span class=\"mq-intro__title-hl\">Máquinas<br>\n        e Equipamentos</span>",
     "Importing <span class=\"mq-intro__title-hl\">Machinery<br>\n        and Equipment</span>"),
    ("Máquinas com tecnologia avançada podem representar um investimento\n        relevante para a indústria e o agronegócio. A WM estrutura a operação\n        desde a análise fiscal até a nacionalização, avaliando classificação,\n        licenciamento e requisitos aplicáveis à carga.",
     "Advanced-technology machinery can be a major investment for industry and\n        agribusiness. WM structures the operation from the tax analysis through to\n        customs clearance, assessing classification, licensing and the requirements\n        that apply to the cargo."),
    ("Quando necessário, o processo inclui suporte para Licença de Importação\n        e análise de exigências como LCVM junto ao IBAMA, reduzindo riscos antes\n        do embarque.",
     "Where required, the process includes support for the Import Licence and a\n        review of requirements such as the LCVM with IBAMA, reducing risk before\n        shipment."),
    ("Nossas soluções →", "Our solutions →"),

    # ── S4 beneficios ──
    ("Nossos diferenciais", "What sets us apart"),
    ("Benefícios de importar máquinas e", "Benefits of importing machinery and"),
    ("equipamentos com a WM", "equipment with WM"),
    ("Máquinas agrícolas", "Agricultural machinery"),
    ("Tratores, colheitadeiras, pulverizadores e implementos, com acompanhamento da operação do embarque à entrega na propriedade.",
     "Tractors, combine harvesters, sprayers and implements, with the operation followed from shipment through to delivery at the farm."),
    ("Máquinas industriais", "Industrial machinery"),
    ("Equipamentos para as indústrias têxtil, alimentícia, plástica e metalmecânica, com apoio na certificação e no desembaraço.",
     "Equipment for the textile, food, plastics and metalworking industries, with support on certification and customs clearance."),
    ("Direto do fabricante", "Direct from the manufacturer"),
    ("Capacidade de importar diretamente de fabricantes, reduzindo intermediários e buscando melhores condições comerciais e custos logísticos.",
     "The ability to import directly from manufacturers, cutting out intermediaries and pursuing better commercial terms and logistics costs."),
    ("Licença de Importação e LCVM", "Import Licence and LCVM"),
    ("Análise da classificação fiscal, verificação da necessidade de licenciamento e assessoria junto ao IBAMA para a emissão do LCVM quando aplicável.",
     "Analysis of the tariff classification, assessment of whether licensing is required, and support with IBAMA for issuing the LCVM where applicable."),
    ("Ex-tarifário e benefícios fiscais", "Ex-tariff and tax benefits"),
    ("Planejamento tributário para aproveitar a redução do Imposto de Importação sobre bens de capital sem produção nacional equivalente.",
     "Tax planning to take advantage of the reduced Import Duty on capital goods with no equivalent Brazilian production."),
    ("Máquinas usadas", "Used machinery"),
    ("Condução das etapas específicas exigidas para máquinas usadas, onde a Licença de Importação costuma travar a operação.",
     "Handling the specific steps required for used machinery, where the Import Licence tends to hold the operation up."),
    ("Saiba mais", "Learn more"),

    # ── S5 gestao ──
    ("Gestão completa<br>", "End-to-end management<br>"),
    ("da operação.<br>", "of the operation.<br>"),
    ("<span class=\"mq-gestao__hl\">documentação</span>", "<span class=\"mq-gestao__hl\">documentation</span>"),
    ("<span class=\"mq-gestao__hl\">entrega na planta</span>", "<span class=\"mq-gestao__hl\">delivery at the plant</span>"),
    ("Documentação<br>sob controle", "Documentation<br>under control"),
    ("Acompanhamento documental para reduzir inconsistências e atrasos.",
     "Document tracking to reduce inconsistencies and delays."),
    ("Pagamentos<br>coordenados", "Coordinated<br>payments"),
    ("Gestão dos pagamentos conforme as etapas e condições da operação.",
     "Payments managed in line with the stages and terms of the operation."),
    ("Gestão financeira<br>da operação", "Financial management<br>of the operation"),
    ("Acompanhamento de cartas de crédito e instrumentos da negociação internacional.",
     "Tracking of letters of credit and other international trade instruments."),
    ("Embarques<br>sob medida", "Tailored<br>shipments"),
    ("Organização de volumes, máquinas e prioridades conforme o cronograma de produção.",
     "Volumes, machines and priorities organised around the production schedule."),
    ("Visibilidade<br>ponta a ponta", "End-to-end<br>visibility"),
    ("Monitoramento dos embarques e dos principais marcos da operação.",
     "Monitoring of shipments and of the key milestones in the operation."),
    ("Da chegada ao<br>destino final", "From arrival to<br>final destination"),
    ("Coordenação da logística nacional, inclusive de cargas superdimensionadas, até a planta.",
     "Coordination of domestic logistics, including oversized cargo, all the way to the plant."),
    ("Coordenamos diferentes etapas da importação para dar mais",
     "We coordinate the different stages of the import to bring more"),
    ("<strong>previsibilidade, controle e eficiência</strong>",
     "<strong>predictability, control and efficiency</strong>"),
    ("à aquisição de máquinas e equipamentos.", "to the purchase of machinery and equipment."),
    ("Conheça nossas soluções →", "See our solutions →"),

    # ── S7 diferenciais ──
    ("<span class=\"mq-diff__title-hl\">Diferenciais da WM</span> na importação de máquinas e equipamentos",
     "<span class=\"mq-diff__title-hl\">What sets WM apart</span> in importing machinery and equipment"),
    ("Relacionamento e suporte junto a fornecedores internacionais.",
     "Relationships with and support from international suppliers."),
    ("Planejamento de embarques, cargas especiais e cronogramas.",
     "Planning of shipments, special cargo and schedules."),
    ("Gestão da Licença de Importação e acompanhamento da entrada no Brasil.",
     "Management of the Import Licence and of entry into Brazil."),
    ("Análise de alternativas aplicáveis a cada operação.",
     "Analysis of the alternatives available for each operation."),
    ("Estruturação da compra e importação internacional.",
     "Structuring of the international purchase and import."),
    ("92% de parametrização em canal verde!", "92% cleared through the green channel!"),
    ("Nosso índice de parametrização em canal verde chega a 92%, e apenas 5% das\n          operações são retidas em canal amarelo. Na prática, o tempo de nacionalização\n          e de liberação da carga no porto com a WM é muito mais curto.",
     "Our green-channel clearance rate reaches 92%, with only 5% of operations held\n          in the yellow channel. In practice, customs clearance and cargo release at\n          the port are far quicker with WM."),

    # ── S8 resultados ──
    ("Nossos<br>\n        <span class=\"mq-result__title-hl\">resultados</span>",
     "Our<br>\n        <span class=\"mq-result__title-hl\">results</span>"),
    ("Como resultado do desejo de <strong>importar máquinas</strong> com as condições\n        mais vantajosas do mercado, conquistamos o índice de\n        <span class=\"mq-result__num\">92%</span> de\n        <strong>parametrização em canal verde</strong>, agregando mais\n        <strong>segurança</strong> e <strong>agilidade</strong> às operações.",
     "Out of the drive to <strong>import machinery</strong> on the best terms in the\n        market, we reached a <span class=\"mq-result__num\">92%</span>\n        <strong>green-channel clearance rate</strong>, bringing more\n        <strong>security</strong> and <strong>speed</strong> to our operations."),
    ("Isso significa que o tempo de nacionalização e liberação da carga no porto\n      <strong>com a WM é muito mais rápido.</strong> Conte com o know-how da WM para\n      importar máquinas através das melhores oportunidades do comércio internacional.",
     "That means customs clearance and cargo release at the port are\n      <strong>much faster with WM.</strong> Count on WM's know-how to import machinery\n      through the best opportunities in international trade."),

    # ── S9 CTA (o formulario e trocado a parte, ver formulario_maquinas_en) ──
    ("Importe máquinas e equipamentos<br>", "Import machinery and equipment<br>"),
    ("com <span class=\"mq-cta__hl\">", "with <span class=\"mq-cta__hl\">"),
    ("Conte com planejamento tributário, gestão logística e\n        acompanhamento da operação de ponta a ponta.",
     "Count on tax planning, logistics management and end-to-end\n        tracking of the operation."),
    ("Fale com um especialista e tire suas dúvidas.", "Talk to a specialist and get your questions answered."),

    # ── alt e aria-label ──
    ("Frota de tratores em operação no campo ao pôr do sol",
     "Fleet of tractors working in the field at sunset"),
    ("Colheitadeira e trator em operação no campo",
     "Combine harvester and tractor working in the field"),
    ("Colheitadeira embarcada em prancha no porto",
     "Combine harvester loaded onto a lowboy trailer at the port"),
    ("Trator sendo transportado em terminal portuário",
     "Tractor being transported at a port terminal"),
    ("Caminhão-prancha transportando trator", "Lowboy truck carrying a tractor"),
    ("Carreta com carga superdimensionada e escolta em rodovia",
     "Truck with oversized cargo and escort on the highway"),
    ("Máquina industrial em operação", "Industrial machine in operation"),
    ("Máquinas agrícolas prontas para embarque", "Agricultural machinery ready for shipment"),
    ("Selo de reconhecimento: 92% de parametrização em canal verde",
     "Recognition seal: 92% cleared through the green channel"),
    ("Contêiner WM Trading e pá carregadeira — We Make it better",
     "WM Trading container and wheel loader — We Make it better"),
    ("Reproduzir vídeo", "Play video"),
    ("Fechar vídeo", "Close video"),
    ("Vídeo institucional", "Corporate video"),
]


FORM_MAQUINAS_EN = '''<form class="mq-cta__form contact-form-js" data-form-type="segmentos">
        <input type="text" name="_gotcha" tabindex="-1" autocomplete="off" aria-hidden="true" style="display:none;">

        <div class="mq-cta__row">
          <label class="mq-cta__field-label" for="mq-nome">Full name *</label>
          <input class="mq-cta__input" id="mq-nome" name="nome" type="text" required>
        </div>

        <div class="mq-cta__row mq-cta__row--2">
          <div>
            <label class="mq-cta__field-label" for="mq-email">E-mail *</label>
            <input class="mq-cta__input" id="mq-email" name="email" type="email" required>
          </div>
          <div>
            <label class="mq-cta__field-label" for="mq-tel">Phone (with country code) *</label>
            <input class="mq-cta__input" id="mq-tel" name="telefone" type="tel" required
                   pattern="[0-9\\s\\(\\)\\+\\-\\.]+" placeholder="+55 27 99999-0000">
          </div>
        </div>

        <div class="mq-cta__row mq-cta__row--2">
          <div>
            <label class="mq-cta__field-label" for="mq-empresa">Company</label>
            <input class="mq-cta__input" id="mq-empresa" name="empresa" type="text">
          </div>
          <div>
            <label class="mq-cta__field-label" for="mq-segmento">Segment</label>
            <select class="mq-cta__input" id="mq-segmento" name="segmento">%s
            </select>
          </div>
        </div>

        <div class="mq-cta__row">
          <label class="mq-cta__field-label" for="mq-forma">How would you like to be contacted? *</label>
          <select class="mq-cta__input" id="mq-forma" name="forma_resposta" required>
            <option value="" disabled selected>Select</option>
            <option value="WhatsApp">WhatsApp</option>
            <option value="Telefone">Phone</option>
            <option value="E-mail">E-mail</option>
          </select>
        </div>

        <div class="mq-cta__row">
          <label class="mq-cta__field-label" for="mq-mensagem">Message *</label>
          <textarea class="mq-cta__input mq-cta__textarea" id="mq-mensagem" name="mensagem" rows="4" required></textarea>
        </div>

        <label class="mq-cta__check">
          <input type="checkbox" name="aceite_privacidade" required value="sim">
          <span data-wm-aceite>I have read and agree to the <a href="/en/privacy-policy/">Privacy Policy</a> and authorise WM Trading to process my data in order to respond to this request.</span>
        </label>

        <label class="mq-cta__check">
          <input type="checkbox" name="aceite_marketing" value="sim">
          <span data-wm-aceite-marketing>I would also like to receive content, materials and commercial communications from WM Trading (optional).</span>
        </label>

        <button type="submit" class="mq-cta__submit">SEND</button>
      </form>'''


def formulario_maquinas_en():
    """Campos do formulario da /en/segments/machines/, na marcacao .mq-cta__.

    Nao da para reaproveitar o formulario_en(): aquele devolve uma <section>
    inteira no molde generico, e aqui o formulario vive dentro do layout proprio
    do CTA. O que se reaproveita sao as TRES REGRAS dele, que existem por motivo:

      - o campo Estado sai. Quem chega pelo ingles em geral nao e do Brasil, e um
        obrigatorio impossivel de responder derruba a conversao;
      - o telefone aceita formato internacional, nao a mascara (DDD) brasileira;
      - o VALUE do segmento continua em PORTUGUES. E o que o Zap espera para
        classificar o lead no Pipedrive; so o rotulo e traduzido.

    O data-form-type continua "segmentos", igual ao da versao PT: os ramos em
    ingles do Zap estao adormecidos desde 09/07, e um envio que nao casa com ramo
    nenhum e descartado em silencio — o lead sumiria sem erro na tela.
    """
    opcoes = "".join(
        '\n              <option value="%s"%s>%s</option>'
        % (valor, " selected" if valor == "Máquinas e Equipamentos" else "", rotulo)
        for valor, rotulo in SEGMENTOS_EN)

    return FORM_MAQUINAS_EN % opcoes


def maquinas_em_ingles(pagina):
    """Gera /en/segments/machines/ com o DESENHO da /segmentos/maquinas/.

    Mesma razao da home e da /about/: a pagina de maquinas tem layout proprio de
    9 secoes (mosaico no hero, sanfona de beneficios, faixa de resultados). Pelo
    molde generico ela viraria outra pagina, sem nada disso.

    Reaproveita o /css/maquinas.css e o /js/maquinas.js sem copia: as classes
    .mq- sao as mesmas nos dois idiomas.

    A SECAO DE BLOG SAI. A vitrine da versao PT lista posts de /blog/, e nao
    existe blog em ingles — a arvore /en/ tem 27 paginas e nenhuma e post.
    Mandar quem le em ingles para um artigo em portugues, sem aviso, e pior do
    que nao ter a secao. A versao EN fica com 8 secoes.
    """
    origem = os.path.join(ROOT, "segmentos", "maquinas.html")
    if not os.path.exists(origem):
        print("  AVISO: segmentos/maquinas.html nao existe — /en/segments/machines/ nao foi gerada")
        return None
    html = open(origem, encoding="utf-8").read()

    # 1) fora a vitrine de blog
    ini = html.find('<section class="mq-blog"')
    if ini == -1:
        print("  AVISO: secao .mq-blog nao encontrada — a versao EN pode ter saido com posts em portugues")
    else:
        fim = html.index("</section>", ini) + len("</section>")
        # o comentario que abre a secao tambem vai junto
        abre = html.rfind("<!--", 0, ini)
        html = html[:abre] + html[fim:]

    # 2) formulario em ingles no lugar do brasileiro (Estado sai, tel internacional)
    f_ini = html.find('<form class="mq-cta__form')
    if f_ini == -1:
        print("  AVISO: formulario nao encontrado em maquinas.html")
    else:
        f_fim = html.index("</form>", f_ini) + len("</form>")
        html = html[:f_ini] + formulario_maquinas_en() + html[f_fim:]

    # 3) o texto do corpo
    faltando = []
    # DA MAIS LONGA PARA A MAIS CURTA, sempre. "Maquinas agricolas" e prefixo de
    # "Maquinas agricolas prontas para embarque": na ordem do arquivo a entrada
    # curta traduzia o prefixo e a longa nunca mais casava. Ordenar por tamanho
    # resolve isso sem depender de ninguem manter a lista na ordem certa.
    for ptxt, entxt in sorted(TEXTOS_MAQUINAS_EN, key=lambda e: -len(e[0])):
        if ptxt not in html:
            faltando.append(ptxt[:60])
            continue
        html = html.replace(ptxt, entxt)
    if faltando:
        print("  AVISO: %d trecho(s) de TEXTOS_MAQUINAS_EN nao casaram (texto mudou na versao PT?):"
              % len(faltando))
        for t in faltando:
            print("           %r" % t)

    # 4) links do corpo que tem par em ingles
    for pt_url, en_url in (("/solucoes-wm/", "/en/solutions-wm/"),
                           ("/politica-de-privacidade/", "/en/privacy-policy/")):
        html = html.replace('href="%s"' % pt_url, 'href="%s"' % en_url)

    # 5) cabecalho: titulo, descricao, canonical, og, lang
    titulo = "WM Trading — %s" % pagina["titulo"]
    html = re.sub(r"<title>.*?</title>", "<title>%s</title>" % titulo, html, flags=re.S)
    for prop, valor in (('name="description"', pagina["description"]),
                        ('property="og:description"', pagina["description"]),
                        ('property="og:title"', titulo)):
        html = re.sub(r'(<meta\s+' + prop + r'\s+content=")[^"]*(")',
                      lambda m, v=valor: m.group(1) + v + m.group(2), html)
    for tag in (r'<link\s+rel="canonical"\s+href="', r'<meta\s+property="og:url"\s+content="'):
        html = re.sub(r"(" + tag + r')[^"]*(")',
                      lambda m: m.group(1) + SITE + pagina["en"] + m.group(2), html)
    html = re.sub(r'<meta\s+property="og:locale"\s+content="[^"]*"',
                  '<meta property="og:locale" content="en_US"', html, count=1)
    html = re.sub(r'<html[^>]*\blang="[^"]*"', '<html lang="en"', html, count=1)

    # mesmo motivo da home: caminho relativo copiado para /en/ resolve contra /en/
    html = bp.make_paths_absolute(html)

    saida = caminho_saida(pagina["en"])
    os.makedirs(os.path.dirname(saida), exist_ok=True)
    with open(saida, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    return saida


def quem_somos_em_ingles(pagina):
    """Gera /en/about/ com o DESENHO da /about/ em portugues e o texto em ingles.

    Mesma razao da home (ver home_em_ingles): a /about/ tem 10 secoes proprias —
    hero com a sede, mosaico, KPIs, os 7 valores, medidores de satisfacao. Pelo
    molde generico de pagina de texto ela virava outra pagina, sem nada disso.

    O texto sai do mesmo dicionario de js/i18n.js que o botao de idioma usa, e e
    escrito NO ARQUIVO: se dependesse do JS, o que o Google le seria portugues e
    /en/about/ passaria por copia da versao PT.

    Alem do que o data-i18n cobre, aqui tambem trocamos alt/aria-label (ver
    ATRIBUTOS_QS_EN) e o link do botao de vagas, que aponta para /carreiras/ e na
    arvore em ingles tem par proprio.
    """
    tr = traducoes_en()
    if not tr:
        print("  AVISO: dicionario ingles vazio — /en/about/ nao foi gerada")
        return None

    origem = os.path.join(ROOT, "about.html")
    if not os.path.exists(origem):
        print("  AVISO: about.html nao existe — rode o build_pages.py antes")
        return None
    html = open(origem, encoding="utf-8").read()

    faltando = []

    def troca(m):
        tag, attrs, _ehhtml, chave, inner = m.groups()
        if re.search(r"<" + tag + r"[\s>]", inner):
            return m.group(0)
        if chave not in tr:
            if chave.startswith("qs."):
                faltando.append(chave)
            return m.group(0)
        return "<%s%s>%s</%s>" % (tag, attrs, tr[chave], tag)

    html = re.sub(r"<(\w+)([^>]*\bdata-i18n(-html)?=\"([^\"]+)\"[^>]*)>(.*?)</\1>",
                  troca, html, flags=re.S)
    if faltando:
        print("  AVISO: sem traducao em ingles: %s" % sorted(set(faltando)))

    for ptxt, entxt in ATRIBUTOS_QS_EN:
        html = html.replace(ptxt, entxt)

    # o botao de vagas tem par em ingles
    html = html.replace('href="/carreiras/" class="btn"', 'href="/en/careers/" class="btn"')

    titulo = "WM Trading \u2014 %s" % pagina["titulo"]
    html = re.sub(r"<title>.*?</title>", "<title>%s</title>" % titulo, html, flags=re.S)
    for prop, valor in (('name="description"', pagina["description"]),
                        ('property="og:description"', pagina["description"]),
                        ('property="og:title"', titulo)):
        html = re.sub(r'(<meta\s+' + prop + r'\s+content=")[^"]*(")',
                      lambda m, v=valor: m.group(1) + v + m.group(2), html)
    for tag in (r'<link\s+rel="canonical"\s+href="', r'<meta\s+property="og:url"\s+content="'):
        html = re.sub(r'(' + tag + r')[^"]*(")',
                      lambda m: m.group(1) + SITE + pagina["en"] + m.group(2), html)
    html = re.sub(r'<meta\s+property="og:locale"\s+content="[^"]*"',
                  '<meta property="og:locale" content="en_US"', html, count=1)
    html = re.sub(r'<html[^>]*\blang="[^"]*"', '<html lang="en"', html, count=1)

    # mesmo motivo da home: caminho relativo copiado para /en/ resolve contra /en/
    html = bp.make_paths_absolute(html)

    saida = caminho_saida(pagina["en"])
    os.makedirs(os.path.dirname(saida), exist_ok=True)
    with open(saida, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    return saida


def menu_para_ingles(caminho_arquivo, pares):
    """Faz o menu e o rodape das paginas /en/ apontarem para as paginas /en/.

    O molde de menu vem do index.html, entao nasce apontando para os enderecos em
    portugues. Sem esta troca, quem chega do Google numa pagina em ingles — 10% do
    organico — volta para o portugues no primeiro clique do menu.

    So troca o que TEM par. Aeronaves, blog, podcast e materiais nao tem versao em
    ingles: continuam apontando para o portugues, que e honesto — melhor levar ao
    conteudo certo em outra lingua do que a lugar nenhum.

    Limitado ao cabecalho e ao rodape de proposito: o corpo da pagina vem do
    content/en/paginas.json e nao deve ser reescrito por busca e troca.
    """
    with open(caminho_arquivo, encoding="utf-8") as f:
        html = f.read()

    trocas = 0

    def troca_bloco(bloco):
        nonlocal trocas
        for pt, en in pares.items():
            if pt == "/":
                continue  # o logo aponta para a home; tratado a parte
            for forma in (pt, pt.rstrip("/")):
                antes = bloco
                bloco = bloco.replace(f'href="{forma}"', f'href="{en}"')
                if bloco != antes:
                    trocas += 1
        # o logo e o "voltar para o inicio" vao para a home em ingles
        bloco = bloco.replace('href="/"', 'href="/en/"')
        bloco, n = oculta_sem_ingles(bloco)
        trocas += n
        bloco, n = rotulos_em_ingles(bloco)
        trocas += n
        # Os 5 titulos de primeiro nivel e os 22 do rodape TEM data-i18n, entao o
        # navegador ja os mostrava em ingles. Mas no ARQUIVO continuavam em
        # portugues — e e o arquivo que o Google le. Embutido aqui, a pagina /en/
        # fica inteira em ingles na origem, sem depender do JS rodar.
        tr = traducoes_en()

        def _marcado(m):
            tag, attrs, _eh, chave, inner = m.groups()
            if re.search(r"<" + tag + r"[\s>]", inner) or chave not in tr:
                return m.group(0)
            return "<%s%s>%s</%s>" % (tag, attrs, tr[chave], tag)

        bloco = re.sub(r'<(\w+)([^>]*\bdata-i18n(-html)?="([^"]+)"[^>]*)>(.*?)</\1>',
                       _marcado, bloco, flags=re.S)
        return bloco

    # O rodape nao usa a tag semantica <footer> (e uma div .footer-links), so o
    # marcador de comentario do build_pages.py serve como inicio confiavel.
    for abre, fecha in (("<header", "</header>"), ('<div class="footer-links">', "</body>")):
        i = html.find(abre)
        j = html.find(fecha, i)
        if i == -1 or j == -1:
            continue
        html = html[:i] + troca_bloco(html[i:j]) + html[j:]

    if trocas:
        with open(caminho_arquivo, "w", encoding="utf-8", newline="\n") as f:
            f.write(html)
    return trocas


def corpo_para_ingles(caminho_arquivo, pares):
    """Faz os links DO CORPO apontarem para /en/. So para paginas de corpo copiado.

    O menu_para_ingles se limita a cabecalho e rodape de proposito: nas paginas de
    molde generico o corpo vem do content/en/paginas.json e nao pode ser reescrito
    por busca e troca. Mas a home e a /about/ nao usam molde nenhum — o corpo delas
    e o corpo da pagina em PORTUGUES copiado, com os data-i18n traduzidos. Os links
    vieram junto, apontando para portugues, e nada os corrigia.

    O buraco era grande: 24 links so na home — os 15 cards do carrossel de
    segmentos, o "ver todos", as 4 modalidades e o solucoes-wm. Quem chegava do
    Google na home em ingles (10% do organico) caia em portugues no primeiro
    clique de CONTEUDO, nao so no menu, que ja estava resolvido desde 18/08.

    Troca o que tem par no paginas.json MAIS o DESTINO_SEM_PAR, para os casos em
    que a pagina PT nao tem irma em ingles mas o assunto dela ja existe em /en/.
    O que nao esta em nenhum dos dois continua apontando para o portugues: levar
    ao conteudo certo em outra lingua e melhor do que a lugar nenhum.

    A troca casa o atributo href INTEIRO, com as aspas. E o que impede
    href="/segmentos" de comer o comeco de href="/segmentos/autopecas/".
    """
    with open(caminho_arquivo, encoding="utf-8") as f:
        html = f.read()

    # o corpo e o que sobra entre o fim do cabecalho e o inicio do rodape; os dois
    # extremos sao do menu_para_ingles e nao devem ser mexidos aqui
    i = html.find("</header>")
    j = html.find('<div class="footer-links">', i)
    if i == -1 or j == -1:
        return 0

    corpo, trocas = html[i:j], 0
    for pt, en in dict(pares, **DESTINO_SEM_PAR).items():
        formas = (pt,) if pt == "/" else (pt, pt.rstrip("/"))
        for forma in formas:
            if not forma:
                continue
            alvo = 'href="%s"' % forma
            n = corpo.count(alvo)
            if n:
                corpo = corpo.replace(alvo, 'href="%s"' % en)
                trocas += n

    if trocas:
        with open(caminho_arquivo, "w", encoding="utf-8", newline="\n") as f:
            f.write(html[:i] + corpo + html[j:])
    return trocas


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

    gerados, com_par, links_en, links_corpo = 0, 0, 0, 0
    pares = {p["pt"]: p["en"] for p in paginas}
    print(f"gerando {len(paginas)} paginas em /en/\n")

    for p in paginas:
        saida = caminho_saida(p["en"])
        os.makedirs(os.path.dirname(saida), exist_ok=True)

        # A HOME NAO USA O MOLDE GENERICO: ela tem 9 secoes proprias e e a 3a
        # pagina mais clicada do site. Ver home_em_ingles().
        corpo_copiado = False
        if p["en"] == "/en/":
            if home_em_ingles(p) is None:
                continue
            corpo_copiado = True
        # A /about/ TAMBEM nao usa o molde generico: 10 secoes proprias. Ver
        # quem_somos_em_ingles().
        elif p["en"].rstrip("/") == "/en/about":
            if quem_somos_em_ingles(p) is None:
                continue
            corpo_copiado = True
        # A /segmentos/maquinas/ e a TERCEIRA pagina de corpo proprio: 9 secoes
        # escritas a mao, com o mesmo css/js dos dois idiomas. Ver
        # maquinas_em_ingles() — e a irma da trava em SEGMENT_URL_OVERRIDES do
        # build_pages, que impede o gerador de refazer a versao PT.
        elif p["en"].rstrip("/") == "/en/segments/machines":
            if maquinas_em_ingles(p) is None:
                continue
            corpo_copiado = True
        # A /en/blog/ e o unico caso em que o corpo JA ESTA PRONTO quando este
        # script roda: quem escreve as duas listagens e o build_pages.py, que e
        # onde estao os posts (ver gerar_listagens_do_blog). Aqui so passamos
        # para traduzir o menu e injetar o hreflang — reescrever pelo molde
        # generico apagaria a grade de artigos.
        elif p["en"].rstrip("/") == "/en/blog":
            if not os.path.exists(caminho_saida(p["en"])):
                print("  AVISO: /en/blog/ nao existe — rode o build_pages.py antes")
                continue
        else:
            corpo = corpo_html(p)
            if not corpo:
                print(f"  pulada (sem conteudo): {p['en']}")
                continue
            bp.render_html_page(
                saida, p["titulo"], p["description"], corpo,
                head_tpl, header_tpl, footer_tpl, lang="en")

        # menu e rodape apontando para as paginas /en/ que existem
        links_en += menu_para_ingles(saida, pares)

        # nas duas de corpo copiado da versao PT, os links do CONTEUDO tambem
        # nasciam em portugues; nas de molde generico o corpo vem do JSON em
        # ingles e nao pode ser reescrito. Ver corpo_para_ingles().
        if corpo_copiado:
            links_corpo += corpo_para_ingles(saida, pares)

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
    print(f"links de menu levados p/ EN: {links_en}")
    print(f"links de CORPO levados p/ EN: {links_corpo}")
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
