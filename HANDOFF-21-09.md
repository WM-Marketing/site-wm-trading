# Passagem de bastão — site WM Trading, 21/09/2026

Resumo para continuar em outro chat. Tudo que está aqui foi verificado; o que é
suposição está marcado como tal.

---

## Estado agora

| | |
|---|---|
| Repositório | **em dia** com o GitHub, nada a publicar |
| PRs abertos | nenhum |
| `verificar.py` | **REPROVADO — 6 erros**, nenhum deles meu (ver abaixo) |
| Working copy | `~/Downloads/site-wm-trading` |

Push na `main` publica direto no Vercel. O deploy leva ~45–60s.

---

## O que trava o portão (não é meu, e vem de dias)

```
[ERRO] 2 fontes com versao_en: true e SEM a marca traducao_revisada:
       content/blog/impostos-importacao-aeronaves.mdx
       content/blog/taxes-on-aircraft-imports-brazil.mdx
[ERRO] 1 hreflang incompleto — /blog/ (falta o par no lado PT)
```

Os dois posts são da **Maine**, de 18/09. Quem revisa inglês é o **Renato** —
falta ele marcar `traducao_revisada: true`. É um minuto de trabalho.

O hreflang da `/blog/` se resolve rodando os builds na ordem certa e commitando
a saída.

**Já publiquei por cima desse portão vermelho algumas vezes, a pedido.** Vale
insistir: quanto mais tempo ele fica vermelho por algo conhecido, mais as
pessoas se acostumam a ignorá-lo — e aí ele para de servir para o que existe.

---

## Pendências de trabalho

### 1. Infográficos — esperando arquivos (o usuário foi buscar)

Na `/materiais/`, os 5 infográficos apontam para `/fale-conosco/`: o visitante
preenche um formulário comercial e não recebe material nenhum.

**Causa:** em `build_pages.py` (~linha 3152) a `infographics_list` é só cinco
strings de título, sem arquivo. Nunca foi construído.

**Só a Lei 14.300 tem material próprio.** Os outros quatro não existem — busquei
em Git, `wp-content`, URLs antigas, Wayback (nenhuma captura) e OneDrive inteiro.

**Decidido:** construir o mecanismo espelhando o e-book (JSON + LP + liberação
após envio), publicar só o que tem material, e **abrir a imagem** em vez de
forçar download — mostrando na própria página, porque `window.open` depois de
chamada assíncrona é barrado por bloqueador de pop-up.

**Armadilha:** o `vercel.json` tem redirects para
`/infograficos/entreposto-aduaneiro/` e `/infograficos/leasing-de-aeronaves/`.
Se as LPs nascerem nesses endereços, o redirect intercepta. **Remover os dois.**

### 2. `banner-resultados.jpg` da /segmentos/aco/ (2100 × 552)

Ainda é um render 3D genérico — a única imagem da página que valia trocar e
ficou pendente. Na página de Máquinas esse espaço traz contêiner da WM.

### 3. Leads da LP de carne suína não geram aviso interno

Por decisão do usuário, o formulário não entra no Monday — logo, **não há item
no board nem e-mail interno**. Alguém precisa acompanhar o Pipedrive direto.
É uma linha em `CONFIG_FORMULARIO` (`api/_monday.js`) se mudarem de ideia.

### 4. As 28 páginas `/en/` sem marca de revisão

Anteriores à regra de 27/08, então só geram aviso. Combinar com o Renato se
vale revisar aos poucos — o formato do `REVISAO-TRADUCAO-EN.md` serve.

### 5. Rastrear telefones corrompidos no Pipedrive

Até 17/09 a máscara corrompia número digitado com `+55`. Leads antigos da LP de
suínos e do popup de WhatsApp com telefone começando em **`(55)`** são a
assinatura do defeito. O DDD 55 existe (RS), então não é prova sozinho.

---

## O que foi feito nesta sessão (tudo no ar)

- **`/segmentos/aco/`** — layout de 9 seções clonado de Máquinas, 3 benefícios,
  fusão das duas seções que repetiam o "92% canal verde", faixa com foto própria
- **`/en/segments/steel/` e `/en/segments/photovoltaic-equipment/`** — saíram do
  molde genérico; o `maquinas_em_ingles()` virou `segmento_em_ingles()` genérico.
  Revisadas pelo Renato, que achou dois defeitos reais que passaram por mim
- **`/interno/padrao-de-emails/`** — página interna, acessível por link e fora
  do Google (noindex em 3 camadas). **Não é privada** — só escondida de buscador
- **LP de carne suína** — removidos 3 depoimentos inventados que estavam no ar;
  15 → 12 filiais; tempo de mercado agora calculado a partir de 2004
- **Máscara de telefone** — `+55` corrompia o número silenciosamente
  (`+55 27 99999-0000` virava `(55) 27999-9900`, válido e errado). Corrigido na
  LP e no popup, mais o fixo que saía mal formatado
- **Integração Monday** — token vencido, reconfigurado e validado
- **`/carreiras/`** — botão ia para o formulário comercial, agora vai para a
  Gupy; hero novo com foto da equipe e gradiente; foto em resolução maior

---

## Como trabalhar neste repo (o essencial)

**Ordem dos builds, sempre:**
```bash
python3 scripts/build_pages.py && python3 scripts/build_en.py && python3 scripts/verificar.py
```
O `build_pages.py` sozinho **apaga o hreflang de ~38 páginas**.

**As armadilhas que só quebram no build SEGUINTE** estão na memória, em
`armadilhas-build-site-wm.md`. Resumo: travas de página manual, capa da versão
EN, cache de 30 dias nas imagens (trocar o NOME, não só o conteúdo), e o
`sitemap.xml` que incha sozinho depois de um `git pull`.

**Verificar a página NO AR, não só local.** Dois defeitos desta sessão passaram
limpos no teste local e só apareceram em produção.

**Servidor local:** o sandbox não enxerga `~/Downloads`. Rode você mesmo:
```bash
cd ~/Downloads/site-wm-trading && python3 -m http.server 4321
```

---

## Pessoas

- **Renato Furtado** — revisa inglês. Nenhuma tradução publica sem ele
- **Maine De Jesus Pinheiro** — publica posts de blog
