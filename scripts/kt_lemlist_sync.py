import os
import requests
from dotenv import load_dotenv

# Zet lokaal je variabelen klaar.
load_dotenv("/Users/wouterarts/recruitin/.env", override=True)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", os.environ.get("SUPABASE_SERVICE_KEY"))
LEMLIST_API_KEY = os.environ.get("LEMLIST_API_KEY")

# Laat de .env `KT_LEMLIST_CAMPAIGN_ID` domineren over de generieke Vacaturekanon Lemlist ID
LEMLIST_CAMPAIGN_ID = os.environ.get("KT_LEMLIST_CAMPAIGN_ID", os.environ.get("LEMLIST_CAMPAIGN_ID"))

def get_ready_leads():
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/kt_leads?status=eq.ready_for_lemlist",
        headers={"Authorization": f"Bearer {SUPABASE_KEY}", "apikey": SUPABASE_KEY}
    )
    return resp.json() if resp.ok else []

def mark_lead_injected(lead_id, success=True, error_msg=""):
    status = "lemlist_injected" if success else f"failed_lemlist: {error_msg}"
    requests.patch(
        f"{SUPABASE_URL}/rest/v1/kt_leads?id=eq.{lead_id}",
        headers={
            "Authorization": f"Bearer {SUPABASE_KEY}", 
            "apikey": SUPABASE_KEY, 
            "Content-Type": "application/json"
        },
        json={"status": status}
    )

def inject_to_lemlist(lead):
    email = lead.get("email")
    if not email:
        print(f"Skipping {lead['id']} - no email")
        mark_lead_injected(lead['id'], success=False, error_msg="No email")
        return

    print(f"Injecting {email} into Lemlist campaign {LEMLIST_CAMPAIGN_ID}...")
    
    # Custom Lemlist Payload - Deze velden komen in je emails terecht als {{enhanced_vacancy}} e.d.
    payload = {
        "email": email,
        "firstName": lead.get("first_name", ""),
        "lastName": lead.get("last_name", ""),
        "companyName": lead.get("company", ""),
        "phone": lead.get("phone", ""),
        "file_url": lead.get("file_url", ""),
        "enhanced_vacancy": lead.get("enhanced_vacancy_text", ""),
        "vacancy_report": lead.get("vacancy_report", ""),
        "tags": ["KT_LEAD"]
    }

    # Lemlist API gebruikt de API Key als 'password' in Basic Auth
    # Cloudflare bypass header (voorkomt 1010 errors)
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    resp = requests.post(
        f"https://api.lemlist.com/api/campaigns/{LEMLIST_CAMPAIGN_ID}/leads",
        auth=("", LEMLIST_API_KEY),
        json=payload,
        headers=headers
    )

    if resp.ok:
        print(f"✅ Success: {email} zit in de Lemlist funnel!")
        mark_lead_injected(lead['id'], success=True)
    else:
        err = resp.text
        # Als the lead al de Lemlist sequence zit (soms 409 of "already in") is de the update geslaagd genoeg
        if resp.status_code == 409 or "already in the campaign" in err.lower():
            print(f"⚠️ Lead {email} stond al in de campagne.")
            mark_lead_injected(lead['id'], success=True)
        else:
            print(f"❌ Failed: {err}")
            mark_lead_injected(lead['id'], success=False, error_msg=f"{resp.status_code} - {err[:50]}")

def run():
    print("Starting KT Lemlist Sync Worker 🚀 ...")
    if not LEMLIST_API_KEY or not LEMLIST_CAMPAIGN_ID:
        print("Mislukt: Ontbrekende Lemlist API credentials of Campagne ID in de .env file.")
        return

    leads = get_ready_leads()
    print(f"Gevonden: {len(leads)} verwerkte leads gereed voor Lemlist injectie.")
    
    for lead in leads:
        inject_to_lemlist(lead)

if __name__ == "__main__":
    run()
