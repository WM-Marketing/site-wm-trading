# -*- coding: utf-8 -*-
"""Recorta em 3:4, redimensiona e grava em WebP as duas fotos de cada participante."""
import os, subprocess, sys, tempfile
from PIL import Image, ImageOps

ORIGEM = os.path.expanduser("~/Downloads/Participantes Concurso de fantasia walloeen 2026")
DESTINO = sys.argv[1]
LARGURA, ALTURA = 900, 1200     # 3:4, o dobro do tamanho que a pagina usa

# (slug, pasta de origem, [arquivo a, arquivo b]) — a primeira e a foto de capa.
# ZOOM: algumas fotos foram feitas de longe e a fantasia fica pequena no card.
# zoom 1.0 usa o quadro inteiro; acima disso recorta uma janela menor em volta
# do ponto (fx, fy), em fracao da imagem, e depois amplia. Nao inventa pixel:
# o original tem 4032x3024, entao mesmo com zoom 1.6 sobram mais pixels do que
# os 900x1200 de saida.
#   chave "slug-n"  ->  (zoom, fx, fy)
ESCOLHAS = [
    ("davi",     "Davi - Aang",                   ["IMG_7472.HEIC", "IMG_7470.HEIC"]),
    ("eduardo",  "Eduardo - Jason",               ["IMG_7458.HEIC", "IMG_7455.HEIC"]),
    ("gabriela", "Gabriela - Ronald McDonald",    ["IMG_7533.HEIC", "IMG_7531.HEIC"]),
    ("isabela",  "Isabela Melo - Fantasma ",      ["IMG_7477.HEIC", "IMG_7475.HEIC"]),
    ("karine",   "Karine - A Dama dos Alfinetes", ["IMG_7490.HEIC", "IMG_7494.HEIC"]),
    ("malena",   "Malena - Elphaba",              ["IMG_7484.HEIC", "IMG_7478.HEIC"]),
    ("maria",    "Maria Emília - Caveira Mexicana",
     ["WhatsApp Image 2026-10-29 at 14.51.24 (1).jpeg",
      "WhatsApp Image 2026-10-29 at 14.51.24.jpeg"]),
]


def abre(caminho):
    """HEIC nao abre no Pillow desta maquina; o sips converte antes."""
    if caminho.lower().endswith(".heic"):
        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False).name
        subprocess.run(["sips", "-s", "format", "jpeg", caminho, "--out", tmp],
                       check=True, capture_output=True)
        caminho = tmp
    return ImageOps.exif_transpose(Image.open(caminho)).convert("RGB")


ENQUADRAMENTO = {
    "isabela-1": (1.55, 0.53, 0.56),   # fantasma de corpo inteiro numa sala larga
    "isabela-2": (1.35, 0.33, 0.55),   # mesma sala, com os colegas ao fundo
    "malena-1":  (1.30, 0.52, 0.55),   # a capa aberta pede folga, mas nao tanta
    "malena-2":  (1.15, 0.45, 0.52),
    "davi-2":    (1.15, 0.47, 0.52),
}


def recorta(im, zoom=1.0, fx=0.5, fy=0.5):
    """Janela em volta do ponto de interesse antes do corte 3:4."""
    if zoom > 1.0:
        l, a = im.size
        jl, ja = int(l / zoom), int(a / zoom)
        esq = min(max(int(l * fx - jl / 2), 0), l - jl)
        topo = min(max(int(a * fy - ja / 2), 0), a - ja)
        im = im.crop((esq, topo, esq + jl, topo + ja))
    return _tres_por_quatro(im)


def _tres_por_quatro(im):
    """3:4 centrado na horizontal, preso mais perto do topo — e onde esta o rosto."""
    alvo = LARGURA / ALTURA
    l, a = im.size
    if l / a > alvo:
        nova_l = int(round(a * alvo))
        esq = (l - nova_l) // 2
        im = im.crop((esq, 0, esq + nova_l, a))
    else:
        nova_a = int(round(l / alvo))
        topo = int((a - nova_a) * 0.18)
        im = im.crop((0, topo, l, topo + nova_a))
    return im.resize((LARGURA, ALTURA), Image.LANCZOS)


os.makedirs(DESTINO, exist_ok=True)
total = 0
for slug, pasta, arquivos in ESCOLHAS:
    for i, arq in enumerate(arquivos, 1):
        origem = os.path.join(ORIGEM, pasta, arq)
        if not os.path.exists(origem):
            raise SystemExit("nao achei: " + origem)
        saida = os.path.join(DESTINO, f"{slug}-{i}.webp")
        z, fx, fy = ENQUADRAMENTO.get(f"{slug}-{i}", (1.0, 0.5, 0.5))
        recorta(abre(origem), z, fx, fy).save(saida, "WEBP", quality=80, method=6)
        total += os.path.getsize(saida)
        print(f"  {slug}-{i}.webp  {os.path.getsize(saida)//1024} KB")
print(f"total: {total//1024} KB")
