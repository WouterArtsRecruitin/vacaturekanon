#!/usr/bin/env python3
"""
Lemlist B2B Lead Automation & Sync
Haalt 'opt-in' en 'demo' leads uit Supabase en push deze razendsnel naar een actieve Lemlist Drip Campagne.
"""

import os
import sys
import json
import urllib.request
from datetime import datetime
from dotenv import load_dotenv
load_dotenv("/Users/wouterarts/Library/CloudStorage/OneDrive-Gedeeldebibliotheken-Recruitin/.env", override=True)
if "SUPABASE_KEY" in os.environ and "SUPABASE_ANON_KEY" not in os.environ:
    os.environ["SUPABASE_ANON_KEY"] = os.environ["SUPABASE_KEY"]

# Voeg het pad naar supabase_library.py toe
sys.path.append("/Users/wouterarts/Library/CloudStorage/OneDrive-Gedeeldebibliotheken-Recruitin/scripts/vacaturekanon/vacaturekanon/m7-video")
try:
    from supabase_library import VacaturekanonLibrary
except ImportError:
    print("⚠️ supabase_library kan niet worden geïmporteerd.")
# --- CONFIGURATIE ---
from dotenv import load_dotenv
load_dotenv("/Users/wouterarts/Library/CloudStorage/OneDrive-Gedeeldebibliotheken-Recruitin/.env", override=True)

LEMLIST_API_KEY = os.getenv("LEMLIST_API_KEY")
if not LEMLIST_API_KEY:
    print("❌ LEMLIST_API_KEY niet gevonden in environment.")
    sys.exit(1)
# Updated to Waitlist Campaign: Vacaturekanon V2 - Waitlist B2B
LEMLIST_CAMPAIGN_ID = os.getenv("LEMLIST_CAMPAIGN_ID", "cam_zs4iGwL4poCxTt86Y")

def push_to_lemlist(email: str, first_name: str, company: str, tag: str):
    """ Pusht een individuele lead naar Lemlist Lead pool """
    import requests
    url = f"https://api.lemlist.com/api/campaigns/{LEMLIST_CAMPAIGN_ID}/leads"

    payload = {
        "email": email,
        "firstName": first_name,
        "companyName": company,
        "tags": [tag, "vacaturekanon_api_sync"]
    }

    # Cloudflare bypass header (voorkomt 1010 errors)
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

    try:
        res = requests.post(url, json=payload, auth=("", LEMLIST_API_KEY), headers=headers)
        if res.status_code in [200, 201]:
            print(f"✅ Lead {email} succesvol toegevoegd aan Lemlist.")
            return True
        elif res.status_code == 400 and "already in the campaign" in res.text:
            print(f"✅ Lead {email} staat al in Lemlist (400).")
            return True
        else:
            print(f"❌ Fout bij Lemlist push voor {email}. HTTP {res.status_code}: {res.text}")
            return False
    except Exception as e:
        print(f"❌ Fout bij Lemlist push voor {email}: {e}")
        return False

def sync_supabase_to_lemlist():
    """ Hoofdfunctie om de Supabase 'Aanmelding' leads (STAP 2) te synchroniseren. """
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Starten van de Lemlist Sync...")
    
    db = VacaturekanonLibrary()
    
    # We vragen alle 'nieuwe' leads op (Status = 'pending_automation')
    # Let op: Deze methode (_get) heb jij gedefinieerd in supabase_library.py
    leads = db._get("vk_leads", "?status=eq.pending_automation")
    
    if not leads:
        print("Geen nieuwe leads gevonden voor email flow automation.")
        return
        
    print(f"Vond {len(leads)} nieuwe lead(s). Start push...")
    
    for lead in leads:
        email = lead.get('email')
        naam = lead.get('contact_naam', '')
        # Split first name
        first_name = naam.split(" ")[0] if naam else "HR Voorloper"
        company = lead.get('klant_naam', 'Jouw Bedrijf')
        
        success = push_to_lemlist(email, first_name, company, "hot_lead")
        
        if success:
            # Update status in Supabase zodat hij niet 2x doorgestuurd wordt
            db._patch("vk_leads", f"id=eq.{lead['id']}", {"status": "in_lemlist"})

if __name__ == "__main__":
    # Dit script kan bijvoorbeeld elke 15 minuten als CRON of Netlify Scheduled Function draaien
    sync_supabase_to_lemlist()
