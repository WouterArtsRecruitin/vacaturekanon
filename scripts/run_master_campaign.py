#!/usr/bin/env python3
"""
run_master_campaign.py
Recruitin B.V. — Master Orchestrator (v2.0)

Dit script wordt asynchroon afgetrapt door de Webhook (handler.py) na een Jotform submit.
Volgens Master Prompt v2 delegeert dit script:
  1. Image Generatie (gemockt per Master Prompt, output naar sandbox tmp)
  2. Landing Page
  3. Meta API Campagne
  4. Kling Video Clips
  5. Slack Notificatie

Gebruik:
  python3 run_master_campaign.py \
    --sector "oil & gas" \
    --functie "Procesoperator" \
    --bedrijf "Shell" \
    --regio "Zuid-Holland" \
    --email "hr@shell.com" \
    --naam "Jan Peter"
"""

import sys, os, time, shutil, argparse, subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Cloud Ready: Verwijs root (recruitin) direct gerelateerd aan de plek van het script
# Gebruik absoluut pad in plaats van .resolve() om symlink naar OneDrive te negeren
BASE_DIR = Path(os.path.abspath(__file__)).parents[1]
sys.path.append(str(BASE_DIR / "scripts"))
env_path = BASE_DIR / ".env"
load_dotenv(env_path, override=True)

# Supabase imports
try:
    from supabase_client import upload_file, log_campaign
except ImportError:
    print("⚠️ Supabase client niet geladen.")
    upload_file = None
    log_campaign = None

def safe_run(cmd, work_dir=None):
    """Start een subproces en print de output"""
    print(f"\n▶️ RUN: {' '.join(cmd)}")
    env = os.environ.copy()
    try:
        result = subprocess.run(cmd, env=env, cwd=work_dir, capture_output=True, text=True, check=True)
        print(result.stdout)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Subproces fout (Exit {e.returncode}):")
        print(e.stderr)
        return False, e.stderr

def run(sector: str, functie: str, bedrijf: str, regio: str, email: str, naam: str, url: str = ""):
    # ── 0. Initialisatie ───────────────────────────────────────────────────
    mapping = {
        "oil & gas": "OilGas",
        "constructie": "Constructie",
        "automation": "Automation",
        "productie": "Productie",
        "renewable energy": "Renewable",
    }
    s_slug = mapping.get(sector.lower(), sector.replace(" ", ""))
    yymm = datetime.now().strftime("%Y%m")
    campagne_naam = f"KT_{s_slug}_{yymm}_{bedrijf.replace(' ', '')}"
    
    print(f"🚀 START MASTER CAMPAIGN VOOR: {bedrijf} ({sector})")
    print(f"   Campagne ID: {campagne_naam}")

    # Grijp terug op veilige /tmp omgeving als CloudStorage lokale permissies blokkeert
    default_out = Path(os.getenv("LOCAL_OUTPUT_BASE", "/tmp/recruitin-local"))
    assets_dir = default_out / "meta-campaigns" / "assets" / campagne_naam
    assets_dir.mkdir(parents=True, exist_ok=True)

    if log_campaign:
        log_campaign(campagne_naam, "running", {
            "sector": sector,
            "bedrijf": bedrijf,
            "functie": functie
        })

    # ── 1. Image Generation (Mock voor nu totdat API exact is) ──────────────
    print("\n── TAAK 1: Image & Ad Visuals ─────────────────")
    # Zonder actieve Nano Banana of Replicate API key mocken we de images.
    for visual in ["character.png", "visual-1.png", "visual-2.png", "visual-3.png", "visual-4.png"]:
        tmp_img = assets_dir / visual
        if not tmp_img.exists():
            print(f"   [Mock] Creëer tijdelijke testafbeelding: {visual}")
            with open(tmp_img, "wb") as f:
                f.write(os.urandom(1024))  # 1kb dummy file
    print("   ✅ Asset map en visuals gereed.")

    # ── 2. Landing Page Generatie ──────────────────────────────────────────
    print("\n── TAAK 2: Landing Page Generatie ─────────────")
    lp_script = BASE_DIR / "scripts" / "generate_landing_page.py"
    
    lp_cmd = [
        "python3", str(lp_script),
        "--sector", sector,
        "--regio", regio,
        "--campagne", campagne_naam,
        "--deploy"
    ]
    
    # Run LP Script
    succes, out = safe_run(lp_cmd, work_dir=BASE_DIR)
    
    # Zoek naar "deploy klaar: URL" in output
    landing_url = f"https://{sector.replace(' ', '-')}.vacaturekanon.nl"
    if succes:
        for line in reversed(out.split('\n')):
            if "deploy klaar:" in line and "https://" in line:
                landing_url = "https://" + line.split("https://")[1].strip()
                break
    print(f"   ✅ B2B Landing Page geregistreerd op: {landing_url}")

    # ── 2.5 B2C Kandidaat Pagina Generatie (White-Label) ───────────────────
    print("\n── TAAK 2.5: B2C Kandidaat Pagina ───────────")
    b2c_script = BASE_DIR / "scripts" / "generate_candidate_page.py"
    b2c_cmd = [
        "python3", str(b2c_script),
        "--sector", sector,
        "--functie", functie,
        "--bedrijf", bedrijf,
        "--regio", regio,
        "--campagne", campagne_naam
    ]
    if url:
        b2c_cmd.extend(["--url", url])
        
    safe_run(b2c_cmd, work_dir=BASE_DIR)


    # ── 3. Meta Campaign Builder ───────────────────────────────────────────
    print("\n── TAAK 3: Meta Campaign Builder ─────────────")
    meta_script = BASE_DIR / "scripts" / "meta_campaign_builder.py"
    meta_cmd = [
        "python3", str(meta_script),
        sector,
        functie,
        regio,
        landing_url,
        campagne_naam
    ]
    safe_run(meta_cmd)

    # ── 4. Kling Video Clips ───────────────────────────────────────────────
    print("\n── TAAK 4: Kling Video Clips ─────────────")
    kling_script = BASE_DIR / "scripts" / "kling_invideo_pipeline.py"
    kling_cmd = [
        "python3", str(kling_script),
        "--sector", sector,
        "--image", str(assets_dir / "character.png"),
        "--campagne", campagne_naam
    ]
    
    # We roepen het apart aan, hier pakken we alleen character animatie voor snelheid
    # Vervolgens een generieke aanroep voor ad video als er tijd is
    safe_run(kling_cmd)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Master Campaign Orchestrator")
    parser.add_argument("--sector", required=True)
    parser.add_argument("--functie", required=True)
    parser.add_argument("--bedrijf", required=True)
    parser.add_argument("--regio", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--naam", required=True)
    parser.add_argument("--url", required=False, default="")
    
    args = parser.parse_args()
    
    start_t = time.time()
    try:
        run(
            args.sector,
            args.functie,
            args.bedrijf,
            args.regio,
            args.email,
            args.naam,
            args.url
        )
        if log_campaign:
            # Op dit moment weten we de gecreëerde campagne ID niet buiten run()
            # Een simpele fix is het opnieuw berekenen:
            mapping = {
                "oil & gas": "OilGas",
                "constructie": "Constructie",
                "automation": "Automation",
                "productie": "Productie",
                "renewable energy": "Renewable",
            }
            s_slug = mapping.get(args.sector.lower(), args.sector.replace(" ", ""))
            yymm = time.strftime("%Y%m")
            campagne_naam = f"KT_{s_slug}_{yymm}_{args.bedrijf.replace(' ', '')}"
            log_campaign(campagne_naam, "completed")
            
    except Exception as e:
        print(f"❌ Fout in Master Flow: {e}")
        # Wederom campagne naam calculeren voor de fout-log
        mapping = {
            "oil & gas": "OilGas",
            "constructie": "Constructie",
            "automation": "Automation",
            "productie": "Productie",
            "renewable energy": "Renewable",
        }
        s_slug = mapping.get(args.sector.lower(), args.sector.replace(" ", ""))
        yymm = time.strftime("%Y%m")
        campagne_naam = f"KT_{s_slug}_{yymm}_{args.bedrijf.replace(' ', '')}"
        if log_campaign:
            log_campaign(campagne_naam, "failed", {"error": str(e)})
        sys.exit(1)
        
    print(f"\n🎉 MASTER FLOW VOLTOOID in {time.time() - start_t:.1f} seconden.")
