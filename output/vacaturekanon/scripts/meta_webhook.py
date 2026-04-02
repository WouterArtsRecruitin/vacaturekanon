import os
import json
import urllib.request
import urllib.parse
from flask import Flask, request, jsonify

# =========================================================
# META LEAD ADS WEBHOOK (PYTHON)
# Doel: Ontvangt "pings" van Meta, haalt de daadwerkelijke 
# lead data op, en push het naar Slack & Supabase!
# =========================================================

app = Flask(__name__)

# --- VUL DEZE IN UIT JE .ENV -------------
META_APP_SECRET = "mijn_geheime_verificatie_token_beutech" # Verzin een willekeurig woord
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN", "EAAYqzG... (Je Graph API Token met leads_retrieval rechten)")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/JOUW/WEBHOOK/URL")
# ==========================================

def get_lead_details(lead_id):
    """Haalt de echte velden (Naam, Tel, Stad) op bij Meta."""
    url = f"https://graph.facebook.com/v21.0/{lead_id}?access_token={META_ACCESS_TOKEN}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read())
    except Exception as e:
        print(f"[!] Fout bij ophalen lead data: {e}")
        return None

def send_slack_alert(lead_data):
    """Stuurt een alarm naar het Slack kanaal."""
    # Data parsen (Meta levert data in een field_data array)
    fields = {}
    for item in lead_data.get('field_data', []):
        fields[item['name']] = item['values'][0]
    
    name = fields.get('full_name', 'Onbekend')
    phone = fields.get('phone_number', 'Onbekend')
    city = fields.get('city', 'Onbekend')
    
    message = {
        "text": f"🚨 *NIEUWE BEUTECH LEAD BINNEN!* 🚨\n\n*Naam:* {name}\n*Telefoon:* {phone}\n*Woonplaats:* {city}\n\n👉 _Bel deze kandidaat nu direct!_"
    }
    
    try:
        req = urllib.request.Request(SLACK_WEBHOOK_URL, json.dumps(message).encode('utf-8'), {'Content-Type': 'application/json', 'method': 'POST'})
        with urllib.request.urlopen(req) as res:
            print("[+] Slack alert gestuurd!")
    except Exception as e:
        print("[!] Kon geen slack alert sturen:", e)

@app.route('/api/meta-webhook', methods=['GET', 'POST'])
def meta_webhook():
    # 1. META VERIFICATIE FASE (Eenmalig bij instellen App Dashboard)
    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        if mode == 'subscribe' and token == META_APP_SECRET:
            print("[+] Meta Webhook is succesvol geverifieerd door Facebook!")
            return challenge, 200
        else:
            return "Verificatie mislukt", 403

    # 2. LEAD BINNENKOMST FASE (Wanneer kandidaat op 'Aanmelden' klikt)
    if request.method == 'POST':
        data = request.json
        print(f"[INCOMING META PING]: {json.dumps(data)}")
        
        if data.get('object') == 'page':
            for entry in data.get('entry', []):
                for change in entry.get('changes', []):
                    if change.get('field') == 'leadgen':
                        # Meta stuurt géén namen/nummers direct hierin (privacy),
                        # ze sturen enkel een Lead ID. Die moeten we nu ophalen!
                        lead_info = change.get('value', {})
                        lead_id = lead_info.get('leadgen_id')
                        
                        if lead_id:
                            print(f"[+] Lead_id {lead_id} gedetecteerd! Fetching data...")
                            full_lead_data = get_lead_details(lead_id)
                            
                            if full_lead_data:
                                # 1. Waarschuw Wouter onmiddellijk in Slack!
                                send_slack_alert(full_lead_data)
                                
                                # 2. Opslaan in Supabase via jouw eigen library
                                # from supabase_library import insert_lead
                                # supabase_insert_lead(full_lead_data)
                                print("[+] Lead succesvol afgehandeld en doorgestuurd!")

        return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    # Run de server (Gebruik Ngrok voor lokale testing of deploy naar Render)
    print("🚀 Meta Lead Webhook Server draait op http://localhost:5000/api/meta-webhook")
    print("   -> Tip: Om lokaal aan Facebook te koppelen, draai ernaast in je terminal: 'ngrok http 5000'")
    app.run(port=5000)
