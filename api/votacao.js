/* ==========================================================================
   WM Trading — api/votacao.js
   Recebe os votos do Concurso de Fantasia e grava cada um como item no Monday.

   POR QUE NAO REAPROVEITA O api/_monday.js
   Aquele modulo existe para LEAD: board fixo de captacao, colunas de e-mail,
   telefone, segmento. Um voto nao tem nada disso e nao pode cair no board
   comercial. Aqui o board e outro, as colunas sao quatro e o token e o mesmo.

   O BOARD NASCE SOZINHO
   Ninguem precisa criar nada no Monday antes. Na primeira chamada o codigo
   procura o board pelo nome; se nao existir, cria com as quatro colunas e seg
   ue. O id fica em memoria enquanto a instancia viver — nas chamadas seguintes
   e so a mutation. Em uma eleicao de 100 pessoas isso e uma busca, nao cem.

   UM VOTO POR PESSOA
   A coluna "Chave" guarda o nome normalizado (sem acento, minusculo, espaco
   unico). Antes de gravar, o codigo pergunta ao board se aquela chave ja
   existe. Se a consulta FALHAR, o voto entra assim mesmo e o log registra:
   perder a trava de duplicidade e ruim, perder o voto de alguem e pior — a
   duplicata da para resolver olhando o board, o voto perdido nao.
   ========================================================================== */

const MONDAY_ENDPOINT = 'https://api.monday.com/v2';
const MONDAY_API_VERSION = '2026-07';

const NOME_DO_BOARD = 'Concurso de Fantasia WM 2026';

/* Titulo da coluna -> tipo no Monday. A ordem e a ordem em que aparecem. */
const COLUNAS = [
  ['Fantasia votada', 'text'],
  ['Setor', 'text'],
  ['Momento', 'text'],
  ['Chave', 'text'],
];

/* A LISTA DE VERDADE DOS CANDIDATOS MORA AQUI, NAO NO NAVEGADOR.
   O HTML tambem tem a lista, mas e so para desenhar os cards. Se a validacao
   ficasse so la, bastaria um POST a mao para registrar voto em "Fantasia do
   Thiago" e sujar a apuracao. */
const PARTICIPANTES = {
  davi: 'Davi — Aang',
  eduardo: 'Eduardo — Jason',
  gabriela: 'Gabriela — Ronald McDonald',
  isabela: 'Isabela Melo — Fantasma',
  karine: 'Karine — A Dama dos Alfinetes',
  malena: 'Malena — Elphaba',
  maria: 'Maria Emília — Catrina, a Caveira Mexicana',
};

/* Departamentos da WM, como aparecem na listagem do DHO. "Outro" cobre quem
   nao se reconhece em nenhum — melhor um voto com setor impreciso do que um
   voto que a pessoa desiste de dar porque o setor dela nao esta na lista. */
const SETORES = [
  'ADM', 'DHO', 'GEST', 'SEAFI', 'SECOM', 'SEDEP', 'SEFIS', 'SEJUD',
  'SELOG', 'SEMAK', 'SEOPE', 'SETEC', 'SGQ', 'Outro',
];

const ORIGENS_OK = [
  'https://www.wmtrading.com.br',
  'https://wmtrading.com.br',
];
const PREVIEW_OK = /^https:\/\/site-wm-trading-[a-z0-9-]+\.vercel\.app$/;

function origemPermitida(origem) {
  if (!origem) return false;
  return ORIGENS_OK.includes(origem) || PREVIEW_OK.test(origem);
}

/* Cache por instancia da lambda: { id, colunas: {titulo: idDaColuna} }. */
let boardEmCache = null;

async function consultaMonday(query, variables) {
  const token = process.env.MONDAY_API_TOKEN;
  if (!token) throw new Error('MONDAY_API_TOKEN ausente no ambiente');

  const resposta = await fetch(MONDAY_ENDPOINT, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': token,
      'API-Version': MONDAY_API_VERSION,
    },
    body: JSON.stringify({ query, variables: variables || {} }),
  });

  if (!resposta.ok) throw new Error(`Monday respondeu HTTP ${resposta.status}`);

  const corpo = await resposta.json().catch(() => null);
  if (!corpo) throw new Error('Monday devolveu resposta ilegivel');

  /* A API responde 200 COM errors — a mesma armadilha do api/_monday.js. */
  if (Array.isArray(corpo.errors) && corpo.errors.length) {
    const motivo = corpo.errors.map((e) => e && e.message).filter(Boolean).join(' | ');
    throw new Error(`GraphQL: ${motivo || 'erro sem mensagem'}`);
  }
  return corpo.data;
}

/** Procura o board pelo nome. Devolve o id ou null. */
async function procuraBoard() {
  for (let pagina = 1; pagina <= 10; pagina += 1) {
    const dados = await consultaMonday(
      `query($pagina: Int!) { boards(limit: 100, page: $pagina, state: active) { id name } }`,
      { pagina });
    const lista = (dados && dados.boards) || [];
    if (!lista.length) return null;
    /* Varios boards com o mesmo nome so acontece se duas instancias frias
       criarem ao mesmo tempo. Fica com o menor id — o primeiro — para que
       todas as instancias convirjam para o mesmo board. */
    const iguais = lista.filter((b) => b.name === NOME_DO_BOARD).map((b) => String(b.id));
    if (iguais.length) return iguais.sort((a, b) => Number(a) - Number(b))[0];
  }
  return null;
}

async function criaBoard() {
  const dados = await consultaMonday(
    `mutation($nome: String!) {
       create_board(board_name: $nome, board_kind: public) { id }
     }`, { nome: NOME_DO_BOARD });
  const id = dados && dados.create_board && dados.create_board.id;
  if (!id) throw new Error('create_board nao devolveu id');

  for (const [titulo, tipo] of COLUNAS) {
    await consultaMonday(
      `mutation($board: ID!, $titulo: String!, $tipo: ColumnType!) {
         create_column(board_id: $board, title: $titulo, column_type: $tipo) { id }
       }`, { board: String(id), titulo, tipo });
  }
  console.log(`Votacao: board "${NOME_DO_BOARD}" criado (${id})`);
  return String(id);
}

/** Id do board e mapa titulo->coluna, criando o board na primeira vez. */
async function garanteBoard() {
  if (boardEmCache) return boardEmCache;

  const id = (await procuraBoard()) || (await criaBoard());
  const dados = await consultaMonday(
    `query($id: ID!) { boards(ids: [$id]) { columns { id title } } }`, { id });
  const colunas = {};
  const achadas = (dados && dados.boards && dados.boards[0] && dados.boards[0].columns) || [];
  for (const c of achadas) colunas[c.title] = c.id;

  const faltando = COLUNAS.map(([t]) => t).filter((t) => !colunas[t]);
  if (faltando.length) {
    /* Board existia mas alguem renomeou/apagou uma coluna. Recria as que
       faltam em vez de derrubar a votacao. */
    for (const titulo of faltando) {
      const tipo = (COLUNAS.find(([t]) => t === titulo) || [])[1] || 'text';
      const nova = await consultaMonday(
        `mutation($board: ID!, $titulo: String!, $tipo: ColumnType!) {
           create_column(board_id: $board, title: $titulo, column_type: $tipo) { id }
         }`, { board: id, titulo, tipo });
      colunas[titulo] = nova.create_column.id;
      console.log(`Votacao: coluna "${titulo}" recriada no board ${id}`);
    }
  }

  boardEmCache = { id, colunas };
  return boardEmCache;
}

/** Nome sem acento, minusculo, espaco unico — serve de chave de duplicidade. */
function chaveDoNome(nome) {
  return String(nome || '')
    .normalize('NFD').replace(/[̀-ͯ]/g, '')
    .toLowerCase().replace(/[^a-z0-9 ]/g, ' ').replace(/\s+/g, ' ').trim();
}

/** Ja existe voto com esta chave? null quando a consulta falhou. */
async function jaVotou(board, chave) {
  try {
    const dados = await consultaMonday(
      `query($board: ID!, $coluna: String!, $valor: String!) {
         items_page_by_column_values(
           board_id: $board, limit: 1,
           columns: [{ column_id: $coluna, column_values: [$valor] }]
         ) { items { id name } }
       }`,
      { board: board.id, coluna: board.colunas['Chave'], valor: chave });
    const itens = (dados && dados.items_page_by_column_values &&
                   dados.items_page_by_column_values.items) || [];
    return itens.length > 0;
  } catch (err) {
    console.error('Votacao: consulta de duplicidade falhou, o voto segue mesmo assim:', err.message);
    return null;
  }
}

function limpa(valor, maximo) {
  return String(valor == null ? '' : valor).replace(/\s+/g, ' ').trim().slice(0, maximo);
}

/** Data e hora de Brasilia, do relogio do SERVIDOR. */
function momento() {
  const f = new Intl.DateTimeFormat('pt-BR', {
    timeZone: 'America/Sao_Paulo', dateStyle: 'short', timeStyle: 'short',
  });
  return f.format(new Date());
}

module.exports = async function handler(req, res) {
  const origem = req.headers.origin || '';
  if (origemPermitida(origem)) res.setHeader('Access-Control-Allow-Origin', origem);
  res.setHeader('Vary', 'Origin');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Cache-Control', 'no-store');

  if (req.method === 'OPTIONS') return res.status(200).end();

  /* Chamada de conferencia: garante que o board existe e devolve o id, sem
     criar voto nenhum. Serve para preparar o board antes de divulgar o link. */
  if (req.method === 'GET') {
    try {
      const board = await garanteBoard();
      return res.status(200).json({
        ok: true, board: board.id,
        url: `https://wmtrading.monday.com/boards/${board.id}`,
      });
    } catch (err) {
      console.error('Votacao: nao consegui preparar o board:', err);
      return res.status(500).json({ ok: false, error: 'Nao consegui falar com o Monday.' });
    }
  }

  if (req.method !== 'POST') {
    res.setHeader('Allow', ['GET', 'POST']);
    return res.status(405).json({ ok: false, error: 'Método não permitido.' });
  }

  try {
    const dados = req.body || {};

    /* Campo-armadilha: invisivel na tela, so robo preenche. Responde sucesso
       para o robo nao aprender que foi barrado — e nao grava nada. */
    if (dados._gotcha) {
      console.log('Votacao: honeypot preenchido, descartado.');
      return res.status(200).json({ ok: true, registrado: false });
    }

    /* Navegador manda Origin em POST mesmo same-origin; script nao manda. */
    if (origem && !origemPermitida(origem)) {
      return res.status(403).json({ ok: false, error: 'Origem não autorizada.' });
    }

    const nome = limpa(dados.nome, 80);
    const setor = limpa(dados.setor, 40);
    const slug = limpa(dados.participante, 40).toLowerCase();

    if (nome.length < 3 || !/ /.test(nome)) {
      return res.status(400).json({
        ok: false, error: 'Escreva seu nome e sobrenome — é o que valida o voto.' });
    }
    if (!SETORES.includes(setor)) {
      return res.status(400).json({ ok: false, error: 'Escolha o seu setor na lista.' });
    }
    if (!Object.prototype.hasOwnProperty.call(PARTICIPANTES, slug)) {
      return res.status(400).json({ ok: false, error: 'Participante não encontrado.' });
    }

    const board = await garanteBoard();
    const chave = chaveDoNome(nome);
    const repetido = await jaVotou(board, chave);
    if (repetido === true) {
      return res.status(409).json({
        ok: false, jaVotou: true,
        error: 'Este nome já votou. É um voto por pessoa — valeu a tentativa.' });
    }

    const valores = {
      [board.colunas['Fantasia votada']]: PARTICIPANTES[slug],
      [board.colunas['Setor']]: setor,
      [board.colunas['Momento']]: momento() + (repetido === null ? ' (sem checagem de repetido)' : ''),
      [board.colunas['Chave']]: chave,
    };

    const criado = await consultaMonday(
      `mutation($board: ID!, $nome: String!, $valores: JSON!) {
         create_item(board_id: $board, item_name: $nome, column_values: $valores) { id }
       }`,
      { board: board.id, nome, valores: JSON.stringify(valores) });

    const id = criado && criado.create_item && criado.create_item.id;
    if (!id) throw new Error('resposta sem data.create_item.id');

    return res.status(200).json({ ok: true, registrado: true });
  } catch (err) {
    console.error('Votacao: erro ao registrar o voto:', err);
    return res.status(500).json({
      ok: false,
      error: 'Não consegui registrar seu voto agora. Tente de novo em alguns instantes.' });
  }
};
