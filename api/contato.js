/* ==========================================================================
   WM Trading — api/contato.js (Vercel Serverless Function proxying to Zapier)
   ========================================================================== */

module.exports = async function handler(req, res) {
  // CORS Headers
  res.setHeader('Access-Control-Allow-Origin', '*');
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

    // Standardized payload format for Zapier catch hooks
    const payload = {
      nome: data.nome || '',
      email: data.email || '',
      telefone: data.telefone || '',
      empresa: data.empresa || '',
      estado: data.estado || '',
      segmento: data.segmento || '',
      forma_resposta: data.forma_resposta || '',
      mensagem: data.mensagem || '',
      aceite_privacidade: data.aceite_privacidade || '',
      formulario: data.formulario || '',
      url: data.url || '',
      origem: data.origem || 'site wmtrading.com.br',
      enviado_em: new Date().toISOString(),
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

    const response = await fetch(webhook, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`Zapier respondeu com status HTTP ${response.status}`);
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
