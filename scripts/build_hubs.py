"""Gera páginas-hub editoriais a partir de content/hubs/*.json.

As hubs são páginas de orientação e navegação, não listas automáticas de posts.
Elas usam o mesmo cabeçalho, rodapé, SEO e JSON-LD das páginas geradas do site.
"""
import json
import os
from html import escape

from build_pages import ROOT_DIR, load_template_elements, render_html_page


HUBS_DIR = os.path.join(ROOT_DIR, "content", "hubs")


def link_card(card):
    return f'''<a class="guide-card" href="{escape(card['url'])}">
      <span class="guide-card__tag">{escape(card.get('category', card.get('label', 'Conteúdo WM')))}</span>
      <h3>{escape(card['title'])}</h3>
      <p>{escape(card['description'])}</p>
      <span class="link-arrow">Leia o conteúdo <span aria-hidden="true">→</span></span>
    </a>'''


def faq_schema(faqs):
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [{
            "@type": "Question",
            "name": item["question"],
            "acceptedAnswer": {"@type": "Answer", "text": item["answer"]},
        } for item in faqs],
    }


def render_hub(hub, templates):
    head_tpl, header_tpl, footer_tpl = templates
    slug = hub["slug"]
    output = os.path.join(ROOT_DIR, "guias", slug, "index.html")
    os.makedirs(os.path.dirname(output), exist_ok=True)

    primary_links = hub.get("primary_links", hub.get("modalities", []))
    primary_label = hub.get("primary_label", "Modalidade")
    primary_cards = "".join(link_card({**item, "category": item.get("category", primary_label)}) for item in primary_links)
    articles = "".join(link_card(item) for item in hub["articles"])
    checklist = "".join(f"<li>{escape(item)}</li>" for item in hub["considerations"])
    faqs = "".join(
        f"<details><summary>{escape(item['question'])}</summary><p>{escape(item['answer'])}</p></details>"
        for item in hub["faqs"]
    )
    guide = hub.get("feature") or hub["guide"]
    feature_heading = hub.get("feature_heading", "Um guia completo para comparar as modalidades")
    primary_heading = hub.get("primary_heading", "Conheça as duas modalidades de importação indireta")
    primary_intro = hub.get("primary_intro", "Cada estrutura exige análise contratual, documental, tributária e operacional. Entenda como a WM atua em cada uma.")
    considerations_heading = hub.get("considerations_heading", "O que a WM avalia antes de definir a modalidade")
    articles_heading = hub.get("articles_heading", "Aprofunde pontos importantes da operação")
    faq_heading = hub.get("faq_heading", "Perguntas frequentes")
    body = f'''<article class="guide-hub">
  <header class="guide-hero">
    <div class="container">
      <p class="guide-hero__eyebrow">{escape(hub['eyebrow'])}</p>
      <h1>{escape(hub['hero'])}</h1>
      <p class="guide-hero__lead">{escape(hub['intro'])}</p>
    </div>
  </header>

  <section class="guide-section guide-section--soft" aria-labelledby="guia-principal">
    <div class="container">
      <p class="guide-section__eyebrow">COMECE POR AQUI</p>
      <h2 id="guia-principal">{escape(feature_heading)}</h2>
      <div class="guide-feature">
        <div>
          <span class="guide-feature__label">{escape(guide['label'])}</span>
          <h3>{escape(guide['title'])}</h3>
          <p>{escape(guide['description'])}</p>
        </div>
        <div class="guide-feature__action"><a class="btn btn-lg" href="{escape(guide['url'])}">Ler guia completo</a></div>
      </div>
    </div>
  </section>

  <section class="guide-section" aria-labelledby="modalidades">
    <div class="container">
      <p class="guide-section__eyebrow">SOLUÇÕES WM</p>
      <h2 id="modalidades">{escape(primary_heading)}</h2>
      <p class="guide-section__intro">{escape(primary_intro)}</p>
      <div class="guide-card-grid">{primary_cards}</div>
    </div>
  </section>

  <section class="guide-section guide-section--soft" aria-labelledby="avaliacao">
    <div class="container">
      <p class="guide-section__eyebrow">ESTUDO DA OPERAÇÃO</p>
      <h2 id="avaliacao">{escape(considerations_heading)}</h2>
      <ul class="guide-checklist">{checklist}</ul>
    </div>
  </section>

  <section class="guide-section" aria-labelledby="aprofundar">
    <div class="container">
      <p class="guide-section__eyebrow">CONTEÚDOS ESSENCIAIS</p>
      <h2 id="aprofundar">{escape(articles_heading)}</h2>
      <div class="guide-card-grid guide-article-grid">{articles}</div>
    </div>
  </section>

  <section class="guide-section guide-section--soft" aria-labelledby="perguntas">
    <div class="container">
      <p class="guide-section__eyebrow">PERGUNTAS FREQUENTES</p>
      <h2 id="perguntas">{escape(faq_heading)}</h2>
      <div class="guide-faq">{faqs}</div>
    </div>
  </section>

  <section class="guide-cta" aria-labelledby="contato">
    <div class="container">
      <h2 id="contato">{escape(hub['cta_title'])}</h2>
      <p>{escape(hub['cta_text'])}</p>
      <a class="btn btn-white btn-lg guide-cta__button" href="{escape(hub['cta_url'])}">Cadastre-se aqui</a>
    </div>
  </section>
</article>'''
    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Início", "item": "https://www.wmtrading.com.br/"},
            {"@type": "ListItem", "position": 2, "name": "Blog", "item": "https://www.wmtrading.com.br/blog/"},
            {"@type": "ListItem", "position": 3, "name": hub["title"]},
        ],
    }
    collection = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": hub["title"],
        "description": hub["description"],
    }
    render_html_page(
        output, hub["title"], hub["description"], body, head_tpl, header_tpl, footer_tpl,
        jsonld=[collection, breadcrumb, faq_schema(hub["faqs"])],
        extra_head='<link rel="stylesheet" href="/css/import-guides.css" />',
    )
    print(f" - compilado /guias/{slug}/")


def main():
    templates = load_template_elements()
    for filename in sorted(os.listdir(HUBS_DIR)):
        if filename.endswith(".json"):
            with open(os.path.join(HUBS_DIR, filename), encoding="utf-8") as file:
                render_hub(json.load(file), templates)


if __name__ == "__main__":
    main()
