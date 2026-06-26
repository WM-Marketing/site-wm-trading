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

# Define workspace directories
ROOT_DIR = "d:/projects/site_wm/site-wm-trading"
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

    # Extract head content (excluding title and description)
    head_start = html.find("<head>")
    head_end = html.find("</head>")
    head_content = html[head_start + 6:head_end]
    head_content = re.sub(r"<title>.*?</title>", "", head_content)
    head_content = re.sub(r'<meta\s+name="description"\s+content=".*?"\s*/?>', "", head_content)
    
    # Inject dynamic-pages styles and contact-form script
    head_content += '\n  <link rel="stylesheet" href="/css/dynamic-pages.css" />'
    head_content += '\n  <script src="/js/contact-form.js" defer></script>'

    # Extract header (including loader)
    loader_start = html.find('<div id="page-loader"')
    header_end = html.find("</header>") + 9
    header_content = html[loader_start:header_end]

    # Update header links
    header_content = re.sub(
        r'<a\s+href="segmentos-aeronaves\.html"\s+role="menuitem">',
        r'<a href="/segmentos-aeronaves.html" role="menuitem">',
        header_content
    )
    # Add actual generated paths for other segments in the menu
    header_content = re.sub(
        r'<a\s+href="#"\s+role="menuitem">🚗 Autopeças</a>',
        r'<a href="/segmentos/autopecas.html" role="menuitem">🚗 Autopeças</a>',
        header_content
    )
    header_content = re.sub(
        r'<a\s+href="#"\s+role="menuitem">⚙ Aço e Metais</a>',
        r'<a href="/segmentos/aco.html" role="menuitem">⚙ Aço e Metais</a>',
        header_content
    )
    header_content = re.sub(
        r'<a\s+href="#"\s+role="menuitem">☀ Energia Solar</a>',
        r'<a href="/segmentos/equipamentos-fotovoltaicos.html" role="menuitem">☀ Energia Solar</a>',
        header_content
    )
    header_content = re.sub(
        r'<a\s+href="#"\s+role="menuitem">🏭 Máquinas e Equipamentos</a>',
        r'<a href="/segmentos/maquinas.html" role="menuitem">🏭 Máquinas e Equipamentos</a>',
        header_content
    )
    
    # Extract footer
    footer_comment = "<!-- ══════════════════════════════════════\n     FOOTER — FAIXA 1: Links + CTA\n══════════════════════════════════════ -->"
    footer_start = html.find(footer_comment)
    if footer_start == -1:
        footer_start = html.find('<div class="footer-links">')
    footer_content = html[footer_start:]

    # Make all assets paths absolute
    head_content = make_paths_absolute(head_content)
    header_content = make_paths_absolute(header_content)
    footer_content = make_paths_absolute(footer_content)

    return head_content, header_content, footer_content

def make_paths_absolute(content):
    """Prefixes relative css, js, images, and HTML paths with '/' for subdirectories compatibility."""
    content = re.sub(r'href="css/', r'href="/css/', content)
    content = re.sub(r'src="js/', r'src="/js/', content)
    content = re.sub(r'src="images/', r'src="/images/', content)
    content = re.sub(r'src="mapa-brasil/', r'src="/mapa-brasil/', content)
    content = re.sub(r'href="about\.html"', r'href="/about.html"', content)
    content = re.sub(r'href="carreiras\.html"', r'href="/carreiras.html"', content)
    content = re.sub(r'href="fale-conosco\.html"', r'href="/fale-conosco.html"', content)
    content = re.sub(r'href="solucoes-wm\.html"', r'href="/solucoes-wm.html"', content)
    content = re.sub(r'href="index\.html"', r'href="/index.html"', content)
    content = re.sub(r'href="segmentos-aeronaves\.html"', r'href="/segmentos-aeronaves.html"', content)
    content = re.sub(r'href="blog/index\.html"', r'href="/blog/index.html"', content)
    return content

def render_html_page(output_path, title, description, content_body, head_tpl, header_tpl, footer_tpl):
    """Wraps page content in a fully styled, absolute-path templates block and saves it."""
    # Build complete HTML page
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>WM Trading — {title}</title>
  <meta name="description" content="{description}" />
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
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

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
    # Links
    html = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', html)
    # Emphasis
    html = re.sub(r'_(.*?)_', r'<em>\1</em>', html)
    
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
          <input name="telefone" type="tel" required placeholder="Número Telefone * — (DDD) 99999-0000" pattern="[0-9()#&+*\\-=\\.\\s]+" class="input-wm" />
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
            <span>Estou de acordo com a <a href="/politica-de-privacidade.html" class="text-primary underline">política de privacidade</a>.</span>
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
            <span>Estou de acordo com a <a href="/politica-de-privacidade.html" class="text-primary underline">política de privacidade</a>.</span>
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
        render_html_page(output_path, f"Importação {a['maker']} {a['name']}", a["heroTitle"], body_content, head_tpl, header_tpl, footer_tpl)

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
        # Sort episodes by date descending
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
    cookies_md = """
## O que são cookies?

Cookies são pequenos arquivos transferidos para o seu navegador ou dispositivo que nos permitem reconhecer o seu acesso. Eles facilitam a personalização da sua experiência, adequando a apresentação do site às suas preferências.

## Por que usamos cookies?

A WM Trading utiliza cookies para identificar seus acessos aos serviços oferecidos. Essas tecnologias nos ajudam a exibir as informações corretas e a personalizar sua experiência de acordo com as suas configurações. Dependendo das suas preferências, os cookies também podem direcionar anúncios alinhados aos seus interesses.

## Tipos de cookies utilizados

- **Essenciais:** obrigatórios e necessários para a navegação no site. Não coletam informações para fins de marketing e ficam ativos apenas enquanto a janela do navegador permanece aberta.
- **Publicitários:** definidos pelos parceiros publicitários, armazenam a origem das campanhas que levaram o usuário ao site. Têm período de armazenamento de 30 dias e podem ser desativados.

## Como remover ou bloquear cookies?

Você pode gerenciar os cookies pelas configurações do seu navegador. Lembre-se de que desativar cookies pode comprometer o funcionamento adequado de algumas funcionalidades do site. A WM Trading não é responsável pelos cookies de terceiros instalados durante interações externas.

## Alterações nesta política

A política pode sofrer atualizações periódicas. Mudanças relevantes exigirão um novo consentimento dos usuários.
    """
    cookies_body = f"""
    <section class="page-section">
      <div class="container legal-container">
        <h1 class="legal-title">Política de Cookies</h1>
        <div class="prose-wm">
          {markdown_to_html(cookies_md)}
        </div>
      </div>
    </section>
    """
    render_html_page(os.path.join(ROOT_DIR, "politica-de-cookies.html"), "Política de Cookies", "Entenda como a WM Trading utiliza cookies.", cookies_body, head_tpl, header_tpl, footer_tpl)

    # 6H. PRIVACY POLICY
    print(" - compiling politica-de-privacidade.html...")
    privacy_md = """
## 1. Introdução

A Política de Privacidade e Uso de Dados Pessoais da WM Trading visa demonstrar transparência no compromisso com a proteção de dados fornecidos pelos titulares. A empresa não divulga informações pessoais a terceiros sem autorização, exceto em casos de determinação legal ou medida judicial.

Esta política abrange o tratamento de informações coletadas diretamente no site, área do cliente, fichas cadastrais, negociações comerciais e integrações de dados, armazenadas em bases eletrônicas. A aceitação ocorre ao acessar ou utilizar os serviços, indicando concordância com o tratamento conforme a Lei Geral de Proteção de Dados Pessoais (LGPD) nº 13.709/2018.

## 2. Direitos dos usuários sobre os dados pessoais

- **Revogação:** os titulares podem solicitar a revogação das permissões de uso de dados, uma vez expirado o prazo legal de tratamento.
- **Divulgação:** a WM Trading não divulga os dados pessoais dos titulares, exceto por determinação legal ou a pedido do próprio titular.
- **Retificação:** os titulares podem solicitar a retificação de dados, exceto informações em Certificados Digitais, que não podem ser alteradas após a emissão.
- **Exclusão:** direito à exclusão definitiva dos dados ao término da relação, ressalvadas as hipóteses de guarda obrigatória previstas na LGPD.
- **Portabilidade:** solicitações são analisadas caso a caso mediante contato com dpo@wmtrading.com.br.

## 3. Responsabilidades dos titulares

Os titulares têm a obrigação de assegurar que os dados fornecidos à WM Trading sejam precisos, completos e atualizados.

## 4. Tratamento dos seus dados pessoais

Podem ser coletados, durante o cadastro ou uso de produtos e serviços: nome, CPF e/ou RG, data de nascimento, e-mail, telefone, endereço, usuário/senha, dados biométricos e dados financeiros. As informações são necessárias para adquirir serviços e produtos, receber orçamentos e propostas e acessar as plataformas da WM Trading, em atendimento a obrigações legais e regulatórias.

A WM Trading não coleta dados de crianças ou adolescentes menores de 16 anos de forma intencional, e não comercializa os dados pessoais sob sua guarda. As informações são armazenadas com padrões rígidos de confidencialidade e segurança, pelo período necessário ao cumprimento das finalidades (no mínimo 7 anos para titulares com certificação digital; no mínimo 5 anos para demais arquivos de auditoria, ou pelo tempo exigido por lei).
    """
    privacy_body = f"""
    <section class="page-section">
      <div class="container legal-container">
        <h1 class="legal-title">Política de Privacidade</h1>
        <div class="prose-wm">
          {markdown_to_html(privacy_md)}
          
          <h2>5. Controlador de dados</h2>
          <table class="legal-table">
            <thead>
              <tr><th>Campo</th><th>Informação</th></tr>
            </thead>
            <tbody>
              <tr><td>Nome</td><td>WM Comercial Atacadista LTDA</td></tr>
              <tr><td>CNPJ</td><td>06.194.675/0001-03</td></tr>
              <tr><td>Endereço</td><td>Rua Engenheiro Guilherme José Monjardim Varejão, 275 – Enseada do Suá – Vitória/ES – CEP 29050-260</td></tr>
              <tr><td>E-mail (DPO)</td><td>dpo@wmtrading.com.br</td></tr>
            </tbody>
          </table>
          
          <h2>6. Legislação aplicável</h2>
          <p>Este documento é regido pela legislação brasileira. Fica eleito o Foro da Comarca de Vitória/ES como competente para dirimir questões oriundas deste documento.</p>
          <p>Para dúvidas sobre esta Política de Privacidade, entre em contato pelo e-mail dpo@wmtrading.com.br.</p>
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
        render_html_page(post_out_path, title, excerpt[:155], post_detail_html, head_tpl, header_tpl, footer_tpl)

    # Sort listing data by date descending
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

    print("\n[OK] Static site pages successfully generated!")

if __name__ == "__main__":
    main()
