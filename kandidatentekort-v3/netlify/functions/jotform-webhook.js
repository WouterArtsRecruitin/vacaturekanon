// netlify/functions/jotform-webhook.js
// Netlify Function — vervangt api/jotform-webhook.js
// Route: https://kandidatentekort.nl/.netlify/functions/jotform-webhook
// Jotform webhook URL verwijst naar bovenstaand pad

exports.handler = async function (event, context) {
    if (event.httpMethod !== 'POST') {
        return { statusCode: 405, body: JSON.stringify({ error: 'Alleen POST toegestaan' }) };
    }

    console.log("📥 Jotform webhook:", new Date().toISOString());

    try {
        let bodyData = {};

        // Parse body (kan JSON of URL-encoded zijn)
        const contentType = (event.headers['content-type'] || '').toLowerCase();
        if (contentType.includes('application/json')) {
            bodyData = JSON.parse(event.body || '{}');
        } else {
            bodyData = Object.fromEntries(new URLSearchParams(event.body || ''));
        }

        // Jotform stuurt data soms in rawRequest property
        if (bodyData.rawRequest) {
            try {
                bodyData = typeof bodyData.rawRequest === 'string'
                    ? JSON.parse(bodyData.rawRequest)
                    : bodyData.rawRequest;
            } catch (e) { /* keep as is */ }
        }

        // Log volledige payload voor debuggen
        console.log("📦 Raw bodyData keys:", Object.keys(bodyData).join(', '));

        // ── UNIVERSELE VELDDETECTIE ────────────────────────────────────────
        // Jotform gebruikt q{N}_{naam} syntax — veldnummer varieert per form
        let first_name = 'Onbekend', last_name = '', email = '', phone = '', file_url = null;

        for (const [key, val] of Object.entries(bodyData)) {
            const k = key.toLowerCase();

            // Naam (fullname type: object met .first/.last ÓÓÓF gewone string)
            if ((k.includes('naam') || k.includes('name')) && !k.includes('company') && !k.includes('bedrijf')) {
                if (val && typeof val === 'object') {
                    first_name = val.first || val.voornaam || val['first name'] || first_name;
                    last_name  = val.last  || val.achternaam || val['last name']  || last_name;
                } else if (typeof val === 'string' && val.trim()) {
                    const parts = val.trim().split(' ');
                    first_name = parts[0] || first_name;
                    last_name  = parts.slice(1).join(' ') || last_name;
                }
            }

            // Email
            if ((k.includes('email') || k.includes('mail')) && typeof val === 'string' && val.includes('@')) {
                email = val.trim();
            }

            // Telefoon / mobiel
            if ((k.includes('mobiel') || k.includes('phone') || k.includes('telefoon') || k.includes('tel')) && !email) {
                if (typeof val === 'string' && val.trim()) phone = val.trim();
                else if (val && typeof val === 'object') phone = val.full || val.phone || JSON.stringify(val);
            }
            if ((k.includes('mobiel') || k.includes('phone') || k.includes('telefoon') || k.includes('tel')) && typeof val === 'string') {
                phone = val.trim() || phone;
            }

            // Bestand (file upload)
            if (k.includes('upload') || k.includes('vacature') || k.includes('bijlage') || k.includes('bestand') || k.includes('file')) {
                if (Array.isArray(val) && val.length > 0) file_url = val[0];
                else if (typeof val === 'string' && val.startsWith('http')) file_url = val;
            }
        }

        // Fallback als email nog leeg is — check alle strings op @
        if (!email) {
            for (const val of Object.values(bodyData)) {
                if (typeof val === 'string' && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val)) {
                    email = val; break;
                }
            }
        }

        email = email || 'onbekend@kandidatentekort.nl';
        console.log(`✅ Lead: ${first_name} ${last_name} | ${email} | File: ${file_url}`);

        // ── SUPABASE INSERT ────────────────────────────────────────────────
        const supabaseUrl = process.env.SUPABASE_URL;
        const supabaseKey = process.env.SUPABASE_KEY;

        if (!supabaseUrl || !supabaseKey) {
            console.error('❌ Supabase credentials ontbreken!');
            return { statusCode: 500, body: JSON.stringify({ error: 'Config error' }) };
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
                first_name, last_name, email, phone, file_url,
                status: 'pending_ai',
                source: 'kandidatentekort-v3-jotform'
            })
        });

        if (!dbResponse.ok) {
            const err = await dbResponse.text();
            console.error('❌ Supabase fout:', err);
            return { statusCode: 502, body: JSON.stringify({ error: `DB Error: ${err}` }) };
        }

        console.log('🚀 Lead ingevoerd in kt_leads!');

        // ── RESEND BEVESTIGINGSMAIL ────────────────────────────────────────
        // Direct na Supabase insert — Lemlist pakt later over met rapport.
        // ──────────────────────────────────────────────────────────────────
        const resendKey = process.env.RESEND_API_KEY;

        if (resendKey && email && !email.startsWith('onbekend@')) {
            const voornaam = (first_name && first_name !== 'Onbekend') ? first_name.split(' ')[0] : 'daar';

            const confirmHtml = `<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:30px 15px;">
<table width="600" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 15px rgba(0,0,0,.06);">

<tr><td style="background:#0F172A;padding:28px 40px;">
<table><tr>
<td><div style="width:44px;height:44px;background:#E8630A;border-radius:22px;text-align:center;font-size:22px;font-weight:900;color:#fff;line-height:44px;">K</div></td>
<td style="padding-left:14px;">
<p style="margin:0;color:#fff;font-size:17px;font-weight:700;">Kandidatentekort.nl</p>
<p style="margin:2px 0 0;color:#94A3B8;font-size:11px;letter-spacing:1px;text-transform:uppercase;">Vacature Intelligence &mdash; Door Recruitin B.V.</p>
</td></tr></table>
</td></tr>

<tr><td style="padding:38px 40px 28px;">
<p style="font-size:22px;font-weight:800;color:#0F172A;margin:0 0 14px;">Hoi ${voornaam}, je vacature is ontvangen ✅</p>
<p style="font-size:15px;color:#4B5563;line-height:1.8;margin:0 0 28px;">
Onze analyse-engine gaat nu direct aan de slag. <strong>Binnen 24 uur</strong> ontvang je een volledig, persoonlijk rapport in je inbox.
</p>

<table width="100%" cellpadding="0" cellspacing="0" style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;margin-bottom:28px;">
<tr><td style="padding:24px 28px;">
<p style="margin:0 0 16px;font-size:13px;font-weight:700;color:#64748B;text-transform:uppercase;letter-spacing:1px;">Wat je ontvangt:</p>

<table width="100%" style="margin-bottom:12px;"><tr>
<td width="36" valign="top"><div style="width:30px;height:30px;background:#E8630A;border-radius:15px;text-align:center;color:#fff;font-weight:700;font-size:13px;line-height:30px;">1</div></td>
<td style="padding-left:12px;font-size:14px;color:#1F2937;line-height:1.5;"><strong>Executive Scorecard</strong><br><span style="color:#6B7280;">8-dimensionele analyse van je vacaturetekst</span></td>
</tr></table>

<table width="100%" style="margin-bottom:12px;"><tr>
<td width="36" valign="top"><div style="width:30px;height:30px;background:#E8630A;border-radius:15px;text-align:center;color:#fff;font-weight:700;font-size:13px;line-height:30px;">2</div></td>
<td style="padding-left:12px;font-size:14px;color:#1F2937;line-height:1.5;"><strong>Herschreven vacaturetekst</strong><br><span style="color:#6B7280;">Klaar om morgen live te zetten &mdash; in storytelling stijl.</span></td>
</tr></table>

<table width="100%"><tr>
<td width="36" valign="top"><div style="width:30px;height:30px;background:#E8630A;border-radius:15px;text-align:center;color:#fff;font-weight:700;font-size:13px;line-height:30px;">3</div></td>
<td style="padding-left:12px;font-size:14px;color:#1F2937;line-height:1.5;"><strong>30-dagen wervingsroadmap</strong><br><span style="color:#6B7280;">Concrete quick wins voor meer sollicitaties deze maand.</span></td>
</tr></table>
</td></tr></table>

<p style="font-size:14px;color:#6B7280;line-height:1.7;margin:0;">
Vragen? Bel of WhatsApp Wouter direct:
<a href="tel:+31614314593" style="color:#E8630A;font-weight:700;text-decoration:none;">+31 6 1431 4593</a>
</p>
</td></tr>

<tr><td style="background:#0F172A;padding:18px 40px;text-align:center;">
<p style="margin:0;color:#475569;font-size:11px;">© 2026 Recruitin B.V. &middot; Kandidatentekort.nl &middot; Doesburg</p>
</td></tr>

</table></td></tr></table>
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

        return {
            statusCode: 200,
            body: JSON.stringify({ succes: true, email })
        };

    } catch (e) {
        console.error('❌ Crash:', e.message);
        return {
            statusCode: 500,
            body: JSON.stringify({ error: `Crash: ${e.message}` })
        };
    }
};
