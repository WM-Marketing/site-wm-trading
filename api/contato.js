/* ==========================================================================
   WM Trading — api/contato.js (Vercel Serverless Function proxying to Zapier)
   ========================================================================== */

const { criarLead, vaiParaOMonday } = require('./_monday');

/* ══════════════════════════════════════════════════════════════════════════
   BARREIRAS ANTI-ROBO (31/08/2026)

   O honeypot _gotcha sozinho so pega robo que PREENCHE o formulario. Quem
   manda JSON direto para /api/contato/ nunca toca no campo-armadilha e passava
   batido — era possivel criar lead no CRM sem nunca abrir o site.

   Isto NAO substitui um CAPTCHA. Sao filtros baratos que cortam o envio
   automatizado oportunista; contra robo dedicado, so um desafio criptografico
   (Turnstile/reCAPTCHA) resolve.
   ══════════════════════════════════════════════════════════════════════════ */

/* De onde um envio legitimo pode vir. O CORS era "*", entao qualquer site
   podia disparar envios pelo navegador dos visitantes dele. */
const ORIGENS_OK = [
  'https://www.wmtrading.com.br',
  'https://wmtrading.com.br',
];
/* Deploys de preview da Vercel: o formulario precisa continuar testavel neles. */
const PREVIEW_OK = /^https:\/\/site-wm-trading-[a-z0-9-]+\.vercel\.app$/;

function origemPermitida(origem) {
  if (!origem) return false;
  return ORIGENS_OK.includes(origem) || PREVIEW_OK.test(origem);
}

/* Menos que isto nao e gente preenchendo: e script. Sete campos, um deles
   textarea — o formulario mais curto do site leva bem mais que 3 segundos. */
const MS_MINIMO = 3000;
/* Aba aberta ha mais de 12h: o carimbo perdeu o sentido, provavelmente e
   sessao esquecida. Nao barra — so nao serve de prova. */
const MS_MAXIMO = 12 * 60 * 60 * 1000;

module.exports = async function handler(req, res) {
  // CORS restrito a origem do proprio site
  const origem = req.headers.origin || '';
  if (origemPermitida(origem)) {
    res.setHeader('Access-Control-Allow-Origin', origem);
  }
  res.setHeader('Vary', 'Origin');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    res.setHeader('Allow', ['POST']);
    return res.status(405).json({ ok: false, error: 'Método não permitido.' });
  }

  try {
    const data = req.body;

    // Honeypot anti-spam check (if filled, treat as success but discard silently)
    if (data && data._gotcha) {
      console.log('Bot detected via honeypot.');
      return res.status(200).json({ ok: true });
    }

    /* ── ORIGEM ──
       Navegador manda Origin em POST, mesmo same-origin. Requisicao de script
       (curl e afins) nao manda nenhum dos dois. O Referer entra como segunda
       chance: extensao de privacidade as vezes remove um, nao os dois.
       Resposta 200 de proposito: dizer "bloqueado" ensina o robo a ajustar. */
    const referer = req.headers.referer || '';
    const origemDoReferer = referer ? (referer.match(/^https?:\/\/[^/]+/) || [''])[0] : '';
    if (!origemPermitida(origem) && !origemPermitida(origemDoReferer)) {
      console.log(`Bloqueado: origem nao permitida (origin=${origem || '-'} referer=${origemDoReferer || '-'})`);
      return res.status(200).json({ ok: true });
    }

    /* ── TEMPO DE PREENCHIMENTO ──
       O campo so existe se a pagina foi carregada de verdade (js/contact-form.js).
       Ausente ou rapido demais = script. Nao e a prova definitiva: quem sabe do
       campo consegue forjar um numero. Serve como filtro, nao como muralha. */
    const ms = Number(data._ms);
    if (!Number.isFinite(ms) || ms < 0) {
      console.log('Bloqueado: envio sem carimbo de tempo (nao passou pela pagina)');
      return res.status(200).json({ ok: true });
    }
    if (ms < MS_MINIMO) {
      console.log(`Bloqueado: preenchido em ${ms}ms, abaixo do minimo de ${MS_MINIMO}ms`);
      return res.status(200).json({ ok: true });
    }
    if (ms > MS_MAXIMO) {
      console.log(`Aviso: carimbo de ${Math.round(ms / 3600000)}h — aba antiga, envio aceito`);
    }

    // Sem registro de aceite não entra no CRM: o checkbox é obrigatório em todos
    // os formulários, então isto só barra envios adulterados ou fora do padrão.
    if (String(data.aceite_privacidade || '').toLowerCase() !== 'sim') {
      return res.status(400).json({
        ok: false,
        error: 'É necessário aceitar a Política de Privacidade para enviar os seus dados.'
      });
    }

    // Determine form type to look up specific webhook URLs
    // Example: formulario="ebook" -> ZAPIER_WEBHOOK_EBOOK
    const formType = String(data.formulario || '').replace(/[^a-z0-9]+/gi, '_').toUpperCase();
    const webhook = process.env[`ZAPIER_WEBHOOK_${formType}`] || process.env.ZAPIER_WEBHOOK_URL;

    if (!webhook) {
      console.error(`Sem webhook configurado para o formulário tipo: ${formType}`);
      return res.status(503).json({
        ok: false,
        error: 'Serviço de envio temporariamente indisponível. Configurações em andamento.'
      });
    }

    // Prova de consentimento (LGPD art. 8º, § 2º): IP e user agent só podem ser
    // lidos no servidor. Servem exclusivamente para comprovar o aceite e coibir
    // envios automatizados — declarados na Política de Privacidade (item 2.3).
    const ipBruto = req.headers['x-forwarded-for'] || req.headers['x-real-ip'] || '';
    const ip = String(ipBruto).split(',')[0].trim();
    const userAgent = String(req.headers['user-agent'] || '').slice(0, 300);

    // Standardized payload format for Zapier catch hooks
    const payload = {
      nome: data.nome || '',
      email: data.email || '',
      telefone: data.telefone || '',
      empresa: data.empresa || '',
      cargo: data.cargo || '',
      estado: data.estado || '',
      volume: data.volume || '',
      segmento: data.segmento || '',
      forma_resposta: data.forma_resposta || '',
      mensagem: data.mensagem || '',
      formulario: data.formulario || '',
      url: data.url || '',
      origem: data.origem || 'site wmtrading.com.br',
      enviado_em: new Date().toISOString(),
      // Registro de aceite — vai para campos próprios no Pipedrive
      aceite_privacidade: data.aceite_privacidade || '',
      aceite_marketing: data.aceite_marketing || 'nao',
      aceite_texto: data.aceite_texto || '',
      politica_versao: data.politica_versao || '',
      // Horario do SERVIDOR, nao do navegador. O cliente ainda manda um
      // data.aceite_em, mas ele e IGNORADO de proposito: e a prova legal do
      // consentimento (LGPD art. 8, par. 2) e relogio de visitante nao e fonte
      // confiavel. Medido em 17/08: a maquina de teste estava 110 segundos
      // adiantada, e o aceite aparecia no CRM DEPOIS do proprio envio — o que e
      // logicamente impossivel e destroi a credibilidade do registro.
      // Diferenca para enviado_em: os dois passam a ser do servidor e ficam a
      // milissegundos um do outro. Isso e esperado — o aceite e o envio sao o
      // mesmo ato, e o que importa e serem verificaveis, nao distintos.
      aceite_em: new Date().toISOString(),
      aceite_ip: ip,
      aceite_user_agent: userAgent,
      // Identidade do visitante para o join CRM x GA4 (js/utm-tracking.js).
      // wm_vid é ID de primeira parte, gerado pelo site: SEMPRE vem preenchido e
      // é a chave de join exata (sem truncar dígito, sem heurística de formato).
      // clientid e ga_session_id vêm do GA4 e podem faltar — bloqueador, cookie
      // ainda não gravado ou consentimento negado. Quando faltam, ga_status diz o
      // motivo: ok | ok_cookie | sem_cookie | sem_consentimento | sem_gtag | timeout.
      // Ausência é string VAZIA. A tag antiga do GTM gravava a string "false" e o
      // BI descartava em silêncio, sem distinguir recusa de falha técnica.
      wm_vid: data.wm_vid || '',
      ga_session_id: data.ga_session_id || '',
      ga_status: data.ga_status || '',
      // Jornada acumulada no navegador e enviada com o lead. Responde "o que este
      // cliente olhou antes de pedir contato" sem depender de GA4 nem de join —
      // o comercial le direto no negocio. paginas_vistas vem truncada nas ultimas
      // 12 (prefixo "..." quando houve corte); total_paginas conta tudo.
      paginas_vistas: data.paginas_vistas || '',
      total_paginas: data.total_paginas || '',
      total_sessoes: data.total_sessoes || '',
      dias_ate_lead: data.dias_ate_lead || '',
      primeira_visita_em: data.primeira_visita_em || '',
      // Atribuição de mídia/orgânico (preenchidos por js/utm-tracking.js)
      utm_source: data.utm_source || '',
      utm_medium: data.utm_medium || '',
      utm_campaign: data.utm_campaign || '',
      utm_term: data.utm_term || '',
      utm_content: data.utm_content || '',
      utm_source_inicial: data.utm_source_inicial || '',
      utm_campaign_inicial: data.utm_campaign_inicial || '',
      gclid: data.gclid || '',
      msclkid: data.msclkid || '',
      fbclid: data.fbclid || '',
      clientid: data.clientid || '',
      referrer_inicial: data.referrer_inicial || '',
      pagina_entrada: data.pagina_entrada || '',
    };

    // ── MONDAY: TENTATIVA, NUNCA BLOQUEIO ────────────────────────────────
    // A primeira versao (31/08/2026) tratava a falha do Monday como falha do
    // envio, devolvendo 502 antes de chamar o Zapier. Em producao isso derrubou
    // a captacao inteira: os dropdowns do board estavam praticamente vazios — o
    // de Estado so tinha "São Paulo" — entao QUALQUER lead de outro estado era
    // recusado e nao chegava nem ao Pipedrive.
    //
    // A licao: o Monday e destino ADICIONAL, e a captacao nao pode depender da
    // configuracao de um board que este repositorio nao controla. A falha e
    // registrada no log e o lead segue para o Zapier como sempre.
    //
    // Enquanto os labels nao estiverem completos no board, o item so nasce para
    // as combinacoes ja cadastradas — ver MAPA_ROTULOS e CRIAR_LABEL_SE_FALTAR
    // em api/_monday.js.
    // O formulario de e-book nao entra: ver FORMULARIOS_NO_MONDAY.
    let mondayItemId = '';
    if (vaiParaOMonday(data.formulario)) {
      try {
        const item = await criarLead(payload);
        mondayItemId = item.id;
        const vazias = (item.colunasVazias || []).join(', ');
        console.log(`Monday: item ${item.id} criado (${payload.formulario})` +
          (vazias ? ` — COLUNAS QUE NAO GRAVARAM: ${vazias}` : ' — todas as colunas gravadas'));
      } catch (erroMonday) {
        // Motivo tecnico so no log do servidor. O visitante nunca ve mensagem
        // da API, query nem token — e nao e penalizado por uma falha nossa.
        console.error('Monday: falha ao criar item —', erroMonday.message);
      }
    }
    payload.monday_item_id = mondayItemId;

    const response = await fetch(webhook, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      // Aqui sim o envio falhou de verdade: o Zapier e o destino que sustenta a
      // captacao. Se o item do Monday chegou a ser criado, reenviar duplicaria
      // — por isso o id vai no log, para conciliacao manual.
      throw new Error(`Zapier respondeu com status HTTP ${response.status}` +
        (mondayItemId ? ` (item ${mondayItemId} ja criado no Monday)` : ''));
    }

    return res.status(200).json({ ok: true });

  } catch (err) {
    console.error('Erro ao processar formulário:', err);
    return res.status(500).json({
      ok: false,
      error: 'Ocorreu um erro no servidor ao tentar enviar seus dados. Por favor, tente novamente.'
    });
  }
};
