/* ==========================================================================
   WM Trading — api/_monday.js
   Cria o item de lead no board do Monday (SEMAK + SECOM).

   POR QUE UM ARQUIVO SEPARADO, COM UNDERSCORE
   O prefixo "_" impede a Vercel de publicar isto como rota: /api/_monday nao
   existe para o navegador. E um modulo interno, importado pelo api/contato.js.

   O TOKEN SO EXISTE AQUI DENTRO
   process.env.MONDAY_API_TOKEN e lido em tempo de execucao, no servidor. Nunca
   e devolvido em resposta, nunca vai para log e nunca chega ao HTML/JS publico.
   ========================================================================== */

const MONDAY_ENDPOINT = 'https://api.monday.com/v2';
const MONDAY_API_VERSION = '2026-07';
const BOARD_ID = '18428618371';
const GROUP_ID = 'topics'; // "Entrada de LEADS"

/* Tipos de formulario que viram item no Monday.
   O de e-book fica de fora de proposito: tem so nome, e-mail e empresa, e um
   dropdown sem label faz a mutation falhar. */
const FORMULARIOS_NO_MONDAY = new Set(['contato', 'segmentos']);

/* Colunas do board, na ordem do mapeamento acordado. As internas do Monday
   (name, subtasks_mm6ncwjb) nao entram. */
const COL = {
  email:     'email_mm6ne3mn',
  telefone:  'phone_mm6n8r7k',
  empresa:   'text_mm6n47gn',
  estado:    'dropdown_mm6nrrdt',
  segmento:  'dropdown_mm6nne2e',
  contato:   'dropdown_mm6nmzqh',
  mensagem:  'long_text_mm6nrxta',
  data:      'date_mm6n1mfp',
};

/* ROTULOS QUE DIVERGEM ENTRE O SITE E O MONDAY
   O dropdown do Monday casa por texto exato. Onde o value do <option> nao for
   igual ao label cadastrado la, mapeie aqui — e nao no HTML, que precisa
   continuar enviando o que o Zapier espera.

   Caso conhecido: o site envia "Parte e Peças Geral" (sem o S) porque e assim
   que a linha esta na lookup table do Zapier. Se no Monday o label tiver o S,
   descomente a entrada abaixo.

   Enquanto os rotulos nao forem conferidos um a um no board, um valor
   desconhecido faz a mutation falhar — ver CRIAR_LABEL_SE_FALTAR. */
const MAPA_ROTULOS = {
  estado: {
    // 'Exterior': 'Outro País',
  },
  segmento: {
    // 'Parte e Peças Geral': 'Partes e Peças Geral',
  },
  contato: {
    // 'E-mail': 'Email',
  },
};

/* Deixado FALSO de proposito. Com true, o Monday cria sozinho qualquer label
   que nao exista — o que suja o board com variantes ("Email" ao lado de
   "E-mail") e esconde justamente o erro de mapeamento que queremos ver.
   Prefira corrigir o MAPA_ROTULOS acima. */
const CRIAR_LABEL_SE_FALTAR = false;

const LIMITES = { nome: 255, email: 255, telefone: 40, empresa: 255, mensagem: 5000 };

function limpa(valor, max) {
  return String(valor == null ? '' : valor).replace(/\s+/g, ' ').trim().slice(0, max);
}

function rotulo(campo, valor) {
  const v = limpa(valor, 255);
  return MAPA_ROTULOS[campo] && MAPA_ROTULOS[campo][v] ? MAPA_ROTULOS[campo][v] : v;
}

function emailValido(e) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(e);
}

/* AAAA-MM-DD do SERVIDOR, nunca do navegador — mesmo motivo do aceite_em no
   api/contato.js: relogio de visitante nao e fonte confiavel. */
function dataDeHoje() {
  return new Date().toISOString().slice(0, 10);
}

const MUTATION = `
  mutation CreateLead($boardId: ID!, $groupId: String!, $itemName: String!, $columnValues: JSON!) {
    create_item(
      board_id: $boardId
      group_id: $groupId
      item_name: $itemName
      column_values: $columnValues
      create_labels_if_missing: ${CRIAR_LABEL_SE_FALTAR}
    ) {
      id
      name
      column_values { id text }
    }
  }`;

/** Este formulário deve virar item no Monday? */
function vaiParaOMonday(tipoFormulario) {
  return FORMULARIOS_NO_MONDAY.has(String(tipoFormulario || '').toLowerCase());
}

/**
 * Cria o item. Devolve { id } em caso de sucesso.
 * Lanca Error com motivo tecnico — quem chama registra no log e devolve ao
 * visitante uma mensagem generica, nunca este texto.
 */
async function criarLead(data) {
  const token = process.env.MONDAY_API_TOKEN;
  if (!token) throw new Error('MONDAY_API_TOKEN ausente no ambiente');

  const nome = limpa(data.nome, LIMITES.nome);
  const email = limpa(data.email, LIMITES.email).toLowerCase();
  if (!nome) throw new Error('nome vazio');
  if (!emailValido(email)) throw new Error('e-mail em formato invalido');

  const telefone = limpa(data.telefone, LIMITES.telefone);
  const empresa = limpa(data.empresa, LIMITES.empresa);
  const mensagem = limpa(data.mensagem, LIMITES.mensagem);

  /* Chaves fixas, definidas em COL. O payload do visitante nunca escolhe qual
     coluna preencher — so o conteudo. */
  const columnValues = {
    [COL.email]: { email, text: email },
    [COL.empresa]: empresa,
    [COL.mensagem]: { text: mensagem },
    [COL.data]: { date: dataDeHoje() },
  };

  /* Campos opcionais so entram quando tem valor: dropdown com label vazio e
     phone vazio fazem a mutation falhar. */
  if (telefone) columnValues[COL.telefone] = { phone: telefone, countryShortName: 'BR' };

  const dropdowns = [
    [COL.estado, rotulo('estado', data.estado)],
    [COL.segmento, rotulo('segmento', data.segmento)],
    [COL.contato, rotulo('contato', data.forma_resposta)],
  ];
  for (const [coluna, label] of dropdowns) {
    if (label) columnValues[coluna] = { labels: [label] };
  }

  const resposta = await fetch(MONDAY_ENDPOINT, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': token,
      'API-Version': MONDAY_API_VERSION,
    },
    body: JSON.stringify({
      query: MUTATION,
      variables: {
        boardId: BOARD_ID,
        groupId: GROUP_ID,
        itemName: nome,
        columnValues: JSON.stringify(columnValues),
      },
    }),
  });

  if (!resposta.ok) {
    throw new Error(`Monday respondeu HTTP ${resposta.status}`);
  }

  const corpo = await resposta.json().catch(() => null);
  if (!corpo) throw new Error('Monday devolveu resposta ilegivel');

  /* A API do Monday responde 200 COM errors — por isso a checagem do status
     acima nao basta. Sem esta verificacao, um lead que nunca entrou no board
     seria contado como sucesso. */
  if (Array.isArray(corpo.errors) && corpo.errors.length) {
    const motivo = corpo.errors.map((e) => e && e.message).filter(Boolean).join(' | ');
    throw new Error(`GraphQL: ${motivo || 'erro sem mensagem'}`);
  }

  const item = corpo.data && corpo.data.create_item;
  const id = item && item.id;
  if (!id) throw new Error('resposta sem data.create_item.id');

  /* CONFERENCIA DO QUE FOI MESMO GRAVADO
     A mutation pode devolver id sem ter preenchido uma coluna — foi o que
     aconteceu em 31/08/2026 com o dropdown de Estado. Comparamos o que
     mandamos com o que voltou e registramos apenas os IDs das colunas vazias.
     So os IDs: o conteudo e dado do visitante e nao vai para log. */
  const gravadas = new Set(
    (item.column_values || []).filter((c) => c && c.text).map((c) => c.id)
  );
  const vazias = Object.keys(columnValues).filter((c) => !gravadas.has(c));

  return { id: String(id), colunasVazias: vazias };
}

module.exports = { criarLead, vaiParaOMonday };
