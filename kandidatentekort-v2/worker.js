/**
 * kandidatentekort.nl — Cloudflare Worker v2
 * Recruitin B.V. | Wouter Arts
 *
 * Hybride flow:
 *   1. Jotform webhook → parse velden
 *   2. Lead opslaan in Supabase kt_leads (pending_ai)
 *   3. Bevestigingsmail sturen (Resend)
 *   4. Pipedrive deal aanmaken
 *   5. Slack notificatie
 *
 *   AI-rapport + Lemlist injectie → kt_ai_worker.py (cron elke 15 min)
 *
 * Secrets (wrangler secret put):
 *   SUPABASE_URL, SUPABASE_KEY
 *   RESEND_API_KEY
 *   PIPEDRIVE_API_TOKEN
 *   SLACK_WEBHOOK_URL
 *   JOTFORM_WEBHOOK_SECRET  (optioneel)
 */

const FROM_EMAIL  = "wouter@kandidatentekort.nl";
const FROM_NAME   = "Wouter Arts — Kandidatentekort.nl";
const REPLY_TO    = "warts@recruitin.nl";
const CALENDLY    = "https://calendly.com/wouter-arts-/vacature-analyse-advies";
const PHONE       = "+31 6 14 31 45 93";

const PIPEDRIVE_PIPELINE_ID = 2;
const PIPEDRIVE_STAGE_ID    = 8;

// ── Sector data ───────────────────────────────────────────────────────────────
const SECTOR_DATA = {
  "oil & gas":        { schaarste: "8.5/10", slug: "oil-gas",         display: "Oil & Gas" },
  "constructie":      { schaarste: "9.1/10", slug: "constructie",     display: "Constructie" },
  "automation":       { schaarste: "9.4/10", slug: "automation",      display: "Automation" },
  "productie":        { schaarste: "7.8/10", slug: "productie",       display: "Productie" },
  "renewable energy": { schaarste: "9.7/10", slug: "renewable-energy",display: "Renewable Energy" },
  "machinebouw":      { schaarste: "8.9/10", slug: "machinebouw",     display: "Machinebouw" },
};

// ── Main handler ─────────────────────────────────────────────────────────────
export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === "/health") {
      return json({ status: "ok", version: "2.1-hybrid", ts: new Date().toISOString() });
    }

    if (request.method !== "POST" || url.pathname !== "/webhook") {
      return json({ error: "Not found" }, 404);
    }

    let payload;
    try {
      const ct = request.headers.get("content-type") || "";
      if (ct.includes("application/x-www-form-urlencoded")) {
        const text = await request.text();
        payload = parseJotformPayload(text);
      } else {
        payload = await request.json();
      }
    } catch {
      return json({ error: "Invalid body" }, 400);
    }

    // Valideer secret (optioneel)
    if (env.JOTFORM_WEBHOOK_SECRET) {
      const sig = request.headers.get("X-Webhook-Secret") || payload.secret;
      if (sig !== env.JOTFORM_WEBHOOK_SECRET) return json({ error: "Unauthorized" }, 401);
    }

    // Veld-extractie (Jotform en directe JSON)
    const naam     = payload.naam     || payload.q1_naam  || payload.name  || "";
    const email    = payload.email    || payload.q2_email || "";
    const telefoon = payload.telefoon || payload.q3_mobiel|| payload.phone || "";
    const bedrijf  = payload.bedrijf  || payload.company  || "";
    const functie  = payload.functie  || payload.role     || payload.q4_functie || "";
    const sector   = payload.sector   || payload.q5_sector|| "";
    const regio    = payload.regio    || payload.q6_regio || "";
    const file_url = payload.file_url || payload.vacature || extractFileUrl(payload) || null;

    if (!email || !bedrijf) {
      return json({ error: "email en bedrijf zijn verplicht" }, 400);
    }

    const sectorInfo = SECTOR_DATA[sector?.toLowerCase()] || {
      schaarste: "8/10", slug: "nvt", display: sector || "Techniek"
    };
    const campagne = `KT_${toCampagneSlug(sectorInfo.slug)}_${yyyymm()}`;
    const ts       = new Date().toISOString();

    console.log(`[${ts}] Lead: ${bedrijf} | ${functie} | ${sector} | ${email}`);

    // Parallel: Supabase opslaan + Pipedrive deal
    const [supabaseId, pipedriveId] = await Promise.all([
      slaOpInSupabase(env, { naam, email, telefoon, bedrijf, functie, sector: sectorInfo.display, regio, file_url, campagne }),
      maakPipedriveDeal(env, { naam, email, bedrijf, functie, sector: sectorInfo.display, regio, campagne }),
    ]);

    // 1. Resend: directe bevestigingsmail (seconden)
    let emailSent = false;
    if (email.includes("@")) {
      emailSent = await stuurBevestigingsmail(env, { naam, email, bedrijf, functie, sector: sectorInfo.display, regio, sectorInfo, file_url });
    }

    // Slack notificatie
    const fileStatus = file_url ? "\u2705 bestand" : "\u26a0\ufe0f geen bestand";
    await slack(env, `*Nieuwe KT aanvraag \u2014 ${bedrijf}*\nFunctie: ${functie} | ${sectorInfo.display} | ${regio || "-"}\nEmail: ${email} | ${fileStatus}\nPipedrive: ${pipedriveId || "err"} | Resend: ${emailSent ? "\u2705" : "\u274c"}\n_Analyse + Lemlist via cron_`);

    return json({ ok: true, campagne, supabase_id: supabaseId, pipedrive: pipedriveId, email_sent: emailSent });
  }
};

// ── Lemlist directe injectie ─────────────────────────────────────────────────
async function injectInLemlist(env, { email, voornaam, achternaam, bedrijf, functie, sector, campagne }) {
  const campaignId = env.LEMLIST_CAMPAIGN_ID;
  const apiKey     = env.LEMLIST_API_KEY;
  if (!campaignId || !apiKey) { console.error("Lemlist secrets ontbreken"); return false; }
  try {
    const resp = await fetch(`https://api.lemlist.com/api/campaigns/${campaignId}/leads/${encodeURIComponent(email)}`, {
      method: "POST",
      headers: {
        "Content-Type":  "application/json",
        "Authorization": `Basic ${btoa(`:${apiKey}`)}`,
      },
      body: JSON.stringify({
        firstName:   voornaam,
        lastName:    achternaam,
        companyName: bedrijf,
        functie,
        sector,
        campagne,
      }),
    });
    if (resp.ok || resp.status === 409) { // 409 = al in campagne
      console.log(`Lemlist OK: ${email} → ${campaignId}`);
      return true;
    }
    console.error("Lemlist fout:", resp.status, await resp.text());
    return false;
  } catch (e) {
    console.error("Lemlist exception:", e.message);
    return false;
  }
}

// ── Supabase lead opslaan ────────────────────────────────────────────────────
async function slaOpInSupabase(env, { naam, email, telefoon, bedrijf, functie, sector, regio, file_url, campagne }) {
  if (!env.SUPABASE_URL || !env.SUPABASE_KEY) return null;
  const [first_name, ...rest] = (naam || "").split(" ");
  const last_name = rest.join(" ");
  try {
    const resp = await fetch(`${env.SUPABASE_URL}/rest/v1/kt_leads`, {
      method: "POST",
      headers: {
        "apikey":        env.SUPABASE_KEY,
        "Authorization": `Bearer ${env.SUPABASE_KEY}`,
        "Content-Type":  "application/json",
        "Prefer":        "return=representation",
      },
      body: JSON.stringify({
        first_name, last_name, email,
        phone:    telefoon || "",
        file_url: file_url || null,
        status:   "pending_ai",
        source:   `kandidatentekort-jotform|${campagne}`,
      }),
    });
    if (resp.ok) {
      const data = await resp.json();
      return data[0]?.id || null;
    }
    console.error("Supabase fout:", await resp.text());
    return null;
  } catch (e) {
    console.error("Supabase exception:", e.message);
    return null;
  }
}

// ── Bevestigingsmail ─────────────────────────────────────────────────────────
async function stuurBevestigingsmail(env, { naam, email, bedrijf, functie, sector, regio, sectorInfo, file_url }) {
  if (!env.RESEND_API_KEY) return false;

  const voornaam   = naam ? naam.split(" ")[0] : "daar";
  const fileBlok   = file_url
    ? `<p style="background:#f0fdf4;border-left:3px solid #22c55e;padding:12px 16px;border-radius:4px;margin:16px 0;">✅ Je vacature is ontvangen en staat in de wachtrij voor analyse.</p>`
    : `<p style="background:#fef9ec;border-left:3px solid #f59e0b;padding:12px 16px;border-radius:4px;margin:16px 0;">⚠️ We hebben nog geen vacaturetekst ontvangen. Stuur die gerust als reply op deze mail.</p>`;

  const html = `<!DOCTYPE html>
<html lang="nl">
<head><meta charset="UTF-8"><style>
  body{font-family:Arial,sans-serif;background:#f4f4f4;margin:0;padding:0}
  .wrap{max-width:620px;margin:40px auto;background:#fff;border-radius:8px;overflow:hidden}
  .header{background:#060708;padding:28px 40px}
  .logo{color:#fff;font-size:1.1rem;font-weight:700}
  .logo span{color:#E8630A}
  .body{padding:32px 40px;color:#1a1a1a;line-height:1.7}
  h2{color:#060708;font-size:1.25rem;margin:0 0 16px}
  .steps{background:#f9f9f9;border-radius:6px;padding:20px 24px;margin:20px 0}
  .step{display:flex;align-items:flex-start;margin:8px 0;gap:12px}
  .num{background:#E8630A;color:#fff;width:24px;height:24px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:0.8rem;font-weight:700;flex-shrink:0}
  .cta-btn{display:inline-block;background:#E8630A;color:#fff;padding:13px 26px;border-radius:6px;text-decoration:none;font-weight:600;margin:8px 0}
  .footer{background:#f4f4f4;padding:18px 40px;font-size:0.8rem;color:#888;text-align:center}
</style></head>
<body><div class="wrap">
  <div class="header"><div class="logo">kandidaten<span>tekort</span>.nl</div></div>
  <div class="body">
    <h2>We zijn aan de slag, ${voornaam}!</h2>
    <p>We hebben je aanvraag ontvangen voor <strong>${functie}</strong> bij <strong>${bedrijf}</strong> in de <strong>${sector}</strong> sector (regio: ${regio || "Nederland"}).</p>
    ${fileBlok}
    <div class="steps">
      <p style="margin:0 0 12px;font-weight:600">Wat er nu gebeurt:</p>
      <div class="step"><div class="num">1</div><div>Ons systeem filtert clichés weg en benchmarkt jouw voorwaarden tegen regionale concurrenten.</div></div>
      <div class="step"><div class="num">2</div><div>Je ontvangt <strong>binnen 24 uur</strong> een eerlijk wervingsrapport én een compleet herschreven, wervende vacaturetekst apart per mail.</div></div>
      <div class="step"><div class="num">3</div><div>Binnen <strong>24 uur</strong> plannen we vrijblijvend een contactmoment in om te bespreken waar je het meeste talent misloopt.</div></div>
    </div>
    <p>Wil je alvast een gesprek inplannen?</p>
    <a href="${CALENDLY}" class="cta-btn">Plan gratis vacature-analyse →</a>
    <p style="margin-top:28px;font-size:0.9rem;color:#555">Met vriendelijke groet,<br><strong>Wouter Arts</strong><br>Recruitin B.V. | Doesburg<br><a href="tel:${PHONE.replace(/\s/g,'')}" style="color:#E8630A">${PHONE}</a></p>
  </div>
  <div class="footer">kandidatentekort.nl · Recruitin B.V. · Doesburg · <a href="https://recruitin.nl" style="color:#E8630A">recruitin.nl</a></div>
</div></body></html>`;

  try {
    const resp = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${env.RESEND_API_KEY}` },
      body: JSON.stringify({
        from:     `${FROM_NAME} <${FROM_EMAIL}>`,
        to:       [email],
        reply_to: REPLY_TO,
        subject:  `✅ Aanvraag ontvangen — ${bedrijf} | Analyseresultaat volgt`,
        html,
        tags: [{ name: "type", value: "bevestiging" }, { name: "sector", value: sector }],
      }),
    });
    return resp.ok;
  } catch (e) {
    console.error("Resend fout:", e.message);
    return false;
  }
}

// ── Pipedrive deal ────────────────────────────────────────────────────────────
async function maakPipedriveDeal(env, { naam, email, bedrijf, functie, sector, regio, campagne }) {
  if (!env.PIPEDRIVE_API_TOKEN) return null;
  const base    = "https://api.pipedrive.com/v1";
  const headers = { "Content-Type": "application/json" };
  const token   = `?api_token=${env.PIPEDRIVE_API_TOKEN}`;
  try {
    let orgId = null;
    const orgSearch = await fetch(`${base}/organizations/search${token}&term=${encodeURIComponent(bedrijf)}&limit=1`).then(r => r.json());
    if (orgSearch.data?.items?.length > 0) {
      orgId = orgSearch.data.items[0].item.id;
    } else {
      const orgCreate = await fetch(`${base}/organizations${token}`, {
        method: "POST", headers, body: JSON.stringify({ name: bedrijf }),
      }).then(r => r.json());
      orgId = orgCreate.data?.id;
    }
    let personId = null;
    if (naam || email) {
      const personData = { name: naam || bedrijf };
      if (email) personData.email = [{ value: email, primary: true }];
      if (orgId) personData.org_id = orgId;
      const personCreate = await fetch(`${base}/persons${token}`, {
        method: "POST", headers, body: JSON.stringify(personData),
      }).then(r => r.json());
      personId = personCreate.data?.id;
    }
    const dealData = {
      title:       `${bedrijf} — ${functie} (${sector})`,
      pipeline_id: PIPEDRIVE_PIPELINE_ID,
      stage_id:    PIPEDRIVE_STAGE_ID,
      status:      "open",
    };
    if (orgId)    dealData.org_id    = orgId;
    if (personId) dealData.person_id = personId;
    const dealResp = await fetch(`${base}/deals${token}`, {
      method: "POST", headers, body: JSON.stringify(dealData),
    }).then(r => r.json());
    const dealId = dealResp.data?.id;
    if (dealId) {
      await fetch(`${base}/notes${token}`, {
        method: "POST", headers,
        body: JSON.stringify({ content: `Sector: ${sector}\nFunctie: ${functie}\nRegio: ${regio || "-"}\nCampagne: ${campagne}\nBron: kandidatentekort.nl`, deal_id: dealId }),
      });
    }
    return dealId;
  } catch (e) {
    console.error("Pipedrive fout:", e.message);
    return null;
  }
}

// ── Slack notificatie ────────────────────────────────────────────────────────
async function slack(env, text) {
  if (!env.SLACK_WEBHOOK_URL) return;
  try {
    await fetch(env.SLACK_WEBHOOK_URL, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
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

function extractFileUrl(payload) {
  // Jotform file upload fields hebben vaak namen als q4_upload...
  for (const [key, val] of Object.entries(payload)) {
    if (key.toLowerCase().includes("upload") || key.toLowerCase().includes("bestand") || key.toLowerCase().includes("vacature")) {
      if (Array.isArray(val) && val.length > 0) return val[0];
      if (typeof val === "string" && val.startsWith("http")) return val;
    }
  }
  return null;
}

function parseJotformPayload(formBody) {
  const params = new URLSearchParams(formBody);
  const obj = {};
  for (const [key, val] of params.entries()) {
    try { obj[key] = JSON.parse(val); } catch { obj[key] = val; }
  }
  // Probeer rawRequest te parsen als Jotform dat stuurt
  if (obj.rawRequest && typeof obj.rawRequest === "string") {
    try {
      const raw = JSON.parse(obj.rawRequest);
      return { ...obj, ...raw };
    } catch { /* ignore */ }
  }
  return obj;
}
