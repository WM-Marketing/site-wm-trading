# -*- coding: utf-8 -*-
"""
WM Trading — Static HTML Generation Script
Generates static pages, segments, services, aircraft, and blog from JSON/MDX content.
"""
import os
import re
import json
import glob
import shutil
from datetime import datetime

# Define workspace directories (derived from this script's location, works on any machine)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SEO: canonical/og/sitemap sempre apontam para o dominio FINAL (nao o vercel.app),
# para consolidar indexacao no dominio oficial antes e depois da virada.
SITE_URL = "https://www.wmtrading.com.br"
DEFAULT_OG_IMAGE = "/images/logo/fechado_logo_wm_trading_ajustada_logo_laranja.png"
ORGANIZATION_JSONLD = {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "WM Trading",
    "url": SITE_URL,
    "logo": SITE_URL + DEFAULT_OG_IMAGE,
    "description": "Trading company especializada em solucoes completas de importacao e comercio exterior para empresas no Brasil.",
}
# LGPD: versao vigente das politicas de privacidade/cookies.
# Alterar SEMPRE que o texto mudar de forma relevante. Efeitos automaticos:
#   1) o aviso de cookies reaparece para quem aceitou uma versao anterior;
#   2) os formularios passam a gravar esta versao no registro de aceite (prova
#      de consentimento que segue para o Pipedrive).
# Manter em sincronia com a meta wm-politica-versao do index.html e das paginas
# manuais (importacao-carne-suina/index.html, segmentos-aeronaves.html).
POLITICA_VERSAO_ID = "2026-08-11"
POLITICA_VIGENCIA = "11 de agosto de 2026"

CONTENT_DIR = os.path.join(ROOT_DIR, "content")
CSS_DIR = os.path.join(ROOT_DIR, "css")
JS_DIR = os.path.join(ROOT_DIR, "js")
BLOG_OUT_DIR = os.path.join(ROOT_DIR, "blog")
SEGMENTS_OUT_DIR = os.path.join(ROOT_DIR, "segmentos")
AIRCRAFT_OUT_DIR = os.path.join(ROOT_DIR, "aeronaves")
EBOOKS_OUT_DIR = os.path.join(ROOT_DIR, "ebooks")

# Ensure output directories exist
os.makedirs(BLOG_OUT_DIR, exist_ok=True)
os.makedirs(SEGMENTS_OUT_DIR, exist_ok=True)
os.makedirs(AIRCRAFT_OUT_DIR, exist_ok=True)
os.makedirs(EBOOKS_OUT_DIR, exist_ok=True)

# List of branches for footer/contact listing
BRANCHES = [
    {"city": "Vitória", "state": "ES", "phone": "+55 (27) 3022-9700"},
    {"city": "Rio de Janeiro", "state": "RJ", "phone": "+55 (21) 3952-5204"},
    {"city": "São Paulo", "state": "SP", "phone": "+55 (11) 4063-9640"},
    {"city": "Itajaí", "state": "SC", "phone": "+55 (47) 4054-9640"},
    {"city": "Belém", "state": "PA", "phone": "+55 (91) 4042-2072"},
    {"city": "Camaragibe", "state": "PE", "phone": "+55 (81) 3771-0277"},
    {"city": "Fortaleza", "state": "CE", "phone": "+55 (85) 3771-4677"},
    {"city": "Ipanema", "state": "AL", "phone": "+55 (82) 3021-9069"},
    {"city": "Lauro de Freitas", "state": "BA", "phone": "+55 (71) 3512-6603"},
    {"city": "Manaus", "state": "AM", "phone": "+55 (92) 3042-2018"},
    {"city": "Paranaguá", "state": "PR", "phone": "+55 (41) 3514-5914"},
    {"city": "Porto Velho", "state": "RO", "phone": "+55 (69) 3026-0640"},
    {"city": "São Luís", "state": "MA", "phone": "+55 (98) 3042-2212"}
]

# Segment categories for contact form select
SEGMENTS_LIST = [
    "Aeronaves", "Energia Renovável", "Alimentos e Bebidas", "Vestuário/Têxtil",
    "Informática e Eletrônicos", "Metais & Derivados", "Partes e Peças Automotivas",
    "Produtos Químicos", "Partes e Peças Geral", "Cosméticos e Healthcare",
    "Insumos e Matéria Prima", "Medicamentos", "Combustível", "Máquinas e Equipamentos",
    "Setor Automotivo", "Outros"
]

# Segmentos servidos por uma pagina MANUAL, fora do gerador. Para estes:
#   1) nao geramos segmentos/<slug>.html (a pagina manual e a versao oficial);
#   2) o card do indice /segmentos/ aponta para a URL manual, e nao para
#      /segmentos/<slug>.html — que deixaria de existir.
# O JSON em content/segments/ continua sendo lido, porque e de la que vem o
# nome, a descricao do card e a lista do <select> dos formularios.
# Ao remover um slug daqui, o gerador volta a criar a pagina normalmente.
SEGMENT_URL_OVERRIDES = {
    "importacao-aeronaves": "/segmentos-aeronaves.html",
}

# Card thumbnails for the segments index page (segmentos/index.html).
# Order here = display order on the page (aviação → energia/indústria → consumo/tech).
# 400x200 thumbs herdados da página /segmentos/ do site antigo; banners como fallback.
SEGMENT_INDEX_THUMBS = {
    "importacao-aeronaves": "/wp-content/uploads/2025/03/IMPORTACAO-DE-AERONAVES-1.webp",
    "rebocadores": "/wp-content/uploads/2024/07/aircraft-tug-tows.png",
    "drone": "/wp-content/uploads/2024/05/imagens-thumbnail-site_drones.webp",
    "equipamentos-fotovoltaicos": "/wp-content/uploads/2024/05/imagens-thumbnail-site_equi-fotovoltaico.webp",
    "cases-de-usinas-fotovoltaicas": "/wp-content/uploads/2024/06/banner-usinas.webp",
    "produtos-quimicos": "/wp-content/uploads/2024/05/imagens-thumbnail-site_produtos_quimicos.webp",
    "combustivel": "/wp-content/uploads/2024/05/imagens-thumbnail-site_combustivel.webp",
    "derivados-petroleo": "/wp-content/uploads/2024/06/banner-combustivel.webp",
    "maquinas": "/wp-content/uploads/2024/05/imagens-thumbnail-site_maquinas.webp",
    "aco": "/wp-content/uploads/2024/05/imagens-thumbnail-site_aco.webp",
    "cosmeticos": "/wp-content/uploads/2024/05/imagens-thumbnail-site_cosmeticos.webp",
    "informatica-e-telecomunicacoes": "/wp-content/uploads/2024/05/imagens-thumbnail-site_infomartica.webp",
    "autopecas": "/wp-content/uploads/2024/05/imagens-thumbnail-site_autopecas.webp",
    "varejo": "/wp-content/uploads/2024/05/imagens-thumbnail-site_varejo.webp",
    "vinho": "/wp-content/uploads/2024/05/imagens-thumbnail-site_vinho.webp",
}

# States for contact form select
STATES_LIST = [
    "Acre", "Amapá", "Amazonas", "Pará", "Rondônia", "Roraima", "Tocantins",
    "Alagoas", "Bahia", "Ceará", "Maranhão", "Paraíba", "Pernambuco", "Piauí",
    "Rio Grande do Norte", "Sergipe", "Distrito Federal", "Goiás", "Mato Grosso",
    "Mato Grosso do Sul", "Espírito Santo", "Minas Gerais", "Rio de Janeiro",
    "São Paulo", "Paraná", "Rio Grande do Sul", "Santa Catarina", "Exterior"
]

# Mapping of segment slugs to their specific image assets (cover, section_image, benefit_icons, video)
SEGMENT_IMAGES_MAP = {
    "aco": {
        "cover": "/wp-content/uploads/2024/06/banner-aco.webp",
        "video": "",
        "intro_image": "",
        "form_image": "/wp-content/uploads/2024/06/thumb-1co2.png",
        "section_images": [
            "/wp-content/uploads/2024/06/thumb-aco.png",
            "",
            "/wp-content/uploads/2024/06/98.png"
        ],
        "icons": [
            "/wp-content/uploads/2024/06/ico2.png",
            "/wp-content/uploads/2024/06/globo.png",
            "/wp-content/uploads/2024/06/beneficios.png"
        ]
    },
    "autopecas": {
        "cover": "/wp-content/uploads/2024/06/banner-autopecas.webp",
        "video": "https://youtu.be/shyKF2xAZlk",
        "intro_image": "",
        "form_image": "/wp-content/uploads/2024/06/thumb3-autopecas.webp",
        "section_images": [
            "/wp-content/uploads/2024/06/banner-autopecas-426x281-1.webp",
            "",
            "/wp-content/uploads/2024/06/thumb2-autopecas.webp"
        ],
        "icons": [
            "/wp-content/uploads/2024/06/ico2.png",
            "/wp-content/uploads/2024/06/seguranca.png",
            "/wp-content/uploads/2024/06/ico.png"
        ]
    },
    "cases-de-usinas-fotovoltaicas": {
        "cover": "/wp-content/uploads/2024/06/banner-usinas.webp",
        "video": "",
        "intro_image": "",
        "form_image": "",
        "section_images": [
            "/wp-content/uploads/2024/06/Grupo10.png",
            "/wp-content/uploads/2024/06/Grupo91.png",
            "/wp-content/uploads/2024/06/Grupo12.png"
        ],
        "icons": [
            "/wp-content/uploads/2024/06/icoo.png",
            "/wp-content/uploads/2024/06/icooo.png",
            "/wp-content/uploads/2024/06/ico-varejo.png"
        ]
    },
    "combustivel": {
        "cover": "/wp-content/uploads/2024/06/banner-combustivel.webp",
        "video": "https://youtu.be/RTGZirDu90A",
        "intro_image": "",
        "form_image": "/wp-content/uploads/2024/06/thumb-form.png",
        "section_images": [
            "/wp-content/uploads/2024/06/seguranca-1.png",
            "/wp-content/uploads/2024/06/banner-site-combustiveis.webp",
            "/wp-content/uploads/2024/06/expertise.png"
        ],
        "icons": [
            "/wp-content/uploads/2024/06/icon-1.png",
            "/wp-content/uploads/2024/06/icon-2.png",
            "/wp-content/uploads/2024/06/icon-3.png"
        ]
    },
    "cosmeticos": {
        "cover": "/wp-content/uploads/2024/06/banner-header-cosmeticos.webp",
        "video": "",
        "intro_image": "/wp-content/uploads/2024/06/cosmeticos-thumb-1.webp",
        "form_image": "",
        "section_images": [
            "/wp-content/uploads/2024/06/cosmeticos-thumb-2.webp",
            "/wp-content/uploads/2024/06/cosmeticos-thumb-3.webp",
            ""
        ],
        "icons": [
            "/wp-content/uploads/2024/06/icon-1-1.png",
            "/wp-content/uploads/2024/06/icon-2-1.png",
            "/wp-content/uploads/2024/06/icon-3-1.png"
        ]
    },
    "derivados-petroleo": {
        "cover": "/wp-content/uploads/2024/06/banner-combustivel.webp",
        "video": "https://youtu.be/RTGZirDu90A",
        "intro_image": "",
        "form_image": "/wp-content/uploads/2024/06/thumb-form.png",
        "section_images": [
            "/wp-content/uploads/2024/06/seguranca-1.png",
            "/wp-content/uploads/2024/06/banner-site-combustiveis.webp",
            "/wp-content/uploads/2024/06/expertise.png"
        ],
        "icons": [
            "/wp-content/uploads/2024/06/icon-1.png",
            "/wp-content/uploads/2024/06/icon-2.png",
            "/wp-content/uploads/2024/06/icon-3.png"
        ]
    },
    "drone": {
        "cover": "/wp-content/uploads/2024/06/banner-drone.webp",
        "video": "",
        "intro_image": "",
        "form_image": "/wp-content/uploads/2024/06/rhumb3-drone.jpg",
        "section_images": [
            "/wp-content/uploads/2024/06/thumb-drone.png",
            "",
            "/wp-content/uploads/2024/06/thumb2-drone.jpg"
        ],
        "icons": [
            "/wp-content/uploads/2024/06/parametrizacao.png",
            "/wp-content/uploads/2024/06/ico-drone.png",
            "/wp-content/uploads/2024/06/seguranca.png"
        ]
    },
    "equipamentos-fotovoltaicos": {
        "cover": "/wp-content/uploads/2024/06/banner-fotovolaticos.webp",
        "video": "https://youtu.be/IqGdtPnWhyY",
        "intro_image": "",
        "form_image": "",
        "section_images": [
            "/wp-content/uploads/2024/06/thumb-20-anos.png",
            "/wp-content/uploads/2024/06/porcentagem.png",
            "/wp-content/uploads/2024/06/selo.png"
        ],
        "icons": [
            "/wp-content/uploads/2024/06/1.svg",
            "/wp-content/uploads/2024/06/2.svg",
            "/wp-content/uploads/2024/06/3.svg"
        ]
    },
    "importacao-aeronaves": {
        "cover": "/wp-content/uploads/2025/03/IMPORTACAO-DE-AERONAVES-1.webp",
        "video": "https://youtu.be/FOQEa2Xtqjs",
        "intro_image": "/wp-content/uploads/2025/03/importar-o-seu-aviao-com-agilidade-e-seguranca.webp",
        "form_image": "",
        "section_images": [
            "/wp-content/uploads/2025/03/oportunidades-da-importacao.webp",
            "/wp-content/uploads/2025/03/ebook-importacao-aeronaves-mockup-wm.webp"
        ],
        "icons": [
            "/wp-content/uploads/2024/06/icone-1.svg",
            "/wp-content/uploads/2024/06/icone-2.svg",
            "/wp-content/uploads/2024/06/icone-3.svg"
        ]
    },
    "informatica-e-telecomunicacoes": {
        "cover": "/wp-content/uploads/2024/06/banner-informatica.webp",
        "video": "https://youtu.be/nOZQtUS7sgA",
        "intro_image": "",
        "form_image": "/wp-content/uploads/2024/06/Grupo32.webp",
        "section_images": [
            "/wp-content/uploads/2024/06/Grupo12.webp",
            "/wp-content/uploads/2024/06/mosaico-informativa.webp",
            "",
            "/wp-content/uploads/2024/06/Grupo29.webp"
        ],
        "icons": [
            "/wp-content/uploads/2024/06/icon-1-1.png",
            "/wp-content/uploads/2024/06/icon-mao.png",
            "/wp-content/uploads/2024/06/1.svg"
        ]
    },
    "maquinas": {
        "cover": "/wp-content/uploads/2024/06/banner-header-site-maquinas-1920x405-1.png",
        "video": "https://youtu.be/LUHSCxojw9A",
        "intro_image": "",
        "form_image": "",
        "section_images": [
            "/wp-content/uploads/2024/06/thumb-maquinas.png",
            "",
            "/wp-content/uploads/2024/06/thumb2-maquinas.webp"
        ],
        "icons": [
            "/wp-content/uploads/2024/06/parametrizacao.png",
            "/wp-content/uploads/2024/06/beneficios.png",
            "/wp-content/uploads/2024/06/lampada.png"
        ]
    },
    "produtos-quimicos": {
        "cover": "/wp-content/uploads/2024/06/banner-produtos.webp",
        "video": "https://youtu.be/Tp6RgSWexfw",
        "intro_image": "",
        "form_image": "/wp-content/uploads/2024/06/quimico-2.png",
        "section_images": [
            "/wp-content/uploads/2024/06/quimico.png",
            ""
        ],
        "icons": [
            "/wp-content/uploads/2024/06/seguranca.png",
            "/wp-content/uploads/2024/06/beneficios.png",
            "/wp-content/uploads/2024/06/parametrizacao.png"
        ]
    },
    "rebocadores": {
        "cover": "/wp-content/uploads/2024/06/banner-rebocadores-1.webp",
        "video": "https://www.youtube.com/watch?v=T-drV5vtSBM",
        "intro_image": "",
        "form_image": "",
        "section_images": [
            "/wp-content/uploads/2024/06/banner-rebocadores-2.webp",
            "/wp-content/uploads/2024/06/thumb2-rebocadores.png"
        ],
        "icons": [
            "/wp-content/uploads/2024/06/lampada.png",
            "/wp-content/uploads/2024/06/ico-drone.png",
            "/wp-content/uploads/2024/06/parametrizacao.png"
        ]
    },
    "varejo": {
        "cover": "/wp-content/uploads/2024/06/banner-varejo.webp",
        "video": "https://youtu.be/9wt3YYmW_nc",
        "intro_image": "",
        "form_image": "/wp-content/uploads/2024/06/thumb1-varejo.png",
        "section_images": [
            "/wp-content/uploads/2024/06/thumb-varejo.png",
            "",
            "/wp-content/uploads/2024/06/thumb-varejo-porcento.png"
        ],
        "icons": [
            "/wp-content/uploads/2024/06/ico2.png",
            "/wp-content/uploads/2024/06/ico-varejo.png",
            "/wp-content/uploads/2024/06/ico.png"
        ]
    },
    "vinho": {
        "cover": "/wp-content/uploads/2024/06/banner-vinhos.webp",
        "video": "https://youtu.be/9jyMo-25fQ0",
        "intro_image": "",
        "form_image": "",
        "section_images": [
            "/wp-content/uploads/2024/06/thumb-vinho.webp",
            "",
            "/wp-content/uploads/2024/06/thumb-95porcento.png"
        ],
        "icons": [
            "/wp-content/uploads/2024/06/arrow.png",
            "/wp-content/uploads/2024/06/beneficios.png",
            "/wp-content/uploads/2024/06/lampada.png"
        ]
    }
}

def get_clean_phone(phone):
    """Helper to remove non-digit characters from phone numbers."""
    return re.sub(r"\D", "", phone)

def get_youtube_embed_url(url):
    """Extracts YouTube ID and formats it as an embeddable URL."""
    if not url:
        return ""
    match = re.search(r'(?:youtu\.be/|youtube\.com/(?:embed/|v/|watch\?v=|watch\?.+&v=))([^&\s?#\\]+)', url)
    if match:
        video_id = match.group(1)
        return f"https://www.youtube.com/embed/{video_id}"
    return ""


def load_template_elements():
    """Reads index.html to extract common HEAD, HEADER, and FOOTER sections."""
    index_path = os.path.join(ROOT_DIR, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Extract head content (excluding title, description, charset and viewport —
    # render_html_page already emits its own, and duplicating them is invalid HTML)
    head_start = html.find("<head>")
    head_end = html.find("</head>")
    head_content = html[head_start + 6:head_end]
    head_content = re.sub(r"<title>.*?</title>", "", head_content)
    head_content = re.sub(r'<meta\s+name="description"\s+content=".*?"\s*/?>', "", head_content)
    head_content = re.sub(r'<meta\s+charset=".*?"\s*/?>', "", head_content)
    head_content = re.sub(r'<meta\s+name="viewport"\s+content=".*?"\s*/?>', "", head_content)
    # SEO tags do index.html nao devem vazar para as paginas geradas
    # (render_html_page emite as suas proprias, especificas de cada pagina)
    head_content = re.sub(r'<link\s+rel="canonical"[^>]*/?>', "", head_content)
    head_content = re.sub(r'<meta\s+(?:property="(?:og|article):[^"]*"|name="twitter:[^"]*")[^>]*/?>', "", head_content)
    head_content = re.sub(r'<meta\s+name="robots"[^>]*/?>', "", head_content)
    head_content = re.sub(r'<script\s+type="application/ld\+json">.*?</script>', "", head_content, flags=re.S)
    # remove linhas em branco deixadas pelas remocoes acima
    head_content = re.sub(r'\n\s*\n+', '\n', head_content)
    
    # LGPD: a versao das politicas vem sempre do gerador (fonte unica das paginas
    # geradas). Remove a meta herdada do index.html e reinjeta a partir da constante.
    # Vai no INICIO do head: js/consent.js roda sem defer e le esta meta na carga.
    head_content = re.sub(r'<meta\s+name="wm-politica-versao"[^>]*/?>', "", head_content)
    head_content = re.sub(r'\n\s*\n+', '\n', head_content)
    head_content = f'\n  <meta name="wm-politica-versao" content="{POLITICA_VERSAO_ID}" />' + head_content

    # Inject dynamic-pages styles and contact-form script
    head_content += '\n  <link rel="stylesheet" href="/css/dynamic-pages.css" />'
    head_content += '\n  <script src="/js/contact-form.js" defer></script>'
    head_content += '\n  <script src="/js/lightbox.js" defer></script>'

    # Extract header (including loader)
    loader_start = html.find('<div id="page-loader"')
    header_end = html.find("</header>") + 9
    header_content = html[loader_start:header_end]

    # Extract footer (up to </body> — the closing </body></html> is emitted
    # by render_html_page; including it here duplicated the closing tags)
    footer_comment = "<!-- ══════════════════════════════════════\n     FOOTER — FAIXA 1: Links + CTA\n══════════════════════════════════════ -->"
    footer_start = html.find(footer_comment)
    if footer_start == -1:
        footer_start = html.find('<div class="footer-links">')
    footer_end = html.find("</body>")
    footer_content = html[footer_start:footer_end if footer_end != -1 else len(html)]

    # Make all assets paths absolute
    head_content = make_paths_absolute(head_content)
    header_content = make_paths_absolute(header_content)
    footer_content = make_paths_absolute(footer_content)

    return head_content, header_content, footer_content

def make_paths_absolute(content):
    """Prefixes ALL relative href/src paths with '/' so templates work from any subdirectory.

    External URLs (http/https///), anchors (#), mailto:, tel: and data: URIs are left untouched.
    """
    return re.sub(
        r'(href|src)="(?!/|https?://|//|#|mailto:|tel:|data:)([^"]+)"',
        r'\1="/\2"',
        content,
    )

def _esc_attr(s):
    """Escapa texto para uso seguro em atributos HTML."""
    return str(s).replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")


def render_html_page(output_path, title, description, content_body, head_tpl, header_tpl, footer_tpl,
                     lang="pt-BR", og_type="website", og_image=None, jsonld=None):
    """Wraps page content in a fully styled, absolute-path templates block and saves it."""
    # SEO: canonical + Open Graph + Twitter Card + JSON-LD, apontando para o dominio final
    rel_path = os.path.relpath(output_path, ROOT_DIR).replace(os.sep, "/")
    # index.html canoniza para a URL do diretório SEM barra final (/segmentos,
    # /blog) — vercel.json usa trailingSlash:false e 308-redireciona a forma com barra
    if rel_path == "index.html":
        rel_path = ""
    elif rel_path.endswith("/index.html"):
        rel_path = rel_path[:-len("/index.html")]
    canonical_url = f"{SITE_URL}/{rel_path}"
    og_img = og_image or DEFAULT_OG_IMAGE
    if og_img.startswith("/"):
        og_img = SITE_URL + og_img
    full_title = _esc_attr(f"WM Trading — {title}")
    desc_attr = _esc_attr(description)
    og_locale = "en_US" if lang == "en" else "pt_BR"

    jsonld_blocks = [ORGANIZATION_JSONLD] + ([jsonld] if jsonld else [])
    jsonld_html = "\n  ".join(
        '<script type="application/ld+json">%s</script>' % json.dumps(b, ensure_ascii=False)
        for b in jsonld_blocks
    )

    seo_block = f"""<link rel="canonical" href="{canonical_url}" />
  <meta property="og:title" content="{full_title}" />
  <meta property="og:description" content="{desc_attr}" />
  <meta property="og:url" content="{canonical_url}" />
  <meta property="og:type" content="{og_type}" />
  <meta property="og:image" content="{og_img}" />
  <meta property="og:site_name" content="WM Trading" />
  <meta property="og:locale" content="{og_locale}" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="robots" content="index, follow, max-image-preview:large" />
  {jsonld_html}"""

    # Build complete HTML page
    html = f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>WM Trading — {title}</title>
  <meta name="description" content="{desc_attr}" />
  {seo_block}
  {head_tpl}
</head>
<body>

{header_tpl}

<main>
{content_body}
</main>

{footer_tpl}

</body>
</html>
"""
    escrever_se_mudou(output_path, html)

def escrever_se_mudou(output_path, conteudo):
    """Grava so quando o conteudo mudou de verdade.

    O lastmod do sitemap vem do mtime do arquivo (os.path.getmtime). Se o
    gerador reescreve tudo a cada execucao, todo mtime vira "agora" e o sitemap
    passa a declarar as 258 paginas como modificadas hoje — falso, e o Google
    desprioriza lastmod que nao merece confianca. De quebra, cada build sujava
    o diff com 254 linhas de data.

    Preservar o mtime das paginas inalteradas faz o lastmod voltar a significar
    algo e deixa o build idempotente: rodar duas vezes nao produz diff.
    """
    try:
        with open(output_path, "r", encoding="utf-8", newline="") as f:
            if f.read() == conteudo:
                return False
    except FileNotFoundError:
        pass
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        f.write(conteudo)
    return True

def markdown_to_html(text):
    """A clean, lightweight, dependency-free Markdown to HTML parser in Python. Prevents infinite loops."""
    text = text.replace('\r\n', '\n')
    
    # Strip frontmatter if it is passed in the body
    if text.startswith('---'):
        parts = text.split('---', 2)
        if len(parts) >= 3:
            text = parts[2]
            
    lines = text.split('\n')
    new_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        old_i = i
        
        # Blockquotes
        if line.strip().startswith('>'):
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                quote_lines.append(lines[i].strip().lstrip('>').strip())
                i += 1
            quote_text = ' '.join(quote_lines)
            new_lines.append(f'<blockquote>{quote_text}</blockquote>')
            
        # Headers
        elif line.startswith('### '):
            new_lines.append(f'<h3>{line[4:].strip()}</h3>')
            i += 1
        elif line.startswith('## '):
            new_lines.append(f'<h2>{line[3:].strip()}</h2>')
            i += 1
        elif line.startswith('# '):
            new_lines.append(f'<h1>{line[2:].strip()}</h1>')
            i += 1
            
        # Bullet Lists
        elif line.strip().startswith('- ') or line.strip().startswith('* '):
            list_items = []
            while i < len(lines) and (lines[i].strip().startswith('- ') or lines[i].strip().startswith('* ')):
                item_text = lines[i].strip()[2:]
                list_items.append(f'<li>{item_text}</li>')
                i += 1
            new_lines.append(f'<ul>{"".join(list_items)}</ul>')
            
        # Google Sheets published charts
        elif re.match(r'^https://docs\.google\.com/spreadsheets/d/e/[^\s]+/pubchart\?[^\s]+$', line.strip()):
            chart_url = line.strip().replace('&', '&amp;')
            new_lines.append(
                f'<iframe class="google-sheet-chart" src="{chart_url}" '
                'title="Gráfico interativo do Google Sheets" loading="lazy"></iframe>'
            )
            i += 1

        # Gráfico interativo: importação mensal de automóveis de passageiros (SH4 8703)
        elif line.strip() == '{{wm-chart:autos-8703}}':
            new_lines.append('''<figure class="wm-interactive-chart">
  <figcaption>Importação mensal de automóveis de passageiros</figcaption>
  <div class="wm-interactive-chart__canvas"><canvas id="chart-autos-8703" aria-label="Gráfico de linha da importação mensal de automóveis de passageiros, de julho de 2025 a junho de 2026"></canvas></div>
  <p class="wm-interactive-chart__source">Valores FOB em US$ milhões. Fonte: MDIC/Comex Stat.</p>
</figure>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<script>
(() => {
  const canvas = document.getElementById('chart-autos-8703');
  if (!canvas || !window.Chart) return;
  new Chart(canvas, {
    type: 'line',
    data: {
      labels: ['jul./25', 'ago./25', 'set./25', 'out./25', 'nov./25', 'dez./25', 'jan./26', 'fev./26', 'mar./26', 'abr./26', 'mai./26', 'jun./26'],
      datasets: [{
        label: 'Valor FOB (US$ milhões)',
        data: [321.38, 405.49, 484.00, 601.14, 785.16, 678.75, 564.20, 559.68, 1125.77, 1249.62, 1873.87, 2416.53],
        borderColor: '#ff5a1f', backgroundColor: 'rgba(255, 90, 31, 0.18)',
        borderWidth: 3, fill: true, tension: 0.32, pointRadius: 4,
        pointHoverRadius: 6, pointBackgroundColor: '#ff5a1f'
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: ctx => ` US$ ${ctx.parsed.y.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} milhões` } }
      },
      scales: {
        y: { beginAtZero: true, ticks: { callback: value => `US$ ${value.toLocaleString('pt-BR')} mi` }, grid: { color: '#e5e5e5' } },
        x: { grid: { display: false } }
      }
    }
  });
})();
</script>''')
            i += 1

        # YouTube Videos
        elif line.strip().startswith('https://youtu.be/') or line.strip().startswith('https://www.youtube.com/embed/') or line.strip().startswith('https://www.youtube.com/watch'):
            yt_url = line.strip()
            yt_id = ''
            if 'youtu.be/' in yt_url:
                yt_id = yt_url.split('youtu.be/')[1].split('?')[0].split('\\')[0].strip()
            elif 'v=' in yt_url:
                yt_id = yt_url.split('v=')[1].split('&')[0].strip()
            elif 'embed/' in yt_url:
                yt_id = yt_url.split('embed/')[1].split('?')[0].strip()
                
            if yt_id:
                new_lines.append(f'<iframe src="https://www.youtube.com/embed/{yt_id}" allowfullscreen></iframe>')
            else:
                new_lines.append(f'<p>{line}</p>')
            i += 1
            
        # Empty Line
        elif not line.strip():
            new_lines.append('')
            i += 1
            
        # Paragraphs
        else:
            para_lines = []
            while i < len(lines) and lines[i].strip() and not (lines[i].startswith('#') or lines[i].strip().startswith('- ') or lines[i].strip().startswith('* ') or lines[i].strip().startswith('>')):
                para_lines.append(lines[i].strip())
                i += 1
            if i == old_i:
                para_lines.append(line.strip())
                i += 1
            para_text = ' '.join(para_lines)
            if para_text:
                new_lines.append(f'<p>{para_text}</p>')
                
        # Safeguard to prevent infinite loops
        if i == old_i:
            i += 1
            
    html = '\n'.join(new_lines)
    
    # Inline tags replacement
    # Bold
    html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
    # Images (must run before links, otherwise ![alt](url) becomes !<a>)
    def _img_repl(m):
        alt, src, title = m.group(1), m.group(2), m.group(3)
        title_attr = f' title="{title}"' if title else ''
        return f'<img src="{src}" alt="{alt}"{title_attr} loading="lazy" />'
    html = re.sub(r'!\[(.*?)\]\(\s*([^)\s]+)(?:\s+"([^"]*)")?\s*\)', _img_repl, html)
    # Links
    html = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', html)
    # Emphasis — only outside HTML tags, so URLs/attributes with "_" are never corrupted
    parts = re.split(r'(<[^>]+>)', html)
    html = ''.join(
        p if p.startswith('<') else re.sub(r'(?<!\\)_(.*?)(?<!\\)_', r'<em>\1</em>', p)
        for p in parts
    )
    # Markdown-escaped underscores (\_) render as literal "_"
    html = html.replace('\\_', '_')

    # Cluster consecutive standalone images into a thumbnail gallery
    # (rendered as a grid; js/lightbox.js opens them enlarged in a popup).
    # 1) unwrap paragraphs that contain only images
    html = re.sub(r'<p>((?:\s*<img [^>]*/>)+)\s*</p>', r'\1', html)
    # 2) group runs of 2+ adjacent images into .post-gallery
    def _gallery_repl(m):
        imgs = re.findall(r'<img [^>]*/>', m.group(0))
        if len(imgs) < 2:
            return m.group(0)
        return '\n<div class="post-gallery">\n' + '\n'.join(imgs) + '\n</div>\n'
    html = re.sub(r'(?:<img [^>]*/>\s*){2,}', _gallery_repl, html)

    return html

def parse_mdx(file_path):
    """Parses frontmatter metadata and body from a blog MDX file."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    frontmatter = {}
    body = content
    
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            body = parts[2]
            
            # Simple YAML parser
            for line in fm_text.split("\n"):
                if ":" in line:
                    k, v = line.split(":", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k == "categories":
                        # We will read categories array
                        pass
                    elif k.startswith("-"):
                        # category item, skip or handle
                        pass
                    else:
                        frontmatter[k] = v
                        
    # Extract categories manually if needed
    cat_matches = re.findall(r'categories:\s*\n\s*-\s*["\']?(.*?)["\']?\s*\n', content)
    if cat_matches:
        frontmatter["category"] = cat_matches[0]
    else:
        # Fallback category extraction
        category_block = re.search(r'categories:\s*\n((?:\s*-\s*.*?\n)+)', content)
        if category_block:
            cats = re.findall(r'-\s*["\']?(.*?)["\']?', category_block.group(1))
            if cats:
                frontmatter["category"] = cats[0]
        else:
            frontmatter["category"] = "Geral"

    return frontmatter, body

def build_contact_form_html(form_type="contato", selected_segment=""):
    """Generates standard responsive contact form HTML styled with Brand system."""
    segment_options = ""
    for s in SEGMENTS_LIST:
        sel = "selected" if s.lower() == selected_segment.lower() else ""
        segment_options += f'\n          <option value="{s}" {sel}>{s}</option>'
        
    state_options = ""
    for st in STATES_LIST:
        state_options += f'\n          <option value="{st}">{st}</option>'

    return f"""
        <form class="contact-form-js grid gap-4 form-grid-wm form-grid-wm--2col" data-form-type="{form_type}">
          <input type="text" name="_gotcha" tabindex="-1" autocomplete="off" class="hidden" aria-hidden="true" style="display:none;" />
          
          <input name="nome" required placeholder="Nome *" class="input-wm sm-col-span-2" />
          <input name="email" type="email" required placeholder="E-mail *" class="input-wm" />
          <input name="telefone" type="tel" required placeholder="Número Telefone * — (DDD) 99999-0000" pattern="[0-9\\s\\(\\)\\+\\-\\.]+" class="input-wm" />
          <input name="empresa" placeholder="Empresa" class="input-wm" />
          
          <select name="estado" required class="input-wm">
            <option value="" disabled selected>Estado *</option>
            {state_options}
          </select>
          
          <select name="segmento" required class="input-wm sm-col-span-2">
            <option value="" disabled>Segmento *</option>
            {segment_options}
          </select>
          
          <select name="forma_resposta" required class="input-wm sm-col-span-2">
            <option value="" disabled selected>Como deseja ser respondido? *</option>
            <option value="WhatsApp">WhatsApp</option>
            <option value="Telefone">Telefone</option>
            <option value="E-mail">E-mail</option>
          </select>
          
          <textarea name="mensagem" required rows="4" placeholder="Mensagem *" class="input-wm sm-col-span-2 resize-y"></textarea>
          
          <label class="sm-col-span-2 form-checkbox-label">
            <input type="checkbox" name="aceite_privacidade" required value="sim" />
            <span data-wm-aceite>Li e estou de acordo com a <a href="/politica-de-privacidade.html" class="text-primary underline">Política de Privacidade</a> e autorizo a WM Trading a tratar meus dados para responder a esta solicitação.</span>
          </label>

          <label class="sm-col-span-2 form-checkbox-label">
            <input type="checkbox" name="aceite_marketing" value="sim" />
            <span data-wm-aceite-marketing>Também quero receber conteúdos, materiais e comunicações comerciais da WM Trading (opcional).</span>
          </label>

          <button type="submit" class="btn btn-block sm-col-span-2 btn-lg">Enviar</button>
        </form>
    """

def build_ebook_form_html(ebook_title, pdf_url):
    """Generates e-book download form HTML with download trigger binding."""
    return f"""
        <form class="contact-form-js grid gap-4 form-grid-wm" data-form-type="ebook" data-pdf-url="{pdf_url}" data-ebook-title="{ebook_title}">
          <input type="text" name="_gotcha" tabindex="-1" autocomplete="off" class="hidden" aria-hidden="true" style="display:none;" />
          <p class="text-center font-semibold" style="margin-bottom:12px;">Preencha os dados abaixo para acessar o material</p>
          
          <input name="nome" required placeholder="Nome *" class="input-wm" />
          <input name="email" type="email" required placeholder="E-mail *" class="input-wm" />
          <input name="empresa" required placeholder="Empresa *" class="input-wm" />
          
          <label class="form-checkbox-label" style="margin: 8px 0;">
            <input type="checkbox" name="aceite_privacidade" required value="sim" />
            <span data-wm-aceite>Li e estou de acordo com a <a href="/politica-de-privacidade.html" class="text-primary underline">Política de Privacidade</a> e autorizo a WM Trading a tratar meus dados para enviar este material.</span>
          </label>

          <label class="form-checkbox-label" style="margin: 0 0 8px;">
            <input type="checkbox" name="aceite_marketing" value="sim" />
            <span data-wm-aceite-marketing>Também quero receber conteúdos, materiais e comunicações comerciais da WM Trading (opcional).</span>
          </label>

          <button type="submit" class="btn btn-block btn-lg">Quero o material</button>
        </form>
    """

# ----------------- COMPILING PAGES -----------------

def main():
    print("Loading index.html structure templates...")
    head_tpl, header_tpl, footer_tpl = load_template_elements()
    
    # 1. GENERATE SERVICES PAGES
    print("\nGenerating Services...")
    services_files = glob.glob(os.path.join(CONTENT_DIR, "services", "*.json"))
    for file_path in services_files:
        with open(file_path, "r", encoding="utf-8") as f:
            s = json.load(f)
            
        slug = s["slug"]
        print(f" - compiling {slug}...")
        
        # Build Hero
        cover_style = ""
        hero_bg_img = ""
        if "cover" in s and s["cover"]:
            hero_bg_img = f'<img src="{s["cover"]}" alt="{s["title"]}" class="dynamic-hero__bg" />'
            
        hero_html = f"""
        <section class="dynamic-hero">
          {hero_bg_img}
          <div class="container dynamic-hero__container">
            <p class="dynamic-hero__eyebrow">Soluções WM</p>
            <h1 class="dynamic-hero__title">{s["title"]}</h1>
            {f'<p class="dynamic-hero__subtitle">{s["subtitle"]}</p>' if s.get("subtitle") else ''}
            <a href="/fale-conosco.html" class="btn btn-lg">Falar com um especialista</a>
          </div>
        </section>
        """
        
        # Build Intro
        intro_html = ""
        if s.get("intro"):
            intro_html = f"""
            <section class="page-section">
              <div class="container intro-container">
                <p class="intro-text">{s["intro"]}</p>
              </div>
            </section>
            """
            
        # Build Benefits
        benefits_html = ""
        if s.get("benefits") and len(s["benefits"]) > 0:
            cards_html = ""
            for idx, b in enumerate(s["benefits"]):
                cards_html += f"""
                <div class="benefit-card">
                  <span class="card-number-badge">{idx + 1}</span>
                  <h3 class="card-title">{b["title"]}</h3>
                  <p class="card-desc">{b["desc"]}</p>
                </div>
                """
            benefits_html = f"""
            <section class="page-section page-section--alternate">
              <div class="container">
                <h2 class="section-title-center">Por que escolher a WM</h2>
                <div class="cards-grid">
                  {cards_html}
                </div>
              </div>
            </section>
            """
            
        # Build Sections
        sections_html = ""
        if s.get("sections"):
            for idx, sec in enumerate(s["sections"]):
                bg_class = "page-section--alternate" if idx % 2 == 1 else ""
                sections_html += f"""
                <section class="page-section {bg_class}">
                  <div class="container intro-container">
                    <h2 class="card-title" style="font-size: var(--fs-lg); font-weight: var(--fw-light); margin-bottom: 18px;">{sec["heading"]}</h2>
                    <p class="card-desc" style="font-size: var(--fs-base); line-height: 1.7; white-space: pre-line;">{sec["text"]}</p>
                  </div>
                </section>
                """
                
        # Build CTA
        cta_html = f"""
        <section class="page-section" style="background: var(--color-primary); color: var(--color-text-white); text-align: center;">
          <div class="container">
            <h2 class="t-display" style="margin-bottom: 16px;">Vamos desenhar a sua operation?</h2>
            <p class="t-lead" style="margin-bottom: 24px;">Fale com a trading mais completa do Brasil.</p>
            <a href="/fale-conosco.html" class="btn btn-white btn-lg">Fale com a WM</a>
          </div>
        </section>
        """
        
        body_content = hero_html + intro_html + benefits_html + sections_html + cta_html
        output_path = os.path.join(ROOT_DIR, f"{slug}.html")
        render_html_page(output_path, s["name"], s.get("subtitle", s["name"]), body_content, head_tpl, header_tpl, footer_tpl)

    # 2. GENERATE SOLUTIONS HOME (solucoes-wm.json)
    print("Generating Solutions Portal (solucoes-wm.html)...")
    sol_json_path = os.path.join(CONTENT_DIR, "pages", "solucoes-wm.json")
    if os.path.exists(sol_json_path):
        with open(sol_json_path, "r", encoding="utf-8") as f:
            sol = json.load(f)
            
        # Hardcode layout identical to page.tsx structure but using pure static HTML/CSS
        sol_content = f"""
        <section class="dynamic-hero" style="padding: 120px 0;">
          <img src="/wp-content/uploads/2025/04/Nossas_Solucoes_WM_Trading_1.webp" alt="Nossas Soluções WM Trading" class="dynamic-hero__bg" style="opacity: 0.35;" />
          <div class="absolute inset-0 bg-gradient-to-l from-charcoal/95 via-charcoal/70 to-charcoal/20" style="position:absolute; inset:0; background: linear-gradient(to left, rgba(26,26,26,0.95), rgba(26,26,26,0.7), rgba(26,26,26,0.2)); pointer-events:none;"></div>
          <div class="container" style="position:relative; z-index:2; text-align:right;">
            <h1 class="t-display" style="color:var(--color-text-white); font-weight:var(--fw-semibold); font-size:var(--fs-2xl);">{sol.get("texts", ["Nossas Soluções"])[0]}</h1>
            <p class="t-lead" style="color:rgba(255,255,255,0.85); margin-top:20px; max-width:600px; margin-left:auto;">{sol.get("texts", ["", "Conheça nossas soluções"])[1]}</p>
          </div>
        </section>
        
        <section class="page-section">
          <div class="container">
            <div class="intro-container" style="margin-bottom: 50px;">
              <h2 class="t-h2" style="margin-bottom:16px;">Conheça as nossas soluções para importação</h2>
              <p class="intro-text" style="color:var(--color-text-muted);">Com 20 anos de história e experiência, a WM Trading procura solucionar as dores e entregar oportunidades aos clientes em um processo de importação.</p>
              <p class="intro-text" style="color:var(--color-text-muted); margin-top:12px;">Para isso, contamos com uma equipe altamente qualificada e experiente, sempre dedicada a proporcionar o melhor desenho logístico e tributário para sua operação.</p>
            </div>
            
            <div class="cards-grid">
              <!-- Operação por Encomenda -->
              <div class="benefit-card flex flex-col" style="display:flex; flex-direction:column; justify-content:space-between; height:100%;">
                <div>
                  <div class="card-number-badge">1</div>
                  <h3 class="card-title">Operação por Encomenda</h3>
                  <ul class="ebook-info__bullets" style="margin-top:16px;">
                    <li style="color:var(--color-text-muted);">Evitamos a necessidade de abertura de filial do cliente no estado onde a nacionalização será realizada</li>
                    <li style="color:var(--color-text-muted);">Possuímos 7 benefícios fiscais que reduzem o ICMS incidente</li>
                    <li style="color:var(--color-text-muted);">Fornecemos acompanhamento em tempo real de todas as etapas</li>
                    <li style="color:var(--color-text-muted);">Equipe altamente capacitada e sempre atualizada das regulamentações</li>
                  </ul>
                </div>
                <a href="/importacao-por-encomenda.html" class="btn btn-block btn-lg" style="margin-top:24px;">SAIBA MAIS</a>
              </div>
              
              <!-- Operação por Conta e Ordem -->
              <div class="benefit-card flex flex-col" style="display:flex; flex-direction:column; justify-content:space-between; height:100%;">
                <div>
                  <div class="card-number-badge">2</div>
                  <h3 class="card-title">Operação por Conta e Ordem</h3>
                  <ul class="ebook-info__bullets" style="margin-top:16px;">
                    <li style="color:var(--color-text-muted);">A WM Trading cuida de todas as etapas da sua importação</li>
                    <li style="color:var(--color-text-muted);">Otimizamos custos através de benefícios fiscais que reduzem o ICMS</li>
                    <li style="color:var(--color-text-muted);">Transparência total nas operações fornecendo mais segurança jurídica</li>
                    <li style="color:var(--color-text-muted);">Planejamentos detalhados elaborados com inteligência fiscal</li>
                  </ul>
                </div>
                <a href="/importacao-por-conta-e-ordem.html" class="btn btn-block btn-lg" style="margin-top:24px;">SAIBA MAIS</a>
              </div>
              
              <!-- Assessoria Aduaneira -->
              <div class="benefit-card flex flex-col" style="display:flex; flex-direction:column; justify-content:space-between; height:100%;">
                <div>
                  <div class="card-number-badge">3</div>
                  <h3 class="card-title">Assessoria Aduaneira</h3>
                  <ul class="ebook-info__bullets" style="margin-top:16px;">
                    <li style="color:var(--color-text-muted);">Auxiliamos importadoras a lidar com processos alfandegários</li>
                    <li style="color:var(--color-text-muted);">Indicamos as melhores rotas logísticas para as importações</li>
                    <li style="color:var(--color-text-muted);">Tabelas de preços diferenciadas nos principais portos</li>
                    <li style="color:var(--color-text-muted);">Assessoria aduaneira completa: logística, fiscal e tributária</li>
                  </ul>
                </div>
                <a href="/assessoria-aduaneira.html" class="btn btn-block btn-lg" style="margin-top:24px;">SAIBA MAIS</a>
              </div>
            </div>
          </div>
        </section>
        
        <section class="page-section page-section--alternate">
          <div class="container grid gap-10 lg:grid-cols-2" style="display:grid; grid-template-columns: 1fr; gap:40px; align-items:center;">
            <div>
              <h2 class="t-h2" style="margin-bottom:16px;">Global Sourcing</h2>
              <p class="intro-text" style="color:var(--color-text-muted);">Oferecemos o serviço de Global Sourcing a todos os nossos clientes.</p>
              <p class="intro-text" style="color:var(--color-text-muted); margin-top:12px;">Através de parcerias estratégicas e pesquisas eficazes, seguindo regulamentações internas para definir os fornecedores, nós da WM realizamos esse processo com inteligência.</p>
              <p class="intro-text" style="color:var(--color-text-muted); margin-top:12px;">Buscamos o melhor custo-benefício de fornecedores do mercado internacional.</p>
              <a href="/global-sourcing.html" class="btn btn-lg" style="margin-top:24px;">SAIBA MAIS</a>
            </div>
            <div>
              <ul class="ebook-info__bullets" style="list-style:none; padding:0;">
                <li style="background:#fff; padding:20px; border-radius:var(--radius-lg); border:1px solid #efefef; display:flex; gap:16px; margin-bottom:16px; color:var(--color-text-muted);">
                  <span class="card-number-badge" style="margin-bottom:0; width:28px; height:28px;">1</span>
                  <span>Detectamos e estudamos os fornecedores mais adequados para seu caso</span>
                </li>
                <li style="background:#fff; padding:20px; border-radius:var(--radius-lg); border:1px solid #efefef; display:flex; gap:16px; margin-bottom:16px; color:var(--color-text-muted);">
                  <span class="card-number-badge" style="margin-bottom:0; width:28px; height:28px;">2</span>
                  <span>Desenhamos operações com foco na otimização do custo-benefício</span>
                </li>
                <li style="background:#fff; padding:20px; border-radius:var(--radius-lg); border:1px solid #efefef; display:flex; gap:16px; color:var(--color-text-muted);">
                  <span class="card-number-badge" style="margin-bottom:0; width:28px; height:28px;">3</span>
                  <span>Trabalhamos com parceiros globais que ampliam nossa capacidade</span>
                </li>
              </ul>
            </div>
          </div>
        </section>
        """
        render_html_page(
            os.path.join(ROOT_DIR, "solucoes-wm.html"), 
            "Nossas Soluções", 
            "Conheça as soluções em comércio exterior da WM Trading.", 
            sol_content, 
            head_tpl, header_tpl, footer_tpl
        )

    # 3. GENERATE SEGMENTS PAGES
    print("\nGenerating Segments...")
    segments_files = glob.glob(os.path.join(CONTENT_DIR, "segments", "*.json"))
    for file_path in segments_files:
        with open(file_path, "r", encoding="utf-8") as f:
            s = json.load(f)
            
        slug = s["slug"]
        if slug in SEGMENT_URL_OVERRIDES:
            print(f" - skipping segments/{slug} (pagina manual: {SEGMENT_URL_OVERRIDES[slug]})")
            continue
        print(f" - compiling segments/{slug}...")
        
        # Build cover background image
        hero_bg_img = ""
        assets = SEGMENT_IMAGES_MAP.get(slug, {})
        cover_img = assets.get("cover")
        if not cover_img:
            # Fallback
            cover_img = f"/wp-content/uploads/2024/05/imagens-thumbnail-site_{slug}.webp"
            if slug == "equipamentos-fotovoltaicos" or slug == "cases-de-usinas-fotovoltaicas":
                cover_img = "/wp-content/uploads/2024/05/imagens-thumbnail-site_equi-fotovoltaico.webp"
            elif slug == "produtos-quimicos":
                cover_img = "/wp-content/uploads/2024/05/imagens-thumbnail-site_produtos_quimicos.webp"
            elif slug == "autopecas":
                cover_img = "/wp-content/uploads/2024/05/imagens-thumbnail-site_autopecas.webp"
            
        hero_bg_img = f'<img src="{cover_img}" alt="{s["name"]}" class="dynamic-hero__bg" />'
            
        hero_html = f"""
        <section class="dynamic-hero">
          {hero_bg_img}
          <div class="container dynamic-hero__container">
            <p class="dynamic-hero__eyebrow">Segmento</p>
            <h1 class="dynamic-hero__title" style="font-weight: var(--fw-light);">IMPORTAÇÃO DE<br><b><span class="text-primary" style="font-weight: var(--fw-extrabold);">{s["name"].upper()}</span></b></h1>
            <a href="#contato-form" class="btn btn-lg" style="margin-top: 24px;">Falar com um especialista</a>
          </div>
        </section>
        """
        
        # Build Intro Section (Split layout if video or intro image is available)
        video_url = assets.get("video", "")
        intro_img = assets.get("intro_image", "")
        embed_url = get_youtube_embed_url(video_url) if video_url else ""
        
        intro_html = ""
        hero_q = s.get("heroQuestion", f"Quer importar {s['name']} com agilidade e segurança?")
        hero_s = s.get("heroSub", "Entre em contato com a trading mais completa do Brasil para otimizar essa operação para sua empresa!")
        
        if embed_url or intro_img:
            media_html = ""
            if embed_url:
                media_html = f"""
                <div class="split-section__image-wrap">
                  <iframe src="{embed_url}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen style="width:100%; height:315px; border-radius:var(--radius-lg); box-shadow: 0 10px 30px rgba(0,0,0,0.15);"></iframe>
                </div>
                """
            else:
                media_html = f"""
                <div class="split-section__image-wrap">
                  <img src="{intro_img}" alt="{s["name"]}" class="split-section__image" style="width:100%; border-radius:var(--radius-lg); box-shadow: 0 10px 30px rgba(0,0,0,0.15);" />
                </div>
                """
                
            intro_html = f"""
            <section class="page-section">
              <div class="container split-section" style="align-items: center; gap: 40px;">
                <div class="split-section__text">
                  <h2 class="card-title" style="font-size: var(--fs-lg); font-weight: var(--fw-semibold); color: var(--color-primary); margin-bottom: 18px;">{hero_q}</h2>
                  <p class="card-desc" style="font-size: var(--fs-base); line-height: 1.7; color: var(--color-text-dark); margin-bottom: 24px;">{hero_s}</p>
                  <a href="#contato-form" class="btn btn-lg">Falar com um especialista</a>
                </div>
                {media_html}
              </div>
            </section>
            """
        else:
            intro_html = f"""
            <section class="page-section">
              <div class="container intro-container" style="max-width: 800px; margin: 0 auto; text-align: center;">
                <h2 class="card-title" style="font-size: var(--fs-lg); font-weight: var(--fw-semibold); color: var(--color-primary); margin-bottom: 18px;">{hero_q}</h2>
                <p class="card-desc" style="font-size: var(--fs-base); line-height: 1.7; color: var(--color-text-dark);">{hero_s}</p>
                <a href="#contato-form" class="btn btn-lg" style="margin-top: 24px;">Falar com um especialista</a>
              </div>
            </section>
            """
            
        # Build Sections
        sections_html = ""
        section_images = assets.get("section_images", [])
        if s.get("sections"):
            split_sec_count = 0
            for idx, sec in enumerate(s["sections"]):
                bg_class = "page-section--alternate" if idx % 2 == 1 else ""
                img_path = section_images[idx] if idx < len(section_images) else ""
                
                if img_path:
                    text_block = f"""
                    <div class="split-section__text">
                      <h2 class="card-title" style="font-size: var(--fs-lg); font-weight: var(--fw-semibold); color: var(--color-primary); margin-bottom: 18px;">{sec["heading"]}</h2>
                      <p class="card-desc" style="font-size: var(--fs-base); line-height: 1.7; white-space: pre-line; color: var(--color-text-dark);">{sec["text"]}</p>
                    </div>
                    """
                    img_block = f"""
                    <div class="split-section__image-wrap">
                      <img src="{img_path}" alt="{sec["heading"]}" class="split-section__image" />
                    </div>
                    """
                    # Alternate alignment based on split_sec_count
                    if split_sec_count % 2 == 0:
                        inner_html = text_block + img_block
                    else:
                        inner_html = img_block + text_block
                        
                    sections_html += f"""
                    <section class="page-section {bg_class}">
                      <div class="container split-section" style="align-items: center; gap: 40px;">
                        {inner_html}
                      </div>
                    </section>
                    """
                    split_sec_count += 1
                else:
                    sections_html += f"""
                    <section class="page-section {bg_class}">
                      <div class="container intro-container">
                        <h2 class="card-title" style="font-size: var(--fs-lg); font-weight: var(--fw-semibold); color: var(--color-primary); margin-bottom: 18px;">{sec["heading"]}</h2>
                        <p class="card-desc" style="font-size: var(--fs-base); line-height: 1.7; white-space: pre-line; color: var(--color-text-dark);">{sec["text"]}</p>
                      </div>
                    </section>
                    """
                
        # Build Benefits
        benefits_html = ""
        if s.get("benefits") and len(s["benefits"]) > 0:
            cards_html = ""
            benefit_icons = assets.get("icons", [])
            for idx, b in enumerate(s["benefits"]):
                if idx < len(benefit_icons):
                    icon_html = f"""
                    <div class="benefit-card__icon-container">
                      <img src="{benefit_icons[idx]}" alt="{b["title"]}" class="benefit-card__icon" />
                    </div>
                    """
                else:
                    icon_html = f'<span class="card-number-badge">{idx + 1}</span>'
                cards_html += f"""
                <div class="benefit-card benefit-card-centered">
                  {icon_html}
                  <h3 class="card-title">{b["title"]}</h3>
                  <p class="card-desc">{b["desc"]}</p>
                </div>
                """
            benefits_html = f"""
            <section class="page-section page-section--alternate">
              <div class="container">
                <h2 class="section-title-center" style="font-size: var(--fs-xl); font-weight: var(--fw-semibold); color: var(--color-primary); margin-bottom: 8px;">Benefícios de importar {s["name"]} com a WM</h2>
                <p class="text-center" style="color: var(--color-text-muted); font-size: var(--fs-sm); margin-bottom: 40px;">Confira os diferenciais de importar {s["name"]} com a WM</p>
                <div class="cards-grid">
                  {cards_html}
                </div>
              </div>
            </section>
            """
            
        # Build Contact Form Section
        # Map slug to option labels
        form_select_label = "Outros"
        slug_mapping = {
            "aco": "Metais & Derivados",
            "autopecas": "Partes e Peças Automotivas",
            "cosmeticos": "Cosméticos e Healthcare",
            "drone": "Aeronaves",
            "maquinas": "Máquinas e Equipamentos",
            "produtos-quimicos": "Produtos Químicos",
            "vinho": "Alimentos e Bebidas",
            "combustivel": "Combustível",
            "derivados-petroleo": "Combustível",
            "equipamentos-fotovoltaicos": "Energia Renovável",
            "cases-de-usinas-fotovoltaicas": "Energia Renovável",
            "informatica-e-telecomunicacoes": "Informática e Eletrônicos",
            "rebocadores": "Aeronaves",
            "importacao-aeronaves": "Aeronaves",
        }
        selected_seg_label = slug_mapping.get(slug, "Outros")
        
        form_html = build_contact_form_html("segmentos", selected_seg_label)
        form_image = assets.get("form_image", "")
        
        if form_image:
            contact_section_html = f"""
            <section class="page-section" id="contato-form" style="background: var(--color-bg-dark); color: var(--color-text-white);">
              <div class="container split-section" style="align-items: center; gap: 50px;">
                <div class="split-section__text" style="color: var(--color-text-white);">
                  <h2 class="section-title-left" style="color:var(--color-text-white); font-weight:var(--fw-semibold); text-align: left; margin-bottom: 18px; line-height: 1.3;">Solucione sua importação de {s["name"]} com a WM</h2>
                  <p style="color:rgba(255,255,255,0.7); margin-bottom:30px; font-size: var(--fs-base); line-height: 1.6;">Preencha o formulário e um dos nossos especialistas entrará em contato com você.</p>
                  <img src="{form_image}" alt="Solucione sua importação de {s["name"]}" style="width:100%; border-radius: var(--radius-lg); box-shadow: 0 10px 30px rgba(0,0,0,0.3);" />
                </div>
                <div style="background:#fff; color:var(--color-text-dark); padding: 40px; border-radius: var(--radius-xl); box-shadow: 0 10px 30px rgba(0,0,0,0.25); width: 100%;">
                  {form_html}
                </div>
              </div>
            </section>
            """
        else:
            contact_section_html = f"""
            <section class="page-section" id="contato-form" style="background: var(--color-bg-dark); color: var(--color-text-white);">
              <div class="container" style="max-width:800px;">
                <h2 class="section-title-center" style="color:var(--color-text-white); font-weight:var(--fw-semibold);">Solucione sua importação de {s["name"]} com a WM</h2>
                <p class="text-center" style="color:rgba(255,255,255,0.7); margin-bottom:30px;">Preencha o formulário e um dos nossos especialistas entrará em contato com você.</p>
                <div style="background:#fff; color:var(--color-text-dark); padding: 40px; border-radius: var(--radius-xl); box-shadow: 0 10px 30px rgba(0,0,0,0.25);">
                  {form_html}
                </div>
              </div>
            </section>
            """
        
        body_content = hero_html + intro_html + sections_html + benefits_html + contact_section_html
        output_path = os.path.join(SEGMENTS_OUT_DIR, f"{slug}.html")
        render_html_page(output_path, f"Importação de {s['name']}", s.get("heroQuestion", s["name"]), body_content, head_tpl, header_tpl, footer_tpl)

    # 3b. GENERATE SEGMENTS INDEX PAGE (segmentos/index.html) — lista todos os
    # segmentos em cards no padrão da home; alvo do "VER TODOS" e da URL antiga /segmentos/
    print(" - compiling segments index (segmentos/index.html)...")
    seg_by_slug = {}
    for file_path in segments_files:
        with open(file_path, "r", encoding="utf-8") as f:
            s = json.load(f)
        seg_by_slug[s["slug"]] = s

    def build_segment_index_card(slug, s, thumb):
        name = s["name"]
        # cardDesc = texto do card na página /segmentos/ do site antigo
        desc = s.get("cardDesc") or s.get("heroQuestion") or f"Importação de {name} com agilidade e segurança."
        # Segmentos com pagina manual nao tem /segmentos/<slug>.html — o card
        # precisa apontar para a URL de verdade, senao gera link morto.
        url = SEGMENT_URL_OVERRIDES.get(slug, f"/segmentos/{slug}.html")
        return f"""
        <div class="segmento-card">
          <div class="segmento-card-img">
            <a href="{url}" aria-label="Importação de {_esc_attr(name)}">
              <img src="{thumb}" alt="Importação de {_esc_attr(name)}" loading="lazy" />
            </a>
            <div class="segmento-badge-area">
              <span class="segmento-tag">{name}</span>
            </div>
          </div>
          <div class="segmento-content">
            <p class="segmento-card-desc">{desc}</p>
            <a href="{url}" class="link-arrow">Confira →</a>
          </div>
        </div>"""

    index_cards_html = ""
    for slug, thumb in SEGMENT_INDEX_THUMBS.items():
        s = seg_by_slug.pop(slug, None)
        if s:
            index_cards_html += build_segment_index_card(slug, s, thumb)
    # segmentos novos sem thumb mapeado entram no fim usando a capa da própria página
    for slug, s in seg_by_slug.items():
        cover = SEGMENT_IMAGES_MAP.get(slug, {}).get("cover") or \
            f"/wp-content/uploads/2024/05/imagens-thumbnail-site_{slug}.webp"
        index_cards_html += build_segment_index_card(slug, s, cover)

    index_form_html = build_contact_form_html("segmentos", "Outros")
    index_body = f"""
    <section class="dynamic-hero">
      <div class="container dynamic-hero__container">
        <p class="dynamic-hero__eyebrow">Segmentos</p>
        <h1 class="dynamic-hero__title" style="font-weight: var(--fw-light);">Especialistas na importação em<br><b><span class="text-primary" style="font-weight: var(--fw-extrabold);">DIVERSOS SETORES</span></b></h1>
        <p class="dynamic-hero__subtitle">A WM Trading está desde 2004 no mercado e é especialista na importação de diversos setores. Com nossos cases, comprovamos como nossa expertise técnica e planejamento nos fazem referência no mercado.</p>
      </div>
    </section>

    <section class="page-section page-section--alternate">
      <div class="container">
        <div class="segmentos-index-grid">
          {index_cards_html}
        </div>
      </div>
    </section>

    <section class="page-section">
      <div class="container" style="max-width: 800px; margin: 0 auto; text-align: center;">
        <h2 class="section-title-center" style="margin-bottom: 16px;">Confira nosso <span class="text-primary">Blog</span></h2>
        <p class="card-desc" style="font-size: var(--fs-base); line-height: 1.7; color: var(--color-text-dark);">Notícias, artigos e conteúdos sobre importação e comércio exterior para a sua empresa.</p>
        <a href="/blog" class="btn btn-lg" style="margin-top: 24px;">Acessar o Blog →</a>
      </div>
    </section>

    <section class="page-section" id="contato-form" style="background: var(--color-bg-dark); color: var(--color-text-white);">
      <div class="container" style="max-width:800px;">
        <h2 class="section-title-center" style="color:var(--color-text-white); font-weight:var(--fw-semibold);">Não encontrou o seu segmento?</h2>
        <p class="text-center" style="color:rgba(255,255,255,0.7); margin-bottom:30px;">A WM atua em muitos outros setores. Preencha o formulário e um dos nossos especialistas entrará em contato com você.</p>
        <div style="background:#fff; color:var(--color-text-dark); padding: 40px; border-radius: var(--radius-xl); box-shadow: 0 10px 30px rgba(0,0,0,0.25);">
          {index_form_html}
        </div>
      </div>
    </section>
    """
    render_html_page(
        os.path.join(SEGMENTS_OUT_DIR, "index.html"),
        "Segmentos",
        "A WM Trading é especialista na importação de diversos setores: aeronaves, energia solar, aço, máquinas, cosméticos, informática e muito mais.",
        index_body, head_tpl, header_tpl, footer_tpl
    )

    # 4. GENERATE AIRCRAFT PAGES
    print("\nGenerating Aircraft models...")
    aircraft_files = glob.glob(os.path.join(CONTENT_DIR, "aircraft", "*.json"))
    for file_path in aircraft_files:
        with open(file_path, "r", encoding="utf-8") as f:
            a = json.load(f)
            
        slug = a["slug"]
        print(f" - compiling aeronaves/{slug}...")
        
        # Build Hero with cover backdrop
        hero_bg_img = ""
        if "cover" in a and a["cover"]:
            hero_bg_img = f'<img src="{a["cover"]}" alt="{a["name"]}" class="dynamic-hero__bg" />'
            
        hero_html = f"""
        <section class="dynamic-hero">
          {hero_bg_img}
          <div class="container dynamic-hero__container">
            <p class="dynamic-hero__eyebrow">{a["maker"]} · Importação de aeronaves</p>
            <h1 class="dynamic-hero__title">{a["heroTitle"]}</h1>
            {f'<p class="dynamic-hero__subtitle">{a["intro"]}</p>' if a.get("intro") else ''}
            <a href="/fale-conosco.html" class="btn btn-lg">Importar o meu {a["name"]}</a>
          </div>
        </section>
        """
        
        # Specs grid
        specs_html = ""
        if a.get("specs") and len(a["specs"]) > 0:
            cards_html = ""
            for sp in a["specs"]:
                cards_html += f"""
                <div class="spec-card">
                  <p class="spec-card__value">{sp["value"]}</p>
                  <p class="spec-card__label">{sp["label"]}</p>
                </div>
                """
            specs_html = f"""
            <section class="specifications-section">
              <div class="container">
                <h2 class="section-title-center">Especificações do {a["name"]}</h2>
                <div class="specs-grid">
                  {cards_html}
                </div>
              </div>
            </section>
            """
            
        # Highlights
        highlights_html = ""
        if a.get("sections") and len(a["sections"]) > 0:
            cards_html = ""
            for idx, sec in enumerate(a["sections"]):
                cards_html += f"""
                <div class="highlight-card">
                  <h3 class="card-title">{sec["heading"]}</h3>
                  <p class="card-desc">{sec["text"]}</p>
                </div>
                """
            highlights_html = f"""
            <section class="page-section">
              <div class="container">
                <h2 class="section-title-center">Destaques do {a["name"]}</h2>
                <div class="cards-grid">
                  {cards_html}
                </div>
              </div>
            </section>
            """
            
        # Final CTA
        cta_html = f"""
        <section class="page-section" style="background: var(--color-primary); color: var(--color-text-white); text-align: center;">
          <div class="container">
            <h2 class="t-display" style="margin-bottom: 16px;">Importe o seu {a["name"]} com a WM</h2>
            <p class="t-lead" style="margin-bottom: 24px;">Tempo recorde na liberação e expertise total nas leis aeronáuticas.</p>
            <a href="/fale-conosco.html" class="btn btn-white btn-lg">Falar com um especialista</a>
          </div>
        </section>
        """
        
        body_content = hero_html + specs_html + highlights_html + cta_html
        output_path = os.path.join(AIRCRAFT_OUT_DIR, f"{slug}.html")
        # "name" may already include the maker (e.g. "Piper M500") — avoid "Piper Piper M500"
        full_name = a["name"] if a["name"].lower().startswith(a["maker"].lower()) else f"{a['maker']} {a['name']}"
        meta_desc = a.get("metaDescription", a["heroTitle"])
        render_html_page(output_path, f"Importação {full_name}", meta_desc, body_content, head_tpl, header_tpl, footer_tpl)

    # 5. GENERATE EBOOKS LANDING PAGES
    print("\nGenerating Ebook landing pages...")
    ebooks_files = glob.glob(os.path.join(CONTENT_DIR, "ebooks", "*.json"))
    for file_path in ebooks_files:
        with open(file_path, "r", encoding="utf-8") as f:
            e = json.load(f)
            
        slug = e["slug"]
        print(f" - compiling ebooks/{slug}...")
        
        # Bullets
        bullets_html = ""
        if e.get("bullets") and len(e["bullets"]) > 0:
            li_html = ""
            for b in e["bullets"]:
                li_html += f"<li>{b}</li>"
            bullets_html = f'<ul class="ebook-info__bullets">{li_html}</ul>'
            
        form_html = build_ebook_form_html(e["title"], e["pdfUrl"])
        
        ebook_content = f"""
        <section class="ebook-layout">
          <div class="container">
            <div class="ebook-grid">
              <div>
                <p class="ebook-info__tag">E-book gratuito</p>
                <h1 class="ebook-info__title">{e["title"]}</h1>
                {f'<p class="ebook-info__subtitle">{e["subtitle"]}</p>' if e.get("subtitle") else ''}
                <p class="ebook-info__description">{e["description"]}</p>
                {bullets_html}
              </div>
              <div>
                <div class="ebook-form-panel">
                  <h3 class="ebook-form-panel__title">Preencha os dados abaixo para receber o material</h3>
                  {form_html}
                </div>
              </div>
            </div>
          </div>
        </section>
        """
        
        output_path = os.path.join(EBOOKS_OUT_DIR, f"{slug}.html")
        render_html_page(output_path, e["title"], e["description"][:160], ebook_content, head_tpl, header_tpl, footer_tpl)

    # 6. GENERATE INSTITUTIONAL PAGES
    print("\nGenerating Institutional Pages...")
    
    # 6A. ABOUT
    print(" - compiling about.html...")
    values_pills_html = ""
    values = [
        "Inovação e melhoria contínua", "Agilidade", "Ética e transparência",
        "Conectividade", "Desenvolvimento da empresa e das pessoas",
        "Cliente no centro do negócio", "Excelência"
    ]
    for val in values:
        values_pills_html += f'<span class="value-pill">{val}</span>\n'
        
    diffs_html = ""
    differentials = [
        {"title": "Atendimento Personalizado", "desc": "A atenção que prestamos aos nossos clientes é incomparável. Tratamos todos com prioridade e estamos sempre à disposição para oferecer o melhor serviço."},
        {"title": "Ampla Gama de Fornecedores", "desc": "Possuímos uma enorme rede de fornecedores com vantagens exclusivas para otimizar o seu processo de importação."},
        {"title": "Planejamento e Gestão", "desc": "O planejamento é fundamental para enquadrar a operação na modalidade correta e evitar complicações no processo de importação."},
        {"title": "Localização Estratégica", "desc": "Pensando na otimização da cadeia logística e tributária, estamos estrategicamente localizados em 15 estados brasileiros e no Panamá."}
    ]
    for idx, d in enumerate(differentials):
        diffs_html += f"""
        <div class="benefit-card">
          <span class="card-number-badge">{idx + 1}</span>
          <h3 class="card-title">{d["title"]}</h3>
          <p class="card-desc">{d["desc"]}</p>
        </div>
        """
        
    about_body = f"""
    <section class="dynamic-hero">
      <div class="container dynamic-hero__container">
        <p class="dynamic-hero__eyebrow">Conheça nossa história</p>
        <h1 class="dynamic-hero__title">Desde 2004 conectando mercados, movimentando negócios e aproximando pessoas.</h1>
        <p class="dynamic-hero__subtitle">A WM carrega no centro do seu DNA a busca incessante pela excelência e agilidade em todas as entregas.</p>
      </div>
    </section>
    
    <section class="page-section">
      <div class="container intro-container">
        <h2 class="t-h2" style="margin-bottom:20px;">Sobre a WM</h2>
        <div class="intro-text" style="color:var(--color-text-muted); display:flex; flex-direction:column; gap:16px;">
          <p>Tendo o cliente como centro do nosso negócio, rapidamente expandimos nossa atividade, ampliando o número de filiais, conquistando novos benefícios fiscais e ganhando espaço no mercado internacional. Mais do que obcecados por entregar o melhor projeto logístico e tributário, lutamos diariamente para cultivar nossos clientes.</p>
          <p>Hoje a WM é uma das maiores tradings do Brasil, disposta a entregar projetos personalizados para diversas empresas e segmentos. Os 21 anos de experiência em operações bem-sucedidas traduzem a intensidade do desejo de cumprir nossa principal missão: ser a mais completa solução em comércio exterior.</p>
        </div>
      </div>
    </section>
    
    <section class="specifications-section" style="background:var(--color-bg-light);">
      <div class="container specs-grid" style="grid-template-columns: repeat(2, 1fr);">
        <div class="spec-card">
          <p class="spec-card__value">21 anos</p>
          <p class="spec-card__label">de experiência</p>
        </div>
        <div class="spec-card">
          <p class="spec-card__value">15 filiais</p>
          <p class="spec-card__label">Brasil + Panamá</p>
        </div>
        <div class="spec-card">
          <p class="spec-card__value">ISO 9001</p>
          <p class="spec-card__label">certificação</p>
        </div>
        <div class="spec-card">
          <p class="spec-card__value">90%</p>
          <p class="spec-card__label">satisfação dos clientes</p>
        </div>
      </div>
    </section>
    
    <section class="page-section">
      <div class="container">
        <h2 class="section-title-center">Nossos valores</h2>
        <div class="values-wrap">
          {values_pills_html}
        </div>
      </div>
    </section>
    
    <section class="page-section page-section--alternate">
      <div class="container">
        <h2 class="section-title-center">Diferenciais que fazem de nós a sua melhor escolha</h2>
        <div class="cards-grid">
          {diffs_html}
        </div>
      </div>
    </section>
    
    <section class="page-section">
      <div class="container intro-container">
        <h2 class="t-h2" style="margin-bottom:20px;">Nossa política de qualidade</h2>
        <blockquote style="border-left: 4px solid var(--color-primary); padding-left: 20px; font-style: italic; color: var(--color-text-muted); font-size: var(--fs-md); margin-bottom: 24px;">
          “Atuar na Gestão de Comércio Internacional, aproximando empresas, agregando controle nas etapas do processo de importação de mercadorias em geral, com comprometimento e eficácia no atendimento das necessidades dos clientes, com melhoria contínua dos resultados e a capacitação dos nossos colaboradores.”
        </blockquote>
        <p class="intro-text" style="color:var(--color-text-muted);">Trabalhamos com o certificado ISO 9001, dentro de padrões internacionais de qualidade, e mantemos um Sistema de Gestão da Qualidade que nos permite conhecer a opinião dos clientes e aperfeiçoar nossos serviços. Na última Pesquisa de Satisfação, atingimos <strong>90% de satisfação</strong> — e seguimos em busca de mais.</p>
      </div>
    </section>
    
    <section class="page-section" style="background: var(--color-primary); color: var(--color-text-white); text-align: center;">
      <div class="container">
        <h2 class="t-display" style="margin-bottom: 16px;">Tem um projeto em mente?</h2>
        <p class="t-lead" style="margin-bottom: 24px;">Fale com nossos especialistas e garanta a melhor operação para a sua empresa.</p>
        <a href="/fale-conosco.html" class="btn btn-white btn-lg">Quero saber mais</a>
      </div>
    </section>
    """
    render_html_page(os.path.join(ROOT_DIR, "about.html"), "Quem somos", "Conheça a história e os diferenciais da WM Trading.", about_body, head_tpl, header_tpl, footer_tpl)
    
    # 6B. CARREIRAS
    print(" - compiling carreiras.html...")
    carreiras_body = f"""
    <section class="dynamic-hero">
      <div class="container dynamic-hero__container">
        <p class="dynamic-hero__eyebrow">Carreiras</p>
        <h1 class="dynamic-hero__title">Faça parte de uma das maiores tradings do Brasil</h1>
        <p class="dynamic-hero__subtitle">Deseja trabalhar conosco? Conheça nossa cultura e veja se o seu perfil combina com os nossos valores.</p>
      </div>
    </section>
    
    <section class="page-section">
      <div class="container">
        <h2 class="section-title-center">Nossa cultura</h2>
        <div class="cards-grid">
          <div class="benefit-card">
            <h3 class="card-title">Cliente no centro</h3>
            <p class="card-desc">Nosso principal compromisso é com a satisfação do cliente, com um Sistema de Gestão de Qualidade e o certificado ISO 9001.</p>
          </div>
          <div class="benefit-card">
            <h3 class="card-title">Atuação ampla</h3>
            <p class="card-desc">Conquistamos um grande número de licenças (ANVISA, MAPA, Inmetro e outras), o que nos permite atuar em diversos ramos e segmentos.</p>
          </div>
          <div class="benefit-card">
            <h3 class="card-title">Crescimento</h3>
            <p class="card-desc">Não medimos esforços para ampliar o sucesso e a competitividade dos negócios — e das pessoas que fazem a WM acontecer.</p>
          </div>
        </div>
      </div>
    </section>
    
    <section class="page-section page-section--alternate text-center" style="text-align:center;">
      <div class="container intro-container">
        <h2 class="t-h2" style="margin-bottom:16px;">Vagas abertas</h2>
        <p class="intro-text" style="color:var(--color-text-muted);">Confira as oportunidades disponíveis e candidate-se. Estamos sempre em busca de novos talentos.</p>
        <a href="/fale-conosco.html" class="btn btn-lg" style="margin-top:24px;">Quero me candidatar</a>
        <p class="card-desc" style="margin-top:20px; font-size:12px;">Ao se inscrever no processo seletivo, você concorda com o tratamento dos seus dados pessoais nos termos da nossa Declaração de Privacidade para Recrutamento e Seleção.</p>
      </div>
    </section>
    """
    render_html_page(os.path.join(ROOT_DIR, "carreiras.html"), "Trabalhe Conosco", "Faça parte da nossa equipe na WM Trading.", carreiras_body, head_tpl, header_tpl, footer_tpl)

    # 6C. UNIDADES
    print(" - compiling unidades.html...")
    branches_cards = ""
    for b in BRANCHES:
        clean_phone = get_clean_phone(b["phone"])
        branches_cards += f"""
        <div class="branch-card">
          <h3 class="branch-card__title">{b["city"]} <span class="branch-card__state">/ {b["state"]}</span></h3>
          <a href="tel:{clean_phone}" class="branch-card__phone">{b["phone"]}</a>
        </div>
        """
    unidades_body = f"""
    <section class="page-section">
      <div class="container">
        <div style="margin-bottom:40px;">
          <p class="dynamic-hero__eyebrow" style="margin-bottom:8px;">Unidades</p>
          <h1 class="t-display" style="font-weight:var(--fw-semibold); font-size:var(--fs-2xl); line-height:1.2;">Presença em todo o Brasil</h1>
          <p class="intro-text" style="color:var(--color-text-muted); max-width:650px; margin-top:12px;">Estamos estrategicamente localizados em diversos estados — e também no Panamá — para otimizar a logística e a tributação das suas importações. Fale com a filial mais próxima.</p>
        </div>
        
        <div class="branches-grid">
          {branches_cards}
        </div>
        
        <div style="margin-top:60px; text-align:center;">
          <a href="/fale-conosco.html" class="btn btn-lg">Falar com um especialista</a>
        </div>
      </div>
    </section>
    """
    render_html_page(os.path.join(ROOT_DIR, "unidades.html"), "Unidades e Filiais", "Presença comercial nacional da WM Trading.", unidades_body, head_tpl, header_tpl, footer_tpl)

    # 6D. FALE CONOSCO
    print(" - compiling fale-conosco.html...")
    contact_form_html = build_contact_form_html("contato")
    
    # Pre-render list of branches for form page without backslash issues
    branches_li_html = ""
    for b in BRANCHES[:8]:
        clean_phone = get_clean_phone(b["phone"])
        branches_li_html += f"""
        <li style="border-bottom:1px solid #efefef; padding-bottom:10px;">
          <p style="font-weight:var(--fw-semibold); font-size:var(--fs-sm);">{b["city"]} <span style="font-weight:normal; color:var(--color-text-muted);">/ {b["state"]}</span></p>
          <a href="tel:{clean_phone}" class="text-primary" style="font-size:12px; text-decoration:none; font-weight:var(--fw-semibold);">{b["phone"]}</a>
        </li>
        """

    fale_conosco_body = f"""
    <section class="page-section">
      <div class="container">
        <div style="margin-bottom:40px;">
          <p class="dynamic-hero__eyebrow" style="margin-bottom:8px;">Fale Conosco</p>
          <h1 class="t-display" style="font-weight:var(--fw-semibold); font-size:var(--fs-2xl); line-height:1.2;">Tem um projeto de importação?</h1>
          <p class="intro-text" style="color:var(--color-text-muted); max-width:650px; margin-top:12px;">Fale com nossos especialistas e garanta a melhor operação tributária e logística para a sua empresa.</p>
        </div>
        
        <div style="display:grid; grid-template-columns: 1fr; gap:60px; align-items:start;" class="ebook-grid">
          <div style="background:#fff; border:1px solid #efefef; padding:40px; border-radius:var(--radius-xl); box-shadow:var(--shadow-card);">
            {contact_form_html}
          </div>
          <div>
            <h2 class="t-h3" style="margin-bottom:16px;">Nossas filiais</h2>
            <p class="intro-text" style="color:var(--color-text-muted); font-size:var(--fs-sm); margin-bottom:24px;">15 filiais no Brasil + Panamá. Fale com a unidade mais próxima de você.</p>
            <ul style="list-style:none; padding:0; display:grid; grid-template-columns:1fr 1fr; gap:16px;">
              {branches_li_html}
            </ul>
          </div>
        </div>
      </div>
    </section>
    """
    render_html_page(os.path.join(ROOT_DIR, "fale-conosco.html"), "Fale Conosco", "Entre em contato com a equipe de especialistas da WM Trading.", fale_conosco_body, head_tpl, header_tpl, footer_tpl)

    # 6E. PODCAST (WM Cast)
    print(" - compiling podcast.html...")
    podcast_json_path = os.path.join(CONTENT_DIR, "podcast.json")
    episodes_cards = ""
    episodes_count = 0
    if os.path.exists(podcast_json_path):
        with open(podcast_json_path, "r", encoding="utf-8") as f:
            episodes = json.load(f)
            
        episodes_count = len(episodes)
        # Sort episodes by date descending, desempatando por titulo (mesmo
        # motivo do listing do blog: sem desempate a ordem nao e reproduzivel)
        episodes.sort(key=lambda x: x.get("title", ""))
        episodes.sort(key=lambda x: x.get("date", ""), reverse=True)
        
        for ep in episodes:
            raw_date = ep.get("date", "2024-01-01")
            formatted_date = raw_date
            try:
                dt = datetime.strptime(raw_date.split(" ")[0], "%Y-%m-%d")
                formatted_date = dt.strftime("%d/%m/%Y")
            except:
                pass
                
            episodes_cards += f"""
            <a href="{ep["url"]}" target="_blank" rel="noopener noreferrer" class="blog-card" style="padding:24px; text-decoration:none;">
              <span class="blog-card__category" style="font-size:11px;">WM CAST EPISÓDIO</span>
              <h3 class="blog-card__title" style="margin-top:8px; margin-bottom:16px;">{ep["title"]}</h3>
              <div style="display:flex; justify-content:space-between; align-items:center; margin-top:auto; font-size:12px; color:var(--color-text-muted);">
                <span>{formatted_date}</span>
                <span class="text-primary" style="font-weight:var(--fw-semibold);">Assistir →</span>
              </div>
            </a>
            """
            
    podcast_body = f"""
    <section class="page-section">
      <div class="container">
        <div style="margin-bottom:40px;">
          <p class="dynamic-hero__eyebrow" style="margin-bottom:8px;">WM Cast</p>
          <h1 class="t-display" style="font-weight:var(--fw-semibold); font-size:var(--fs-2xl); line-height:1.2;">O podcast do comércio exterior</h1>
          <p class="intro-text" style="color:var(--color-text-muted); max-width:650px; margin-top:12px;">Episódios exclusivos com especialistas do setor, abordando temas essenciais e atuais como segurança, planejamento, regimes tributários e regulamentações para o sucesso das operações de comércio internacional.</p>
          <div style="display:flex; gap:16px; margin-top:24px;">
            <a href="https://open.spotify.com/show/4GBwVHuaEzXhB9TqIyFROi" target="_blank" rel="noopener noreferrer" class="btn">Ouvir no Spotify</a>
            <a href="https://www.youtube.com/channel/UCGdBOuDTCnglBU3expUhMPg" target="_blank" rel="noopener noreferrer" class="btn btn-outline" style="border:1.5px solid #e3e3e3; color:var(--color-text-dark);">Assistir no YouTube</a>
          </div>
        </div>
        
        <!-- Spotify Player -->
        <div style="margin-bottom:48px; border-radius:var(--radius-xl); overflow:hidden; border:1px solid #efefef; box-shadow:var(--shadow-card);">
          <iframe title="WM Cast no Spotify" src="https://open.spotify.com/embed/show/4GBwVHuaEzXhB9TqIyFROi?theme=0" width="100%" height="352" frameborder="0" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" loading="lazy"></iframe>
        </div>
        
        <h2 class="t-h2" style="margin-bottom:24px;">Todos os episódios ({episodes_count})</h2>
        <div class="blog-grid">
          {episodes_cards}
        </div>
      </div>
    </section>
    """
    render_html_page(os.path.join(ROOT_DIR, "podcast.html"), "WM Cast — Podcast", "Ouça o podcast de comércio exterior da WM Trading.", podcast_body, head_tpl, header_tpl, footer_tpl)

    # 6F. MATERIAIS
    print(" - compiling materiais.html...")
    ebooks_list = [
        {"title": "Soluções Logísticas 4PL", "slug": "4pl-ebook"},
        {"title": "Implantação da DUIMP", "slug": "duimp"},
        {"title": "Principais Impostos Incidentes na Importação", "slug": "principais-impostos-incidentes"},
        {"title": "Regime de cotas para Módulos Fotovoltaicos", "slug": "regime-de-cotas-modulos-fotovoltaicos"},
        {"title": "Reduzindo custos com a Gestão Logística da WM", "slug": "gestao-logistica-da-wm"},
        {"title": "Importação de aviões e helicópteros", "slug": "aeronaves-e-helicopteros"},
        {"title": "Importação de equipamentos de energia solar", "slug": "e-book-equipamentos-fotovoltaicos"},
        {"title": "Importação de vinhos", "slug": "importacao-de-vinhos"}
    ]
    ebooks_cards = ""
    for eb in ebooks_list:
        ebooks_cards += f"""
        <a href="/ebooks/{eb["slug"]}.html" class="blog-card" style="padding:24px; text-decoration:none; display:flex; flex-direction:column; justify-content:space-between; height:100%;">
          <div>
            <span class="blog-card__category" style="font-size:11px;">E-BOOK</span>
            <h3 class="blog-card__title" style="margin-top:8px;">{eb["title"]}</h3>
          </div>
          <span class="text-primary" style="font-weight:var(--fw-semibold); font-size:13px; margin-top:20px;">Baixar material →</span>
        </a>
        """
        
    infographics_list = [
        "Lei 14.300/2022 (energia solar)", "Incoterms", "Leasing de Máquinas",
        "Leasing de Aeronaves", "Entreposto Aduaneiro"
    ]
    info_cards = ""
    for info in infographics_list:
        info_cards += f"""
        <div class="blog-card" style="padding:24px;">
          <span class="blog-card__category" style="font-size:11px;">INFOGRÁFICO</span>
          <h3 class="blog-card__title" style="margin-top:8px; margin-bottom:20px; flex-grow:1;">{info}</h3>
          <a href="/fale-conosco.html" class="text-primary" style="font-weight:var(--fw-semibold); font-size:13px; text-decoration:none; margin-top:auto;">Baixar material →</a>
        </div>
        """
        
    materiais_body = f"""
    <section class="page-section">
      <div class="container">
        <div style="margin-bottom:40px;">
          <p class="dynamic-hero__eyebrow" style="margin-bottom:8px;">Materiais</p>
          <h1 class="t-display" style="font-weight:var(--fw-semibold); font-size:var(--fs-2xl); line-height:1.2;">Conteúdos gratuitos</h1>
          <p class="intro-text" style="color:var(--color-text-muted); max-width:650px; margin-top:12px;">Receba nossos e-books e infográficos gratuitamente. Aprofunde-se em importação, tributação e logística.</p>
        </div>
        
        <h2 class="t-h2" style="margin-bottom:24px;">E-books</h2>
        <div class="blog-grid" style="margin-bottom:56px;">
          {ebooks_cards}
        </div>
        
        <h2 class="t-h2" style="margin-bottom:24px;">Infográficos</h2>
        <div class="blog-grid">
          {info_cards}
        </div>
      </div>
    </section>
    """
    render_html_page(os.path.join(ROOT_DIR, "materiais.html"), "Materiais Gratuitos", "Baixe e-books e infográficos sobre comércio exterior.", materiais_body, head_tpl, header_tpl, footer_tpl)

    # 6G. COOKIES POLICY
    print(" - compiling politica-de-cookies.html...")
    # POLITICA DE COOKIES - replica do texto publicado em
    # https://www.wmtrading.com.br/politica-de-cookies/
    # Decisao do Renato (11/08/2026): replicar agora, validar com os
    # responsaveis e alterar depois. A versao reescrita (com a tabela de
    # cookies que o site realmente carrega) ficou guardada FORA do
    # repositorio, em PROPOSTA-POLITICA-COOKIES-v2.html.
    cookies_md_1 = """
A WM TRADING respeita a privacidade dos dados e valoriza o relacionamento com os usuários que acessam ou utilizam os seus serviços na plataforma digital. Utilizamos tecnologia para coletar informações que melhoram a experiência do usuário. Esta Política de Cookies foi desenvolvida para que você compreenda o que são cookies, quais tipos são utilizados, quais informações são coletadas e para quais finalidades.

## O que você encontrará nesta política

- O que são cookies
- Por que usamos cookies
- Quais cookies são utilizados no site da WM TRADING
- Como posso remover ou bloquear os cookies
- Alterações na Política de Cookies

## O que são cookies?

Cookies são pequenos arquivos que transferimos para o seu navegador ou dispositivo, e que nos permitem reconhecer o seu navegador ou dispositivo e saber como e quando os sites, produtos e serviços da WM TRADING são utilizados. Eles são úteis, por exemplo, para adequar a apresentação do site à tela do seu dispositivo, entender as suas preferências e oferecer um serviço mais eficiente.

## Por que usamos cookies?

A WM TRADING utiliza cookies para reconhecer os usuários quando acessam os seus serviços. Essas tecnologias nos ajudam a exibir as informações corretas e a personalizar a sua experiência de acordo com as suas configurações, facilitando o acesso e melhorando a experiência no site. Dependendo das suas preferências, os cookies também podem direcionar anúncios compatíveis com os seus interesses.

## Quais cookies são utilizados no site da WM TRADING?
    """

    cookies_tbl = """
          <table class="legal-table">
            <thead><tr><th>Categoria</th><th>Descrição</th><th>Tempo de expiração</th><th>Obrigatoriedade</th></tr></thead>
            <tbody>
              <tr>
                <td>Essenciais</td>
                <td>São essenciais para permitir a movimentação do usuário no site e fornecer acesso a recursos exclusivos para clientes. Não coletam informações que poderiam ser usadas para fins de marketing.</td>
                <td>O cookie permanece ativo enquanto a janela do navegador estiver aberta. Após o fechamento, é descartado.</td>
                <td>Esta categoria de cookies não pode ser desativada.</td>
              </tr>
              <tr>
                <td>Publicitários</td>
                <td>São definidos no site pelos parceiros publicitários e armazenam a origem da campanha que levou o usuário até o site. Essa informação é enviada à WM TRADING quando o usuário realiza cadastro através dos formulários de contato.</td>
                <td>O cookie fica armazenado por 30 dias.</td>
                <td>Esta categoria de cookies pode ser desativada.</td>
              </tr>
            </tbody>
          </table>
    """

    cookies_md_2 = """
## Como posso remover ou bloquear os cookies?

Se deseja saber quais cookies estão instalados no seu dispositivo, ou deseja excluí-los ou restringi-los, você pode utilizar as configurações do seu navegador. Explicações adicionais estão disponíveis no site do desenvolvedor de cada navegador.

Observamos que o uso de cookies nos permite oferecer uma melhor experiência. Se você bloquear os cookies ou não permitir o funcionamento de alguns deles, não podemos garantir o correto funcionamento de todas as funcionalidades das nossas plataformas, e talvez você não consiga acessar determinadas áreas. Certas funções e páginas podem não funcionar adequadamente — por exemplo, o site pode solicitar a sua localização toda vez que for acessado, mesmo que você já a tenha informado anteriormente.

A WM TRADING não se responsabiliza pelo uso de cookies de plataformas de terceiros. Recomendamos que você limpe o seu histórico de navegação regularmente, para se certificar de que o seu dispositivo utiliza apenas as tecnologias do seu interesse.

## Alterações na Política de Cookies

Como buscamos melhorar continuamente os nossos serviços, esta Política de Cookies pode passar por atualizações para refletir as melhorias realizadas. Recomendamos a visita periódica a esta página para conhecimento sobre as modificações. Caso sejam feitas alterações relevantes que exijam novo consentimento do usuário, publicaremos a atualização e solicitaremos um novo consentimento.

## Dúvidas

Em caso de dúvidas sobre esta Política de Cookies, entre em contato pelo e-mail **dpo@wmtrading.com.br**. Veja também a [Política de Privacidade](/politica-de-privacidade.html).
    """

    cookies_body = f"""
    <section class="page-section">
      <div class="container legal-container">
        <h1 class="legal-title">Política de Cookies</h1>
        <p class="legal-version" style="color:var(--color-text-muted); font-size:14px; margin-bottom:28px;">Última atualização: {POLITICA_VIGENCIA}.</p>
        <div class="prose-wm">
          {markdown_to_html(cookies_md_1)}
          {cookies_tbl}
          {markdown_to_html(cookies_md_2)}
        </div>
      </div>
    </section>
    """
    render_html_page(os.path.join(ROOT_DIR, "politica-de-cookies.html"), "Política de Cookies", "Entenda como a WM Trading utiliza cookies.", cookies_body, head_tpl, header_tpl, footer_tpl)

    # 6H. PRIVACY POLICY
    print(" - compiling politica-de-privacidade.html...")
    # POLITICA DE PRIVACIDADE - replica fiel do texto publicado em
    # https://www.wmtrading.com.br/politica-de-privacidade/
    # Decisao do Renato (11/08/2026): replicar agora o texto que ja esta no ar,
    # acionar os responsaveis para validar e alterar depois. A versao reescrita
    # para a operacao real da WM ficou guardada FORA do repositorio, em
    # PROPOSTA-POLITICA-PRIVACIDADE-v2.html, para a rodada com o Juridico.
    # Unico desvio proposital do original: razao social e endereco atualizados
    # conforme o cartao CNPJ de 2026 (WM Trading LTDA, salas 201 e 301).
    privacy_md_1 = """
## 1. Introdução

**1.1** A Política de Privacidade e Uso de Dados Pessoais tem como objetivo principal: evidenciar a transparência do compromisso da WM TRADING em garantir a proteção dos dados fornecidos pelos titulares de dados.

**1.2** Não fornecemos informações pessoais para terceiros sem a devida autorização e não divulgamos informações que possam identificar os titulares dos dados, salvo em casos de medida judicial ou determinação legal.

**1.3** A presente Política abrange o tratamento que a WM TRADING concede às informações capazes de identificar os usuários, coletadas diretamente em nosso site, área do cliente, ficha cadastral, negociação comercial, automações e integrações de dados, essas armazenadas em bases de dados eletrônicos por meio dos cadastros preenchidos ou dados recebidos advindos de e-mail, integrações entre sistemas, utilização de sistemas, dentre outros.

**1.4** A aceitação da nossa Política se dará quando você acessar ou utilizar o site, aplicativo ou serviços da WM TRADING. Isso indicará que você está ciente e em total acordo com a forma como utilizamos as suas informações e seus dados, cujo tratamento se dará com base na Lei Geral de Proteção de Dados Pessoais nº 13.709/2018 (LGPD).

## 2. Direitos dos usuários sobre os dados pessoais

### 2.1 Direito de Revogação

**2.1.1** Titulares de dados pessoais tratados pela WM TRADING poderão solicitar a revogação das permissões de uso de dados, uma vez que o prazo legal do tratamento esteja expirado, quando for o caso.

### 2.2 Direito de Divulgação

**2.2.1** A WM TRADING não divulga os dados pessoais dos titulares, exceto por determinação legal ou a pedido do próprio titular do dado.

**2.2.2** O titular dos dados pessoais tem o direito de saber, a qualquer tempo, que dados estão sendo tratados, como estão sendo tratados e, quando for o caso, com quem são compartilhados, podendo acessar tais informações através de solicitação prévia.

### 2.3 Direito de Retificação

**2.3.1** O titular tem direito de solicitar a retificação de seus dados pessoais, exceto quando se trata de informações contidas dentro dos Certificados Digitais, uma vez que tais informações são gravadas no momento da emissão do Certificado sem a possibilidade de alteração posterior.

### 2.4 Direito à Exclusão e suas Opções

**2.4.1** O titular tem direito à exclusão definitiva dos dados pessoais que tiver fornecido à WM TRADING, a seu requerimento ou ao término da relação entre as partes, ressalvadas as hipóteses de guarda obrigatória, conforme preconiza a LGPD.

### 2.5 Direito à Portabilidade

**2.5.1** As solicitações de portabilidade de dados serão analisadas caso a caso, acionando o contato dpo@wmtrading.com.br.

## 3. Responsabilidades dos titulares dos dados pessoais

**3.1** Os titulares dos dados pessoais têm a obrigação de assegurar que os dados fornecidos à WM TRADING são precisos, completos e atualizados.

## 4. Política de cookies

**4.1** Cookies são arquivos de texto contendo pequenas quantidades de informações, que são baixadas para o seu dispositivo de navegação quando você visita um site. Eles visam facilitar ou aprimorar a experiência do usuário.

**4.2** Ao utilizar o nosso site ou demais serviços, você concorda com a utilização dos cookies descritos nesta Política. Você pode alterar a configuração dos cookies, a qualquer tempo, diretamente no seu navegador. Ao bloquear os cookies, algumas funcionalidades do site poderão ser limitadas e outras poderão não funcionar.

**4.3** A WM TRADING utiliza os arquivos de cookies para a execução de diferentes tarefas, como: ajudar-nos a entender como o site está sendo usado, permitir que você navegue entre as páginas de maneira mais eficiente, lembrar suas preferências e melhorar sua experiência de navegação, com um conteúdo mais relevante para você e seus interesses, declarados ou inferidos.

**4.4** Abaixo, descrevemos as maneiras como podemos utilizar os cookies:
    """

    privacy_tbl_cookies = """
          <table class="legal-table">
            <thead><tr><th>Finalidade</th><th>Descrição</th></tr></thead>
            <tbody>
              <tr><td>Preferências, recursos e serviços</td><td>Utilizamos cookies para habilitar a funcionalidade de nossos serviços e fornecer recursos, estatísticas e conteúdo personalizado. Também usamos essas tecnologias para lembrar informações sobre seu navegador e suas preferências.</td></tr>
              <tr><td>Plugins</td><td>Utilizamos cookies para habilitar plugins dentro e fora do site da WM TRADING. Nossos plugins podem ser encontrados nos serviços da WM TRADING. Se você interagir com um plugin, ele utilizará cookies para identificar você e iniciar sua solicitação.</td></tr>
              <tr><td>Publicidade personalizada</td><td>Os cookies nos ajudam a mostrar publicidade relevante para você, tanto dentro como fora dos nossos Serviços, a medir o desempenho de tais anúncios e a fornecer relatórios sobre eles. Utilizamos cookies para saber se o conteúdo foi exibido a você ou se alguém que visualizou um anúncio voltou depois e realizou uma ação (por exemplo, baixou um documento técnico ou fez uma compra) em outro site. Do mesmo modo, nossos parceiros ou prestadores de serviços podem utilizar cookies para determinar se exibimos um anúncio ou uma publicação, e qual foi o desempenho desse anúncio ou publicação, ou nos fornecer informações sobre como você interagiu com o anúncio.</td></tr>
              <tr><td>Análise e pesquisa</td><td>Cookies nos ajudam a saber mais sobre o desempenho dos nossos Serviços e plugins em diferentes locais. Nós ou nossos prestadores de serviços usamos cookies para entender, melhorar e pesquisar produtos, recursos e serviços, inclusive enquanto você navega em nossos sites. Nós, ou nossos prestadores de serviços, usamos cookies para determinar e analisar o desempenho de anúncios ou publicações dentro e fora dos serviços oferecidos pela WM TRADING e para saber se você interagiu com nossos sites ou com sites de nossos clientes, conteúdo ou e-mails e fornecer análises com base nessas interações.</td></tr>
              <tr><td>Usabilidade</td><td>Cookie utilizado para guardar as informações compartilhadas com solução de autoatendimento, por exemplo, para melhorar a experiência de uso no site.</td></tr>
              <tr><td>Essenciais</td><td>Cookies que se referem a áreas específicas do nosso site. Permitem a navegação e a utilização das suas aplicações, tal como acessar áreas seguras do site através de login, por exemplo. Sem estes cookies, os serviços que o exijam não podem ser prestados.</td></tr>
            </tbody>
          </table>
    """

    privacy_md_2 = """
### 4.5 Como controlar ou excluir os cookies por meio do seu navegador

**4.5.1** Através do seu navegador é possível ativar, desativar ou excluir cookies. Para fazer isso, basta seguir as instruções do seu navegador, geralmente encontradas em "Ajuda", "Ferramentas" ou "Editar", ou ainda o atalho no teclado Ctrl + Shift + Delete, nos navegadores Firefox, Chrome e Edge/Internet Explorer.

**4.5.2** Desativando os cookies, algumas funcionalidades do site podem deixar de funcionar, conforme mencionado no item 4.2.

## 5. Controlador de dados

**5.1.1** Conforme determina a Lei Geral de Proteção de Dados Pessoais (LGPD), fornecemos as informações detalhadas sobre o controlador responsável pelo tratamento dos seus dados.
    """

    privacy_tbl_controlador = """
          <table class="legal-table">
            <thead><tr><th>Campo</th><th>Informação</th></tr></thead>
            <tbody>
              <tr><td>Nome</td><td>WM TRADING LTDA</td></tr>
              <tr><td>CNPJ</td><td>06.194.675/0001-03</td></tr>
              <tr><td>Inscrição Estadual</td><td>082265933</td></tr>
              <tr><td>Endereço</td><td>Rua Engenheiro Guilherme José Monjardim Varejão, 275 – Salas 201 e 301 – Enseada do Suá – Vitória/ES – CEP 29.050-260</td></tr>
              <tr><td>E-mail</td><td>dpo@wmtrading.com.br</td></tr>
              <tr><td>Telefones</td><td>+55 27 99970-4899</td></tr>
              <tr><td>Nome completo</td><td>Wendel Brambati Ferreira</td></tr>
            </tbody>
          </table>
    """

    privacy_md_3 = """
## 6. Sobre o tratamento dos seus dados pessoais

Seus dados pessoais são coletados e utilizados para lhe proporcionar uma experiência completa, quando usufrui de nossos produtos e/ou serviços, através de nosso site, plataformas ou aplicativos.

### 6.1 Quais informações são coletadas sobre você?

**6.1.1** Podemos coletar os seguintes dados pessoais durante o seu cadastro ou no uso de produtos e/ou serviços da WM TRADING:

- a) Nome
- b) CPF e/ou RG
- c) Data de nascimento
- d) E-mail
- e) Número de telefone
- f) Endereço, código postal e país
- g) Nome de usuário e senha
- h) Dados biométricos
- i) Dados financeiros

### 6.2 Para qual finalidade utilizamos seus dados?

**6.2.1** As informações solicitadas aos titulares de dados são as necessárias para adquirir serviços e/ou produtos, receber informações, orçamentos e propostas e acessar as plataformas da WM TRADING, tendo por finalidade fornecer o desejado ao titular, em atendimento às obrigações legais e regulatórias, entre elas estão:

- a) Identificação cadastral do titular dos dados para fins de compra de produtos ou serviços da WM TRADING
- b) Identificação visual do titular dos dados para fins de emissão de Certificado Digital, seja presencial ou por meio de videoconferência
- c) Identificação profissional do titular dos dados para fins de preenchimento de oportunidades de trabalho, conforme legislação trabalhista
- d) Utilização dos cookies para aperfeiçoamento dos serviços do site
- e) E-mails são utilizados para comunicação de expiração/vencimento de produtos/serviços, contratos, negociações comerciais e demais comunicações dos processos de COMEX/IMPORTAÇÃO visando atendimento de nossas operações de negócio junto a clientes e fornecedores
- f) Plataformas online, e-mail, WhatsApp ou telefone poderão ser utilizados com a finalidade de sanar dúvidas, dar suporte ou auxiliar os titulares dos dados, sejam clientes, funcionários, fornecedores ou prestadores de serviço, em eventuais problemas relacionados às nossas operações de negócio

**6.2.2** Diferentes meios de comunicação poderão ser utilizados para:

- a) Comunicar os usuários/titulares de dados sobre mudanças na Política de Privacidade ou Termos de Uso dos sistemas da WM TRADING, quando necessário
- b) Manutenção de medidas de segurança, auditorias, investigações internas, apuração de denúncias, nos casos devidamente amparados por lei
- c) Contato com potenciais clientes, para oferecer os serviços da plataforma
- d) Divulgação de promoções dos produtos, serviços ou eventos da WM TRADING
- e) Para realizar a cobrança de valores devidos em contraprestação pelo uso dos nossos serviços
- f) Prover garantia da prevenção à fraude e à segurança
- g) Para manter seu cadastro atualizado para contato por telefone, correio eletrônico, SMS ou outros meios de comunicação

### 6.3 Coletamos dados de crianças e adolescentes?

**6.3.1** A WM TRADING não coleta dados de crianças ou adolescentes com menos de 16 (dezesseis) anos de forma intencional.

**6.3.2** Crianças menores de 16 (dezesseis) anos precisam obter o consentimento dos pais ou responsáveis antes de compartilhar dados com a WM TRADING.

**6.3.3** Aconselhamos aos pais e responsáveis que monitorem as crianças ou adolescentes menores de 16 (dezesseis) anos, para garantir que não compartilhem dados com a WM TRADING sem sua prévia autorização.

### 6.4 Como mantemos seus dados pessoais seguros?

**6.4.1** As informações pessoais coletadas são armazenadas com padrões rígidos de confidencialidade e segurança e nenhum documento, informação ou registro que se encontra sob guarda da WM TRADING é fornecido a terceiros, exceto se:

- a) Expressamente autorizado pelo titular do dado
- b) Mediante ordem ou decisão judicial
- c) Cumprimento de obrigação ou determinação legal

**6.4.2** A WM TRADING não comercializa dados pessoais dos titulares que estão sob sua guarda.

### 6.5 Por quanto tempo armazenamos seus dados?

**6.5.1** Armazenamos os seus dados durante o período necessário para cumprir os objetivos e finalidades para os quais eles foram coletados.

**6.5.2** Para dados pessoais de titulares de certificação digital, por no mínimo 7 (sete) anos, a partir da expiração ou revogação do Certificado Digital.

**6.5.3** Para demais informações, inclusive os arquivos de auditoria, deverão ser retidas por, no mínimo, 5 (cinco) anos ou pelo tempo necessário exigido por lei para preservação de direitos, controles de fraudes e segurança jurídica.

### 6.6 Relacionamento com terceiros

Essa Política de Privacidade e Uso de Dados Pessoais é aplicável à WM TRADING em complemento à Política de Segurança da Informação e outras políticas institucionais.

**6.6.1** Para o atendimento das finalidades elencadas no item 6.2 desta Política, os dados poderão ser compartilhados com as empresas do Grupo WM TRADING, bem como provedores de serviço e fornecedores, para satisfazer necessidades dos produtos e/ou serviços ora contratados, os quais serão considerados operadores.

## 7. Atualização da Política de Privacidade e Uso de Dados

**7.1** A WM TRADING se reserva ao direito de alterar essa Política sempre que necessário, visando fornecer ao titular de dados mais segurança e transparência. Sempre que houver alterações que ensejem novas autorizações, será publicada uma nova versão, sujeita a um novo consentimento.

## 8. Legislação aplicável

**8.1** Este documento é regido e deve ser interpretado de acordo com a legislação brasileira. Fica eleito o Foro da Comarca de Vitória, Estado do Espírito Santo, como competente para dirimir quaisquer questões porventura oriundas do presente documento, com expressa renúncia a qualquer outro, por mais privilegiado que seja.

## 9. Condições gerais

**9.1** A WM TRADING se reserva ao direito de notificar seus clientes de qualquer informação que afete a segurança dos produtos ou serviços fornecidos.

Se você tiver alguma pergunta sobre esta Política de Privacidade ou as práticas deste site, por gentileza entre em contato pelo e-mail **dpo@wmtrading.com.br**.
    """

    privacy_body = f"""
    <section class="page-section">
      <div class="container legal-container">
        <h1 class="legal-title">Política de Privacidade</h1>
        <p class="legal-version" style="color:var(--color-text-muted); font-size:14px; margin-bottom:28px;">Última atualização: {POLITICA_VIGENCIA}.</p>
        <div class="prose-wm">
          {markdown_to_html(privacy_md_1)}
          {privacy_tbl_cookies}
          {markdown_to_html(privacy_md_2)}
          {privacy_tbl_controlador}
          {markdown_to_html(privacy_md_3)}
        </div>
      </div>
    </section>
    """
    render_html_page(os.path.join(ROOT_DIR, "politica-de-privacidade.html"), "Política de Privacidade", "Política de Privacidade e Uso de Dados Pessoais da WM Trading.", privacy_body, head_tpl, header_tpl, footer_tpl)

    # 7. GENERATE BLOG POSTS & LISTING
    print("\nGenerating Blog...")
    blog_posts_files = glob.glob(os.path.join(CONTENT_DIR, "blog", "*.mdx"))
    posts_data = []
    
    # Compile each blog post page
    for file_path in blog_posts_files:
        basename = os.path.basename(file_path)
        print(f" - compiling blog post {basename}...")
        fm, body = parse_mdx(file_path)
        
        # Get elements
        title = fm.get("title", "Post sem título")
        slug = fm.get("slug", basename.replace(".mdx", ""))
        date_str = fm.get("date", "2024-01-01T00:00:00.000Z")
        author = fm.get("author", "WM Trading")
        excerpt = fm.get("excerpt", "")
        category = fm.get("category", "Geral")
        cover = fm.get("cover", "")
        
        # Format date for displaying
        display_date = date_str
        try:
            # Parse ISO date string
            # date_str: "2026-04-23T13:41:28.000Z"
            dt = datetime.strptime(date_str.split("T")[0], "%Y-%m-%d")
            display_date = dt.strftime("%d/%m/%Y")
        except Exception as ex:
            pass

        # Save post data for index listing
        posts_data.append({
            "title": title,
            "slug": slug,
            "date": date_str,
            "display_date": display_date,
            "author": author,
            "excerpt": excerpt,
            "category": category,
            "cover": cover
        })
        
        # Build Post Detail Page content
        cover_html = f'<div class="post-cover-wrap"><img src="{cover}" alt="{title}" class="post-cover" /></div>' if cover else ""
        
        post_detail_html = f"""
        <article class="blog-section">
          <div class="container">
            <header class="post-header">
              <div class="post-meta">
                <span class="post-meta__category">{category}</span>
                <span>•</span>
                <span>{display_date}</span>
                <span>•</span>
                <span>Por {author}</span>
              </div>
              <h1 class="post-title">{title}</h1>
              <a href="/blog/index.html" class="link-arrow" style="margin-top:10px;">← Voltar ao Blog</a>
            </header>
            
            {cover_html}
            
            <div class="post-content-container">
              <div class="prose-wm">
                {markdown_to_html(body)}
              </div>
              <div style="margin-top: 60px; padding-top: 30px; border-top: 1px solid #efefef;">
                <a href="/blog/index.html" class="link-arrow">← Voltar ao Blog</a>
              </div>
            </div>
          </div>
        </article>
        """
        
        post_out_path = os.path.join(BLOG_OUT_DIR, f"{slug}.html")
        # Posts em ingles (frontmatter lang: "en", ou originalUrl /en/) declaram o idioma correto
        post_lang = fm.get("lang") or ("en" if "/en/" in fm.get("originalUrl", "") else "pt-BR")
        post_jsonld = {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": title,
            "datePublished": date_str,
            "author": {"@type": "Person", "name": author},
            "publisher": {"@type": "Organization", "name": "WM Trading", "logo": {"@type": "ImageObject", "url": SITE_URL + DEFAULT_OG_IMAGE}},
            "image": (SITE_URL + cover) if cover else (SITE_URL + DEFAULT_OG_IMAGE),
            "mainEntityOfPage": f"{SITE_URL}/blog/{slug}.html",
        }
        render_html_page(post_out_path, title, excerpt[:155], post_detail_html, head_tpl, header_tpl, footer_tpl,
                         lang=post_lang, og_type="article", og_image=cover or None, jsonld=post_jsonld)

    # Sort listing data by date descending, desempatando por slug.
    # Sem o desempate a ordem vinha do glob.glob() (ordem do sistema de
    # arquivos), e posts com data identica trocavam de lugar entre maquinas —
    # mudando o post em destaque do blog sozinho, a cada regeracao.
    # Dois sorts encadeados: o sort do Python e estavel, entao o resultado e
    # data DESC com slug ASC (ordenar pela tupla inverteria o slug tambem).
    posts_data.sort(key=lambda x: x["slug"])
    posts_data.sort(key=lambda x: x["date"], reverse=True)
    
    # 8. GENERATE BLOG LISTING PAGE (blog/index.html)
    print("Generating Blog Listing page (blog/index.html)...")
    
    # Get all unique categories for filtering
    categories_set = set(p["category"] for p in posts_data if p.get("category"))
    categories_list = sorted(list(categories_set))
    
    filter_buttons_html = '<button class="filter-btn active" data-filter="all">Todos</button>\n'
    for cat in categories_list:
        filter_buttons_html += f'<button class="filter-btn" data-filter="{cat}">{cat}</button>\n'
        
    cards_grid_html = ""
    for p in posts_data:
        cover_img_html = f'<img src="{p["cover"]}" alt="{p["title"]}" class="blog-card__cover" loading="lazy" />' if p["cover"] else ''
        cards_grid_html += f"""
        <div class="blog-card-item" data-category="{p["category"]}" style="display:flex;">
          <a href="/blog/{p["slug"]}.html" class="blog-card">
            <div class="blog-card__cover-wrap">
              {cover_img_html}
            </div>
            <div class="blog-card__content">
              <div class="blog-card__meta">
                <span class="blog-card__category">{p["category"]}</span>
                <span>{p["display_date"]}</span>
              </div>
              <h3 class="blog-card__title">{p["title"]}</h3>
              <p class="blog-card__excerpt">{p["excerpt"]}</p>
              <span class="blog-card__link">Ler artigo →</span>
            </div>
          </a>
        </div>
        """
        
    blog_listing_html = """
    <section class="page-section" style="padding-bottom:20px;">
      <div class="container" style="text-align:center;">
        <p class="dynamic-hero__eyebrow" style="margin-bottom:8px;">Blog</p>
        <h1 class="t-display" style="font-weight:var(--fw-semibold); font-size:var(--fs-2xl); line-height:1.2; margin-bottom:12px;">Blog da WM Trading</h1>
        <p class="intro-text" style="color:var(--color-text-muted); max-width:600px; margin: 0 auto 30px auto;">Acompanhe os principais insights sobre comércio exterior, tributação, logística e tendências de mercado.</p>
        
        <div class="blog-search-wrap">
          <svg class="blog-search-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <input type="text" id="blog-search" placeholder="Pesquisar artigos por palavra-chave..." class="blog-search-input" />
        </div>
        
        <div class="blog-filters">
          {filter_buttons_html}
        </div>
      </div>
    </section>
    
    <section class="blog-section" style="padding-top:0;">
      <div class="container">
        <div class="blog-grid" id="blog-posts-grid">
          {cards_grid_html}
        </div>
        
        <div class="blog-pagination-container">
          <button id="load-more-btn" class="btn btn-lg">Carregar mais artigos</button>
        </div>
      </div>
    </section>
    
    <script>
      document.addEventListener('DOMContentLoaded', function() {
        const searchInput = document.getElementById('blog-search');
        const filterButtons = document.querySelectorAll('.filter-btn');
        const cards = document.querySelectorAll('.blog-card-item');
        const loadMoreBtn = document.getElementById('load-more-btn');
        let visibleCount = 12;

        function updateFilter() {
          const activeFilter = document.querySelector('.filter-btn.active').dataset.filter;
          const searchText = searchInput.value.toLowerCase().trim();
          let matchCount = 0;

          cards.forEach(card => {
            const category = card.dataset.category || '';
            const title = card.querySelector('.blog-card__title').textContent.toLowerCase();
            const excerpt = card.querySelector('.blog-card__excerpt').textContent.toLowerCase();
            
            const matchesFilter = (activeFilter === 'all' || category.toLowerCase() === activeFilter.toLowerCase());
            const matchesSearch = (!searchText || title.includes(searchText) || excerpt.includes(searchText));

            if (matchesFilter && matchesSearch) {
              card.classList.remove('filtered-out');
              matchCount++;
              if (matchCount <= visibleCount) {
                card.style.display = 'flex';
              } else {
                card.style.display = 'none';
              }
            } else {
              card.classList.add('filtered-out');
              card.style.display = 'none';
            }
          });

          if (loadMoreBtn) {
            const totalMatches = document.querySelectorAll('.blog-card-item:not(.filtered-out)').length;
            if (visibleCount >= totalMatches) {
              loadMoreBtn.style.display = 'none';
            } else {
              loadMoreBtn.style.display = 'inline-block';
            }
          }
        }

        filterButtons.forEach(btn => {
          btn.addEventListener('click', () => {
            filterButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            visibleCount = 12;
            updateFilter();
          });
        });

        searchInput.addEventListener('input', () => {
          visibleCount = 12;
          updateFilter();
        });

        if (loadMoreBtn) {
          loadMoreBtn.addEventListener('click', () => {
            visibleCount += 12;
            updateFilter();
          });
        }

        updateFilter();
      });
    </script>
    """.replace("{filter_buttons_html}", filter_buttons_html).replace("{cards_grid_html}", cards_grid_html)
    
    render_html_page(os.path.join(ROOT_DIR, "blog", "index.html"), "Blog da WM Trading", "Confira as notícias e artigos da WM Trading.", blog_listing_html, head_tpl, header_tpl, footer_tpl)

    # 9. SITEMAP.XML — todas as paginas .html do site, apontando para o dominio final
    print("\nGenerating sitemap.xml...")
    skip_dirs = {".git", ".claude", ".agents", ".cursor", ".windsurf", "node_modules",
                 "scripts", "content", "docs", "brand", "api", "js", "css", "images",
                 "wp-content", "mapa-brasil"}
    sitemap_pages = []
    for walk_root, walk_dirs, walk_files in os.walk(ROOT_DIR):
        walk_dirs[:] = [d for d in walk_dirs if d not in skip_dirs and not d.startswith(".")]
        for fn in walk_files:
            if fn.endswith(".html"):
                rel = os.path.relpath(os.path.join(walk_root, fn), ROOT_DIR).replace(os.sep, "/")
                mtime = datetime.fromtimestamp(os.path.getmtime(os.path.join(walk_root, fn)))
                sitemap_pages.append((rel, mtime.strftime("%Y-%m-%d")))
    sitemap_pages.sort()
    entries = []
    for rel, lastmod in sitemap_pages:
        if rel == "index.html":
            loc = SITE_URL + "/"
        elif rel.endswith("/index.html"):
            # index.html de subpasta entra como URL do diretório sem barra final
            # (/segmentos, /blog) — alinhado ao trailingSlash:false da Vercel
            loc = f"{SITE_URL}/{rel[:-len('/index.html')]}"
        else:
            loc = f"{SITE_URL}/{rel}"
        entries.append(f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{lastmod}</lastmod>\n  </url>")
    sitemap_xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                   '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                   + "\n".join(entries) + "\n</urlset>\n")
    escrever_se_mudou(os.path.join(ROOT_DIR, "sitemap.xml"), sitemap_xml)
    print(f" - sitemap.xml com {len(sitemap_pages)} paginas")

    print("\n[OK] Static site pages successfully generated!")

if __name__ == "__main__":
    main()
