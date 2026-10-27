# -*- coding: utf-8 -*-
"""
Gera as duas versoes do convite da WM Party 26 a partir do pacote do designer.

O pacote vem como um HTML unico de 1,2 MB que carrega React, Babel e o proprio
codigo da animacao de dentro de si — tudo num manifesto base64+gzip embutido.
Nada vem de fora: medido no navegador, zero requisicao externa. Por isso o link
de confirmacao nao esta em texto puro no arquivo; ele vive comprimido dentro
desse manifesto, e trocar exige abrir, editar e fechar de novo.

Duas mudancas, so:
  1. RSVP_URL  -> o formulario do publico certo (colaboradores ou clientes).
  2. <base>    -> faz "assets/..." resolver sempre em /wm-party-26/assets/,
                  qualquer que seja o endereco da pagina. Sem isso, uma pagina
                  servida em /wm-party-26/colaboradores/ procuraria os arquivos
                  em /wm-party-26/colaboradores/assets/ — e as duas versoes
                  precisariam de uma copia dos 10 MB cada.

Uso: python3 -I gera_convites.py <index.html original> <pasta de saida>
"""
import base64
import gzip
import json
import re
import sys
import zlib

MARCA_RSVP = "const RSVP_URL = 'https://www.wmtrading.com.br';"

# O fundo da revelacao veio como PNG de 2251x4000 com 4,2 MB — degrade suave, o
# pior caso possivel para PNG. Em WebP com o mesmo canal alfa sao 81 KB: menos de
# 2% do peso, com diferenca media de 0,6 em 255 por canal de cor e alfa identico.
# Num convite que as pessoas abrem no celular, isso e um terco do download.
TROCA_FUNDO = ("assets/bg-revelacao.png", "assets/bg-revelacao.webp")

PUBLICOS = {
    "colaboradores": "https://forms.monday.com/forms/5c61c4a157846e8cecd3dbb20f69875c?r=use1",
    "clientes": "https://forms.monday.com/forms/0cf7000d4faa94ffe2658435aa79908b?r=use1",
}

BASE_HREF = '<base href="/wm-party-26/">'


def descomprime(entrada):
    bruto = base64.b64decode(entrada["data"])
    if not entrada.get("compressed"):
        return bruto
    for tentativa in (gzip.decompress, zlib.decompress, lambda b: zlib.decompress(b, -15)):
        try:
            return tentativa(bruto)
        except Exception:
            pass
    raise SystemExit("nao consegui descomprimir uma entrada do manifesto")


def comprime(entrada, dados):
    # mtime=0 para o arquivo sair igual a cada execucao.
    bruto = gzip.compress(dados, mtime=0) if entrada.get("compressed") else dados
    entrada["data"] = base64.b64encode(bruto).decode("ascii")


def gera(html, publico, url_form):
    manifesto_m = re.search(r'(<script type="__bundler/manifest"[^>]*>)(.*?)(</script>)', html, re.S)
    manifesto = json.loads(manifesto_m.group(2).strip())

    trocas = 0
    for entrada in manifesto.values():
        if "javascript" not in entrada.get("mime", ""):
            continue
        codigo = descomprime(entrada).decode("utf-8")
        if MARCA_RSVP not in codigo:
            continue
        codigo = codigo.replace(MARCA_RSVP, f"const RSVP_URL = '{url_form}';")
        if TROCA_FUNDO[0] not in codigo:
            raise SystemExit(f"nao achei a referencia a {TROCA_FUNDO[0]} para trocar pelo WebP")
        codigo = codigo.replace(*TROCA_FUNDO)
        comprime(entrada, codigo.encode("utf-8"))
        trocas += 1
    if trocas != 1:
        raise SystemExit(f"esperava trocar o RSVP_URL em 1 arquivo, troquei em {trocas}")

    novo = json.dumps(manifesto, ensure_ascii=False, separators=(",", ":"))
    html = html[:manifesto_m.start(2)] + novo + html[manifesto_m.end(2):]

    # O documento final e montado a partir do bloco "template"; o <base> tem que
    # entrar la, nao no HTML de fora, senao o navegador nao o enxerga.
    tpl_m = re.search(r'(<script type="__bundler/template"[^>]*>)(.*?)(</script>)', html, re.S)
    template = json.loads(tpl_m.group(2).strip())
    if BASE_HREF not in template:
        alvo = '<meta charset="utf-8">'
        if alvo not in template:
            raise SystemExit("nao achei o <meta charset> do template para ancorar o <base>")
        template = template.replace(alvo, alvo + "\n" + BASE_HREF, 1)
    html = html[:tpl_m.start(2)] + _como_json(template) + html[tpl_m.end(2):]
    return html


def _como_json(texto):
    """Serializa escapando a barra de "</script>", como o pacote original faz.

    O template e um documento HTML inteiro guardado dentro de um <script>. Se o
    "</script>" dele sair literal, o navegador fecha o bloco ali e o resto do
    documento vira texto solto na pagina — a primeira versao que gerei tinha
    8 "</script>" contra os 5 do original, e teria ido ao ar quebrada.
    """
    return json.dumps(texto, ensure_ascii=False).replace("</", "<\\u002F")


def main():
    origem, saida = sys.argv[1], sys.argv[2]
    with open(origem, encoding="utf-8") as f:
        original = f.read()
    for publico, url_form in PUBLICOS.items():
        destino = f"{saida}/{publico}.html"
        with open(destino, "w", encoding="utf-8") as f:
            f.write(gera(original, publico, url_form))
        print(f"  {destino}  ({url_form.split('/forms/')[1][:12]}...)")


if __name__ == "__main__":
    main()
