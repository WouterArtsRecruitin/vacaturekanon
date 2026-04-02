import os, io, requests, datetime, re, subprocess, tempfile, json
from dotenv import load_dotenv
import anthropic

load_dotenv("/Users/wouterarts/recruitin/.env", override=True)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", os.environ.get("SUPABASE_SERVICE_KEY"))
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
JOTFORM_API_KEY = os.environ.get("JOTFORM_API_KEY")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
CALENDLY = "https://calendly.com/wouter-arts-/vacature-analyse-advies"

prompt_analist = """Jij bent de meest genadeloze, scherpe senior recruitment consultant in de Nederlandse technische arbeidsmarkt (Installatietechniek, Machinebouw, Constructie, Oil/Gas).
Je combineert Intelligence Group data met 15+ jaar ervaring. (Bijv: Geen salaris = -35% conversie. Generieke tekst = -22% conversie).

## CONTEXT:
- Bedrijf: {bedrijf}
- Originele Vacaturetekst: 
{vacature_text}

## JOUW OPDRACHT:
Beoordeel deze vacature ongenuanceerd. Lever EXACT het volgende XML formaat op (gebruik precies deze tags). 

<overall_score>
6.2
</overall_score>
<score_section>
Salaris Transparantie: 2/10 - Aantrekkingskracht: 6/10 - Call-to-action: 4/10
</score_section>
<top_3_improvements>
- Eerste snoeiharde kritiekpunt of blocker (bijv. ontbreken van salaris).
- Tweede punt over gebrek aan echte technische diepgang of onduidelijke eisen.
- Derde pijnlijk generiek cliché dat er direct uit moet.
</top_3_improvements>
"""

prompt_copywriter = """Jij bent de allerbeste B2B copywriter / headhunter van Nederland voor technische profielen. Jouw specialisme: hardcore rollen voor techneuten.

## CONTEXT:
- Bedrijf: {bedrijf}
- Top Verbeterpunten (van de Analist): 
{verbeterpunten}
- Originele tekst:
{vacature_text}

## JOUW EXPERTISE EN REGELS (V2.0 MARKT):
1. **Salaris & Voorwaarden:** Techneuten negeren 'marktconform'. Voeg specificaties toe (bijv. "€3.500 - €4.500") en secundaire voorwaarden (bus, merk gereedschap).
2. **Psychologie & Tone:** Praat VAN ENGINEER TOT ENGINEER. Verboden: "spin in het web", "dynamische". Powerwoorden: "optimaliseren", "verantwoording", "systematisch".
3. **Structuur:** Geen standaard praatje. Je levert EXACT het volgende rapport af in zuivere Markdown. Volg de indeling en de kopjes letterlijk op.

## VERPLICHTE OUTPUT STRUCTUUR:

═══════════════════════════════════════════════════════════════
**VACATURE SCORE: [Kies een realistische score /100]**
**SECTOR: [Kies best passende technische sector]**
**DOELGROEP: [Functietitel]**
═══════════════════════════════════════════════════════════════

### 🚨 TOP 3 CRITICAL BLOCKERS
[Beschrijf de 3 grootste afhaak-triggers in de originele tekst. Behandel per blocker: Waarom probleem? Wat is de conversie-impact?]

---

### ⚡ WEEK 1 QUICK WINS (Implementatie <2 uur)
[Benoem 2 super concrete aanpassingen. Laat Voor/Na voorbeelden zien.]

---

### 🎯 STRATEGISCHE VERBETERINGEN (2-4 weken)
[Benoem 1 of 2 diepere adviezen voor employer branding of structuur.]

---

### 📝 VERBETERDE VACATURETEKST (VOLLEDIG HERSCHREVEN)
# [Functie] | [Bedrijf] | [Salaris]
[Hier volgt de herschreven, snoeiharde technische vacaturetekst (minimaal 400 woorden). Focus op techniek, geen corporate blabla, gebruik scannable bulletpoints.]

---

### 🚀 30-DAGEN IMPLEMENTATIE ROADMAP
**WEEK 1: QUICK WINS**
- [x] [Taak 1]
- [x] [Taak 2]
- [x] [Taak 3]
**Verwacht resultaat:** +[X]% meer sollicitaties

**WEEK 2-3: OPTIMALISATIE**
- [ ] [Taak 4]
- [ ] [Taak 5]

---

### 💰 ROI IMPACT BEREKENING
**BASELINE METRICS**
- Verwachte conversie huidige tekst: ~[X]%
- Verwachte doorlooptijd: [X] dagen

**EXPECTED POST-OPTIMIZATION**
- Views/dag: x[X]
- Conversie: [X]%
- Time-to-hire: ~[X] dagen

**ROI SUMMARY:**
- Days saved: ~[X] dagen per hire
- Monthly impact: [Beschrijf effect op kwalitatieve leads]
"""

def extract_xml_robust(text, tag):
    match = re.search(f"<{tag}>(.*?)</{tag}>", text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""

def md_to_html(text):
    text = text.replace('<', '&lt;').replace('>', '&gt;')
    text = re.sub(r'(?m)^[═]+$', r'<hr style="border:0;border-top:2px solid #334155;margin:20px 0;">', text)
    text = re.sub(r'```(.*?)```', r'<pre style="background:#F8FAFC;padding:15px;border:1px solid #E2E8F0;border-radius:6px;font-family:monospace;white-space:pre-wrap;color:#334155;line-height:1.5;">\1</pre>', text, flags=re.DOTALL)
    text = re.sub(r'(?m)^### (.*)$', r'<h3 style="color:#0F172A;margin-top:25px;margin-bottom:10px;font-size:18px;">\1</h3>', text)
    text = re.sub(r'(?m)^## (.*)$', r'<h2 style="color:#1E3A8A;border-bottom:2px solid #DBEAFE;padding-bottom:8px;margin-top:30px;margin-bottom:15px;font-size:20px;">\1</h2>', text)
    text = re.sub(r'(?m)^# (.*)$', r'<h1 style="color:#111827;font-size:26px;margin-bottom:20px;font-weight:900;">\1</h1>', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'(?m)^-\s+\[ \]', r'- ◻️', text)
    text = re.sub(r'(?m)^-\s+\[x\]', r'- ✅', text)
    text = re.sub(r'(?m)^[-*]\s+(.*)$', r'<li style="margin-bottom:6px;margin-left:15px;">\1</li>', text)
    blocks = text.split('\n\n')
    out = []
    for b in blocks:
        b = b.strip()
        if not b: continue
        if '<li' in b:
            out.append(f'<ul style="color:#374151;margin-top:5px;padding-left:10px;">\n{b}\n</ul>')
        elif b.startswith('<h') or b.startswith('<pre') or b.startswith('<hr'):
            out.append(b)
        else:
            b = b.replace('\n', '<br>')
            out.append(f'<p style="color:#374151;line-height:1.7;font-size:15px;">{b}</p>')
    return '\n'.join(out)

def get_full_report_html(bedrijf, score, full_markdown):
    html_body = md_to_html(full_markdown)
    safe_score = score if str(score).strip() else "??"
    return f'''<!DOCTYPE html>
<html>
<head><title>Vacature Rapport - {bedrijf}</title><meta charset="UTF-8"></head>
<body style="margin:0;padding:40px;background-color:#F8FAFC;font-family:Arial,sans-serif;">
<div style="max-width:800px;margin:0 auto;background:#FFFFFF;padding:40px;border-radius:12px;box-shadow:0 10px 15px -3px rgba(0,0,0,0.1);">
<h1 style="color:#0F172A;border-bottom:2px solid #E2E8F0;padding-bottom:15px;margin-top:0;">📊 Volledig Rapport: {bedrijf}</h1>
<div style="background-color:#0F172A;padding:20px;border-radius:8px;margin-bottom:30px;color:white;text-align:center;">
<p style="margin:0;font-size:16px;text-transform:uppercase;letter-spacing:1px;color:#94A3B8;">Oorspronkelijke Score</p>
<p style="margin:5px 0 0 0;font-size:36px;font-weight:bold;color:#10B981;">{safe_score} / 10</p>
</div>
<div style="margin-top:20px;">{html_body}</div>
<hr style="margin-top:50px;border:0;border-top:1px solid #E2E8F0;">
<div style="text-align:center;margin-top:20px;">
<p style="font-size:16px;font-weight:bold;color:#1E293B;margin-bottom:10px;">Benieuwd hoe we jouw recruitment performance structureel kunnen verhogen?</p>
<a href="{CALENDLY}" style="display:inline-block;padding:12px 24px;background-color:#FF6B35;color:white;text-decoration:none;border-radius:6px;font-weight:bold;margin-top:10px;">Boek een Korte Intake met Wouter</a>
<p style="color:#64748B;font-size:13px;margin-top:25px;">Gegenereerd door Kandidatentekort.nl | B2B Recruitment Automation</p>
</div>
</div>
</body></html>'''

def get_acquisitie_email_html(voornaam, bedrijf, analysis, improved_preview_text, original_text="", report_url=""):
    score = analysis.get('overall_score', 'N/A')
    score_section = analysis.get('score_section', '')
    improvements = analysis.get('top_3_improvements', [])

    improvements_html = ''.join([
        f'''<tr>
        <td style="padding:15px 0;border-bottom:1px solid #FDE68A;">
        <table cellpadding="0" cellspacing="0" width="100%"><tr>
        <td width="40" valign="top"><table cellpadding="0" cellspacing="0"><tr><td style="width:32px;height:32px;background-color:#EF4444;border-radius:16px;text-align:center;font-weight:bold;color:white;font-size:14px;line-height:32px;">{i+1}</td></tr></table></td>
        <td style="padding-left:12px;color:#78350F;font-size:15px;line-height:24px;font-family:Arial,sans-serif;">{imp}</td>
        </tr></table>
        </td></tr>''' for i, imp in enumerate(improvements)
    ])

    lines = improved_preview_text.split('\n')
    teaser_lines = []
    word_count = 0
    for line in lines:
        teaser_lines.append(line)
        word_count += len(line.split())
        if word_count > 120 and len(teaser_lines) > 2:
            break
    
    improved_preview = '\n'.join(teaser_lines) + "\n\n*[... Rest van de vacaturetekst verborgen ...]*"
    original_display = original_text[:400] + '...\n\n*[...]*' if len(original_text) > 400 else original_text

    original_display = original_display.replace('\n', '<br>')
    improved_preview = improved_preview.replace('\n', '<br>')
    improved_preview = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', improved_preview)
    improved_preview = re.sub(r'#(.*?)\<br\>', r'<strong style="font-size:18px;color:#0F172A;">\1</strong><br>', improved_preview)

    score_color, score_bg, score_border, score_label, score_emoji = "#6B7280", "#F9FAFB", "#6B7280", "Geanalyseerd", "📊"
    try:
        score_num = float(score)
        if score_num >= 8.0:
            score_color, score_bg, score_border, score_label, score_emoji = "#10B981", "#ECFDF5", "#10B981", "Uitstekend", "🏆"
        elif score_num >= 6.5:
            score_color, score_bg, score_border, score_label, score_emoji = "#3B82F6", "#EFF6FF", "#3B82F6", "Goed", "👍"
        elif score_num >= 5.0:
            score_color, score_bg, score_border, score_label, score_emoji = "#F59E0B", "#FFFBEB", "#F59E0B", "Kan flink beter", "📈"
        else:
            score_color, score_bg, score_border, score_label, score_emoji = "#EF4444", "#FEF2F2", "#EF4444", "Conversie Killer", "⚠️"
    except: pass

    categories_html = ""
    if score_section:
        score_parts = re.findall(r'([A-Za-z\s-]+):\s*(\d+)/10', score_section)
        if score_parts:
            categories_html = '<table width="100%" cellpadding="0" cellspacing="0" style="margin-top:20px;"><tr>'
            for name, cat_score in score_parts[:3]:
                cat_score_int = int(cat_score)
                cat_color, cat_icon = ("#10B981", "✅") if cat_score_int >= 7 else ("#F59E0B", "⚡") if cat_score_int >= 5 else ("#EF4444", "❗")
                categories_html += f'''<td width="33%" align="center" style="padding:10px;">
                <table cellpadding="0" cellspacing="0"><tr><td align="center" style="font-size:24px;padding-bottom:4px;">{cat_icon}</td></tr>
                <tr><td align="center" style="font-size:24px;font-weight:bold;color:{cat_color};font-family:Arial,sans-serif;">{cat_score}</td></tr>
                <tr><td align="center" style="font-size:11px;color:#6B7280;text-transform:uppercase;font-family:Arial,sans-serif;">{name.strip()}</td></tr></table>
                </td>'''
            categories_html += '</tr></table>'

    return f'''<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head><meta charset="UTF-8">
<style>body, table, td {{margin:0;padding:0;font-family:Arial,Helvetica,sans-serif;}} table {{border-collapse:collapse !important;}}</style>
</head>
<body style="margin:0;padding:0;background-color:#f3f4f6;width:100%;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#f3f4f6;">
<tr><td align="center" style="padding:30px 15px;">
<table role="presentation" width="700" cellpadding="0" cellspacing="0" border="0" style="background-color:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 10px rgba(0,0,0,0.05);">
<tr>
<td style="background-color:#0F172A;padding:40px 45px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
<tr>
<td width="60" valign="middle">
<table role="presentation" cellpadding="0" cellspacing="0" border="0">
<tr><td style="width:56px;height:56px;background-color:#FF6B35;border-radius:28px;text-align:center;font-size:26px;font-weight:bold;color:#ffffff;line-height:56px;">R</td></tr>
</table>
</td>
<td style="padding-left:16px;" valign="middle">
<p style="margin:0;color:#ffffff;font-size:22px;font-weight:bold;letter-spacing:1px;">RECRUITIN</p>
<p style="margin:4px 0 0 0;color:#94A3B8;font-size:13px;text-transform:uppercase;">Vacature Intelligence Platform</p>
</td>
</tr>
</table>
</td>
</tr>

<tr>
<td style="padding:40px 45px 30px;">
<p style="margin:0 0 15px 0;font-size:22px;font-weight:bold;color:#1F2937;">Hoi {voornaam},</p>
<p style="margin:0 0 15px 0;font-size:16px;color:#4B5563;line-height:1.6;">We hebben zojuist jouw vacature voor <strong>{bedrijf}</strong> door onze B2B Recruitment Intelligence Engine gehaald.</p>
<p style="margin:0 0 15px 0;font-size:16px;color:#4B5563;line-height:1.6;"><strong>Waarom?</strong> Omdat The huidige arbeidsmarkt genadeloos is. 65% van de technici scant vacatures mobiel en haakt binnen 5 seconden af bij gebrek aan transparantie of overmatig corporate jargon. Onze engine identificeert absolute blinde vlekken die jullie nu direct conversie (en dus kandidaten) kosten.</p>
<p style="margin:0;font-size:16px;font-weight:bold;color:#0F172A;line-height:1.6;">Hier is het keiharde resultaat van jouw actuele vacaturetekst:</p>
</td>
</tr>

<tr>
<td style="padding:0 45px 40px;background-color:#ffffff;" align="center">
<div style="background-color:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;padding:35px;">
<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:20px;">
<tr><td align="center" style="width:130px;height:130px;border:8px solid {score_color};border-radius:75px;background-color:#ffffff;">
<p style="margin:25px 0 0 0;font-size:46px;font-weight:900;color:{score_color};line-height:1;">{score}</p>
<p style="margin:2px 0 0 0;font-size:14px;color:#9CA3AF;font-weight:bold;">/10</p>
</td></tr>
</table>
<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:15px;">
<tr><td style="background-color:{score_bg};border:2px solid {score_border};border-radius:20px;padding:8px 24px;">
<p style="margin:0;font-size:15px;font-weight:bold;color:{score_color};">{score_emoji} {score_label}</p>
</td></tr>
</table>
{categories_html}
</div>
</td>
</tr>

<tr>
<td style="padding:0 45px 40px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#FFFBEB;border-left:4px solid #F59E0B;border-radius:0 8px 8px 0;">
<tr><td style="padding:25px 30px;">
<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:15px;">
<tr>
<td width="40" valign="middle"><table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr><td style="width:36px;height:36px;background-color:#F59E0B;border-radius:18px;text-align:center;font-size:18px;line-height:36px;">🎯</td></tr></table></td>
<td style="padding-left:14px;" valign="middle">
<p style="margin:0;font-size:18px;font-weight:bold;color:#92400E;">De Grootste Conversie-Killers</p>
</td>
</tr>
</table>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">{improvements_html}</table>
</td></tr>
</table>
</td>
</tr>

<tr>
<td style="padding:0 45px 40px;">
<p style="margin:0 0 8px 0;font-size:14px;color:#6366F1;font-weight:bold;text-transform:uppercase;">Sneak Peek</p>
<p style="margin:0 0 25px 0;font-size:22px;font-weight:bold;color:#0F172A;">Jouw Vacature Hook: Voor & Na</p>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
<tr>
<td width="48%" valign="top" style="background-color:#FEF2F2;border:1px solid #FECACA;border-radius:8px;padding:25px;">
<p style="margin:0 0 15px 0;font-size:13px;font-weight:bold;color:#DC2626;text-transform:uppercase;">❌ Jouw Huidige Intro</p>
<p style="margin:0;font-size:13px;color:#7F1D1D;line-height:1.7;">{original_display}</p>
</td>
<td width="4%"></td>
<td width="48%" valign="top" style="background-color:#ECFDF5;border:1px solid #A7F3D0;border-radius:8px;padding:25px;box-shadow:0 10px 15px -3px rgba(16, 185, 129, 0.1);">
<p style="margin:0 0 15px 0;font-size:13px;font-weight:bold;color:#059669;text-transform:uppercase;">✅ Onze High-Conversion Hook</p>
<p style="margin:0;font-size:13px;color:#064E3B;line-height:1.7;">{improved_preview}</p>
</td>
</tr>
</table>
</td>
</tr>

<tr>
<td style="padding:0 45px 50px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;">
<tr><td style="padding:35px;text-align:center;">
<p style="margin:0 0 15px 0;font-size:20px;font-weight:bold;color:#0F172A;">Jouw Live Resultaten Zijn Beschikbaar</p>
<p style="margin:0 0 25px 0;font-size:15px;color:#4B5563;line-height:1.6;">De AI heeft jouw <strong>volledige</strong> tekst tot op het bot geanalyseerd en een ijzersterke versie voor je uitgeschreven ter vergelijking.</p>
<table role="presentation" cellpadding="0" cellspacing="0" border="0" align="center" style="margin-bottom:20px;"><tr>
<td style="background-color:#1E3A8A;border-radius:6px;"><a href="{report_url}" style="display:block;padding:16px 32px;color:#ffffff;font-size:16px;font-weight:bold;text-decoration:none;">📄 Bekijk je Volledige Rapport Direct</a></td>
</tr></table>
<p style="margin:0;font-size:14px;color:#52525B;">Liever the data bespreken the een intake? <a href="{CALENDLY}" style="color:#FF6B35;font-weight:bold;text-decoration:none;">The hier een korte belafspraak 📞</a></p>
</td></tr>
</table>
</td>
</tr>

<tr><td style="background-color:#0F172A;padding:30px 45px;text-align:center;">
<p style="margin:0;color:#64748B;font-size:12px;">© 2026 Kandidatentekort.nl | B2B Recruitment Automation</p>
</td></tr>
</table>
</td></tr>
</table>
</body>
</html>'''

def download_jotform_file(file_url, lead_id):
    if not file_url.startswith("http"): return None, file_url
    try:
        resp = requests.get(file_url, params={"apiKey": JOTFORM_API_KEY})
        if resp.ok:
            content = resp.content
            ext = ".pdf" if file_url.lower().endswith(".pdf") else ".docx"
            storage_path = f"{lead_id}/vacature{ext}"
            up_resp = requests.post(f"{SUPABASE_URL}/storage/v1/object/kt_vacatures/{storage_path}",
                headers={"Authorization": f"Bearer {SUPABASE_KEY}", "apikey": SUPABASE_KEY, "Content-Type": "application/octet-stream"},
                data=content)
            if up_resp.ok or up_resp.status_code == 400:
                perma_url = f"{SUPABASE_URL}/storage/v1/object/public/kt_vacatures/{storage_path}"
                return content, perma_url
            return content, file_url
    except Exception as e: print("Download err:", e)
    return None, file_url

def upload_html_report(lead_id, html_content):
    storage_path = f"{lead_id}/analyse_rapport.html"
    try:
        up_resp = requests.post(f"{SUPABASE_URL}/storage/v1/object/kt_vacatures/{storage_path}",
            headers={"Authorization": f"Bearer {SUPABASE_KEY}", "apikey": SUPABASE_KEY, "Content-Type": "text/html; charset=utf-8"},
            data=html_content.encode('utf-8'))
        
        # If successfully uploaded OR 400 (already exists), assume URL exists.
        return f"{SUPABASE_URL}/storage/v1/object/public/kt_vacatures/{storage_path}"
    except Exception as e:
        print("Upload HTML err:", e)
        return ""

def process_lead(lead):
    file_url = lead.get("file_url")
    if not file_url: return

    content, permanent_url = download_jotform_file(file_url, lead['id'])
    if permanent_url != file_url:
        requests.patch(f"{SUPABASE_URL}/rest/v1/kt_leads?id=eq.{lead['id']}",
                       headers={"Authorization": f"Bearer {SUPABASE_KEY}", "apikey": SUPABASE_KEY, "Content-Type": "application/json"},
                       json={"file_url": permanent_url})
        file_url = permanent_url

    if not content: content = b"Dummy Omdat de download mislukt is."

    is_pdf = file_url.lower().endswith('.pdf')
    vacature_text = ""
    bedrijf_naam = f"{lead.get('first_name', '')} {lead.get('last_name', '')}".strip() or "Onbekend"

    if not is_pdf:
        try:
            from docx import Document
            doc = Document(io.BytesIO(content))
            vacature_text = "\n".join([p.text for p in doc.paragraphs])
        except Exception as e: vacature_text = f"Fout bij lezen DOCX: {str(e)}"
    else:
        try:
            import tempfile, subprocess
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
                tf.write(content)
                tf_path = tf.name
            result = subprocess.run(["/opt/homebrew/bin/pdftotext", "-layout", tf_path, "-"], capture_output=True, text=True)
            vacature_text = result.stdout.strip()
            try: os.remove(tf_path)
            except: pass
            if not vacature_text: vacature_text = "Waarschuwing: PDF bevatte geen uitleesbare tekst."
        except Exception as e: vacature_text = f"Fout bij lezen PDF: {str(e)}"

    print(f"Stap 1: Analist XML uitvoeren voor {bedrijf_naam}...")
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    
    try:
        p1 = prompt_analist.format(bedrijf=bedrijf_naam, vacature_text=vacature_text)
        r1 = client.messages.create(
            model="claude-3-haiku-20240307", max_tokens=2000,
            messages=[{"role": "user", "content": p1}]
        )
        xml_text = r1.content[0].text
        
        overall_score = extract_xml_robust(xml_text, 'overall_score')
        score_section = extract_xml_robust(xml_text, 'score_section')
        top_3 = extract_xml_robust(xml_text, 'top_3_improvements')
        
        json_analysis = {
            "overall_score": overall_score,
            "score_section": score_section,
            "top_3_improvements": [t.strip().lstrip('- ') for t in top_3.split('\n') if t.strip()]
        }

        print(f"Stap 2: Copywriter Hook Teaser voor {bedrijf_naam}...")
        p2 = prompt_copywriter.format(bedrijf=bedrijf_naam, verbeterpunten=top_3, vacature_text=vacature_text)
        r2 = client.messages.create(
            model="claude-3-haiku-20240307", max_tokens=3000,
            messages=[{"role": "user", "content": p2}]
        )
        improved_text = r2.content[0].text
        
        payload = {
            "status": "ready_for_email",
            "raw_vacancy_text": vacature_text,
            "enhanced_vacancy_text": improved_text,
            "vacancy_report": json.dumps(json_analysis)
        }
        
        dbRes = requests.patch(f"{SUPABASE_URL}/rest/v1/kt_leads?id=eq.{lead['id']}",
                       headers={"Authorization": f"Bearer {SUPABASE_KEY}", "apikey": SUPABASE_KEY, "Content-Type": "application/json"},
                       json=payload)
        
        if dbRes.ok: print(f"✅ V2.0 AI Teaser Succes voor {lead['id']}")
        else: print(f"❌ DB Update failed: {dbRes.text}")

    except Exception as e:
        print(f"Failed to process AI: {e}")
        requests.patch(f"{SUPABASE_URL}/rest/v1/kt_leads?id=eq.{lead['id']}",
                       headers={"Authorization": f"Bearer {SUPABASE_KEY}", "apikey": SUPABASE_KEY, "Content-Type": "application/json"},
                       json={"status": f"failed_ai: {str(e)}"})

def run_ai_processor():
    resp = requests.get(f"{SUPABASE_URL}/rest/v1/kt_leads?status=eq.pending_ai", headers={"Authorization": f"Bearer {SUPABASE_KEY}", "apikey": SUPABASE_KEY})
    leads = resp.json() if resp.ok else []
    for lead in leads: process_lead(lead)

def run_email_sender():
    time_threshold = (datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=23)).isoformat()
    url = f"{SUPABASE_URL}/rest/v1/kt_leads?status=eq.ready_for_email&created_at=lte.{time_threshold}"
    # url = f"{SUPABASE_URL}/rest/v1/kt_leads?status=eq.ready_for_email" # Uncomment to bypass delay
    resp = requests.get(url, headers={"Authorization": f"Bearer {SUPABASE_KEY}", "apikey": SUPABASE_KEY})
    leads = resp.json() if resp.ok else []
    
    for lead in leads:
        email_addr = lead.get('email', '')
        if not email_addr or '@' not in email_addr: continue
            
        try: analysis = json.loads(lead.get("vacancy_report", "{}"))
        except: analysis = {}
        
        bedrijf_naam = lead.get('company', '')
        voornaam = f"{lead.get('first_name','')} {lead.get('last_name','')}".strip().split()[0] if lead.get('first_name') else "daar"
        full_text = lead.get("enhanced_vacancy_text", "")

        # 1. Generate Full HTML Report and Upload to Supabase
        report_html = get_full_report_html(bedrijf_naam, analysis.get('overall_score', ''), full_text)
        upload_html_report(lead['id'], report_html)
        
        # 2. Vercel Endpoint that forces HTML rendering instead of Supabase 404 raw text
        report_url = f"https://vacaturekanon.nl/api/rapport?id={lead['id']}"

        # 3. Embed the Report URL in the Acquisitie Email
        html = get_acquisitie_email_html(
            voornaam=voornaam,
            bedrijf=bedrijf_naam,
            analysis=analysis,
            improved_preview_text=full_text,
            original_text=lead.get("raw_vacancy_text", ""),
            report_url=report_url or CALENDLY
        )
            
        if not RESEND_API_KEY: continue
        res_mail = requests.post("https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
            json={"from": "Wouter Arts <wouter@kandidatentekort.nl>", "to": [email_addr], "reply_to": "warts@recruitin.nl", "subject": f"📊 Jouw Vacature Analyse Score — {bedrijf_naam}", "html": html, "tags": [{"name": "type", "value": "acquisitie-teaser"}]}
        )
        if res_mail.ok:
            requests.patch(f"{SUPABASE_URL}/rest/v1/kt_leads?id=eq.{lead['id']}", headers={"Authorization": f"Bearer {SUPABASE_KEY}", "apikey": SUPABASE_KEY, "Content-Type": "application/json"}, json={"status": "ready_for_lemlist"})
            print(f"✅ Teaser Email delivered for {lead['id']}")

def run():
    run_ai_processor()
    run_email_sender()

if __name__ == "__main__":
    run()
