/**
 * kandidatentekort.nl — Cloudflare Worker v2
 * Recruitin B.V. | Wouter Arts
 *
 * Flow: Jotform submit → Claude rapport → Pipedrive deal → Resend email
 *
 * Env vars (set via wrangler secret put):
 *   ANTHROPIC_API_KEY
 *   PIPEDRIVE_API_TOKEN
 *   RESEND_API_KEY
 *   JOTFORM_WEBHOOK_SECRET   (optioneel, voor validatie)
 *   META_PIXEL_ID            (voor bevestigingspagina)
 *   SLACK_WEBHOOK_URL        (optioneel, voor notificaties)
 */

// ── Sector data ───────────────────────────────────────────────────────────────
const SECTOR_DATA = {
  "oil & gas":        { schaarste: "8.5/10", slug: "oil-gas",        display: "Oil & Gas" },
  "constructie":      { schaarste: "9.1/10", slug: "constructie",    display: "Constructie" },
  "automation":       { schaarste: "9.4/10", slug: "automation",     display: "Automation" },
  "productie":        { schaarste: "7.8/10", slug: "productie",      display: "Productie" },
  "renewable energy": { schaarste: "9.7/10", slug: "renewable-energy", display: "Renewable Energy" },
  "machinebouw":      { schaarste: "8.9/10", slug: "machinebouw",    display: "Machinebouw" },
};

const PIPEDRIVE_PIPELINE_ID = 2;
const PIPEDRIVE_STAGE_ID    = 8;
const FROM_EMAIL            = "wouter@recruitin.nl";
const FROM_NAME             = "Wouter Arts — Recruitin";
const REPLY_TO              = "wouter@recruitin.nl";

// ── Main handler ─────────────────────────────────────────────────────────────
export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // Health check
    if (url.pathname === "/health") {
      return json({ status: "ok", version: "2.0", ts: new Date().toISOString() });
    }

    // Alleen POST /webhook accepteren
    if (request.method !== "POST" || url.pathname !== "/webhook") {
      return json({ error: "Not found" }, 404);
    }

    let payload;
    try {
      payload = await request.json();
    } catch {
      return json({ error: "Invalid JSON" }, 400);
    }

    // Verplichte velden
    const { sector, functie, bedrijf, regio, email, naam } = payload;
    if (!sector || !functie || !bedrijf) {
      return json({ error: "sector, functie en bedrijf zijn verplicht" }, 400);
    }

    // Valideer Jotform secret (optioneel)
    if (env.JOTFORM_WEBHOOK_SECRET) {
      const sig = request.headers.get("X-Webhook-Secret") || payload.secret;
      if (sig !== env.JOTFORM_WEBHOOK_SECRET) {
        return json({ error: "Unauthorized" }, 401);
      }
    }

    const sectorInfo = SECTOR_DATA[sector.toLowerCase()] || {
      schaarste: "8/10", slug: sector.toLowerCase().replace(/\s+/g, "-"), display: sector
    };
    const campagneNaam = `KT_${toCampagneSlug(sectorInfo.slug)}_${yyyymm()}`;
    const ts           = new Date().toISOString();

    console.log(`[${ts}] Inkomend: ${bedrijf} | ${functie} | ${sector} | ${regio}`);

    // Parallel: genereer rapport + maak Pipedrive deal
    const [rapport, pipedriveId] = await Promise.all([
      genRapport(env, { sector: sectorInfo.display, functie, bedrijf, regio, sectorInfo }),
      maakPipedriveDeal(env, { sector: sectorInfo.display, functie, bedrijf, regio, email, naam, campagneNaam }),
    ]);

    console.log(`[OK] Rapport gegenereerd (${rapport.length} chars), Pipedrive deal: ${pipedriveId}`);

    // Stuur email via Resend
    let emailSent = false;
    if (email && email.includes("@")) {
      emailSent = await stuurEmail(env, { naam, email, bedrijf, functie, sector: sectorInfo.display, regio, rapport, campagneNaam });
    }

    // Slack notificatie
    await slack(env, `*Nieuwe aanvraag — ${bedrijf}*\nFunctie: ${functie} | Sector: ${sectorInfo.display} | Regio: ${regio || "-"}\nEmail: ${emailSent ? "verstuurd" : "overgeslagen"} | Pipedrive: ${pipedriveId || "fout"}\nCampagne: ${campagneNaam}`);

    return json({
      ok:          true,
      campagne:    campagneNaam,
      pipedrive:   pipedriveId,
      email_sent:  emailSent,
      rapport_len: rapport.length,
    });
  }
};

// ── Claude rapport generatie ─────────────────────────────────────────────────
async function genRapport(env, { sector, functie, bedrijf, regio, sectorInfo }) {
  const prompt = `Je bent recruitment marktanalist voor Recruitin B.V. in Nederland.

Genereer een beknopt maar overtuigend arbeidsmarktrapport voor:
- Bedrijf: ${bedrijf}
- Functie: ${functie}
- Sector: ${sector}
- Regio: ${regio || "Nederland"}
- Schaarste index: ${sectorInfo.schaarste}

Het rapport bevat:
1. **Marktoverzicht** (3-4 zinnen over schaarste van ${functie} in ${sector})
2. **Doorlooptijd** (realistische verwachting in weken)
3. **Concurrentiepositie** (wat doet de markt, wat moet ${bedrijf} bieden)
4. **Top 3 aanbevelingen** (concrete acties voor ${bedrijf})
5. **Recruitin aanpak** (hoe wij dit oplossen — kort, geen harde verkoop)

Toon: zakelijk, data-gedreven, direct. Max 350 woorden. Schrijf in jij-vorm naar de lezer.
Begin direct met het rapport — geen "Beste..." aanhef.`;

  const resp = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type":         "application/json",
      "x-api-key":            env.ANTHROPIC_API_KEY,
      "anthropic-version":    "2023-06-01",
    },
    body: JSON.stringify({
      model:      "claude-haiku-4-5-20251001",
      max_tokens: 600,
      messages:   [{ role: "user", content: prompt }],
    }),
  });

  if (!resp.ok) {
    console.error("Claude fout:", resp.status, await resp.text());
    return fallbackRapport({ sector, functie, bedrijf, regio, sectorInfo });
  }

  const data = await resp.json();
  return data.content?.[0]?.text || fallbackRapport({ sector, functie, bedrijf, regio, sectorInfo });
}

function fallbackRapport({ sector, functie, bedrijf, regio, sectorInfo }) {
  return `## Arbeidsmarktanalyse — ${bedrijf}

De schaarste van ${functie} professionals in de ${sector} sector bedraagt ${sectorInfo.schaarste} op onze index. In regio ${regio || "Nederland"} is de vraag de afgelopen 12 maanden met 34% gestegen terwijl het aanbod gelijk bleef.

**Gemiddelde doorlooptijd:** 8-14 weken bij traditioneel werven.

**Onze aanpak:** Via gerichte LinkedIn sourcing en Meta Ads campagnes bereiken wij passieve kandidaten die niet actief zoeken maar wel openstaan voor een stap. Resultaat: gemiddeld 3 gekwalificeerde kandidaten binnen 4 weken.

Wij nemen binnen 24 uur contact met je op om de mogelijkheden te bespreken.`;
}

// ── Pipedrive deal aanmaken ──────────────────────────────────────────────────
async function maakPipedriveDeal(env, { sector, functie, bedrijf, regio, email, naam, campagneNaam }) {
  if (!env.PIPEDRIVE_API_TOKEN) return null;

  const base = "https://api.pipedrive.com/v1";
  const headers = { "Content-Type": "application/json" };
  const token = `?api_token=${env.PIPEDRIVE_API_TOKEN}`;

  try {
    // Zoek of maak organisatie
    let orgId = null;
    const orgSearch = await fetch(`${base}/organizations/search${token}&term=${encodeURIComponent(bedrijf)}&limit=1`).then(r => r.json());
    if (orgSearch.data?.items?.length > 0) {
      orgId = orgSearch.data.items[0].item.id;
    } else {
      const orgCreate = await fetch(`${base}/organizations${token}`, {
        method: "POST",
        headers,
        body: JSON.stringify({ name: bedrijf }),
      }).then(r => r.json());
      orgId = orgCreate.data?.id;
    }

    // Zoek of maak persoon
    let personId = null;
    if (naam || email) {
      const personData = { name: naam || bedrijf };
      if (email) personData.email = [{ value: email, primary: true }];
      if (orgId) personData.org_id = orgId;
      const personCreate = await fetch(`${base}/persons${token}`, {
        method: "POST",
        headers,
        body: JSON.stringify(personData),
      }).then(r => r.json());
      personId = personCreate.data?.id;
    }

    // Maak deal
    const dealData = {
      title:       `${bedrijf} — ${functie} (${sector})`,
      pipeline_id: PIPEDRIVE_PIPELINE_ID,
      stage_id:    PIPEDRIVE_STAGE_ID,
      status:      "open",
    };
    if (orgId)    dealData.org_id    = orgId;
    if (personId) dealData.person_id = personId;

    const dealResp = await fetch(`${base}/deals${token}`, {
      method: "POST",
      headers,
      body: JSON.stringify(dealData),
    }).then(r => r.json());

    const dealId = dealResp.data?.id;

    // Voeg notitie toe met campagne info
    if (dealId) {
      await fetch(`${base}/notes${token}`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          content:  `Sector: ${sector}\nFunctie: ${functie}\nRegio: ${regio || "-"}\nCampagne: ${campagneNaam}\nBron: kandidatentekort.nl`,
          deal_id:  dealId,
        }),
      });
    }

    return dealId;
  } catch (e) {
    console.error("Pipedrive fout:", e.message);
    return null;
  }
}

// ── Resend email ─────────────────────────────────────────────────────────────
async function stuurEmail(env, { naam, email, bedrijf, functie, sector, regio, rapport, campagneNaam }) {
  if (!env.RESEND_API_KEY) return false;

  const voornaam = naam ? naam.split(" ")[0] : "daar";
  const html = `<!DOCTYPE html>
<html lang="nl">
<head><meta charset="UTF-8"><style>
  body { font-family: 'DM Sans', Arial, sans-serif; background: #f4f4f4; margin: 0; padding: 0; }
  .wrap { max-width: 620px; margin: 40px auto; background: #fff; border-radius: 8px; overflow: hidden; }
  .header { background: #060708; padding: 32px 40px; }
  .logo { color: #fff; font-size: 1.1rem; font-weight: 700; }
  .logo span { color: #E8630A; }
  .body { padding: 36px 40px; color: #1a1a1a; line-height: 1.7; }
  h2 { color: #060708; font-size: 1.3rem; margin: 0 0 16px; }
  .rapport { background: #f9f9f9; border-left: 3px solid #E8630A; padding: 20px 24px; border-radius: 4px; margin: 24px 0; white-space: pre-wrap; font-size: 0.95rem; }
  .cta-btn { display: inline-block; background: #E8630A; color: #fff; padding: 14px 28px; border-radius: 6px; text-decoration: none; font-weight: 600; margin: 8px 0; }
  .footer { background: #f4f4f4; padding: 20px 40px; font-size: 0.8rem; color: #888; text-align: center; }
</style></head>
<body><div class="wrap">
  <div class="header"><div class="logo">kandidaten<span>tekort</span>.nl</div></div>
  <div class="body">
    <h2>Jouw gratis arbeidsmarktanalyse — ${bedrijf}</h2>
    <p>Hoi ${voornaam},</p>
    <p>Bedankt voor je aanvraag. Hieronder vind je de analyse voor de positie <strong>${functie}</strong> in de <strong>${sector}</strong> sector.</p>
    <div class="rapport">${rapport.replace(/\n/g, "<br>").replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")}</div>
    <p>Wil je bespreken hoe we dit concreet aanpakken voor ${bedrijf}?</p>
    <a href="https://calendly.com/recruitin/intake" class="cta-btn">Plan een gesprek →</a>
    <p style="margin-top:32px;font-size:0.9rem;color:#555;">Met vriendelijke groet,<br><strong>Wouter Arts</strong><br>Recruitin B.V. | Doesburg<br><a href="tel:+31612345678" style="color:#E8630A;">+31 6 ...</a></p>
  </div>
  <div class="footer">kandidatentekort.nl · Recruitin B.V. · Doesburg · <a href="https://recruitin.nl" style="color:#E8630A;">recruitin.nl</a></div>
</div></body></html>`;

  try {
    const resp = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        "Content-Type":  "application/json",
        "Authorization": `Bearer ${env.RESEND_API_KEY}`,
      },
      body: JSON.stringify({
        from:     `${FROM_NAME} <${FROM_EMAIL}>`,
        to:       [email],
        reply_to: REPLY_TO,
        subject:  `Jouw gratis arbeidsmarktanalyse — ${bedrijf}`,
        html,
        tags: [
          { name: "campagne", value: campagneNaam },
          { name: "sector",   value: sector },
        ],
      }),
    });
    if (!resp.ok) {
      console.error("Resend fout:", resp.status, await resp.text());
      return false;
    }
    return true;
  } catch (e) {
    console.error("Resend exception:", e.message);
    return false;
  }
}

// ── Slack notificatie ────────────────────────────────────────────────────────
async function slack(env, text) {
  if (!env.SLACK_WEBHOOK_URL) return;
  try {
    await fetch(env.SLACK_WEBHOOK_URL, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ text }),
    });
  } catch { /* stil falen */ }
}

// ── Helpers ──────────────────────────────────────────────────────────────────
function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
  });
}

function yyyymm() {
  const d = new Date();
  return `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, "0")}`;
}

function toCampagneSlug(slug) {
  return slug.split("-").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join("");
}
