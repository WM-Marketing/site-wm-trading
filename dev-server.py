# -*- coding: utf-8 -*-
"""Servidor local que imita a Vercel: cleanUrls + trailingSlash + tabela de redirects.

Sem isto o teste nao vale nada: com `python -m http.server`, /en/about/ da 404
(o arquivo e en/about.html) e a tabela de redirects nem existe. Este arquivo esta
no .gitignore — ferramenta local, nao entra no repositorio nem na Vercel.
"""
import http.server, json, os, re, socketserver, urllib.parse

RAIZ = os.path.dirname(os.path.abspath(__file__))
PORTA = 8123
cfg = json.load(open(os.path.join(RAIZ, "vercel.json"), encoding="utf-8"))
REDIRECTS = cfg.get("redirects", [])

def casa(origem, caminho):
    if origem == caminho:
        return caminho
    if ":" in origem:
        padrao = "^" + re.sub(r":\w+\([^)]*\)|:\w+[*+]?", "(.*)", re.escape(origem)
                              .replace(r"\:", ":").replace(r"\(", "(").replace(r"\)", ")")
                              .replace(r"\*", "*").replace(r"\+", "+").replace(r"\.", ".")) + "$"
        if re.match(padrao, caminho):
            return caminho
    return None

class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=RAIZ, **k)

    def do_GET(self):
        caminho = urllib.parse.urlparse(self.path).path

        # arquivo estatico (css/js/imagem) passa direto
        if re.search(r"\.[a-z0-9]{2,5}$", caminho, re.I) and not caminho.endswith(".html"):
            return super().do_GET()

        # 0) cleanUrls: /x.html redireciona para a forma sem extensao
        if caminho.endswith(".html"):
            return self.desvia(caminho[:-5] + "/", 307)

        # 1) trailingSlash: a Vercel normaliza ANTES de consultar os redirects
        if not caminho.endswith("/"):
            return self.desvia(caminho + "/", 307)

        # 2) tabela de redirects
        for r in REDIRECTS:
            if casa(r["source"], caminho):
                return self.desvia(r["destination"], 302)

        # 3) cleanUrls: /x/ -> x.html, senao x/index.html
        rel = caminho.strip("/")
        for tentativa in ([ "index.html" ] if not rel else [rel + ".html", rel + "/index.html"]):
            alvo = os.path.join(RAIZ, tentativa.replace("/", os.sep))
            if os.path.isfile(alvo):
                self.path = "/" + tentativa
                return super().do_GET()

        self.send_error(404, f"nao encontrado: {caminho}")

    def desvia(self, destino, codigo):
        # 307/302 e nao 308/301 DE PROPOSITO: o navegador guarda redirecionamento
        # PERMANENTE e passa a nem consultar o servidor. Um engano no dev-server
        # fica gravado no navegador e reaparece como se fosse defeito do site —
        # aconteceu com /mapa-brasil/*.html em 18/08.
        self.send_response(codigo)
        self.send_header("Location", destino)
        self.end_headers()

    def log_message(self, *a):
        pass

class Servidor(socketserver.ThreadingTCPServer):
    # A home pede dezenas de imagens em paralelo. Servidor de uma requisicao por
    # vez enfileira tudo e o navegador trava esperando. Paginas leves passavam,
    # a home nao.
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    with Servidor(("127.0.0.1", PORTA), H) as s:
        print(f"servidor local imitando a Vercel em http://127.0.0.1:{PORTA}")
        s.serve_forever()
