#!/usr/bin/env python3
"""
supabase_library.py — Vacaturekanon Asset Library Client
Gebruikt Supabase REST API direct (geen supabase-py dependency nodig).

Project: recruitin-growth-engine
URL:     https://vaiikkhaulkqdknwvroj.supabase.co

Tabellen (aanmaken via --setup-schema):
  campaigns        — Klant/campagne metadata
  assets           — Gegenereerde images en videos
  reference_library — Goedgekeurde benchmark assets

Usage:
  python3 supabase_library.py --test
  python3 supabase_library.py --setup-schema
  python3 supabase_library.py --list-campaigns
  python3 supabase_library.py --seed-heijmans
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

# ── Config ─────────────────────────────────────────────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://vaiikkhaulkqdknwvroj.supabase.co")
SUPABASE_KEY = os.environ.get(
    "SUPABASE_ANON_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZhaWlra2hhdWxrcWRrbnd2cm9qIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzAzNDM2MzcsImV4cCI6MjA4NTkxOTYzN30.ZAzmG-QF1QZgEbG4ajw9K8KiwgJ0Mk1U741ZpryU-cg"
)

# ── SQL Schema ─────────────────────────────────────────────────────────────
SCHEMA_SQL = """
-- ════════════════════════════════════════════════════════════
-- VACATUREKANON Asset Library Schema
-- Project: recruitin-growth-engine
-- Voer uit in Supabase SQL Editor (dashboard → SQL Editor)
-- ════════════════════════════════════════════════════════════

-- Campagnes tabel
CREATE TABLE IF NOT EXISTS campaigns (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    klant_naam      TEXT NOT NULL,
    sector          TEXT NOT NULL,
    rol_titel       TEXT,
    contact_naam    TEXT,
    contact_email   TEXT,
    contact_tel     TEXT,
    vacature_url    TEXT,
    website         TEXT,
    primaire_kleur  TEXT DEFAULT '#0066CC',
    status          TEXT DEFAULT 'pending',
    notes           TEXT,
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Assets tabel
CREATE TABLE IF NOT EXISTS assets (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    campaign_id     UUID REFERENCES campaigns(id) ON DELETE CASCADE,
    asset_type      TEXT NOT NULL,
    scene           TEXT,
    file_name       TEXT,
    local_path      TEXT,
    drive_url       TEXT,
    prompt_used     TEXT,
    ai_tool         TEXT DEFAULT 'nano_banana_pro',
    quality_score   INTEGER,
    is_reference    BOOLEAN DEFAULT FALSE,
    notes           TEXT
);

-- Reference library
CREATE TABLE IF NOT EXISTS reference_library (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    added_at        TIMESTAMPTZ DEFAULT NOW(),
    campaign_id     UUID REFERENCES campaigns(id),
    asset_id        UUID REFERENCES assets(id),
    sector          TEXT NOT NULL,
    scene           TEXT,
    quality_tier    TEXT DEFAULT 'silver',
    ai_tool         TEXT,
    prompt_snapshot TEXT,
    tags            TEXT[],
    added_by        TEXT DEFAULT 'wouter_arts'
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_assets_campaign ON assets(campaign_id);
CREATE INDEX IF NOT EXISTS idx_assets_scene ON assets(scene);
CREATE INDEX IF NOT EXISTS idx_ref_sector ON reference_library(sector);
CREATE INDEX IF NOT EXISTS idx_ref_tier ON reference_library(quality_tier);

-- Updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS campaigns_updated_at ON campaigns;
CREATE TRIGGER campaigns_updated_at
    BEFORE UPDATE ON campaigns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
"""

# ── Heijmans BTS Reference Data ────────────────────────────────────────────
HEIJMANS_DIR = Path(
    "/Users/wouterarts/Library/CloudStorage/"
    "OneDrive-Gedeeldebibliotheken-Recruitin/"
    "meta-campaigns/assets/Heijmans_BTS_A_202603"
)

HEIJMANS_SCENES = {
    "bts_bloopers/2_interview.png":       {"scene": "awareness",     "tags": ["golden_hour", "interview", "outdoor", "construction", "authentic"]},
    "bts_bloopers/3_hero_v3.png":         {"scene": "conversion",    "tags": ["night", "hero", "cinematic", "outdoor", "construction", "epic"]},
    "bts_bloopers/4a_forgot_lines.png":   {"scene": "awareness",     "tags": ["golden_hour", "emotion", "authentic", "humor", "construction"]},
    "bts_bloopers/4b_wrong_truck_v3.png": {"scene": "consideration", "tags": ["night", "outdoor", "storytelling", "construction"]},
    "bts_bloopers/1_clapperboard.png":    {"scene": "awareness",     "tags": ["bts", "clapperboard", "construction", "golden_hour"]},
    "v3/char-front.png":                  {"scene": "char_front",    "tags": ["portrait", "front_facing", "construction", "orange_hivis"]},
    "v3/B2-briefing.png":                 {"scene": "consideration", "tags": ["teamwork", "briefing", "outdoor", "construction"]},
    "v3/B1-arrival.png":                  {"scene": "awareness",     "tags": ["arrival", "outdoor", "golden_hour", "construction"]},
}


class VacaturekanonLibrary:
    """Supabase REST API client voor de Vacaturekanon asset library."""

    def __init__(self):
        self.url = SUPABASE_URL.rstrip("/")
        self.key = SUPABASE_KEY

    def _headers(self, extra=None):
        h = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }
        if extra:
            h.update(extra)
        return h

    def _get(self, path, params=""):
        url = f"{self.url}/rest/v1/{path}{params}"
        req = urllib.request.Request(url, headers=self._headers())
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            print(f"❌ GET {path}: HTTP {e.code} — {e.read().decode()[:200]}")
            return None
        except Exception as e:
            print(f"❌ GET {path}: {e}")
            return None

    def _post(self, path, data):
        url = f"{self.url}/rest/v1/{path}"
        body = json.dumps(data).encode()
        req = urllib.request.Request(url, data=body, headers=self._headers(), method="POST")
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            print(f"❌ POST {path}: HTTP {e.code} — {body[:200]}")
            return None
        except Exception as e:
            print(f"❌ POST {path}: {e}")
            return None

    def _patch(self, path, filter_param, data):
        url = f"{self.url}/rest/v1/{path}?{filter_param}"
        body = json.dumps(data).encode()
        req = urllib.request.Request(url, data=body, headers=self._headers(), method="PATCH")
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status
        except urllib.error.HTTPError as e:
            print(f"❌ PATCH {path}: HTTP {e.code}")
            return None
        except Exception as e:
            print(f"❌ PATCH {path}: {e}")
            return None

    def test_connection(self) -> bool:
        """Test of de Supabase verbinding werkt."""
        result = self._get("")
        return result is not None

    # ── Campaigns ──────────────────────────────────────────────────────────

    def create_campaign(self, klant_naam: str, sector: str, **kwargs) -> str | None:
        data = {
            "klant_naam":     klant_naam,
            "sector":         sector,
            "rol_titel":      kwargs.get("rol_titel"),
            "contact_naam":   kwargs.get("contact_naam"),
            "contact_email":  kwargs.get("contact_email"),
            "contact_tel":    kwargs.get("contact_tel"),
            "vacature_url":   kwargs.get("vacature_url"),
            "website":        kwargs.get("website"),
            "primaire_kleur": kwargs.get("primaire_kleur", "#0066CC"),
            "status":         "pending",
            "notes":          kwargs.get("notes"),
        }
        result = self._post("vk_campaigns", data)
        if result and isinstance(result, list) and result:
            cid = result[0]["id"]
            print(f"✅ Campagne: {klant_naam} [{cid[:8]}...]")
            return cid
        return None

    def update_status(self, campaign_id: str, status: str):
        self._patch("vk_campaigns", f"id=eq.{campaign_id}", {"status": status})

    def list_campaigns(self, limit: int = 20) -> list:
        result = self._get("vk_campaigns", f"?order=created_at.desc&limit={limit}")
        return result or []

    # ── Assets ─────────────────────────────────────────────────────────────

    def register_asset(
        self,
        campaign_id: str,
        asset_type: str,
        scene: str,
        local_path: str = "",
        prompt_used: str = "",
        ai_tool: str = "nano_banana_pro",
        quality_score: int = None,
        is_reference: bool = False,
        notes: str = "",
    ) -> str | None:
        data = {
            "campaign_id":   campaign_id,
            "asset_type":    asset_type,
            "scene":         scene,
            "file_name":     Path(local_path).name if local_path else None,
            "local_path":    local_path or None,
            "prompt_used":   (prompt_used[:2000] if prompt_used else None),
            "ai_tool":       ai_tool,
            "quality_score": quality_score,
            "is_reference":  is_reference,
            "notes":         notes or None,
        }
        result = self._post("vk_assets", data)
        if result and isinstance(result, list) and result:
            return result[0]["id"]
        return None

    # ── Reference Library ──────────────────────────────────────────────────

    def add_reference(
        self,
        campaign_id: str,
        asset_id: str,
        sector: str,
        scene: str,
        quality_tier: str = "silver",
        ai_tool: str = "nano_banana_pro",
        prompt_snapshot: str = "",
        tags: list = None,
    ) -> bool:
        data = {
            "campaign_id":     campaign_id,
            "asset_id":        asset_id,
            "sector":          sector,
            "scene":           scene,
            "quality_tier":    quality_tier,
            "ai_tool":         ai_tool,
            "prompt_snapshot": prompt_snapshot[:3000] if prompt_snapshot else None,
            "tags":            tags or [],
        }
        result = self._post("vk_reference_library", data)
        if result:
            print(f"  ⭐ Reference [{quality_tier}]: {sector}/{scene} {tags}")
            return True
        return False

    def get_references(self, sector: str = None, quality_tier: str = None) -> list:
        params = "?order=added_at.desc"
        if sector:
            params += f"&sector=eq.{sector}"
        if quality_tier:
            params += f"&quality_tier=eq.{quality_tier}"
        return self._get("vk_reference_library", params) or []

    # ── Heijmans Seeding ───────────────────────────────────────────────────

    def seed_heijmans(self) -> bool:
        print("🌱 Seeden: Heijmans BTS als gold reference...")

        cid = self.create_campaign(
            klant_naam="Heijmans NV",
            sector="constructie",
            rol_titel="Senior Uitvoerder Wegenbouw",
            website="heijmans.nl",
            notes="GOLD benchmark — Heijmans BTS_A_202603 campagne"
        )
        if not cid:
            print("❌ Kon campagne niet aanmaken")
            return False

        ok = 0
        for rel, meta in HEIJMANS_SCENES.items():
            full = HEIJMANS_DIR / rel
            if not full.exists():
                print(f"  ⚠️  Niet gevonden: {rel}")
                continue

            aid = self.register_asset(
                campaign_id=cid,
                asset_type="image",
                scene=meta["scene"],
                local_path=str(full),
                ai_tool="leonardo_phoenix_v1",
                quality_score=5,
                is_reference=True,
                notes="Heijmans BTS gold benchmark",
            )
            if aid:
                self.add_reference(
                    campaign_id=cid,
                    asset_id=aid,
                    sector="constructie",
                    scene=meta["scene"],
                    quality_tier="gold",
                    ai_tool="leonardo_phoenix_v1",
                    tags=meta["tags"],
                )
                ok += 1

        self.update_status(cid, "done")
        print(f"\n✅ {ok}/{len(HEIJMANS_SCENES)} Heijmans assets als gold reference gezaaid")
        return ok > 0


def load_env():
    for p in [
        Path(__file__).parent / ".env",
        Path("/Users/wouterarts/Library/CloudStorage/OneDrive-Gedeeldebibliotheken-Recruitin/output/vacaturekanon/scripts/.env"),
    ]:
        if p.exists():
            for line in p.read_text().splitlines():
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())
            break


def main():
    load_env()
    parser = argparse.ArgumentParser(description="Vacaturekanon Supabase Library")
    parser.add_argument("--test",           action="store_true", help="Test verbinding")
    parser.add_argument("--setup-schema",   action="store_true", help="Print SQL schema")
    parser.add_argument("--list-campaigns", action="store_true", help="Toon campagnes")
    parser.add_argument("--seed-heijmans",  action="store_true", help="Seed Heijmans BTS gold")
    parser.add_argument("--list-reference", metavar="SECTOR",    help="Toon reference library (of 'all')")
    args = parser.parse_args()

    if args.setup_schema:
        print(SCHEMA_SQL)
        return

    lib = VacaturekanonLibrary()

    if args.test:
        ok = lib.test_connection()
        print("✅ Supabase verbinding OK" if ok else "❌ Verbinding mislukt")
        return

    if args.list_campaigns:
        camps = lib.list_campaigns()
        if not camps:
            print("Geen campagnes (of tabellen bestaan nog niet — run --setup-schema)")
            return
        print(f"\n{'ID':10} {'Klant':20} {'Sector':12} {'Status'}")
        print("-" * 55)
        for c in camps:
            print(f"{c['id'][:8]:10} {c['klant_naam']:20} {c['sector']:12} {c['status']}")
        return

    if args.seed_heijmans:
        lib.seed_heijmans()
        return

    if args.list_reference:
        sector = None if args.list_reference == "all" else args.list_reference
        refs = lib.get_references(sector=sector)
        if not refs:
            print("Geen reference assets")
            return
        for r in refs:
            t = ", ".join(r.get("tags") or [])
            print(f"[{r['quality_tier']:6}] {r['sector']:12} {r['scene']:14} {t}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
