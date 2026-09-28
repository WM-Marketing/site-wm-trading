#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera css/base.css juntando, NESTA ORDEM, os 4 CSS que toda pagina carrega:

    variables.css -> reset.css -> main.css -> responsive.css

Por que existe (28/09/2026): eram 4 <link> que travavam a primeira exibicao
da pagina, cada um uma ida e volta ao servidor. Viraram 1. A Vercel nao roda
build (site estatico), entao o base.css vai commitado.

    python scripts/build_css.py            # regrava css/base.css
    python scripts/build_css.py --checar   # so confere; sai 1 se estiver velho

REGRA: NUNCA edite css/base.css. Edite os 4 arquivos de origem e rode este
script. O scripts/verificar.py reprova se o base.css estiver desatualizado.
As paginas especificas (aco.css, dynamic-pages.css etc.) continuam separadas.
"""

import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTES = ["variables.css", "reset.css", "main.css", "responsive.css"]
DESTINO = os.path.join(RAIZ, "css", "base.css")

CABECALHO = (
    "/* =============================================================\n"
    "   ARQUIVO GERADO — NAO EDITE.\n"
    "   Edite css/{} e rode: python scripts/build_css.py\n"
    "   ============================================================= */\n"
).format(", css/".join(FONTES))


def montar():
    partes = [CABECALHO]
    for nome in FONTES:
        with open(os.path.join(RAIZ, "css", nome), encoding="utf-8") as f:
            corpo = f.read().rstrip("\n")
        partes.append(f"\n/* ---- css/{nome} ---- */\n{corpo}\n")
    return "".join(partes)


def atual():
    try:
        with open(DESTINO, encoding="utf-8", newline="") as f:
            return f.read()
    except FileNotFoundError:
        return None


def main():
    esperado = montar()
    if "--checar" in sys.argv:
        if atual() != esperado:
            print("css/base.css DESATUALIZADO — rode: python scripts/build_css.py")
            sys.exit(1)
        print("css/base.css em dia")
        return
    with open(DESTINO, "w", encoding="utf-8", newline="\n") as f:
        f.write(esperado)
    print(f"css/base.css gerado ({len(esperado.encode('utf-8'))} bytes)")


if __name__ == "__main__":
    main()
