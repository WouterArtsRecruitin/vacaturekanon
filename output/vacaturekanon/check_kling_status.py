import os
import time
import json
import urllib.request
import jwt

# Load env safely
try:
    with open('/Users/wouterarts/Library/CloudStorage/OneDrive-Gedeeldebibliotheken-Recruitin/output/vacaturekanon/scripts/.env', 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                k, v = line.strip().split('=', 1)
                os.environ[k] = v
except: pass

AK = os.environ.get("KLING_ACCESS_KEY", "")
SK = os.environ.get("KLING_SECRET_KEY", "")

def generate_jwt(ak, sk):
    headers = {
        "alg": "HS256",
        "typ": "JWT"
    }
    payload = {
        "iss": ak,
        "exp": int(time.time()) + 1800,
        "nbf": int(time.time()) - 5
    }
    token = jwt.encode(payload, sk, headers=headers)
    return token

def check_status(task_id):
    url = f"https://api.klingai.com/v1/videos/image2video/{task_id}"
    token = generate_jwt(AK, SK)
    req = urllib.request.Request(url, method='GET')
    req.add_header("Authorization", f"Bearer {token}")
    
    try:
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode())
            status = res.get('data', {}).get('task_status', 'unknown')
            
            if status == "succeed":
                videos = res.get('data', {}).get('task_result', {}).get('videos', [])
                if videos:
                    target_url = videos[0].get('url')
                    print(f"🎬 KLING BEREKENING KLAAR!")
                    print(f"✅ Video URL: {target_url}")
                    download_mp4(target_url, task_id)
            elif status == "failed":
                print("❌ De Kling rendertaak is vastgelopen of geweigerd (failed).")
                print(json.dumps(res, indent=2))
            else:
                print(f"⏳ Task Status: {status.upper()}... De video is nog aan het renderen. (Dit duurt doorgaans 5 minuten).")
                
    except urllib.error.HTTPError as e:
        print(f"❌ API Error: {e.code} - {e.read().decode()}")

def download_mp4(url, task_id):
    output_path = f"/Users/wouterarts/Library/CloudStorage/OneDrive-Gedeeldebibliotheken-Recruitin/output/vacaturekanon/showcase_video_pipeline/scene_1_intake/scene_1_final_render.mp4"
    print(f"⬇️ Downloaden naar {output_path} ...")
    urllib.request.urlretrieve(url, output_path)
    print("✅ Download voltooid! Je kan hem direct afspelen.")

if __name__ == "__main__":
    # The task_id from our previous push
    target_task = "864011130002997290" 
    if not AK or not SK:
        print("❌ API keys ontbreken in scripts/.env")
    else:
        check_status(target_task)
