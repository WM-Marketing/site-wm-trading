# -*- coding: utf-8 -*-
"""
Gera as duas versoes do convite da WM Party 26 a partir do pacote do designer.

O pacote vem como um HTML unico de 1,2 MB que carrega React, Babel e o proprio
codigo da animacao de dentro de si — tudo num manifesto base64+gzip embutido.
Nada vem de fora: medido no navegador, zero requisicao externa. Por isso o link
de confirmacao nao esta em texto puro no arquivo; ele vive comprimido dentro
desse manifesto, e trocar exige abrir, editar e fechar de novo.

Mudancas:
  1. RSVP_URL  -> o formulario do publico certo (colaboradores ou clientes).
  2. <base>    -> faz "assets/..." resolver sempre em /wm-party-26/assets/,
                  qualquer que seja o endereco da pagina. Sem isso, uma pagina
                  servida em /wm-party-26/colaboradores/ procuraria os arquivos
                  em /wm-party-26/colaboradores/assets/ — e as duas versoes
                  precisariam de uma copia dos 10 MB cada.
  3. COMPILA O JSX AQUI e tira o Babel da pagina. O carregador decide pelo
     sufixo do modulo: /\.(jsx|tsx)/ carrega o Babel e compila no aparelho;
     qualquer outra coisa roda o codigo direto. Entregue como veio, a pagina
     baixava 3 MB de compilador (90% de todo o JavaScript dela) e compilava a
     animacao no celular a cada abertura. Medido numa gravacao de tela de um
     iPhone: 8 segundos de tela em branco ate o envelope aparecer.
     A compilacao usa o PROPRIO Babel do pacote (7.29.0) com os mesmos presets
     do carregador, entao o resultado e o mesmo que o aparelho produziria.

Uso: python3 -I gera_convites.py <index.html original> <pasta de saida>
"""
import base64
import gzip
import subprocess
import tempfile
import json
import os
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

# O compilador que vem no pacote e os dois modulos em JSX que ele compilaria no
# aparelho. O carregador referencia cada modulo como "<uuid>#/<arquivo>".
UUID_BABEL = "ff7bcba6-4f23-460b-bd84-10070ca16387"
# Versao "leve": desliga as camadas que o celular repinta a cada quadro. Serve
# para o proprio aparelho do usuario dizer se o custo esta no desenho ou na
# animacao em si — nao da para medir isso num Mac, onde sobra GPU.
#   1. O grao: retangulo de tela cheia com feTurbulence (ruido pixel a pixel) e
#      mix-blend-mode overlay por cima de tudo.
#   2. Os tres desfoques do fundo aquarela. O caminho "horizon" e recalculado a
#      cada quadro, entao o navegador nao reaproveita nada: ele refaz um
#      desfoque gaussiano de 22 px sobre 1080x1920, trinta vezes por segundo.
# O grao sai, SEMPRE. Nao e opcional: era a camada que travava a animacao em
# celular, confirmado pelo usuario testando variantes no proprio aparelho em
# 27/10/2026 (a versao sem grao correu bem; a versao sem os desfoques do
# horizonte nao era necessaria).
#
# O custo nao era o ruido — o feTurbulence tem geometria fixa e e rasterizado
# uma vez. Era o mix-blend-mode overlay num retangulo de tela cheia por cima de
# tudo: enquanto o envelope flutua, o navegador precisa remisturar a pilha
# inteira a cada quadro, e isso nao cabe no orcamento de um aparelho de 2018.
#
# O preco visual e pequeno: o grao era uma textura a 35% de opacidade. O
# horizonte difuso de aquarela, que e o efeito que se ve, continua intacto.
# Ajustes de tipografia do fecho da carta, pedidos pelo Thiago em 27/10/2026
# olhando a pagina pronta: o paragrafo estava pequeno ao lado dos 36 px dos
# dados do evento, e o "Confirmar presenca" vinha em peso 300 — mais leve que
# tudo em volta, o que fazia o unico elemento clicavel da pagina parecer
# legenda. A largura do paragrafo sobe junto (500 -> 518, o mesmo fim de linha
# do botao) para a fonte maior nao empurrar uma quarta linha contra o botao.
TIPOGRAFIA = [
    ("width: 500, fontFamily: SANS, fontSize: 26, lineHeight: '40px'",
     "width: 518, fontFamily: SANS, fontSize: 30, lineHeight: '44px'"),
    ("fontWeight: 300, fontSize: 33, color: '#7C7C7C'",
     "fontWeight: 700, fontSize: 33, color: '#7C7C7C'"),
]

SEM_GRAO = ("{grain && <Grain />}", "{false && <Grain />}")

# Previa do link (WhatsApp, LinkedIn, e-mail). Entra no <head> do HTML CRU, nao
# no documento que o carregador monta: o robo do WhatsApp nao executa
# JavaScript, entao qualquer etiqueta posta em tempo de execucao e invisivel
# para ele. A imagem (2000x1050, proporcao 1,905) foi feita pelo Thiago.
SITE = "https://www.wmtrading.com.br"
PREVIA = SITE + "/wm-party-26/assets/preview.jpg"
DESCRICAO = ("Um ano de conquista merece uma comemoração especial. "
             "29 de novembro, das 12h às 17h, no Cerimonial Oasis, em Vitória.")


def etiquetas_de_previa(publico):
    return "\n".join([
        '  <meta property="og:type" content="website">',
        '  <meta property="og:site_name" content="WM Trading">',
        '  <meta property="og:locale" content="pt_BR">',
        '  <meta property="og:title" content="WM Party 26 — Convite">',
        f'  <meta property="og:description" content="{DESCRICAO}">',
        f'  <meta property="og:url" content="{SITE}/wm-party-26/{publico}/">',
        f'  <meta property="og:image" content="{PREVIA}">',
        '  <meta property="og:image:type" content="image/jpeg">',
        '  <meta property="og:image:width" content="2000">',
        '  <meta property="og:image:height" content="1050">',
        '  <meta property="og:image:alt" content="Envelope do convite da WM Party 26">',
        '  <meta name="twitter:card" content="summary_large_image">',
        f'  <meta name="description" content="{DESCRICAO}">',
    ])

MODULOS_JSX = {
    "1dbc9ba4-bdf0-4952-be59-1c12176ea796": "animations-v3.jsx",
    "58429d41-745a-4c37-b8f4-ae25ee3edbe7": "wm-party.jsx",
}


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


def compila_jsx(babel_js, fontes):
    """Compila os modulos JSX com o Babel do pacote, num node de fora.

    Roda o babel.min.js num contexto de VM porque ele e UMD e espera um
    "window"; sem isso o node nao expoe o global Babel.
    """
    with tempfile.TemporaryDirectory() as pasta:
        caminho_babel = os.path.join(pasta, "babel.min.js")
        with open(caminho_babel, "wb") as f:
            f.write(babel_js)
        entradas = {}
        for nome, codigo in fontes.items():
            alvo = os.path.join(pasta, nome)
            with open(alvo, "w", encoding="utf-8") as f:
                f.write(codigo)
            entradas[nome] = alvo
        script = """
            const vm = require('vm'), fs = require('fs');
            const ctx = { window: {}, self: {}, console, setTimeout, clearTimeout, process };
            ctx.global = ctx; ctx.globalThis = ctx;
            vm.createContext(ctx);
            vm.runInContext(fs.readFileSync(process.argv[1], 'utf8'), ctx, { filename: 'babel.min.js' });
            const B = ctx.Babel || ctx.window.Babel;
            const saida = {};
            for (const par of process.argv.slice(2)) {
                const [nome, caminho] = par.split('::');
                saida[nome] = B.transform(fs.readFileSync(caminho, 'utf8'),
                    { filename: '/' + nome, presets: ['react', 'typescript'] }).code;
            }
            process.stdout.write(JSON.stringify(saida));
        """
        args = ["node", "-e", script, caminho_babel]
        args += [f"{nome}::{caminho}" for nome, caminho in entradas.items()]
        r = subprocess.run(args, capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit("falhou ao compilar o JSX:\n" + r.stderr)
        return json.loads(r.stdout)


def gera(html, publico, url_form):
    manifesto_m = re.search(r'(<script type="__bundler/manifest"[^>]*>)(.*?)(</script>)', html, re.S)
    manifesto = json.loads(manifesto_m.group(2).strip())

    # Primeiro as trocas de texto, ainda no JSX; depois compila.
    fontes, trocas, grao_removido = {}, 0, False
    for uuid, nome in MODULOS_JSX.items():
        if uuid not in manifesto:
            raise SystemExit(f"o modulo {nome} sumiu do manifesto")
        codigo = descomprime(manifesto[uuid]).decode("utf-8")
        if MARCA_RSVP in codigo:
            codigo = codigo.replace(MARCA_RSVP, f"const RSVP_URL = '{url_form}';")
            if TROCA_FUNDO[0] not in codigo:
                raise SystemExit(f"nao achei a referencia a {TROCA_FUNDO[0]} para trocar pelo WebP")
            codigo = codigo.replace(*TROCA_FUNDO)
            for de, para in TIPOGRAFIA:
                if codigo.count(de) != 1:
                    raise SystemExit(f"nao achei (ou achei repetido) o trecho de tipografia {de!r}")
                codigo = codigo.replace(de, para)
            trocas += 1
        if SEM_GRAO[0] in codigo:
            codigo = codigo.replace(*SEM_GRAO)
            grao_removido = True
        fontes[nome] = codigo
    if trocas != 1:
        raise SystemExit(f"esperava trocar o RSVP_URL em 1 modulo, troquei em {trocas}")
    if not grao_removido:
        raise SystemExit("nao achei a camada de grao para remover — ela trava a "
                         "animacao em celular, entao nao da para seguir sem conferir")

    if UUID_BABEL not in manifesto:
        raise SystemExit("nao achei o Babel no manifesto — o pacote mudou de formato")
    compilados = compila_jsx(descomprime(manifesto[UUID_BABEL]), fontes)
    for uuid, nome in MODULOS_JSX.items():
        comprime(manifesto[uuid], compilados[nome].encode("utf-8"))
    del manifesto[UUID_BABEL]

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
    # O carregador decide pelo sufixo: com .js ele roda o codigo direto, sem
    # pedir o compilador.
    for nome in MODULOS_JSX.values():
        if nome not in template:
            raise SystemExit(f"nao achei a referencia a {nome} no template")
        template = template.replace(nome, nome.replace(".jsx", ".js"))
    html = html[:tpl_m.start(2)] + _como_json(template) + html[tpl_m.end(2):]

    # Sem isso o carregador ainda anunciaria o Babel entre os recursos externos.
    ext_m = re.search(r'(<script type="__bundler/ext_resources"[^>]*>)(.*?)(</script>)', html, re.S)
    recursos = [r for r in json.loads(ext_m.group(2).strip()) if r.get("uuid") != UUID_BABEL]
    html = html[:ext_m.start(2)] + json.dumps(recursos, ensure_ascii=False) + html[ext_m.end(2):]

    # Por ultimo, para nao deslocar as posicoes de que as reescritas acima
    # dependem (foi o que quebrou na primeira tentativa).
    ancora = "  <title>WM Party 26 — Convite</title>"
    if ancora not in html:
        raise SystemExit("nao achei o <title> do HTML cru para ancorar a previa do link")
    html = html.replace(ancora, ancora + "\n" + etiquetas_de_previa(publico), 1)
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
