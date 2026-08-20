# -*- coding: utf-8 -*-
"""
WM Trading — Otimizacao das imagens pesadas que o site REALMENTE serve.

Contexto (auditoria de 20/08/2026): o repo tem ~375 MB de imagem, mas so parte e
servida. A listagem /blog/ sozinha referencia 216 capas somando 88 MB, e uma unica
PNG de 39,5 MB e ao mesmo tempo a capa de um post e o thumbnail dele no card.

O que este script faz
---------------------
1. Monta o inventario de imagens e descobre QUEM referencia cada uma.
2. Para cada imagem servida acima do limite, gera uma versao WebP redimensionada.
3. Reescreve as referencias na FONTE (content/**, css/**, as 2 paginas manuais e o
   proprio build_pages.py) — nunca no HTML gerado, que o build refaz.
4. Nao apaga o original.

Duas regras que este script respeita, e que existem por motivo
--------------------------------------------------------------
* NOME NOVO, SEMPRE. `/images` e `/wp-content` respondem com cache de 30 dias
  (`max-age=2592000` no vercel.json). Sobrescrever `foo.png` deixaria quem ja
  visitou o site com a versao antiga por um mes. Por isso a saida e `foo-v2.webp`.
* SO A FONTE. O site e gerado. Editar `blog/x.html` seria desfeito no proximo
  build; o que vale e o `cover:` do `content/blog/x.mdx`.

Depois de rodar com --aplicar, e OBRIGATORIO reconstruir, nesta ordem:

    python scripts/build_pages.py
    python scripts/build_en.py     # senao o hreflang de 24 paginas desaparece
    python scripts/verificar.py

Uso
---
    python scripts/otimizar_imagens.py                  # relatorio, nao escreve
    python scripts/otimizar_imagens.py --aplicar        # converte e reescreve
    python scripts/otimizar_imagens.py --limite 500     # baixa o corte para 500 KB
    python scripts/otimizar_imagens.py --so blog        # so caminhos com "blog"
"""
import argparse
import collections
import os
import re
import sys
from urllib.parse import quote, unquote

EXTENSOES = (".jpg", ".jpeg", ".png", ".webp", ".avif", ".gif")

# Paginas fora do gerador: aqui a referencia se edita no proprio HTML.
# Manter em sincronia com o comentario do build_pages.py sobre paginas manuais.
PAGINAS_MANUAIS = ("importacao-carne-suina/index.html", "segmentos-aeronaves.html")

# Diretorios cujo HTML e GERADO — nao editar, o build refaz.
DIRS_GERADOS = ("blog/", "en/", "segmentos/", "aeronaves/", "ebooks/")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def rel(caminho):
    return os.path.relpath(caminho, RAIZ).replace(os.sep, "/")


def e_fonte_morta(caminho_rel):
    """content/pages/ e legado: o gerador le dali APENAS solucoes-wm.json.

    Descoberto em 20/08/2026. As duplicatas de assessoria-aduaneira, global-sourcing,
    importacao-por-*, segmentos_* e as de aeronave nao tem efeito nenhum se editadas —
    as paginas de servico vem de content/services/, os segmentos de content/segments/
    e as aeronaves de content/aircraft/. Reescrever aqui daria falso sucesso: a imagem
    seria convertida e o HTML no ar continuaria apontando para a antiga.
    """
    return (caminho_rel.startswith("content/pages/")
            and caminho_rel != "content/pages/solucoes-wm.json")


def serve_ao_navegador(caminho_rel):
    """So HTML e CSS provam que a imagem chega no navegador.

    Arquivo de conteudo (content/**) diz de onde a referencia SAI, nao que ela chegue
    a alguma pagina — um .json morto referencia imagem que ninguem serve.
    """
    return caminho_rel.endswith((".html", ".css"))


def e_gerado(caminho_rel):
    """HTML gerado pelo build_pages/build_en (nao editar diretamente)."""
    if caminho_rel in PAGINAS_MANUAIS:
        return False
    if not caminho_rel.endswith(".html"):
        return False
    if caminho_rel.startswith(DIRS_GERADOS):
        return True
    # HTML na raiz tambem e gerado (index, about, servicos, 404, ...)
    return "/" not in caminho_rel


def inventario_imagens():
    imgs = {}
    for base, dirs, arquivos in os.walk(RAIZ):
        dirs[:] = [d for d in dirs if d not in (".git", "node_modules", "__pycache__")]
        for a in arquivos:
            if a.lower().endswith(EXTENSOES):
                p = os.path.join(base, a)
                try:
                    imgs[rel(p)] = os.path.getsize(p)
                except OSError:
                    pass
    return imgs


def arquivos_de_texto():
    """Arquivos onde uma referencia de imagem pode aparecer."""
    saida = []
    for base, dirs, arquivos in os.walk(RAIZ):
        dirs[:] = [d for d in dirs if d not in (".git", "node_modules", "__pycache__")]
        for a in arquivos:
            if a.endswith((".html", ".css", ".mdx", ".json", ".md", ".py", ".js")):
                r = rel(os.path.join(base, a))
                if r.startswith("scripts/otimizar_imagens.py"):
                    continue
                saida.append(r)
    return saida


def variantes(caminho_img):
    """Formas em que a referencia pode estar escrita no texto."""
    v = {"/" + caminho_img, caminho_img}
    q = quote(caminho_img)
    v.add("/" + q)
    v.add(q)
    # caminho relativo usado por pagina manual (sem a barra inicial)
    return {x for x in v if x}


def indexa_referencias(imgs, textos):
    """imagem -> {arquivo: [variantes encontradas]}"""
    conteudos = {}
    for t in textos:
        try:
            conteudos[t] = open(os.path.join(RAIZ, t), encoding="utf-8", errors="replace").read()
        except OSError:
            pass

    refs = collections.defaultdict(dict)
    for img in imgs:
        vs = variantes(img)
        for t, s in conteudos.items():
            achadas = [v for v in vs if v in s]
            if achadas:
                refs[img][t] = achadas
    return refs


# --------------------------------------------------------------------------
# Duas excecoes descobertas ao perfilar o lote de 20/08/2026. Sao automaticas de
# proposito: depender de alguem lembrar do parametro na hora e como nao ter regra.
# --------------------------------------------------------------------------

LIMITE_CORES_CHAPADAS = 20000   # acima disso e foto; abaixo, arte/recorte
MAX_LADO_FAIXA = 1920           # faixa de topo nao pode encolher e ser esticada
PROPORCAO_FAIXA = 3.0           # largura/altura a partir do qual e faixa


def e_arte_chapada(im):
    """Recorte de produto, infografico, logo — cor lisa e borda dura.

    Compressao com perda mancha o fundo liso e suja a borda do recorte. Nesses
    casos vale WebP SEM perda: continua bem menor que o PNG original.
    """
    if im.mode in ("P", "1", "L"):
        return True
    amostra = im
    if im.width * im.height > 8_000_000:
        # reduz por vizinho-mais-proximo: nao inventa cor nova na contagem
        amostra = im.resize((im.width // 4, im.height // 4), Image.NEAREST)
    try:
        cores = amostra.convert("RGB").getcolors(maxcolors=LIMITE_CORES_CHAPADAS)
    except Exception:
        return False
    return cores is not None   # None = passou do teto = e foto


def e_faixa_de_topo(caminho_rel, im):
    """Banner que atravessa o topo da pagina, tipo 1920x405."""
    if "banner" in caminho_rel.rsplit("/", 1)[-1].lower():
        return True
    return im.height > 0 and (im.width / float(im.height)) >= PROPORCAO_FAIXA


def converte(origem_rel, destino_rel, max_lado, qualidade):
    """Devolve (bytes, dimensao, motivo) — motivo diz qual regra pegou."""
    from PIL import Image

    src = os.path.join(RAIZ, origem_rel)
    dst = os.path.join(RAIZ, destino_rel)
    with Image.open(src) as im:
        chapada = e_arte_chapada(im)
        faixa = e_faixa_de_topo(origem_rel, im)

        if im.mode in ("P", "LA"):
            im = im.convert("RGBA")
        tem_alfa = im.mode in ("RGBA", "LA")
        if not tem_alfa and im.mode != "RGB":
            im = im.convert("RGB")

        teto = max(max_lado, MAX_LADO_FAIXA) if faixa else max_lado
        l, a = im.size
        if max(l, a) > teto:
            fator = teto / float(max(l, a))
            im = im.resize((max(1, int(l * fator)), max(1, int(a * fator))), Image.LANCZOS)

        if chapada:
            im.save(dst, "WEBP", lossless=True, method=6)
        else:
            im.save(dst, "WEBP", quality=qualidade, method=6)

        motivos = []
        if chapada:
            motivos.append("arte chapada -> sem perda")
        if faixa:
            motivos.append("faixa de topo -> teto %dpx" % teto)
        dim = im.size
    return os.path.getsize(dst), dim, ", ".join(motivos) or "foto -> q%d" % qualidade


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limite", type=int, default=900, help="corte em KB (padrao 900)")
    ap.add_argument("--max-lado", type=int, default=1600, help="maior lado em px (padrao 1600)")
    ap.add_argument("--qualidade", type=int, default=82, help="qualidade WebP (padrao 82)")
    ap.add_argument("--so", default=None, help="filtra por trecho do caminho")
    ap.add_argument("--aplicar", action="store_true", help="escreve de verdade")
    args = ap.parse_args()

    corte = args.limite * 1024

    print("Inventariando imagens...")
    imgs = inventario_imagens()
    textos = arquivos_de_texto()
    print("  %d imagens, %d arquivos de texto para varrer" % (len(imgs), len(textos)))
    refs = indexa_referencias(imgs, textos)

    # "servida" = aparece em HTML ou CSS. Referencia que existe so em content/**
    # (ou pior, so em content/pages morto) nao prova que alguma pagina a entrega.
    servidas, orfas, fantasmas = {}, {}, {}
    for i, t in imgs.items():
        onde = refs.get(i, {})
        if any(serve_ao_navegador(f) for f in onde):
            servidas[i] = t
        elif onde and all(e_fonte_morta(f) for f in onde):
            fantasmas[i] = t
        else:
            orfas[i] = t

    alvos = []
    for img, tam in servidas.items():
        if tam < corte:
            continue
        if args.so and args.so not in img:
            continue
        if img.lower().endswith(".webp") and "-v2.webp" in img:
            continue
        alvos.append((tam, img))
    alvos.sort(reverse=True)

    print()
    print("=" * 74)
    print("  servidas : %6.1f MB em %d arquivos  (chegam no navegador)"
          % (sum(servidas.values()) / 1048576, len(servidas)))
    print("  orfas    : %6.1f MB em %d arquivos  (nao servidas — nao mexer agora)"
          % (sum(orfas.values()) / 1048576, len(orfas)))
    if fantasmas:
        print("  fantasmas: %6.1f MB em %d arquivos  (referidas SO em content/pages morto)"
              % (sum(fantasmas.values()) / 1048576, len(fantasmas)))
    print("  ALVOS    : %6.1f MB em %d arquivos acima de %d KB"
          % (sum(t for t, _ in alvos) / 1048576, len(alvos), args.limite))
    print("=" * 74)

    if not alvos:
        print("\nNada acima do corte. Nada a fazer.")
        return 0

    sem_fonte = []
    feitos = []
    antes = depois = 0

    for tam, img in alvos:
        pasta, arq = img.rsplit("/", 1) if "/" in img else ("", img)
        stem = arq.rsplit(".", 1)[0]
        novo = ("%s/%s-v2.webp" % (pasta, stem)) if pasta else ("%s-v2.webp" % stem)

        onde = refs[img]
        fontes = {f: v for f, v in onde.items()
                  if not e_gerado(f) and not e_fonte_morta(f)}
        gerados = [f for f in onde if e_gerado(f)]
        mortas = [f for f in onde if e_fonte_morta(f)]

        print()
        print("-" * 74)
        print("  %6.1f MB  %s" % (tam / 1048576, img))
        if fontes:
            for f in sorted(fontes):
                print("       fonte  : %s" % f)
        if gerados:
            print("       gerado : %s%s" % (", ".join(sorted(gerados)[:2]),
                                            " +%d" % (len(gerados) - 2) if len(gerados) > 2 else ""))
        if mortas:
            print("       morto  : %s  (content/pages legado — NAO reescrevo)"
                  % ", ".join(sorted(mortas)[:2]))

        if not fontes:
            print("       [!] SEM FONTE — referencia so em HTML gerado. Nao vou reescrever")
            print("           sozinho: precisa achar de onde o gerador tira esse caminho.")
            sem_fonte.append(img)
            continue

        if os.path.exists(os.path.join(RAIZ, novo)):
            print("       [=] %s ja existe — pulando conversao" % novo)
            continue

        if not args.aplicar:
            print("       -> geraria %s (max %dpx, q%d)" % (novo, args.max_lado, args.qualidade))
            print("       -> reescreveria %d arquivo(s) de fonte" % len(fontes))
            antes += tam
            continue

        try:
            novo_tam, dim, motivo = converte(img, novo, args.max_lado, args.qualidade)
        except Exception as e:
            print("       [!] falhou a conversao: %s" % e)
            continue

        if novo_tam >= tam:
            os.remove(os.path.join(RAIZ, novo))
            print("       [--] a versao nova ficou MAIOR (%.0f KB vs %.0f KB) — descartada,"
                  % (novo_tam / 1024.0, tam / 1024.0))
            print("            original mantido e referencias intactas. (%s)" % motivo)
            continue

        trocas = 0
        for f, vs in fontes.items():
            caminho = os.path.join(RAIZ, f)
            s = open(caminho, encoding="utf-8").read()
            o = s
            for v in sorted(vs, key=len, reverse=True):
                # a variante nova espelha a forma da antiga (com ou sem barra, escapada ou nao)
                if v.startswith("/"):
                    alvo_novo = "/" + novo
                else:
                    alvo_novo = novo
                if "%" in v:
                    alvo_novo = quote(unquote(alvo_novo), safe="/")
                s = s.replace(v, alvo_novo)
            if s != o:
                open(caminho, "w", encoding="utf-8", newline="").write(s)
                trocas += 1

        ganho = 100.0 * (1 - novo_tam / float(tam))
        print("       [ok] %.0f KB  %dx%d  (-%.1f%%)  %d fonte(s)  [%s]"
              % (novo_tam / 1024.0, dim[0], dim[1], ganho, trocas, motivo))
        feitos.append((img, novo, tam, novo_tam))
        antes += tam
        depois += novo_tam

    print()
    print("=" * 74)
    if args.aplicar:
        print("  convertidas : %d" % len(feitos))
        print("  antes       : %.1f MB" % (antes / 1048576))
        print("  depois      : %.1f MB" % (depois / 1048576))
        if antes:
            print("  reducao     : %.1f%%" % (100.0 * (1 - depois / float(antes))))
        print()
        print("  AGORA, nesta ordem — sem isso o HTML no ar nao muda:")
        print("    python scripts/build_pages.py")
        print("    python scripts/build_en.py")
        print("    python scripts/verificar.py")
        print()
        print("  Os originais NAO foram apagados: viram orfaos e podem sair depois,")
        print("  junto com a limpeza dos outros arquivos nao servidos.")
    else:
        print("  SIMULACAO — nada foi escrito. Rode de novo com --aplicar.")
        print("  Reducao esperada: os %.1f MB acima viram tipicamente 1-3%% disso." % (antes / 1048576))

    if sem_fonte:
        print()
        print("  [!] %d imagem(ns) referenciada(s) so em HTML gerado, precisam de olho:" % len(sem_fonte))
        for i in sem_fonte:
            print("      - %s" % i)
    print("=" * 74)
    return 0


if __name__ == "__main__":
    sys.exit(main())
