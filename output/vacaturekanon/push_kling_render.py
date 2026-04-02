import os
import sys
import time
import json
import base64
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

def encode_img(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def push_to_kling():
    print("🚀 Pushing V4 Scene 1 frames to Kling API for Interpolation...")
    start_img = "/Users/wouterarts/.gemini/antigravity/brain/a4d519de-e069-453a-affb-eefbffdb0bbd/scene1_startframe_v4_1774024526581.png"
    end_img = "/Users/wouterarts/.gemini/antigravity/brain/a4d519de-e069-453a-affb-eefbffdb0bbd/scene1_endframe_v4_1774024540611.png"
    
    if not os.path.exists(start_img) or not os.path.exists(end_img):
        print("❌ FOUT: Kan de start/end renders niet vinden!")
        return

    print("📸 Encoding images...")
    img1_b64 = encode_img(start_img)
    img2_b64 = encode_img(end_img)
    
    url = "https://api.klingai.com/v1/videos/image2video"
    prompt = "Smooth 3D camera pan. The dark empty glassmorphism UI form magically types out glowing text. Floating UI components snap into place with satisfying kinetic motion. High-end SaaS motion graphics, smooth 60fps."
    
    payload = {
        "model_name": "kling-v1",
        "mode": "pro",
        "image": img1_b64,
        "image_tail": img2_b64,
        "prompt": prompt,
        "duration": "5"
    }
    
    data = json.dumps(payload).encode('utf-8')
    token = generate_jwt(AK, SK)
    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {token}")
    
    try:
        print("🤖 Verzoek verzenden naar Kling API...")
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode())
            print(f"✅ Succes! API Response: {json.dumps(res, indent=2)}")
    except urllib.error.HTTPError as e:
        print(f"❌ API Error: {e.code} - {e.read().decode()}")

if __name__ == "__main__":
    if not AK or not SK:
        print("❌ KLING_ACCESS_KEY of KLING_SECRET_KEY ontbreekt in scripts/.env")
    else:
        push_to_kling()
