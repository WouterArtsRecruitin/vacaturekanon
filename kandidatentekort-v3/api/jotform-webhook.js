export default async function handler(req, res) {
    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'We accepteren alleen POST webhooks van Jotform.' });
    }

    console.log("📥 Nieuwe webhook hit van JotForm:", new Date().toISOString());

    try {
        let bodyData = req.body || {};
        
        // Parse de body stringify of URL params indien nodig
        if (typeof bodyData === 'string') {
            try { bodyData = JSON.parse(bodyData); } 
            catch(e) { bodyData = Object.fromEntries(new URLSearchParams(bodyData)); }
        }

        // Jotform steekt de velden vaak in een stringified JSON 'rawRequest' property.
        if (bodyData && bodyData.rawRequest) {
            try {
                bodyData = typeof bodyData.rawRequest === 'string' 
                            ? JSON.parse(bodyData.rawRequest) 
                            : bodyData.rawRequest;
            } catch (e) {
                // leave as is
            }
        }

        // --- FILTER DE JOTFORM VELDEN ---
        const first_name = bodyData?.q1_naam?.first || bodyData?.naam?.first || bodyData?.q1_naam || bodyData?.naam || "Onbekend";
        const last_name  = bodyData?.q1_naam?.last  || bodyData?.naam?.last  || "";
        const email      = bodyData?.q2_email        || bodyData?.email        || "onbekend@kandidatentekort.nl";
        const phone      = bodyData?.q3_mobiel       || bodyData?.mobiel       || "";
        
        // File upload field from Jotform
        const fileUploadData = bodyData?.q4_uploadTechnische || bodyData?.vacature || [];
        const file_url = Array.isArray(fileUploadData) && fileUploadData.length > 0
            ? fileUploadData[0]
            : (typeof fileUploadData === 'string' ? fileUploadData : null);

        console.log(`✅ Gefilterde V3 Lead: Email ${email} | Document: ${file_url}`);

        // ── STAP 1: SUPABASE INSERT ──────────────────────────────────────────────
        const supabaseUrl = process.env.SUPABASE_URL;
        const supabaseKey = process.env.SUPABASE_KEY;
        
        if (!supabaseUrl || !supabaseKey) {
            console.error("❌ Ontbrekende Supabase credentials!");
            return res.status(500).json({ error: 'Config error' });
        }

        const dbResponse = await fetch(`${supabaseUrl}/rest/v1/kt_leads`, {
            method: 'POST',
            headers: {
                'apikey': supabaseKey,
                'Authorization': `Bearer ${supabaseKey}`,
                'Content-Type': 'application/json',
                'Prefer': 'return=minimal'
            },
            body: JSON.stringify({
                first_name,
                last_name,
                email,
                phone,
                file_url,
                status: 'pending_ai',
                source: 'kandidatentekort-v3-jotform'
            })
        });

        if (!dbResponse.ok) {
            const err = await dbResponse.text();
            console.error("❌ Supabase INSERT fout:", err);
            return res.status(502).json({ error: `DB Error: ${err}` });
        }

        console.log(`🚀 Lead geinjecteerd in kt_leads!`);

        // ── STAP 2: DIRECTE BEVESTIGINGSMAIL VIA RESEND ─────────────────────────
        // Verstuurd DIRECT na Supabase insert.
        // Lemlist pakt LATER over zodra rapport + vacaturetekst klaar zijn (na 24u).
        // ────────────────────────────────────────────────────────────────────────
        const resendKey = process.env.RESEND_API_KEY;

        if (resendKey && email && !email.startsWith('onbekend@')) {
            const voornaam = (first_name && first_name !== 'Onbekend')
                ? first_name.split(' ')[0]
                : 'daar';

            const confirmHtml = `<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f3f4f6;">
<tr><td align="center" style="padding:30px 15px;">
<table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 15px rgba(0,0,0,0.06);">

  <!-- HEADER -->
  <tr><td style="background:#0F172A;padding:28px 40px;">
    <table width="100%"><tr>
      <td width="44">
        <div style="width:44px;height:44px;background:#E8630A;border-radius:22px;text-align:center;font-size:22px;font-weight:900;color:#fff;line-height:44px;">K</div>
      </td>
      <td style="padding-left:14px;">
        <p style="margin:0;color:#ffffff;font-size:17px;font-weight:700;">Kandidatentekort.nl</p>
        <p style="margin:2px 0 0;color:#94A3B8;font-size:11px;letter-spacing:1px;text-transform:uppercase;">Vacature Intelligence — Door Recruitin B.V.</p>
      </td>
    </tr></table>
  </td></tr>

  <!-- BODY -->
  <tr><td style="padding:38px 40px 28px;">
    <p style="font-size:22px;font-weight:800;color:#0F172A;margin:0 0 14px;line-height:1.3;">Hoi ${voornaam}, je vacature is ontvangen ✅</p>
    <p style="font-size:15px;color:#4B5563;line-height:1.8;margin:0 0 28px;">
      Goed nieuws — onze analyse-engine gaat nu direct aan de slag met jouw vacaturetekst. 
      <strong>Binnen 24 uur</strong> ontvang je een volledig, persoonlijk rapport in je inbox.
    </p>

    <!-- STAPPEN BOX -->
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;margin-bottom:28px;">
      <tr><td style="padding:24px 28px;">
        <p style="margin:0 0 16px;font-size:13px;font-weight:700;color:#64748B;text-transform:uppercase;letter-spacing:1px;">Wat je ontvangt:</p>

        <table width="100%" style="margin-bottom:12px;"><tr>
          <td width="36" valign="top"><div style="width:30px;height:30px;background:#E8630A;border-radius:15px;text-align:center;color:#fff;font-weight:700;font-size:13px;line-height:30px;">1</div></td>
          <td style="padding-left:12px;font-size:14px;color:#1F2937;line-height:1.5;"><strong>Executive Scorecard</strong><br><span style="color:#6B7280;">8-dimensionele analyse — waar verlies je nu technisch talent?</span></td>
        </tr></table>

        <table width="100%" style="margin-bottom:12px;"><tr>
          <td width="36" valign="top"><div style="width:30px;height:30px;background:#E8630A;border-radius:15px;text-align:center;color:#fff;font-weight:700;font-size:13px;line-height:30px;">2</div></td>
          <td style="padding-left:12px;font-size:14px;color:#1F2937;line-height:1.5;"><strong>Herschreven vacaturetekst</strong><br><span style="color:#6B7280;">Klaar om morgen live te zetten — in storytelling stijl.</span></td>
        </tr></table>

        <table width="100%"><tr>
          <td width="36" valign="top"><div style="width:30px;height:30px;background:#E8630A;border-radius:15px;text-align:center;color:#fff;font-weight:700;font-size:13px;line-height:30px;">3</div></td>
          <td style="padding-left:12px;font-size:14px;color:#1F2937;line-height:1.5;"><strong>30-dagen wervingsroadmap</strong><br><span style="color:#6B7280;">Concrete quick wins voor meer sollicitaties deze maand.</span></td>
        </tr></table>
      </td></tr>
    </table>

    <p style="font-size:14px;color:#6B7280;line-height:1.7;margin:0;">
      Vragen? Bel of WhatsApp Wouter direct: 
      <a href="tel:+31614314593" style="color:#E8630A;font-weight:700;text-decoration:none;">+31 6 1431 4593</a>
    </p>
  </td></tr>

  <!-- FOOTER -->
  <tr><td style="background:#0F172A;padding:18px 40px;text-align:center;">
    <p style="margin:0;color:#475569;font-size:11px;">© 2026 Recruitin B.V. · Kandidatentekort.nl · KvK 74603433 · Doesburg</p>
  </td></tr>

</table>
</td></tr>
</table>
</body></html>`;

            const resendResp = await fetch('https://api.resend.com/emails', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${resendKey}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    from: 'Wouter Arts <wouter@kandidatentekort.nl>',
                    to: [email],
                    reply_to: 'warts@recruitin.nl',
                    subject: `✅ Ontvangen — jouw vacature rapport is onderweg (binnen 24u)`,
                    html: confirmHtml,
                    tags: [{ name: 'type', value: 'kt-bevestiging' }]
                })
            });

            if (resendResp.ok) {
                console.log(`📧 Bevestigingsmail verzonden → ${email}`);
            } else {
                const resendErr = await resendResp.text();
                console.warn(`⚠️ Resend mislukt (niet fataal): ${resendErr}`);
            }
        }

        return res.status(200).json({ succes: true, email });

    } catch (e) {
        console.error("❌ Crash in Jotform Webhook:", e.message);
        return res.status(500).json({ error: `Crash: ${e.message}` });
    }
}
