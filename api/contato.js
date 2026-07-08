/* ==========================================================================
   WM Trading — api/contato.js
   Vercel Serverless Function: formulários do site → Pipedrive (API direta)

   Fluxo por lead:
     1. find-or-create Organização (campo "empresa", se informado)
     2. find-or-create Pessoa (busca por e-mail exato)
     3. find-or-create Label do lead (por tipo de formulário)
     4. create Lead (pessoa + org + label + owner opcional)
     5. create Note no lead (mensagem, segmento, estado, página, UTMs)

   Env vars (painel Vercel — nunca no repositório):
     PIPEDRIVE_API_TOKEN  (obrigatória)
     PIPEDRIVE_OWNER_ID   (opcional — ID do usuário dono dos leads;
                           sem ela o dono é o usuário do token)
   ========================================================================== */

const PD_API = 'https://api.pipedrive.com/v1';

// tipo de formulário (payload.formulario) -> nome da label no Pipedrive
const LEAD_LABELS = {
  contato: 'Site - Contato',
  segmentos: 'Site - Segmento',
  ebook: 'Site - E-book',
  infografico: 'Site - E-book',
  whatsapp: 'Site - WhatsApp',
};
const LABEL_COLOR = 'blue';

async function pd(path, opts, token) {
  const sep = path.includes('?') ? '&' : '?';
  const res = await fetch(`${PD_API}${path}${sep}api_token=${token}`, {
    ...opts,
    headers: { 'Content-Type': 'application/json', ...((opts && opts.headers) || {}) },
  });
  const json = await res.json().catch(() => ({}));
  if (!res.ok || json.success === false) {
    const detail = json && json.error ? json.error : `HTTP ${res.status}`;
    throw new Error(`Pipedrive ${path.split('?')[0]}: ${detail}`);
  }
  return json.data;
}

async function findOrCreateOrg(empresa, token) {
  if (!empresa) return null;
  const found = await pd(
    `/organizations/search?term=${encodeURIComponent(empresa)}&exact_match=true&limit=1`,
    {}, token
  );
  const hit = found && found.items && found.items[0];
  if (hit) return hit.item.id;
  const org = await pd('/organizations', {
    method: 'POST',
    body: JSON.stringify({ name: empresa }),
  }, token);
  return org.id;
}

async function findOrCreatePerson(data, orgId, token) {
  if (data.email) {
    const found = await pd(
      `/persons/search?term=${encodeURIComponent(data.email)}&fields=email&exact_match=true&limit=1`,
      {}, token
    );
    const hit = found && found.items && found.items[0];
    if (hit) return hit.item.id;
  }
  const person = await pd('/persons', {
    method: 'POST',
    body: JSON.stringify({
      name: data.nome || data.email || 'Lead do site',
      email: data.email ? [{ value: data.email, primary: true }] : undefined,
      phone: data.telefone ? [{ value: data.telefone, primary: true }] : undefined,
      org_id: orgId || undefined,
    }),
  }, token);
  return person.id;
}

async function findOrCreateLabel(formType, token) {
  const wanted = LEAD_LABELS[formType] || 'Site - Contato';
  try {
    const labels = (await pd('/leadLabels', {}, token)) || [];
    const hit = labels.find((l) => l.name.toLowerCase() === wanted.toLowerCase());
    if (hit) return hit.id;
    const created = await pd('/leadLabels', {
      method: 'POST',
      body: JSON.stringify({ name: wanted, color: LABEL_COLOR }),
    }, token);
    return created.id;
  } catch (err) {
    console.error('Label indisponível (lead segue sem label):', err.message);
    return null; // label é acessório — nunca derruba o lead
  }
}

const esc = (s) => String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

function buildNote(data) {
  const rows = [
    ['Formulário', data.formulario],
    ['Mensagem', data.mensagem],
    ['Segmento', data.segmento],
    ['Estado', data.estado],
    ['Forma de resposta', data.forma_resposta],
    ['Telefone', data.telefone],
    ['E-mail', data.email],
    ['Aceite de privacidade', data.aceite_privacidade],
    ['Página', data.url],
    ['UTM source', data.utm_source],
    ['UTM medium', data.utm_medium],
    ['UTM campaign', data.utm_campaign],
    ['UTM term', data.utm_term],
    ['UTM content', data.utm_content],
    ['gclid', data.gclid],
    ['msclkid', data.msclkid],
    ['Origem', data.origem],
  ].filter(([, v]) => v);
  return rows.map(([k, v]) => `<b>${k}:</b> ${esc(v)}`).join('<br>');
}

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Cache-Control', 'no-store, max-age=0');

  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') {
    res.setHeader('Allow', ['POST']);
    return res.status(405).json({ ok: false, error: 'Método não permitido.' });
  }

  const token = process.env.PIPEDRIVE_API_TOKEN;
  if (!token) {
    console.error('PIPEDRIVE_API_TOKEN não configurado na Vercel.');
    return res.status(503).json({
      ok: false,
      error: 'Serviço de envio temporariamente indisponível. Configurações em andamento.',
    });
  }

  try {
    const data = req.body || {};

    // Honeypot anti-spam: bot preencheu campo invisível -> finge sucesso e descarta
    if (data._gotcha) {
      console.log('Bot detectado via honeypot.');
      return res.status(200).json({ ok: true });
    }

    // Guarda mínima contra POST vazio direto na API
    if (!data.email && !data.telefone) {
      return res.status(400).json({ ok: false, error: 'Informe e-mail ou telefone.' });
    }

    const formType = String(data.formulario || 'contato').toLowerCase();

    const orgId = await findOrCreateOrg((data.empresa || '').trim(), token);
    const personId = await findOrCreatePerson(data, orgId, token);
    const labelId = await findOrCreateLabel(formType, token);

    const ownerId = parseInt(process.env.PIPEDRIVE_OWNER_ID, 10);
    const lead = await pd('/leads', {
      method: 'POST',
      body: JSON.stringify({
        title: `[Site] ${data.nome || data.email}${data.empresa ? ` — ${data.empresa}` : ''}`,
        person_id: personId,
        organization_id: orgId || undefined,
        label_ids: labelId ? [labelId] : undefined,
        owner_id: Number.isFinite(ownerId) ? ownerId : undefined,
      }),
    }, token);

    const note = buildNote(data);
    if (note) {
      await pd('/notes', {
        method: 'POST',
        body: JSON.stringify({ lead_id: lead.id, content: note }),
      }, token).catch((err) => console.error('Nota falhou (lead já criado):', err.message));
    }

    return res.status(200).json({ ok: true });
  } catch (err) {
    console.error('Erro ao processar formulário:', err);
    return res.status(500).json({
      ok: false,
      error: 'Ocorreu um erro no servidor ao tentar enviar seus dados. Por favor, tente novamente.',
    });
  }
};
