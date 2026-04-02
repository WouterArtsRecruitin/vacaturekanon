#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║  VACATUREKANON — GEFASEERDE FLOW TESTER                         ║
║  Recruitin B.V. | Wouter Arts | 2026                            ║
║                                                                  ║
║  Test de volledige automation flow stap voor stap:              ║
║  Phase 1 → ENV & credentials check                              ║
║  Phase 2 → Supabase connectiviteit + schema                     ║
║  Phase 3 → Jotform webhook (live endpoint)                      ║
║  Phase 4 → Lemlist API & campagne                               ║
║  Phase 5 → Pipedrive API & deal aanmaken                        ║
║  Phase 6 → Meta Ads API                                         ║
║  Phase 7 → Netlify / Vercel deployment check                    ║
║  Phase 8 → End-to-end simulatie (volledige keten)               ║
╚══════════════════════════════════════════════════════════════════╝

Gebruik:
    python3 vk_flow_tester.py              # Alle fases
    python3 vk_flow_tester.py --fase 1     # Specifieke fase
    python3 vk_flow_tester.py --fase 2 4   # Meerdere specifieke fases
    python3 vk_flow_tester.py --fase 1-6   # Range van fases
    python3 vk_flow_tester.py --verbose    # Met uitgebreide output
"""

import os
import sys
import json
import time
import base64
import argparse
import traceback
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# ── Kleuren voor terminal output ─────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"
DIM    = "\033[2m"

# ── Config ────────────────────────────────────────────────────────────────────
ENV_PATH = Path("/Users/wouterarts/Library/CloudStorage/OneDrive-Gedeeldebibliotheken-Recruitin/.env")
VERCEL_WEBHOOK = "https://vacaturekanon-hook.vercel.app/api/jotform-webhook"
NETLIFY_SITE   = "https://vacaturekanon.nl"

# ── Test state ────────────────────────────────────────────────────────────────
results   = []
warnings  = []
todos     = []
test_lead_email = f"vk-test-{int(time.time())}@test.vacaturekanon.nl"
verbose   = False

# ─────────────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────────────

def log(msg, color=RESET):
    print(f"{color}{msg}{RESET}")

def header(fase_nr, titel):
    print(f"\n{BOLD}{BLUE}{'═'*60}{RESET}")
    print(f"{BOLD}{BLUE}  FASE {fase_nr}: {titel.upper()}{RESET}")
    print(f"{BOLD}{BLUE}{'═'*60}{RESET}")

def ok(test, detail=""):
    results.append({"ok": True, "test": test, "detail": detail})
    detail_str = f" {DIM}({detail}){RESET}" if detail else ""
    print(f"  {GREEN}✅ PASS:{RESET} {test}{detail_str}")

def fail(test, detail="", fix=""):
    results.append({"ok": False, "test": test, "detail": detail, "fix": fix})
    print(f"  {RED}❌ FAIL:{RESET} {test}")
    if detail:
        print(f"     {RED}→ {detail}{RESET}")
    if fix:
        print(f"     {YELLOW}💡 Fix: {fix}{RESET}")

def warn(test, detail=""):
    warnings.append({"test": test, "detail": detail})
    print(f"  {YELLOW}⚠️  WARN:{RESET} {test}")
    if detail:
        print(f"     {YELLOW}→ {detail}{RESET}")

def todo(item, prio="medium"):
    todos.append({"item": item, "prio": prio})

def get_default_headers(custom_headers):
    h = custom_headers.copy() if custom_headers else {}
    if "User-Agent" not in h:
        h["User-Agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    return h

def http_get(url, headers=None, timeout=10):
    req = urllib.request.Request(url, headers=get_default_headers(headers))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")
    except Exception as e:
        return 0, str(e)

def http_post(url, data, headers=None, timeout=15):
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    for k, v in get_default_headers(headers).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")
    except Exception as e:
        return 0, str(e)

def http_patch(url, data, headers=None, timeout=10):
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="PATCH")
    req.add_header("Content-Type", "application/json")
    for k, v in get_default_headers(headers).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")
    except Exception as e:
        return 0, str(e)


# ─────────────────────────────────────────────────────────────────────────────
#  FASE 1: ENV & Credentials Check
# ─────────────────────────────────────────────────────────────────────────────

def fase_1_env():
    header(1, "ENV & Credentials Check")

    # .env bestand aanwezig?
    if ENV_PATH.exists():
        ok(".env bestand aanwezig", str(ENV_PATH))
        load_dotenv(ENV_PATH, override=True)
    else:
        fail(".env bestand aanwezig", str(ENV_PATH),
             f"Maak {ENV_PATH} aan met alle keys")
        return

    required_vars = {
        "SUPABASE_URL":          "Supabase REST endpoint",
        "SUPABASE_KEY":          "Supabase service_role key",
        "LEMLIST_API_KEY":       "Lemlist API key",
        "PIPEDRIVE_API_TOKEN":   "Pipedrive API token",
        "META_ACCESS_TOKEN":     "Meta Graph API token",
        "META_ACCOUNT_ID":       "Meta Ad Account ID",
        "META_PAGE_ID":          "Meta Page ID",
        "META_PIXEL_ID":         "Meta Pixel ID",
        "NETLIFY_SITE_ID":       "Netlify site ID",
        "SLACK_WEBHOOK_URL":     "Slack webhook (optioneel)",
        "LEMLIST_CAMPAIGN_ID":   "Lemlist campagne ID",
    }

    missing = []
    for var, desc in required_vars.items():
        val = os.getenv(var)
        if val and val not in ("your-key-here", "", "None"):
            ok(f"{var} aanwezig", f"{desc} — {val[:12]}...")
        elif var == "SLACK_WEBHOOK_URL":
            warn(f"{var} niet ingesteld", "Optioneel maar aanbevolen voor notificaties")
            todo("Slack webhook configureren in .env", "low")
        else:
            fail(f"{var} aanwezig", f"{desc} — ontbreekt of placeholder",
                 f"Voeg {var}=<waarde> toe aan {ENV_PATH}")
            missing.append(var)

    if missing:
        todo(f"Ontbrekende ENV vars invullen: {', '.join(missing)}", "high")

    # Check token lengtes / formaat
    meta_token = os.getenv("META_ACCESS_TOKEN", "")
    if meta_token and len(meta_token) < 100:
        warn("META_ACCESS_TOKEN lijkt kort", "Controleer of het een long-lived token is (>100 chars)")
        todo("META_ACCESS_TOKEN vernieuwen naar long-lived token (geldig 60 dagen)", "high")

    account_id = os.getenv("META_ACCOUNT_ID", "")
    if account_id and not account_id.startswith("act_"):
        warn("META_ACCOUNT_ID formaat", "Verwacht formaat: act_XXXXXXXXX")


# ─────────────────────────────────────────────────────────────────────────────
#  FASE 2: Supabase Check
# ─────────────────────────────────────────────────────────────────────────────

def fase_2_supabase():
    header(2, "Supabase Connectiviteit & Schema")

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        fail("Supabase credentials beschikbaar", "SUPABASE_URL of SUPABASE_KEY ontbreekt")
        todo("Supabase credentials configureren", "high")
        return

    # Verbinding testen
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
    }
    status, body = http_get(f"{supabase_url}/rest/v1/vk_leads?limit=1", headers)

    if status == 200:
        ok("Supabase REST API bereikbaar", f"HTTP {status}")
    elif status == 401:
        fail("Supabase REST API bereikbaar", f"HTTP 401 — ongeldige key",
             "Controleer SUPABASE_KEY (moet service_role zijn)")
        return
    elif status == 404:
        fail("Supabase tabel vk_leads bestaat", "Tabel niet gevonden (404)",
             "Voer CREATE TABLE vk_leads uit in Supabase SQL editor")
        todo("Supabase tabel vk_leads aanmaken", "high")
        return
    else:
        fail("Supabase REST API bereikbaar", f"HTTP {status} — {body[:100]}")
        return

    # Check tabel schema via een test insert + delete
    log("  📊 Schema valideren via test insert...", DIM)
    test_row = {
        "email":        test_lead_email,
        "contact_naam": "VK Test User",
        "klant_naam":   "Test Corp BV",
        "status":       "test_e2e",
        "bron":         "e2e_tester",
    }
    post_headers = {**headers, "Content-Type": "application/json", "Prefer": "return=representation"}
    ins_status, ins_body = http_post(f"{supabase_url}/rest/v1/vk_leads", test_row, post_headers)

    if ins_status in (200, 201):
        ok("Test rij ingevoegd in vk_leads", f"email: {test_lead_email}")
        try:
            inserted = json.loads(ins_body)
            lead_id = inserted[0].get("id") if isinstance(inserted, list) else inserted.get("id")
            if lead_id:
                ok("id auto-increment werkt", f"id={lead_id}")

                # Cleanup: delete test row
                del_req = urllib.request.Request(
                    f"{supabase_url}/rest/v1/vk_leads?id=eq.{lead_id}",
                    method="DELETE"
                )
                for k, v in headers.items():
                    del_req.add_header(k, v)
                try:
                    urllib.request.urlopen(del_req, timeout=10)
                    ok("Test rij opgeruimd na test")
                except:
                    warn("Test rij opruimen mislukt", f"Verwijder handmatig: id={lead_id}")
            else:
                warn("id niet in response", "Controleer of id kolom als PK is geconfigureerd")
        except:
            warn("Response parsen mislukt", ins_body[:100])
    elif ins_status == 409:
        warn("Test insert — conflict", "Email bestaat al (niet erg voor test)")
    else:
        fail("Test rij invoegen in vk_leads", f"HTTP {ins_status} — {ins_body[:200]}",
             "Controleer tabel structuur en RLS policies")
        todo("Supabase RLS policy controleren voor vk_leads (service_role moet kunnen schrijven)", "high")

    # Check of 'status' kolom de juiste waarden accepteert
    try:
        data = json.loads(body)
        if isinstance(data, list) and len(data) > 0:
            sample = data[0]
            expected_cols = {"email", "contact_naam", "klant_naam", "status", "bron"}
            actual_cols   = set(sample.keys())
            missing_cols  = expected_cols - actual_cols
            if missing_cols:
                fail("Verwachte kolommen aanwezig", f"Mist: {missing_cols}",
                     "Voer ALTER TABLE vk_leads ADD COLUMN ... uit")
                todo(f"Supabase kolommen toevoegen: {missing_cols}", "high")
            else:
                ok("Alle verwachte kolommen aanwezig", str(expected_cols))
    except:
        pass

    # Pending leads tellen
    get_headers = {**headers, "Content-Type": "application/json"}
    cnt_status, cnt_body = http_get(
        f"{supabase_url}/rest/v1/vk_leads?status=eq.pending_automation&select=count",
        {**headers, "Prefer": "count=exact", "Range-Unit": "items", "Range": "0-0"}
    )
    try:
        pending = json.loads(cnt_body)
        if isinstance(pending, list):
            log(f"  📊 {len(pending)} leads met status 'pending_automation'", DIM)
            if len(pending) == 0:
                warn("Geen pending_automation leads", "Lemlist sync heeft niks te doen")
    except:
        pass


# ─────────────────────────────────────────────────────────────────────────────
#  FASE 3: Jotform Webhook (Vercel endpoint)
# ─────────────────────────────────────────────────────────────────────────────

def fase_3_webhook():
    header(3, "Jotform Webhook — Vercel Endpoint")

    # Health check
    log(f"  🌐 Endpoint: {VERCEL_WEBHOOK}", DIM)
    status, body = http_get(VERCEL_WEBHOOK)

    if status == 405:
        ok("Vercel endpoint bereikbaar (405 = GET geweigerd, correct gedrag)", f"HTTP {status}")
    elif status == 200:
        ok("Vercel endpoint bereikbaar", f"HTTP {status}")
    elif status == 0:
        fail("Vercel endpoint bereikbaar", body,
             "Check Vercel dashboard voor deployment issues")
        todo("Vercel deployment herstellen voor vacaturekanon-hook", "high")
        return
    else:
        warn("Onverwachte status bij GET", f"HTTP {status}")

    # POST test met minimale payload
    log("  📤 Test POST met minimale Jotform payload...", DIM)
    payload = {
        "q2_email":   test_lead_email,
        "q1_naam":    "Test Contactpersoon",
        "q5_bedrijf": "E2E Test Corp BV",
    }
    post_status, post_body = http_post(VERCEL_WEBHOOK, payload)

    if post_status == 200:
        ok("Webhook POST succesvol", f"HTTP {post_status}")
        try:
            resp = json.loads(post_body)
            if resp.get("succes") or resp.get("success"):
                ok("Response bevat succes: true")
            else:
                warn("Response heeft geen 'succes'=true", str(resp)[:100])
            if resp.get("email"):
                ok("Email in response aanwezig", resp.get("email"))
        except:
            warn("Response body parsen mislukt", post_body[:100])
    elif post_status == 500:
        fail("Webhook POST succesvol", f"HTTP 500 — {post_body[:200]}",
             "Check Vercel function logs via dashboard")
        todo("Webhook 500 error debuggen in Vercel logs", "high")
    elif post_status == 502:
        fail("Webhook POST succesvol", f"HTTP 502 — Database error in response",
             "Check Supabase credentials in Vercel environment variables")
        todo("SUPABASE_URL en SUPABASE_KEY toevoegen aan Vercel environment", "high")
    else:
        fail("Webhook POST succesvol", f"HTTP {post_status} — {post_body[:150]}")

    # Verifieer of Supabase de lead heeft ontvangen (check voor test email)
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    if supabase_url and supabase_key and post_status == 200:
        time.sleep(2)  # even wachten op async write
        headers = {"apikey": supabase_key, "Authorization": f"Bearer {supabase_key}"}
        chk_status, chk_body = http_get(
            f"{supabase_url}/rest/v1/vk_leads?email=eq.{test_lead_email}", headers
        )
        try:
            rows = json.loads(chk_body)
            if isinstance(rows, list) and len(rows) > 0:
                ok("Lead via webhook ook in Supabase terecht gekomen ✅", f"{len(rows)} rij(en)")
                # Opruimen
                lead_id = rows[0].get("id")
                if lead_id:
                    del_req = urllib.request.Request(
                        f"{supabase_url}/rest/v1/vk_leads?id=eq.{lead_id}", method="DELETE"
                    )
                    for k, v in headers.items():
                        del_req.add_header(k, v)
                    try:
                        urllib.request.urlopen(del_req, timeout=10)
                    except:
                        pass
            else:
                warn("Lead niet teruggevonden in Supabase na webhook",
                     "Mogelijk schrijft webhook toch niet naar DB")
                todo("Webhook → Supabase flow verificeren (check Vercel env vars)", "high")
        except:
            pass

    # Check of Jotform webhook ingesteld is
    log("  ℹ️  Jotform form ID: 260757174181359", DIM)
    log("  ℹ️  Controleer handmatig in Jotform: Settings → Integrations → Webhooks", DIM)
    todo("Jotform webhook URL verifiëren: " + VERCEL_WEBHOOK, "medium")


# ─────────────────────────────────────────────────────────────────────────────
#  FASE 4: Lemlist API & Campagne
# ─────────────────────────────────────────────────────────────────────────────

def fase_4_lemlist():
    header(4, "Lemlist API & Campagne Check")

    api_key     = os.getenv("LEMLIST_API_KEY", "4c075a8a91a4e7eb6a609a3d2da5b13b")
    campaign_id = os.getenv("LEMLIST_CAMPAIGN_ID", "cam_zs4iGwL4poCxTt86Y")
    auth_b64    = base64.b64encode(f":{api_key}".encode()).decode()

    # API bereikbaarheid
    status, body = http_get("https://api.lemlist.com/api/campaigns",
                             {"Authorization": f"Basic {auth_b64}"})
    if status == 200:
        ok("Lemlist API bereikbaar", f"HTTP {status}")
    elif status == 401:
        fail("Lemlist API bereikbaar", "HTTP 401 — ongeldige API key",
             "Controleer LEMLIST_API_KEY in .env")
        todo("Lemlist API key vernieuwen", "high")
        return
    else:
        fail("Lemlist API bereikbaar", f"HTTP {status} — {body[:100]}")
        return

    # Campagne vinden
    try:
        campaigns = json.loads(body)
        target = next((c for c in campaigns if c.get("_id") == campaign_id), None)
        if target:
            ok("Doelcampagne gevonden", f"{target.get('name')} ({campaign_id})")
            camp_status = target.get("status", "unknown")
            if camp_status == "active":
                ok("Campagne is actief")
            else:
                warn(f"Campagne status: {camp_status}", "Campagne is niet actief")
                todo(f"Lemlist campagne activeren: {target.get('name')}", "high")
        else:
            fail("Doelcampagne gevonden", f"ID {campaign_id} niet gevonden in {len(campaigns)} campagnes",
                 "Update LEMLIST_CAMPAIGN_ID in .env met het juiste ID")
            if campaigns:
                log(f"  {DIM}Beschikbare campagnes:", DIM)
                for c in campaigns[:5]:
                    log(f"    - {c.get('name')} ({c.get('_id')}) — {c.get('status')}", DIM)
            todo("LEMLIST_CAMPAIGN_ID corrigeren in .env", "high")
    except Exception as e:
        warn("Campagne response parsen", str(e))

    # Test lead toevoegen (en direct verwijderen)
    log("  📧 Test: lead toevoegen aan campagne...", DIM)
    lead_payload = {
        "email":       test_lead_email,
        "firstName":   "VKTest",
        "companyName": "E2E Test Corp",
        "tags":        ["e2e_test"],
    }
    add_status, add_body = http_post(
        f"https://api.lemlist.com/api/campaigns/{campaign_id}/leads",
        lead_payload,
        {"Authorization": f"Basic {auth_b64}"}
    )

    if add_status in (200, 201):
        ok("Test lead toegevoegd aan Lemlist campagne ✅")
        # Verwijder test lead
        del_url = f"https://api.lemlist.com/api/campaigns/{campaign_id}/leads/{test_lead_email}"
        del_req = urllib.request.Request(del_url, method="DELETE")
        del_req.add_header("Authorization", f"Basic {auth_b64}")
        try:
            urllib.request.urlopen(del_req, timeout=10)
            ok("Test lead opgeruimd uit Lemlist")
        except:
            warn("Test lead opruimen mislukt", f"Verwijder handmatig: {test_lead_email}")
    elif add_status == 400 and "already" in add_body.lower():
        ok("Lead al aanwezig in campagne (400 — expected)", add_body[:80])
    elif add_status == 404:
        fail("Campagne ID correct voor lead toevoeging", f"HTTP 404 — campagne niet gevonden",
             "Controleer LEMLIST_CAMPAIGN_ID")
        todo("Lemlist campagne ID verifiëren en updaten", "high")
    else:
        fail("Test lead toevoegen aan Lemlist", f"HTTP {add_status} — {add_body[:150]}")
        todo("Lemlist lead-push debuggen (check API key rechten)", "medium")

    # Check: HTML rendering in Lemlist
    warn("Lemlist HTML email rendering",
         "Controleer of email body correct gerenderd wordt (eerder issue met HTML tags)")
    todo("Lemlist email templates testen via preview in dashboard", "medium")


# ─────────────────────────────────────────────────────────────────────────────
#  FASE 5: Pipedrive API
# ─────────────────────────────────────────────────────────────────────────────

def fase_5_pipedrive():
    header(5, "Pipedrive API & Deal Flow")

    token  = os.getenv("PIPEDRIVE_API_TOKEN", "efdacf799867b37cc4b9ec2234ac136a6e48c4e9")
    base   = "https://api.pipedrive.com/v1"

    # API bereikbaarheid
    status, body = http_get(f"{base}/users/me?api_token={token}")
    if status == 200:
        try:
            user = json.loads(body).get("data", {})
            ok("Pipedrive API bereikbaar", f"Ingelogd als: {user.get('name', 'onbekend')}")
        except:
            ok("Pipedrive API bereikbaar", f"HTTP {status}")
    elif status == 401:
        fail("Pipedrive API bereikbaar", "HTTP 401 — ongeldige token",
             "Vernieuwen via Pipedrive Settings → API")
        todo("Pipedrive API token vernieuwen", "high")
        return
    else:
        fail("Pipedrive API bereikbaar", f"HTTP {status}")
        return

    # Pipelines/Stages ophalen
    status, body = http_get(f"{base}/stages?api_token={token}")
    if status == 200:
        try:
            stages = json.loads(body).get("data", [])
            ok(f"Pipedrive stages beschikbaar", f"{len(stages)} stage(s) gevonden")
            if verbose:
                for s in stages[:5]:
                    log(f"    Stage {s.get('id')}: {s.get('name')} (pipeline {s.get('pipeline_id')})", DIM)
        except:
            pass
    else:
        warn("Pipedrive stages ophalen", f"HTTP {status}")

    # Test person aanmaken
    log("  👤 Test: person aanmaken...", DIM)
    person_data = {
        "name":  "VK E2E Test Persoon",
        "email": [{"value": test_lead_email, "primary": True}],
        "phone": [{"value": "+31600000000", "primary": True}],
        "api_token": token,
    }
    p_status, p_body = http_post(f"{base}/persons", person_data)
    person_id = None
    if p_status in (200, 201):
        try:
            person_id = json.loads(p_body).get("data", {}).get("id")
            ok("Test persoon aangemaakt in Pipedrive", f"id={person_id}")
        except:
            warn("Person ID parsen mislukt")
    else:
        fail("Test persoon aanmaken in Pipedrive", f"HTTP {p_status} — {p_body[:150]}")
        todo("Pipedrive person-aanmaak debuggen", "medium")

    # Test deal aanmaken
    log("  💼 Test: deal aanmaken...", DIM)
    deal_data = {
        "title":     "E2E Test — VK Flow Tester",
        "api_token": token,
    }
    if person_id:
        deal_data["person_id"] = person_id

    d_status, d_body = http_post(f"{base}/deals", deal_data)
    deal_id = None
    if d_status in (200, 201):
        try:
            deal_id = json.loads(d_body).get("data", {}).get("id")
            ok("Test deal aangemaakt in Pipedrive", f"id={deal_id}")
        except:
            warn("Deal ID parsen mislukt")
    else:
        fail("Test deal aanmaken in Pipedrive", f"HTTP {d_status} — {d_body[:150]}")

    # Cleanup
    if deal_id:
        del_req = urllib.request.Request(
            f"{base}/deals/{deal_id}?api_token={token}", method="DELETE"
        )
        try:
            urllib.request.urlopen(del_req, timeout=10)
            ok("Test deal opgeruimd")
        except Exception as e:
            warn("Test deal opruimen", str(e))

    if person_id:
        del_req = urllib.request.Request(
            f"{base}/persons/{person_id}?api_token={token}", method="DELETE"
        )
        try:
            urllib.request.urlopen(del_req, timeout=10)
            ok("Test persoon opgeruimd")
        except Exception as e:
            warn("Test persoon opruimen", str(e))

    # Check integratie in webhook
    warn("Pipedrive integratie in webhook",
         "Webhook logt alleen — Pipedrive API call is nog niet geïmplementeerd in jotform-webhook.js")
    todo("Pipedrive deal-aanmaak implementeren in Vercel webhook (jotform-webhook.js)", "high")


# ─────────────────────────────────────────────────────────────────────────────
#  FASE 6: Meta Ads API
# ─────────────────────────────────────────────────────────────────────────────

def fase_6_meta():
    header(6, "Meta Ads API Check")

    token   = os.getenv("META_ACCESS_TOKEN", "")
    account = os.getenv("META_ACCOUNT_ID", "act_1236576254450117")
    base    = "https://graph.facebook.com/v21.0"

    if not token:
        fail("META_ACCESS_TOKEN aanwezig")
        todo("Meta long-lived access token genereren en in .env zetten", "high")
        return

    # Token validatie
    status, body = http_get(f"{base}/me?access_token={token}&fields=name,id")
    if status == 200:
        try:
            me = json.loads(body)
            ok("Meta API token valide", f"Account: {me.get('name')} (id={me.get('id')})")
        except:
            ok("Meta API token valide", f"HTTP {status}")
    elif status == 400:
        fail("Meta API token valide", "HTTP 400 — token verlopen of ongeldig",
             "Genereer nieuw long-lived token via Meta Business Suite")
        todo("Meta access token vernieuwen (verloopt elke 60 dagen)", "high")
        return
    else:
        fail("Meta API token valide", f"HTTP {status} — {body[:100]}")
        return

    # Token debug info ophalen
    debug_status, debug_body = http_get(
        f"{base}/debug_token?input_token={token}&access_token={token}"
    )
    if debug_status == 200:
        try:
            debug = json.loads(debug_body).get("data", {})
            exp_time = debug.get("expires_at", 0)
            if exp_time:
                exp_dt = datetime.fromtimestamp(exp_time)
                days_left = (exp_dt - datetime.now()).days
                if days_left < 7:
                    warn(f"Meta token verloopt over {days_left} dag(en)!", f"Verloopdatum: {exp_dt.date()}")
                    todo("Meta access token dringend vernieuwen!", "high")
                elif days_left < 14:
                    warn(f"Meta token verloopt over {days_left} dag(en)", f"Verloopdatum: {exp_dt.date()}")
                    todo("Meta access token binnenkort vernieuwen", "medium")
                else:
                    ok(f"Meta token geldig", f"Nog {days_left} dagen (tot {exp_dt.date()})")
            else:
                ok("Meta token — geen vervaldatum (page/system token)")
        except:
            pass

    # Ad account verify
    status, body = http_get(
        f"{base}/{account}?fields=name,account_status,spend_cap,balance&access_token={token}"
    )
    if status == 200:
        try:
            acct = json.loads(body)
            ok("Ad account bereikbaar", f"{acct.get('name')} ({account})")
            if acct.get("account_status") != 1:
                status_map = {1: "Actief", 2: "Uitgeschakeld", 3: "Niet-bevestigd", 7: "Gearchiveerd", 9: "In beoordeling"}
                warn(f"Ad account status: {status_map.get(acct.get('account_status'), acct.get('account_status'))}")
        except:
            ok("Ad account bereikbaar", f"HTTP {status}")
    else:
        fail("Ad account bereikbaar", f"HTTP {status}")
        todo("META_ACCOUNT_ID verifiëren in .env (formaat: act_XXXXX)", "high")

    # Waitlist campagne check
    camp_status, camp_body = http_get(
        f"{base}/{account}/campaigns?fields=name,status,effective_status&limit=50&access_token={token}"
    )
    if camp_status == 200:
        try:
            camps = json.loads(camp_body).get("data", [])
            waitlist = next((c for c in camps if "WAITLIST" in c.get("name", "").upper() and
                             c.get("effective_status") == "ACTIVE"), None)
            if waitlist:
                ok("Waitlist campagne actief", f"{waitlist.get('name')}")
            else:
                warn("Geen actieve WAITLIST campagne gevonden")
        except:
            pass
    else:
        warn("Campagnes ophalen", f"HTTP {camp_status}")


# ─────────────────────────────────────────────────────────────────────────────
#  FASE 7: Netlify / Vercel Deployment Check
# ─────────────────────────────────────────────────────────────────────────────

def fase_7_deployment():
    header(7, "Netlify / Vercel Deployment Check")

    # Vercel webhook endpoint
    log(f"  🌐 Vercel: {VERCEL_WEBHOOK}", DIM)
    status, _ = http_get(VERCEL_WEBHOOK)
    if status in (200, 405):
        ok("Vercel webhook endpoint live", f"HTTP {status}")
    else:
        fail("Vercel webhook endpoint live", f"HTTP {status}")
        todo("Vercel deployment controleren en repareren", "high")

    # Vacaturekanon.nl hoofd site
    log(f"  🌐 Netlify: {NETLIFY_SITE}", DIM)
    status, body = http_get(NETLIFY_SITE, timeout=15)
    if status == 200:
        ok("vacaturekanon.nl bereikbaar", f"HTTP {status}")
        if "vacaturekanon" in body.lower() or "waitlist" in body.lower():
            ok("Site heeft verwachte content")
        else:
            warn("Site content onverwacht", "Controleer of juiste site deployed is")
    elif status == 301 or status == 302:
        ok("vacaturekanon.nl bereikbaar (redirect)", f"HTTP {status}")
    else:
        fail("vacaturekanon.nl bereikbaar", f"HTTP {status}",
             "Check Netlify dashboard voor deployment status")
        todo("Netlify deployment van vacaturekanon.nl controleren", "high")

    # Netlify Functions check
    netlify_func = "https://vacaturekanon.nl/.netlify/functions/jotform-webhook"
    st2, _ = http_get(netlify_func, timeout=10)
    if st2 in (200, 405, 404):
        if st2 == 404:
            warn("Netlify Function endpoint", f"404 — functie niet gevonden op {netlify_func}")
            todo("Netlify function jotform-webhook deployen (of switch naar Vercel)", "medium")
        else:
            ok("Netlify Function endpoint bereikbaar", f"HTTP {st2}")
    else:
        warn("Netlify Function endpoint", f"HTTP {st2}")

    # Landing page slug check
    test_slug = "danda-electric-plc-programmeur"
    slug_url  = f"https://vacaturekanon.nl/{test_slug}/"
    log(f"  🌐 Test slug: {slug_url}", DIM)
    st3, _ = http_get(slug_url, timeout=10)
    if st3 == 200:
        ok("Test landing page bereikbaar", test_slug)
    elif st3 == 404:
        warn("Test landing page 404", f"{test_slug} niet gevonden")
        todo("Landing page deployment flow testen en repareren", "medium")
    else:
        warn("Test landing page status", f"HTTP {st3}")

    # Check GitHub Actions config
    gh_workflow = Path("/Users/wouterarts/vacaturekanon-pages/.github/workflows")
    if gh_workflow.exists():
        workflows = list(gh_workflow.glob("*.yml"))
        if workflows:
            ok("GitHub Actions workflows aanwezig", f"{len(workflows)} workflow(s)")
        else:
            warn("Geen GitHub Actions .yml bestanden gevonden")
            todo("GitHub Actions auto-deploy workflow aanmaken", "medium")
    else:
        warn(".github/workflows map niet gevonden")
        todo("GitHub Actions inrichten voor auto-deploy", "medium")


# ─────────────────────────────────────────────────────────────────────────────
#  FASE 8: End-to-End Simulatie
# ─────────────────────────────────────────────────────────────────────────────

def fase_8_e2e():
    header(8, "End-to-End Keten Simulatie")

    log("  🔄 Simuleer complete Jotform → Supabase → Lemlist keten...", DIM)

    # Stap 1: Webhook POST (zoals Jotform zou sturen)
    jotform_payload = {
        "q1_naam":    "E2E Test Manager",
        "q2_email":   test_lead_email,
        "q5_bedrijf": "E2E Simulatie BV",
        "formID":     "260757174181359",
        "submissionID": f"e2e-test-{int(time.time())}",
    }

    log("  [1/4] Jotform webhook → Vercel...", DIM)
    w_status, w_body = http_post(VERCEL_WEBHOOK, jotform_payload)
    if w_status == 200:
        ok("[1/4] Webhook ontvangen en verwerkt")
    else:
        fail("[1/4] Webhook verwerking", f"HTTP {w_status} — {w_body[:100]}")
        todo("Webhook flow repareren (blokkeert hele keten)", "high")

    # Stap 2: Verifieer Supabase write
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    lead_in_db   = False
    lead_id      = None

    if supabase_url and supabase_key:
        time.sleep(2)
        headers = {"apikey": supabase_key, "Authorization": f"Bearer {supabase_key}"}
        log("  [2/4] Supabase: lead verificeren...", DIM)
        chk_status, chk_body = http_get(
            f"{supabase_url}/rest/v1/vk_leads?email=eq.{test_lead_email}", headers
        )
        try:
            rows = json.loads(chk_body)
            if isinstance(rows, list) and len(rows) > 0:
                ok("[2/4] Lead gevonden in Supabase ✅", f"status={rows[0].get('status')}")
                lead_in_db = True
                lead_id    = rows[0].get("id")
            else:
                fail("[2/4] Lead NIET in Supabase gevonden",
                     "Webhook schrijft mogelijk niet naar database",
                     "Check SUPABASE_URL en SUPABASE_KEY in Vercel environment")
                todo("Supabase schrijf-integratie in Vercel webhook repareren", "high")
        except:
            fail("[2/4] Supabase response parsen", chk_body[:100])

    # Stap 3: Lemlist push simulatie
    api_key     = os.getenv("LEMLIST_API_KEY", "4c075a8a91a4e7eb6a609a3d2da5b13b")
    campaign_id = os.getenv("LEMLIST_CAMPAIGN_ID", "cam_zs4iGwL4poCxTt86Y")
    auth_b64    = base64.b64encode(f":{api_key}".encode()).decode()

    log("  [3/4] Lemlist: lead pushen...", DIM)
    lead_payload = {
        "email":       test_lead_email,
        "firstName":   "E2E Test",
        "companyName": "E2E Simulatie BV",
        "tags":        ["e2e_test", "vacaturekanon_api_sync"],
    }
    l_status, l_body = http_post(
        f"https://api.lemlist.com/api/campaigns/{campaign_id}/leads",
        lead_payload,
        {"Authorization": f"Basic {auth_b64}"}
    )
    if l_status in (200, 201):
        ok("[3/4] Lead gepusht naar Lemlist ✅")
    elif l_status == 400 and "already" in l_body.lower():
        ok("[3/4] Lead al in Lemlist (expected bij hertest)", l_body[:60])
    else:
        fail("[3/4] Lemlist push", f"HTTP {l_status} — {l_body[:100]}")
        todo("Lemlist push automatiseren als onderdeel van de webhook flow", "high")

    # Stap 4: Supabase status update simuleren
    if lead_in_db and lead_id and supabase_url and supabase_key:
        log("  [4/4] Supabase status → 'in_lemlist'...", DIM)
        patch_headers = {
            "apikey":        supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type":  "application/json",
        }
        p_status, p_body = http_patch(
            f"{supabase_url}/rest/v1/vk_leads?id=eq.{lead_id}",
            {"status": "in_lemlist"},
            patch_headers
        )
        if p_status in (200, 201, 204):
            ok("[4/4] Supabase status bijgewerkt naar 'in_lemlist' ✅")
        else:
            fail("[4/4] Supabase status updaten", f"HTTP {p_status} — {p_body[:100]}")
            todo("Supabase PATCH in lemlist_automation.py debuggen", "medium")

    # Cleanup
    log("  🧹 E2E test data opruimen...", DIM)
    if lead_id and supabase_url and supabase_key:
        headers = {"apikey": supabase_key, "Authorization": f"Bearer {supabase_key}"}
        del_req = urllib.request.Request(
            f"{supabase_url}/rest/v1/vk_leads?id=eq.{lead_id}", method="DELETE"
        )
        for k, v in headers.items():
            del_req.add_header(k, v)
        try:
            urllib.request.urlopen(del_req, timeout=10)
            ok("Test data opgeruimd uit Supabase")
        except:
            warn("Supabase cleanup mislukt", f"Verwijder handmatig: id={lead_id}")

    # Lemlist cleanup
    del_url = f"https://api.lemlist.com/api/campaigns/{campaign_id}/leads/{test_lead_email}"
    del_req = urllib.request.Request(del_url, method="DELETE")
    del_req.add_header("Authorization", f"Basic {auth_b64}")
    try:
        urllib.request.urlopen(del_req, timeout=10)
        ok("Test data opgeruimd uit Lemlist")
    except:
        pass


# ─────────────────────────────────────────────────────────────────────────────
#  FASE 9: Landing Page Generatie Pipeline
# ─────────────────────────────────────────────────────────────────────────────

def fase_9_landing_page():
    header(9, "Landing Page Generatie Pipeline")

    # ── Template builder aanwezig?
    builder_path = Path("/Users/wouterarts/Library/CloudStorage/OneDrive-Gedeeldebibliotheken-Recruitin/scripts/vacaturekanon/vacaturekanon/m3-automation/template-builder.js")
    example_path = Path("/Users/wouterarts/Library/CloudStorage/OneDrive-Gedeeldebibliotheken-Recruitin/scripts/vacaturekanon/vacaturekanon/m3-automation/example-kandidaat.json")
    templates_dir = builder_path.parent / "templates"

    if builder_path.exists():
        ok("template-builder.js aanwezig", str(builder_path.name))
    else:
        fail("template-builder.js aanwezig", str(builder_path),
             "Zorg dat m3-automation/template-builder.js bestaat")
        todo("Template builder herstellen in m3-automation/", "high")

    if example_path.exists():
        ok("example-kandidaat.json aanwezig")
        try:
            data = json.loads(example_path.read_text())
            required = ["functietitel", "bedrijfsnaam", "regio", "sector"]
            missing = [f for f in required if not data.get(f)]
            if missing:
                fail("Alle verplichte velden in example JSON", f"Mist: {missing}")
                todo(f"example-kandidaat.json aanvullen met: {missing}", "medium")
            else:
                ok("Verplichte velden aanwezig in example JSON", str(required))
        except Exception as e:
            fail("example-kandidaat.json parseerbaar", str(e))
    else:
        fail("example-kandidaat.json aanwezig", str(example_path))
        todo("example-kandidaat.json aanmaken in m3-automation/", "medium")

    if templates_dir.exists():
        tmpl_files = list(templates_dir.glob("*.html"))
        if tmpl_files:
            ok(f"HTML templates aanwezig", f"{len(tmpl_files)} templates: {[t.name for t in tmpl_files]}")
        else:
            fail("HTML templates aanwezig", f"Geen .html in {templates_dir}",
                 "Kopieer kandidaat-template.html en prospect-template.html naar templates/")
            todo("HTML templates aanmaken in m3-automation/templates/", "high")
    else:
        fail("templates/ map aanwezig", str(templates_dir))
        todo("templates/ map aanmaken met kandidaat-template.html", "high")

    # ── vacaturekanon_v2.py (orchestrator) check
    v2_path = Path("/Users/wouterarts/Library/CloudStorage/OneDrive-Gedeeldebibliotheken-Recruitin/output/vacaturekanon/scripts/vacaturekanon_v2.py")
    if v2_path.exists():
        ok("vacaturekanon_v2.py orchestrator aanwezig", f"{v2_path.stat().st_size // 1024} KB")
        # Check of GitHub token ingesteld is (nodig voor push)
        github_token = os.getenv("GITHUB_TOKEN", "")
        if github_token and len(github_token) > 10:
            ok("GITHUB_TOKEN aanwezig voor GitHub push")
        else:
            warn("GITHUB_TOKEN ontbreekt", "vacaturekanon_v2.py kan geen HTML naar GitHub pushen")
            todo("GITHUB_TOKEN toevoegen aan .env (nodig voor landing page deploy)", "high")
    else:
        fail("vacaturekanon_v2.py aanwezig", str(v2_path))
        todo("vacaturekanon_v2.py herstellen in output/vacaturekanon/scripts/", "high")

    # ── GitHub API bereikbaarheid
    github_token = os.getenv("GITHUB_TOKEN", "")
    github_repo  = os.getenv("GITHUB_REPO", "WouterArtsRecruitin/vacaturekanon-pages")
    if github_token:
        log("  🐙 GitHub API bereikbaarheid testen...", DIM)
        gh_status, gh_body = http_get(
            f"https://api.github.com/repos/{github_repo}",
            {"Authorization": f"token {github_token}", "User-Agent": "vk-flow-tester"}
        )
        if gh_status == 200:
            try:
                repo = json.loads(gh_body)
                ok("GitHub API bereikbaar", f"Repo: {repo.get('full_name')} — {repo.get('visibility')}")
            except:
                ok("GitHub API bereikbaar", f"HTTP {gh_status}")
        elif gh_status == 401:
            fail("GitHub API bereikbaar", "HTTP 401 — token ongeldig",
                 "Vernieuw GITHUB_TOKEN via github.com/settings/tokens")
            todo("GITHUB_TOKEN vernieuwen (classic token met repo scope)", "high")
        elif gh_status == 404:
            fail("GitHub Repo gevonden", f"{github_repo} niet gevonden — verkeerde repo naam?",
                 f"Controleer GITHUB_REPO in .env")
            todo(f"GITHUB_REPO corrigeren in .env (huidig: {github_repo})", "high")
        else:
            warn("GitHub API status onverwacht", f"HTTP {gh_status}")
    else:
        warn("GitHub API test overgeslagen", "GITHUB_TOKEN niet ingesteld")

    # ── Netlify deploy webhook check
    netlify_hook = os.getenv("NETLIFY_HOOK_URL", "")
    if netlify_hook:
        ok("NETLIFY_HOOK_URL aanwezig (deploy webhook)", netlify_hook[:40] + "...")
    else:
        warn("NETLIFY_HOOK_URL niet ingesteld", "Nodig voor auto-deploy na HTML push")
        todo("NETLIFY_HOOK_URL instellen in .env (via Netlify → Site settings → Build hooks)", "medium")

    # ── Imagen API (Gemini)
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if gemini_key:
        log("  🎨 Gemini/Imagen API check...", DIM)
        img_status, img_body = http_get(
            f"https://generativelanguage.googleapis.com/v1beta/models?key={gemini_key}"
        )
        if img_status == 200:
            try:
                models = json.loads(img_body).get("models", [])
                imagen = [m for m in models if "imagen" in m.get("name", "").lower()]
                ok("Gemini API bereikbaar", f"{len(models)} modellen, {len(imagen)} Imagen modellen")
            except:
                ok("Gemini API bereikbaar", f"HTTP {img_status}")
        elif img_status == 400:
            fail("Gemini API bereikbaar", "HTTP 400 — ongeldige API key")
            todo("GEMINI_API_KEY controleren in .env", "high")
        else:
            warn("Gemini API status", f"HTTP {img_status}")
    else:
        warn("GEMINI_API_KEY niet ingesteld", "Imagen 4 hero image generatie werkt niet")
        todo("GEMINI_API_KEY toevoegen aan .env voor hero image generatie", "high")


# ─────────────────────────────────────────────────────────────────────────────
#  FASE 10: Meta Campagne Builder Dry-Run
# ─────────────────────────────────────────────────────────────────────────────

def fase_10_meta_campagne():
    header(10, "Meta Campagne Builder — Dry-Run")

    token   = os.getenv("META_ACCESS_TOKEN", "")
    account = os.getenv("META_ACCOUNT_ID", "act_1236576254450117")
    page_id = os.getenv("META_PAGE_ID", "660118697194302")
    pixel   = os.getenv("META_PIXEL_ID", "238226887541404")
    base    = "https://graph.facebook.com/v21.0"

    if not token:
        fail("META_ACCESS_TOKEN voor campagne builder", "Ontbreekt")
        return

    # ── Script aanwezig?
    builder = Path("/tmp/build_waitlist_meta.py")
    if not builder.exists():
        builder = Path("/Users/wouterarts/recruitin/meta-campaigns/agents/agent-04-meta-campaign.py")
    if builder.exists():
        ok("Meta campagne builder script aanwezig", builder.name)
    else:
        warn("Meta campagne builder script niet gevonden op standaard paden")
        todo("build_waitlist_meta.py / meta_campaign_builder.py beschikbaar maken", "medium")

    # ── Vereiste Meta rechten checken (via /me/permissions)
    log("  🔐 Meta API permissies checken...", DIM)
    perm_status, perm_body = http_get(
        f"{base}/me/permissions?access_token={token}"
    )
    if perm_status == 200:
        try:
            perms = {p["permission"]: p["status"] for p in json.loads(perm_body).get("data", [])}
            required_perms = ["ads_management", "ads_read", "pages_read_engagement"]
            for p in required_perms:
                if perms.get(p) == "granted":
                    ok(f"Permissie: {p}", "granted")
                else:
                    warn(f"Permissie: {p}", f"status={perms.get(p, 'NIET AANWEZIG')}")
                    todo(f"Meta permissie '{p}' aanvragen voor token", "high")
        except:
            warn("Permissies parsen mislukt", perm_body[:80])
    else:
        warn("Meta permissies ophalen", f"HTTP {perm_status}")

    # ── Pixel valideren
    log("  📊 Meta Pixel valideren...", DIM)
    pix_status, pix_body = http_get(
        f"{base}/{pixel}?fields=name,status&access_token={token}"
    )
    if pix_status == 200:
        try:
            pix = json.loads(pix_body)
            ok("Meta Pixel bereikbaar", f"{pix.get('name')} (id={pixel})")
        except:
            ok("Meta Pixel bereikbaar", f"HTTP {pix_status}")
    else:
        fail("Meta Pixel bereikbaar", f"HTTP {pix_status} — pixel {pixel} niet gevonden",
             "Controleer META_PIXEL_ID in .env")
        todo("META_PIXEL_ID verifiëren in .env", "high")

    # ── Page valideren
    log("  📄 Meta Page valideren...", DIM)
    page_status, page_body = http_get(
        f"{base}/{page_id}?fields=name,fan_count&access_token={token}"
    )
    if page_status == 200:
        try:
            page = json.loads(page_body)
            ok("Meta Page bereikbaar", f"{page.get('name')} — {page.get('fan_count', 0):,} followers")
        except:
            ok("Meta Page bereikbaar", f"HTTP {page_status}")
    else:
        fail("Meta Page bereikbaar", f"HTTP {page_status}",
             "Controleer META_PAGE_ID in .env")
        todo("META_PAGE_ID verifiëren in .env", "high")

    # ── Dry-run: campagne aanmaken als PAUSED en direct verwijderen
    log("  🧪 Dry-run: test campagne aanmaken (PAUSED) en direct verwijderen...", DIM)
    camp_data = {
        "name":                  f"VK_E2E_TEST_{int(time.time())}",
        "objective":             "OUTCOME_LEADS",
        "status":                "PAUSED",
        "special_ad_categories": "[]",
        "access_token":          token,
    }

    # Gebruik form-encoded POST (Meta API vereiste)
    try:
        import urllib.parse
        body_enc = urllib.parse.urlencode(camp_data).encode("utf-8")
        req = urllib.request.Request(
            f"{base}/{account}/campaigns",
            data=body_enc,
            method="POST"
        )
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        with urllib.request.urlopen(req, timeout=15) as r:
            camp_result = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        camp_result = json.loads(e.read().decode())
    except Exception as e:
        camp_result = {"error": str(e)}

    camp_id = camp_result.get("id")
    if camp_id:
        ok("Test campagne aangemaakt (PAUSED)", f"id={camp_id}")
        # Direct verwijderen
        try:
            del_body = urllib.parse.urlencode({"access_token": token}).encode()
            del_req = urllib.request.Request(
                f"{base}/{camp_id}", data=del_body, method="DELETE"
            )
            del_req.add_header("Content-Type", "application/x-www-form-urlencoded")
            urllib.request.urlopen(del_req, timeout=10)
            ok("Test campagne opgeruimd uit Meta")
        except Exception as e:
            warn("Test campagne verwijderen", str(e))
    else:
        err_msg = camp_result.get("error", {}).get("message", str(camp_result))
        fail("Test campagne aanmaken", err_msg[:150],
             "Controleer of token ads_management permissie heeft")
        todo("Meta token permissies uitbreiden (ads_management vereist)", "high")

    # ── Aanbeveling: campagnes altijd als PAUSED aanmaken
    ok("Workflow check: campagnes aangemaakt als PAUSED", "conform Recruitin B.V. regel")


# ─────────────────────────────────────────────────────────────────────────────
#  FASE 11: Lemlist Email Sequence Builder
# ─────────────────────────────────────────────────────────────────────────────

def fase_11_lemlist_sequence():
    header(11, "Lemlist Email Sequence Builder")

    api_key  = os.getenv("LEMLIST_API_KEY", "4c075a8a91a4e7eb6a609a3d2da5b13b")
    auth_b64 = base64.b64encode(f":{api_key}".encode()).decode()

    # ── Sequence markdown bestanden checken
    seq_dir = Path("/Users/wouterarts/Library/CloudStorage/OneDrive-Gedeeldebibliotheken-Recruitin/scripts/vacaturekanon/vacaturekanon/m5-email-sequences")
    if seq_dir.exists():
        md_files = list(seq_dir.glob("*.md"))
        ok(f"Email sequences map aanwezig", f"{len(md_files)} .md bestanden")
        for f in md_files:
            log(f"    📄 {f.name} ({f.stat().st_size // 1024} KB)", DIM)
    else:
        fail("Email sequences map aanwezig", str(seq_dir))
        todo("m5-email-sequences map aanmaken met sequence .md bestanden", "high")
        return

    # ── build_lemlist.py aanwezig?
    builder = seq_dir / "build_lemlist.py"
    if builder.exists():
        ok("build_lemlist.py aanwezig")
    else:
        fail("build_lemlist.py aanwezig", str(builder))
        todo("build_lemlist.py aanmaken in m5-email-sequences/", "high")

    # ── Sequence parse test
    seq_file = seq_dir / "sequence-onboarding.md"
    if not seq_file.exists():
        seq_files_found = list(seq_dir.glob("sequence-*.md"))
        if seq_files_found:
            seq_file = seq_files_found[0]
        else:
            warn("Geen sequence-*.md bestanden gevonden")
            todo("Email sequence markdown bestanden aanmaken", "medium")
            seq_file = None

    if seq_file and seq_file.exists():
        content = seq_file.read_text()
        import re
        email_blocks = re.findall(r"## Email \d+", content)
        if email_blocks:
            ok(f"Email sequence parseerbaar", f"{len(email_blocks)} emails in {seq_file.name}")
        else:
            warn(f"Geen '## Email X' blokken gevonden in {seq_file.name}",
                 "build_lemlist.py verwacht '## Email X — Dag Y' headers")
            todo(f"Email sequence format corrigeren in {seq_file.name}", "medium")

    # ── Bestaande Lemlist campagnes ophalen
    log("  📋 Lemlist campagnes ophalen...", DIM)
    status, body = http_get("https://api.lemlist.com/api/campaigns",
                             {"Authorization": f"Basic {auth_b64}"})
    if status == 200:
        try:
            camps = json.loads(body)
            ok(f"Lemlist campagnes beschikbaar", f"{len(camps)} campagnes")
            for c in camps[:5]:
                state = c.get("status", "?")
                icon = "🟢" if state == "active" else "🔴"
                log(f"    {icon} {c.get('name')} — {state} (id={c.get('_id')})", DIM)
            if camps:
                log(f"\n  {YELLOW}💡 Kopieer het juiste _id naar LEMLIST_CAMPAIGN_ID in .env{RESET}")
        except Exception as e:
            warn("Campagnes parsen", str(e))
    elif status == 403:
        fail("Lemlist API — campagnes ophalen", "HTTP 403 (Cloudflare block of rate limit)",
             "Lemlist API kan via Python geblokkeerd worden door Cloudflare. Test via curl of Postman.")
        todo("Lemlist API key verifiëren via Lemlist dashboard (Settings → Integrations → API)", "high")
        warn("Lemlist 403 — Cloudflare rate limit",
             "Probeer: curl -u :\"$LEMLIST_API_KEY\" https://api.lemlist.com/api/campaigns")
    else:
        fail("Lemlist API bereikbaar", f"HTTP {status}")

    # ── HTML email render check
    warn("Lemlist HTML rendering",
         "Eerder issue: body bevatte raw HTML tags in plaats van rendered HTML")
    todo("Email body testen via Lemlist preview (issue: newlines → <br> conversie)", "medium")
    todo("Overweeg Lemlist native templates in plaats van HTML injection", "low")


# ─────────────────────────────────────────────────────────────────────────────
#  FASE 12: Supabase → Lemlist Sync Automation
# ─────────────────────────────────────────────────────────────────────────────

def fase_12_lemlist_sync():
    header(12, "Supabase → Lemlist Sync Automation")

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    api_key      = os.getenv("LEMLIST_API_KEY", "4c075a8a91a4e7eb6a609a3d2da5b13b")
    campaign_id  = os.getenv("LEMLIST_CAMPAIGN_ID", "cam_zs4iGwL4poCxTt86Y")
    auth_b64     = base64.b64encode(f":{api_key}".encode()).decode()

    # ── lemlist_automation.py aanwezig?
    sync_script = Path("/Users/wouterarts/Library/CloudStorage/OneDrive-Gedeeldebibliotheken-Recruitin/output/vacaturekanon/scripts/lemlist_automation.py")
    if sync_script.exists():
        ok("lemlist_automation.py aanwezig", f"{sync_script.stat().st_size // 1024} KB")
    else:
        fail("lemlist_automation.py aanwezig", str(sync_script))
        todo("lemlist_automation.py aanmaken voor Supabase → Lemlist sync", "high")

    # ── supabase_library.py check (dependency van sync script)
    supa_lib = Path("/Users/wouterarts/Library/CloudStorage/OneDrive-Gedeeldebibliotheken-Recruitin/scripts/vacaturekanon/vacaturekanon/m7-video/supabase_library.py")
    if supa_lib.exists():
        ok("supabase_library.py aanwezig", "dependency voor lemlist_automation.py")
    else:
        fail("supabase_library.py aanwezig", str(supa_lib),
             "lemlist_automation.py importeert VacaturekanonLibrary vanuit dit bestand")
        todo("supabase_library.py aanmaken of dependency verwijderen uit lemlist_automation.py", "high")

    # ── Pending leads in Supabase
    if supabase_url and supabase_key:
        headers = {"apikey": supabase_key, "Authorization": f"Bearer {supabase_key}"}
        status, body = http_get(
            f"{supabase_url}/rest/v1/vk_leads?status=eq.pending_automation", headers
        )
        if status == 200:
            try:
                pending = json.loads(body)
                if isinstance(pending, list):
                    ok(f"Pending leads in Supabase", f"{len(pending)} leads met status=pending_automation")
                    if len(pending) > 0:
                        log(f"  {YELLOW}⚡ Er zijn {len(pending)} leads die nog Lemlist sync nodig hebben!{RESET}")
                        todo("lemlist_automation.py uitvoeren om pending leads te synchen", "high")
                    else:
                        ok("Geen backlog — alle leads al gesynchroniseerd")
            except:
                warn("Pending leads parsen")
        else:
            fail("Pending leads ophalen", f"HTTP {status}")
    else:
        warn("Supabase credentials ontbreken", "Kan pending leads niet tellen")

    # ── In-Lemlist leads tellen
    if supabase_url and supabase_key:
        headers = {"apikey": supabase_key, "Authorization": f"Bearer {supabase_key}"}
        status, body = http_get(
            f"{supabase_url}/rest/v1/vk_leads?status=eq.in_lemlist", headers
        )
        if status == 200:
            try:
                in_lem = json.loads(body)
                ok("in_lemlist leads geteld", f"{len(in_lem)} leads al in Lemlist")
            except:
                pass

    # ── CRON / scheduled trigger aanwezig?
    warn("CRON voor lemlist_automation.py",
         "Geen automatische scheduler gevonden — sync draait alleen handmatig")
    todo("CRON of Netlify Scheduled Function instellen voor lemlist_automation.py (elke 15 min)", "medium")

    # ── Test push simuleren
    log("  🔄 Test sync simulatie (1 lead → Lemlist → Supabase update)...", DIM)
    lead_payload = {
        "email":       test_lead_email,
        "firstName":   "Sync Test",
        "companyName": "Sync Test Corp",
        "tags":        ["e2e_sync_test"],
    }
    l_status, l_body = http_post(
        f"https://api.lemlist.com/api/campaigns/{campaign_id}/leads",
        lead_payload,
        {"Authorization": f"Basic {auth_b64}"}
    )
    if l_status in (200, 201):
        ok("Sync simulatie: lead in Lemlist campaign", "push gelukt")
        # Cleanup
        del_req = urllib.request.Request(
            f"https://api.lemlist.com/api/campaigns/{campaign_id}/leads/{test_lead_email}",
            method="DELETE"
        )
        del_req.add_header("Authorization", f"Basic {auth_b64}")
        try:
            urllib.request.urlopen(del_req, timeout=10)
        except:
            pass
    elif l_status == 400 and "already" in l_body.lower():
        ok("Sync simulatie: lead al in campagne (ok)", l_body[:60])
    else:
        fail("Sync simulatie: lead push naar Lemlist", f"HTTP {l_status} — {l_body[:100]}",
             "Controleer Lemlist API key en campaign ID")
        todo("Lemlist sync debuggen: API key of campaign ID incorrect", "high")


# ─────────────────────────────────────────────────────────────────────────────
#  FASE 13: Video & Kling Pipeline Check
# ─────────────────────────────────────────────────────────────────────────────

def fase_13_kling_video():
    header(13, "Video Pipeline — Kling & Leonardo AI")

    import hmac
    import hashlib

    kling_access = os.getenv("KLING_ACCESS_KEY", "")
    kling_secret = os.getenv("KLING_SECRET_KEY", "")
    leonardo_key = os.getenv("LEONARDO_API_KEY", "")

    # ── Kling credentials
    if kling_access and kling_secret:
        ok("Kling API keys aanwezig", f"access={kling_access[:8]}... secret={kling_secret[:8]}...")

        # JWT genereren voor Kling
        log("  🎬 Kling JWT genereren en API testen...", DIM)
        try:
            import struct

            def b64url(data):
                import base64
                return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

            header_j = json.dumps({"alg": "HS256", "typ": "JWT"}).encode()
            now = int(time.time())
            payload_j = json.dumps({
                "iss": kling_access,
                "exp": now + 1800,
                "nbf": now - 5,
            }).encode()
            msg = b64url(header_j) + "." + b64url(payload_j)
            sig = hmac.new(kling_secret.encode(), msg.encode(), hashlib.sha256).digest()  # type: ignore[attr-defined]
            jwt_token = msg + "." + b64url(sig)

            k_status, k_body = http_get(
                "https://api.klingai.com/v1/videos/text2video",
                {"Authorization": f"Bearer {jwt_token}"}
            )
            if k_status in (200, 405, 422):
                ok("Kling API bereikbaar (JWT auth werkt)", f"HTTP {k_status}")
            elif k_status == 401:
                fail("Kling API JWT auth", "HTTP 401 — token ongeldig",
                     "Controleer KLING_ACCESS_KEY en KLING_SECRET_KEY")
                todo("Kling API keys vernieuwen", "high")
            else:
                warn("Kling API status", f"HTTP {k_status} — {k_body[:80]}")
        except Exception as e:
            fail("Kling JWT genereren", str(e))
    else:
        warn("Kling API keys ontbreken", "Video generatie niet mogelijk")
        todo("KLING_ACCESS_KEY en KLING_SECRET_KEY toevoegen aan .env", "medium")

    # ── Leonardo AI
    if leonardo_key:
        ok("LEONARDO_API_KEY aanwezig", f"{leonardo_key[:8]}...")
        log("  🖼️  Leonardo AI check...", DIM)
        leo_status, leo_body = http_get(
            "https://cloud.leonardo.ai/api/rest/v1/me",
            {"Authorization": f"Bearer {leonardo_key}"}
        )
        if leo_status == 200:
            try:
                me = json.loads(leo_body).get("user_details", [{}])[0]
                ok("Leonardo AI API bereikbaar", f"username={me.get('username', 'onbekend')}")
                tokens = me.get("tokenRenewalDate", "")
                if tokens:
                    log(f"    Token renewal: {tokens}", DIM)
            except:
                ok("Leonardo AI API bereikbaar", f"HTTP {leo_status}")
        elif leo_status == 401:
            fail("Leonardo AI API bereikbaar", "HTTP 401 — ongeldige key",
                 "Vernieuw LEONARDO_API_KEY via leonardo.ai")
            todo("LEONARDO_API_KEY vernieuwen", "medium")
        else:
            warn("Leonardo AI API status", f"HTTP {leo_status}")
    else:
        warn("LEONARDO_API_KEY niet ingesteld", "Karakter-afbeelding generatie niet mogelijk")
        todo("LEONARDO_API_KEY toevoegen aan .env", "medium")

    # ── Video pipeline scripts check
    video_scripts = [
        Path("/Users/wouterarts/recruitin/scripts/kling_video_generator.py"),
        Path("/Users/wouterarts/recruitin/scripts/kling_invideo_pipeline.py"),
        Path("/Users/wouterarts/Library/CloudStorage/OneDrive-Gedeeldebibliotheken-Recruitin/output/vacaturekanon/scripts/bts_werkenbij_beutech.py"),
    ]
    for vscript in video_scripts:
        if vscript.exists():
            ok(f"Video script aanwezig", vscript.name)
        else:
            warn(f"Video script niet gevonden", str(vscript))

    # ── Storyboard check
    storyboard_dir = Path("/Users/wouterarts/Library/CloudStorage/OneDrive-Gedeeldebibliotheken-Recruitin/scripts/vacaturekanon/vacaturekanon/m7-video/storyboards")
    if storyboard_dir.exists():
        boards = list(storyboard_dir.glob("*.md"))
        ok("Storyboard templates aanwezig", f"{len(boards)} storyboards")
    else:
        warn("Storyboard map niet gevonden", str(storyboard_dir))
        todo("m7-video/storyboards/ aanmaken met storyboard templates", "low")


# ─────────────────────────────────────────────────────────────────────────────
#  RAPPORT & TODO LIJST
# ─────────────────────────────────────────────────────────────────────────────

def print_rapport():
    passed  = [r for r in results if r["ok"]]
    failed  = [r for r in results if not r["ok"]]
    total   = len(results)

    print(f"\n{BOLD}{'═'*60}{RESET}")
    print(f"{BOLD}  📊 TESTRAPPORT — {datetime.now().strftime('%d-%m-%Y %H:%M')}{RESET}")
    print(f"{BOLD}{'═'*60}{RESET}")
    print(f"  {GREEN}✅ Geslaagd: {len(passed)}/{total}{RESET}")
    if failed:
        print(f"  {RED}❌ Mislukt:  {len(failed)}/{total}{RESET}")
    if warnings:
        print(f"  {YELLOW}⚠️  Warnings: {len(warnings)}{RESET}")

    if failed:
        print(f"\n{BOLD}{RED}  GEFAALDE TESTS:{RESET}")
        for f in failed:
            print(f"  {RED}❌ {f['test']}{RESET}")
            if f.get("detail"):
                print(f"     → {f['detail']}")
            if f.get("fix"):
                print(f"     {YELLOW}💡 {f['fix']}{RESET}")

    print(f"\n{BOLD}{'═'*60}{RESET}")
    print(f"{BOLD}  📋 TODO LIJST{RESET}")
    print(f"{BOLD}{'═'*60}{RESET}")

    prio_order = {"high": 0, "medium": 1, "low": 2}
    prio_labels = {"high": f"{RED}🔴 [HIGH]{RESET}  ", "medium": f"{YELLOW}🟡 [MED]{RESET}   ", "low": f"{GREEN}🟢 [LOW]{RESET}   "}

    sorted_todos = sorted(set(t["item"] for t in todos),
                          key=lambda x: prio_order.get(next((t["prio"] for t in todos if t["item"] == x), "low"), 2))

    seen = set()
    for prio in ["high", "medium", "low"]:
        items = [t for t in todos if t["prio"] == prio and t["item"] not in seen]
        for t in items:
            seen.add(t["item"])
            print(f"  {prio_labels[prio]} {t['item']}")

    print(f"\n{BOLD}{'═'*60}{RESET}")
    score_pct = int(len(passed) / total * 100) if total > 0 else 0
    if score_pct == 100:
        print(f"{BOLD}{GREEN}  🎉 ALLES GROEN! Flow is volledig operationeel.{RESET}")
    elif score_pct >= 70:
        print(f"{BOLD}{YELLOW}  ⚡ {score_pct}% gehaald — bijna klaar, pak de rode punten aan.{RESET}")
    else:
        print(f"{BOLD}{RED}  🚨 {score_pct}% — Kritieke issues vereisen aandacht.{RESET}")
    print(f"{BOLD}{'═'*60}{RESET}\n")

    # Schrijf rapport naar bestand
    rapport_path = Path("/tmp") / f"vk_test_rapport_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    rapport_data = {
        "timestamp": datetime.now().isoformat(),
        "score":     f"{len(passed)}/{total}",
        "passed":    passed,
        "failed":    failed,
        "warnings":  warnings,
        "todos":     todos,
    }
    with open(rapport_path, "w") as f:
        json.dump(rapport_data, f, indent=2, ensure_ascii=False)
    print(f"  {DIM}📁 Rapport opgeslagen: {rapport_path}{RESET}\n")


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────────────────────

FASEN = {
    1:  ("ENV & Credentials",           fase_1_env),
    2:  ("Supabase",                    fase_2_supabase),
    3:  ("Jotform Webhook",             fase_3_webhook),
    4:  ("Lemlist API",                 fase_4_lemlist),
    5:  ("Pipedrive",                   fase_5_pipedrive),
    6:  ("Meta Ads API",                fase_6_meta),
    7:  ("Deployment Check",            fase_7_deployment),
    8:  ("End-to-End Simulatie",        fase_8_e2e),
    9:  ("Landing Page Generatie",      fase_9_landing_page),
    10: ("Meta Campagne Builder",       fase_10_meta_campagne),
    11: ("Lemlist Sequence Builder",    fase_11_lemlist_sequence),
    12: ("Supabase → Lemlist Sync",     fase_12_lemlist_sync),
    13: ("Video Pipeline (Kling)",      fase_13_kling_video),
}

def main():
    global verbose

    parser = argparse.ArgumentParser(
        description="Vacaturekanon — Gefaseerde Flow Tester",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--fase", nargs="*",
                        help="Fase nummers om te testen (bijv: 1 2 3 of 1-6). Standaard: alle.")
    parser.add_argument("--verbose", action="store_true",
                        help="Uitgebreide output")
    args = parser.parse_args()
    verbose = args.verbose

    # Bepaal welke fases
    te_testen = list(FASEN.keys())
    if args.fase:
        te_testen = []
        for f in args.fase:
            if "-" in f:
                start, end = f.split("-")
                te_testen.extend(range(int(start), int(end) + 1))
            else:
                te_testen.append(int(f))
        te_testen = sorted(set(te_testen))

    print(f"\n{BOLD}{CYAN}{'╔' + '═'*58 + '╗'}{RESET}")
    print(f"{BOLD}{CYAN}║{'  VACATUREKANON — AUTOMATION FLOW TESTER':^58}║{RESET}")
    print(f"{BOLD}{CYAN}║{'  Recruitin B.V. | ' + datetime.now().strftime('%d-%m-%Y %H:%M'):^58}║{RESET}")
    print(f"{BOLD}{CYAN}{'╚' + '═'*58 + '╝'}{RESET}")
    print(f"  Fases: {', '.join(str(f) for f in te_testen)}")
    print(f"  Test email: {test_lead_email}")

    load_dotenv(ENV_PATH, override=True)

    for fase_nr in te_testen:
        if fase_nr not in FASEN:
            print(f"  {YELLOW}⚠️  Onbekende fase: {fase_nr}{RESET}")
            continue
        _, fn = FASEN[fase_nr]
        try:
            fn()
        except Exception as e:
            fail(f"Fase {fase_nr} — onverwachte crash", str(e))
            if verbose:
                traceback.print_exc()

    print_rapport()


if __name__ == "__main__":
    main()
