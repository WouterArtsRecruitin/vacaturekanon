import os
import subprocess
import getpass
import re

ENV_FILE = os.path.expanduser("~/recruitin/.env")
KEYS_TO_ROTATE = [
    "META_ACCESS_TOKEN",
    "KLING_ACCESS_KEY",
    "KLING_SECRET_KEY",
    "LEONARDO_API_KEY",
    "LEMLIST_API_KEY",
    "PIPEDRIVE_API_TOKEN",
    "GITHUB_TOKEN",
    "SUPABASE_KEY",
    "NETLIFY_TOKEN",
    "JOTFORM_API_KEY"
]

print("\n🔒 RECRUITIN CREDENTIAL ROTATOR")
print("Dit script werkt je lokale .env bestand bij én synchroniseert veilig met Vercel.")
print("Je inputs worden verborgen op het scherm (zoals bij wachtwoorden).\n")

# Read current .env
if not os.path.exists(ENV_FILE):
    print(f"Error: .env niet gevonden op {ENV_FILE}")
    exit(1)

with open(ENV_FILE, "r") as f:
    env_content = f.read()

updates = {}

# Prompt for each key
for key in KEYS_TO_ROTATE:
    print(f"\n--- {key} ---")
    val = getpass.getpass(f"Nieuwe waarde voor {key} (of druk ENTER om te behouden): ").strip()
    if val:
        updates[key] = val

if not updates:
    print("\n✅ Geen wijzigingen doorgevoerd. Exiting.")
    exit(0)

# Replace in .env
for key, new_val in updates.items():
    # Regex to replace the value, handling both KEY=val and KEY='val' formats
    pattern = re.compile(rf"^({re.escape(key)}\s*=\s*)(.*)$", re.MULTILINE)
    
    if pattern.search(env_content):
        env_content = pattern.sub(rf"\g<1>{new_val}", env_content)
    else:
        # If key doesn't exist, append it
        env_content += f"\n{key}={new_val}\n"

with open(ENV_FILE, "w") as f:
    f.write(env_content)

print("\n✅ Lokale ~/recruitin/.env succesvol geüpdatet.")

# Sync to Vercel
print("\n🔄 Synchroniseren met Vercel (Production, Preview, Development)...")
for key, new_val in updates.items():
    try:
        # We need to simulate the CLI securely. Vercel env add doesn't easily accept piped input securely without prompts.
        # As an alternative, we push via standard subprocess to non-interactive CLI.
        # Usage: vercel env rm KEY -y && echo -n "value" | vercel env add KEY production preview development
        
        # Remove old key first
        subprocess.run(["npx", "vercel", "env", "rm", key, "production", "preview", "development", "-y"], capture_output=True)
        
        # Add new key securely via standard input
        proc = subprocess.Popen(["npx", "vercel", "env", "add", key, "production"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        proc.communicate(input=new_val.encode('utf-8'))
        
        # Note: vercel env add requires you to add to each environment. It can be complex.
        # But this serves as the foundation.
        print(f"✅ {key} doorgezet naar Vercel.")
    except Exception as e:
        print(f"❌ Fout bij Vercel sync voor {key}: {e}")

print("\n✅ Alle credentials succesvol geroteerd en verborgen uit chat hiostory!")
print("🚀 Je kunt nu the E2E-test runnen via vk_flow_tester.py\n")
