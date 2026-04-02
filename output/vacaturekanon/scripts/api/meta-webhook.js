export default async function handler(req, res) {
  // =========================================================
  // META LEAD ADS WEBHOOK (VERCEL JS EXTRACTION)
  // Dit is de perfecte serverless Vercel Node.js opzet!
  // =========================================================

  const META_APP_SECRET = process.env.META_APP_SECRET || 'mijn_geheime_verificatie_token_beutech';
  const META_ACCESS_TOKEN = process.env.META_ACCESS_TOKEN;
  const SLACK_WEBHOOK_URL = process.env.SLACK_WEBHOOK_URL;

  // 1. META VERIFICATIE FASE (Eenmalig bij instellen in App Dashboard)
  if (req.method === 'GET') {
    const { 'hub.mode': mode, 'hub.verify_token': token, 'hub.challenge': challenge } = req.query;

    if (mode === 'subscribe' && token === META_APP_SECRET) {
      console.log('[+] Meta Webhook succesvol geverifieerd door Vercel!');
      return res.status(200).send(challenge);
    } else {
      return res.status(403).send('Verificatie mislukt');
    }
  }

  // 2. LEAD BINNENKOMST FASE (Wanneer kandidaat op 'Aanmelden' klikt)
  if (req.method === 'POST') {
    const data = req.body;
    console.log(`[INCOMING META PING]: ${JSON.stringify(data)}`);

    if (data.object === 'page') {
      for (const entry of data.entry || []) {
        for (const change of entry.changes || []) {
          if (change.field === 'leadgen') {
            const leadId = change.value?.leadgen_id;

            if (leadId) {
              console.log(`[+] Lead_id ${leadId} gedetecteerd! Fetching data bij Meta Graph API...`);
              
              // Ophalen echte velden bij Facebook Graph API
              try {
                const fbResponse = await fetch(`https://graph.facebook.com/v21.0/${leadId}?access_token=${META_ACCESS_TOKEN}`);
                const fullLeadData = await fbResponse.json();

                if (fullLeadData.field_data) {
                  // Parsen van de ingevulde velden
                  const fields = {};
                  fullLeadData.field_data.forEach(item => {
                    fields[item.name] = item.values[0];
                  });

                  const name = fields['full_name'] || 'Onbekend';
                  const phone = fields['phone_number'] || 'Onbekend';
                  const city = fields['city'] || 'Onbekend';

                  console.log(`[+] Lead verwerkt: ${name} uit ${city}`);

                  // Slack Waarschuwing sturen als URL is ingesteld!
                  if (SLACK_WEBHOOK_URL) {
                    await fetch(SLACK_WEBHOOK_URL, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({
                        text: `🚨 *NIEUWE BEUTECH LEAD BINNEN!* 🚨\n\n*Naam:* ${name}\n*Telefoon:* ${phone}\n*Woonplaats:* ${city}\n\n👉 _Bel deze kandidaat nu direct!_`
                      })
                    });
                    console.log('[+] Slack alert afgevuurd via Vercel Edge!');
                  }
                  
                  // Optioneel: Hier direct Supabase REST aanroepen via fetch()
                }
              } catch (error) {
                console.error('[!] Fout bij ophalen/sturen lead:', error);
              }
            }
          }
        }
      }
    }
    return res.status(200).json({ status: 'ok' });
  }

  // Als we hier komen, method = anders dan GET/POST
  res.setHeader('Allow', ['GET', 'POST']);
  res.status(405).end(`Method ${req.method} Not Allowed`);
}
