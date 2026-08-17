# -*- coding: utf-8 -*-
"""Avisa o IndexNow das URLs do site — usar NO DIA DA VIRADA, depois do DNS.

O IndexNow alimenta o indice do Bing, que por sua vez alimenta o ChatGPT e o
Copilot. Sem ele, o lado das IAs leva semanas para perceber a mudanca; com ele,
minutos. Nao depende de conta no Bing Webmaster Tools — basta a chave estar
publicada na raiz do site.

Uso:
    python scripts/avisar_indexnow.py --teste     # confere tudo, nao envia
    python scripts/avisar_indexnow.py             # envia de verdade

Rodar SO depois de:
  1. o DNS ja apontar para a Vercel;
  2. o robots.txt ja estar liberado.
Avisar antes disso manda o Bing bater num site que ainda responde Disallow.
"""
import argparse
import json
import os
import re
import sys
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOST = "www.wmtrading.com.br"
ENDPOINT = "https://api.indexnow.org/indexnow"
LIMITE = 10000  # maximo de URLs por envio


def achar_chave():
    """A chave e um .txt na raiz cujo nome, sem extensao, e o proprio conteudo."""
    for nome in os.listdir(RAIZ):
        if not nome.endswith(".txt"):
            continue
        caminho = os.path.join(RAIZ, nome)
        try:
            with open(caminho, encoding="ascii") as f:
                conteudo = f.read().strip()
        except (UnicodeDecodeError, OSError):
            continue
        if conteudo and nome[:-4] == conteudo and re.fullmatch(r"[0-9a-fA-F]{8,128}", conteudo):
            return conteudo, nome
    return None, None


def urls_do_sitemap():
    with open(os.path.join(RAIZ, "sitemap.xml"), encoding="utf-8") as f:
        return re.findall(r"<loc>\s*(.*?)\s*</loc>", f.read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--teste", action="store_true",
                    help="confere tudo e mostra o que seria enviado, sem enviar")
    args = ap.parse_args()

    chave, arquivo = achar_chave()
    if not chave:
        sys.exit("ERRO: chave do IndexNow nao encontrada na raiz do repo.")

    urls = urls_do_sitemap()
    if not urls:
        sys.exit("ERRO: sitemap.xml sem nenhuma URL.")

    fora = [u for u in urls if HOST not in u]
    if fora:
        sys.exit(f"ERRO: {len(fora)} URL(s) do sitemap nao sao de {HOST}. Ex.: {fora[0]}")

    print(f"chave    : {chave}  (servida em https://{HOST}/{arquivo})")
    print(f"URLs     : {len(urls)}")
    print(f"exemplos : {urls[0]}")
    print(f"           {urls[len(urls) // 2]}")

    if len(urls) > LIMITE:
        sys.exit(f"ERRO: {len(urls)} URLs passa do limite de {LIMITE} por envio.")

    corpo = {
        "host": HOST,
        "key": chave,
        "keyLocation": f"https://{HOST}/{arquivo}",
        "urlList": urls,
    }

    if args.teste:
        print("\n[teste] nada foi enviado.")
        print("Antes de enviar de verdade, confira que estas duas coisas ja valem:")
        print(f"  1. https://{HOST}/{arquivo} responde 200 com o texto da chave")
        print(f"  2. https://{HOST}/robots.txt esta liberado (sem 'Disallow: /')")
        return

    dados = json.dumps(corpo).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT, data=dados,
        headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            print(f"\nHTTP {r.status} — {len(urls)} URLs enviadas ao IndexNow")
            print("200/202 = aceito. O Bing processa em minutos.")
    except urllib.error.HTTPError as e:
        print(f"\nHTTP {e.code}: {e.read().decode('utf-8', 'replace')[:300]}")
        print("403 costuma ser chave que ainda nao esta acessivel na raiz do site.")
        sys.exit(1)


if __name__ == "__main__":
    main()
