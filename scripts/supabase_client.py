import os
import requests
from pathlib import Path

# Configuratie laden via .env of OS Vars
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

BUCKET_NAME = "assets"

def get_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }

def ensure_bucket_exists():
    """Zorgt ervoor dat de public 'assets' bucket beschikbaar is in Supabase."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("⚠️  Supabase integratie uitgeschakeld: SUPABASE_URL of SUPABASE_KEY ontbreekt.")
        return False
        
    url = f"{SUPABASE_URL}/storage/v1/bucket"
    try:
        r = requests.get(f"{url}/{BUCKET_NAME}", headers=get_headers())
        if r.status_code == 200:
            return True
            
        # Maak emmer aan als deze ontbreekt
        payload = {"id": BUCKET_NAME, "name": BUCKET_NAME, "public": True}
        create_req = requests.post(url, headers=get_headers(), json=payload)
        
        if create_req.status_code in [200, 201]:
            print("✅ Supabase 'assets' bucket succesvol aangemaakt.")
            return True
        else:
            print(f"❌ Failed to create bucket: {create_req.text}")
            return False
    except Exception as e:
        print(f"❌ Supabase Bucket fout: {e}")
        return False

def upload_file(local_path: str, remote_path: str) -> str:
    """Uploads een bestand naar Supabase en retourneert de public URL."""
    if not ensure_bucket_exists():
        return None
        
    url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{remote_path}"
    
    headers = get_headers()
    # Bepaal Mime-Type
    if local_path.endswith('.mp4'):
        headers["Content-Type"] = "video/mp4"
    elif local_path.endswith('.png'):
        headers["Content-Type"] = "image/png"
    elif local_path.endswith('.webp'):
        headers["Content-Type"] = "image/webp"
    else:
        headers["Content-Type"] = "application/octet-stream"

    try:
        with open(local_path, "rb") as f:
            file_data = f.read()
            
        r = requests.post(url, headers=headers, data=file_data)
        
        if r.status_code in [200, 201]:
            public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{remote_path}"
            return public_url
        elif r.status_code == 409:
            # File already exists
            print(f"   ℹ️ Bestand bestond al in cloud ({remote_path}).")
            return f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{remote_path}"
        else:
            print(f"❌ Supabase Upload fout [{r.status_code}]: {r.text}")
            return None
    except Exception as e:
        print(f"❌ Upload exception: {e}")
        return None

def log_campaign(campagne_id: str, status: str, extra_data: dict = None) -> bool:
    """Logs of updatet u status van een campagne naar de Supabase Postgres database."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("⚠️ Supabase db_log overgeslagen: credenties ontbreken.")
        return False

    url = f"{SUPABASE_URL}/rest/v1/campagnes"
    headers = get_headers()
    headers["Content-Type"] = "application/json"
    # Gebruik upsert gedrag op basis van unieke campagne_id
    headers["Prefer"] = "resolution=merge-duplicates,return=minimal"

    payload = {
        "campagne_id": campagne_id,
        "status": status,
    }
    if extra_data:
        payload.update(extra_data)

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        if r.status_code in [200, 201, 204]:
            print(f"   ✅ Db_Log: {campagne_id} -> {status}")
            return True
        else:
            print(f"❌ Db_Log API Error [{r.status_code}]: {r.text}")
            return False
    except Exception as e:
        print(f"❌ Db_log exception: {e}")
        return False
