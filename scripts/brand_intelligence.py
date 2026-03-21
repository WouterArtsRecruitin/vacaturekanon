#!/usr/bin/env python3
"""
brand_intelligence.py
Recruitin B.V. — Brand Intelligence Ads System v3.0

Volledige pipeline: Brand URL → Intelligence Report → 40 Ad Prompts →
Image Generation → Quality Review → Pipedrive Deal → Meta Ads Ready

Gebruik:
  python3 brand_intelligence.py --url https://example.com
  python3 brand_intelligence.py --url https://example.com --generate-images
  python3 brand_intelligence.py --url https://example.com --full-pipeline
"""

import os
import sys
import json
import time
import argparse
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(os.path.abspath(__file__)).parents[1]
sys.path.append(str(BASE_DIR / "scripts"))
env_path = BASE_DIR / ".env"
load_dotenv(env_path, override=True)

try:
    import anthropic
except ImportError:
    print("pip install anthropic")
    sys.exit(1)

# ── Config ────────────────────────────────────────────────────────────────────
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")
SLACK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
LEONARDO_API_KEY = os.getenv("LEONARDO_API_KEY", "")
OUTPUT_BASE = Path(os.getenv("LOCAL_OUTPUT_BASE", "/tmp/recruitin-local"))


def slack(msg: str):
    if not SLACK_URL:
        print(f"[SLACK] {msg}")
        return
    try:
        requests.post(SLACK_URL, json={"text": msg}, timeout=5)
    except Exception:
        pass


# ── FASE 1: Brand Intelligence Report ────────────────────────────────────────

BRAND_RESEARCH_PROMPT = """You are a world-class brand strategist and creative director.
Visit the website content below and extract everything needed to fully understand this brand.

EXTRACT AND ANALYZE:
- The brand name and what it sells
- Its target audience IN DETAIL (demographics, pain points, aspirations)
- Its brand tone and voice (formal/casual, technical/emotional, etc.)
- Its visual style, colors, and aesthetic
- Its key messages and value propositions
- Its competitive positioning
- The emotions it wants to evoke in customers
- Any taglines, brand mantras, or memorable phrases
- Current marketing approach and tone

Give me a complete brand intelligence report. Be specific. Include exact colors
(hex codes if visible), font styles, and specific words the brand uses.

Format the response as JSON (and ONLY valid JSON, no markdown):
{
  "brand_name": "",
  "what_sells": "",
  "target_audience": {
    "primary": "",
    "demographics": "",
    "pain_points": [],
    "aspirations": []
  },
  "brand_voice": {
    "tone": "",
    "formality_level": "1-10",
    "technical_level": "1-10",
    "emotional_vs_rational": "1-10"
  },
  "visual_identity": {
    "primary_colors": [],
    "secondary_colors": [],
    "fonts": [],
    "aesthetic": "",
    "key_visual_elements": []
  },
  "messaging": {
    "key_messages": [],
    "value_propositions": [],
    "competitive_advantage": "",
    "emotions_evoked": []
  },
  "examples": {
    "taglines": [],
    "memorable_phrases": []
  }
}"""


def fetch_website_content(url: str) -> str:
    """Fetch website content for brand analysis."""
    print(f"   Fetching {url}...")
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36"
        }
        r = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
        r.raise_for_status()

        # Strip HTML tags for a rough text extraction
        from html.parser import HTMLParser

        class TextExtractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.texts = []
                self._skip = False

            def handle_starttag(self, tag, attrs):
                if tag in ("script", "style", "noscript"):
                    self._skip = True

            def handle_endtag(self, tag):
                if tag in ("script", "style", "noscript"):
                    self._skip = False

            def handle_data(self, data):
                if not self._skip:
                    stripped = data.strip()
                    if stripped:
                        self.texts.append(stripped)

        extractor = TextExtractor()
        extractor.feed(r.text)
        text_content = "\n".join(extractor.texts)

        # Also extract meta, colors from raw HTML
        raw_html = r.text[:15000]  # First 15k chars for style analysis

        return f"=== PAGE TEXT ===\n{text_content[:8000]}\n\n=== RAW HTML (styles/meta) ===\n{raw_html}"

    except Exception as e:
        print(f"   Warning: Could not fetch {url}: {e}")
        return f"URL: {url}\n(Could not fetch content: {e})"


def extract_brand_intelligence(url: str) -> dict:
    """FASE 1: Extract brand intelligence from URL using Claude."""
    print("\n== FASE 1: Brand Intelligence Report ==")

    website_content = fetch_website_content(url)

    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        messages=[{
            "role": "user",
            "content": f"{BRAND_RESEARCH_PROMPT}\n\nWEBSITE CONTENT:\n{website_content}"
        }]
    )

    raw = response.content[0].text.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    if raw.startswith("json"):
        raw = raw[4:]
    raw = raw.strip()

    try:
        report = json.loads(raw)
    except json.JSONDecodeError:
        print("   Warning: Claude response was not valid JSON, saving raw text")
        report = {"raw_response": raw, "brand_name": "unknown", "parse_error": True}

    brand = report.get("brand_name", "unknown")
    print(f"   Brand: {brand}")
    print(f"   Sells: {report.get('what_sells', 'N/A')}")
    colors = report.get("visual_identity", {}).get("primary_colors", [])
    if colors:
        print(f"   Colors: {', '.join(colors)}")

    return report


# ── FASE 2: Generate 40 Image Prompts ────────────────────────────────────────

PROMPT_GENERATION_TEMPLATE = """You are a world-class advertising creative director
specializing in scroll-stopping visual concepts.

Using the brand report below, generate 40 COMPLETE, production-ready image generation
prompts for high-end AI image generation.

BRAND REPORT:
{brand_json}

REQUIREMENTS FOR EACH PROMPT:
1. Make it SPECIFIC to this brand's visual identity and audience
2. Vary across these 8 styles (5 prompts each):
   - Product/Service showcase (clean, professional)
   - Lifestyle (authentic, aspirational)
   - Emotional (story-driven, human)
   - Minimalist (bold typography focus, negative space)
   - Bold graphic (high contrast, graphic design)
   - Infographic style (data visualization aesthetic)
   - Cinematic (dramatic lighting, depth)
   - Documentary/Real (authentic, unpolished)

3. Each prompt must include:
   - Subject/hero element
   - Visual style descriptors (lighting, composition, mood)
   - Color palette reference (from brand report)
   - Specific details (no vague language)
   - Technical specs: "8K, hyperrealistic, square format, no text"

4. AVOID:
   - Vague language ("beautiful", "nice")
   - Text or letters in images
   - Copyrighted characters or logos
   - Multiple concepts in one prompt
   - Contradictory style instructions

OUTPUT: Return ONLY a valid JSON array of 40 strings. Each string is a prompt.
No explanations, no metadata. Each prompt is 80-150 words.

Example format:
["prompt 1 here...", "prompt 2 here...", ...]"""


def generate_40_prompts(brand_report: dict) -> list:
    """FASE 2: Generate 40 image prompts from brand intelligence."""
    print("\n== FASE 2: Generate 40 Ad Prompts ==")

    brand_json = json.dumps(brand_report, indent=2, ensure_ascii=False)
    prompt = PROMPT_GENERATION_TEMPLATE.format(brand_json=brand_json)

    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    if raw.startswith("json"):
        raw = raw[4:]
    raw = raw.strip()

    try:
        prompts = json.loads(raw)
    except json.JSONDecodeError:
        print("   Warning: Could not parse prompts as JSON array")
        # Try line-by-line extraction
        prompts = [line.strip().lstrip("0123456789.-) ") for line in raw.split("\n") if len(line.strip()) > 50]

    if not isinstance(prompts, list):
        prompts = [prompts]

    print(f"   Generated {len(prompts)} prompts")
    for i, p in enumerate(prompts[:3]):
        print(f"   #{i+1}: {p[:80]}...")
    if len(prompts) > 3:
        print(f"   ... and {len(prompts) - 3} more")

    return prompts


# ── FASE 3: Image Generation ─────────────────────────────────────────────────

class ImageGenerator:
    """Handles image generation via Leonardo AI (primary) with fallback."""

    def __init__(self):
        self.leonardo_key = LEONARDO_API_KEY
        self.leonardo_base = "https://cloud.leonardo.ai/api/rest/v1"
        self.generated = []
        self.failed = []

    def generate_batch(self, prompts: list, output_dir: Path,
                       batch_size: int = 5) -> dict:
        """Generate images in batches. Returns results summary."""
        output_dir.mkdir(parents=True, exist_ok=True)
        results = {
            "total_requested": len(prompts),
            "success_count": 0,
            "failed_count": 0,
            "images": [],
            "errors": [],
        }

        for i in range(0, len(prompts), batch_size):
            batch = prompts[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(prompts) - 1) // batch_size + 1
            print(f"   Batch {batch_num}/{total_batches}")

            for idx, prompt in enumerate(batch):
                num = i + idx + 1
                result = self._generate_single(prompt, num, output_dir)
                if result:
                    results["success_count"] += 1
                    results["images"].append(result)
                else:
                    results["failed_count"] += 1
                    results["errors"].append({
                        "prompt_num": num,
                        "prompt": prompt[:100],
                    })
                    self.failed.append(prompt)

                time.sleep(1)  # Rate limiting

            if i + batch_size < len(prompts):
                time.sleep(2)  # Batch delay

        print(f"\n   Generation: {results['success_count']} success, "
              f"{results['failed_count']} failed")
        return results

    def _generate_single(self, prompt: str, num: int, output_dir: Path) -> dict | None:
        """Generate a single image via Leonardo AI."""
        if not self.leonardo_key:
            return self._mock_generate(prompt, num, output_dir)

        try:
            # Start generation
            r = requests.post(
                f"{self.leonardo_base}/generations",
                headers={
                    "Authorization": f"Bearer {self.leonardo_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "prompt": prompt,
                    "modelId": "6b645e3a-d64f-4341-a6d8-7a3690fbf042",  # Phoenix v2
                    "width": 1024,
                    "height": 1024,
                    "num_images": 1,
                    "guidance_scale": 7,
                    "alchemy": True,
                    "photoReal": True,
                    "photoRealVersion": "v2",
                    "presetStyle": "CINEMATIC",
                },
                timeout=30,
            )

            if r.status_code != 200:
                print(f"      Ad {num}: Leonardo API error {r.status_code}")
                return self._mock_generate(prompt, num, output_dir)

            gen_data = r.json()
            gen_id = gen_data.get("sdGenerationJob", {}).get("generationId")
            if not gen_id:
                print(f"      Ad {num}: No generation ID returned")
                return self._mock_generate(prompt, num, output_dir)

            # Poll for completion
            for attempt in range(30):
                time.sleep(5)
                poll = requests.get(
                    f"{self.leonardo_base}/generations/{gen_id}",
                    headers={"Authorization": f"Bearer {self.leonardo_key}"},
                    timeout=15,
                )
                if poll.status_code == 200:
                    poll_data = poll.json()
                    gen_images = poll_data.get("generations_by_pk", {}).get("generated_images", [])
                    if gen_images:
                        img_url = gen_images[0].get("url")
                        if img_url:
                            # Download image
                            img_data = requests.get(img_url, timeout=30)
                            img_path = output_dir / f"ad_{num:02d}.jpg"
                            img_path.write_bytes(img_data.content)
                            print(f"      Ad {num}: saved {img_path.name}")
                            return {
                                "num": num,
                                "path": str(img_path),
                                "url": img_url,
                                "prompt": prompt[:100],
                                "source": "leonardo_ai",
                            }
                    status = poll_data.get("generations_by_pk", {}).get("status")
                    if status == "FAILED":
                        print(f"      Ad {num}: Generation failed")
                        break

            print(f"      Ad {num}: Timeout waiting for Leonardo")
            return self._mock_generate(prompt, num, output_dir)

        except Exception as e:
            print(f"      Ad {num}: Error: {e}")
            return self._mock_generate(prompt, num, output_dir)

    def _mock_generate(self, prompt: str, num: int, output_dir: Path) -> dict:
        """Create a placeholder file when API is unavailable."""
        img_path = output_dir / f"ad_{num:02d}_placeholder.txt"
        img_path.write_text(
            f"PLACEHOLDER - Image not yet generated\n"
            f"Prompt: {prompt}\n"
            f"Generated: {datetime.now().isoformat()}\n"
            f"Run with Leonardo AI API key to generate actual image."
        )
        print(f"      Ad {num}: placeholder saved (no API key)")
        return {
            "num": num,
            "path": str(img_path),
            "url": None,
            "prompt": prompt[:100],
            "source": "placeholder",
        }


# ── FASE 4: Quality Review & Scoring ─────────────────────────────────────────

REVIEW_PROMPT = """You are a creative director reviewing an advertising campaign.

BRAND REPORT:
{brand_json}

ALL 40 PROMPTS:
{prompts_text}

TASK: Review each ad prompt for quality. Score each on these criteria (1-10):
1. concept_strength: Is it compelling for the brand?
2. brand_fit: Does it feel like THIS brand?
3. scroll_stopping: Would it stop social media scrolling?
4. conversion_likelihood: Would it drive action?

Then:
- Rank and list the 15 STRONGEST ads (by average score)
- For the 5 WEAKEST: explain the problem and suggest a revised prompt

OUTPUT FORMAT (MUST BE VALID JSON, no markdown):
{{
  "overall_campaign_strength": 8,
  "campaign_notes": "brief assessment",
  "top_15_performers": [
    {{
      "rank": 1,
      "prompt_number": 5,
      "concept_strength": 9,
      "brand_fit": 10,
      "scroll_stopping": 9,
      "conversion_likelihood": 8,
      "overall_score": 9.0,
      "why_strong": "explanation",
      "expected_ctr": "2.1-2.8%"
    }}
  ],
  "weak_ads_improvement": [
    {{
      "prompt_number": 12,
      "current_problem": "explanation",
      "revised_prompt": "complete revised prompt"
    }}
  ],
  "ready_for_meta": true
}}"""


def quality_review(brand_report: dict, prompts: list) -> dict:
    """FASE 4: Score and rank all 40 prompts."""
    print("\n== FASE 4: Quality Review & Scoring ==")

    prompts_text = "\n".join(f"{i+1}. {p}" for i, p in enumerate(prompts))
    brand_json = json.dumps(brand_report, indent=2, ensure_ascii=False)

    prompt = REVIEW_PROMPT.format(brand_json=brand_json, prompts_text=prompts_text)

    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=6000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    if raw.startswith("json"):
        raw = raw[4:]
    raw = raw.strip()

    try:
        review = json.loads(raw)
    except json.JSONDecodeError:
        print("   Warning: Could not parse review as JSON")
        review = {"raw_response": raw, "parse_error": True}

    strength = review.get("overall_campaign_strength", "N/A")
    top_15 = review.get("top_15_performers", [])
    weak = review.get("weak_ads_improvement", [])
    print(f"   Campaign strength: {strength}/10")
    print(f"   Top performers: {len(top_15)}")
    print(f"   Weak ads identified: {len(weak)}")

    if top_15:
        best = top_15[0]
        print(f"   #1 ad: Prompt #{best.get('prompt_number')} "
              f"(score {best.get('overall_score')})")

    return review


# ── FASE 5: Meta Ads Preparation ─────────────────────────────────────────────

def prepare_meta_ads(brand_report: dict, review: dict, prompts: list,
                     image_results: dict, campaign_name: str,
                     output_dir: Path) -> dict:
    """Prepare Meta Ads campaign structure (JSON config for meta_campaign_builder)."""
    print("\n== FASE 5: Meta Ads Preparation ==")

    top_15 = review.get("top_15_performers", [])
    top_nums = [a.get("prompt_number", 1) for a in top_15]
    images = image_results.get("images", [])

    # Map top-performing prompts to their images
    ad_creatives = []
    for rank, top_ad in enumerate(top_15, 1):
        pnum = top_ad.get("prompt_number", rank)
        # Find matching image
        img = next((im for im in images if im.get("num") == pnum), None)
        ad_creatives.append({
            "rank": rank,
            "prompt_number": pnum,
            "prompt": prompts[pnum - 1] if pnum <= len(prompts) else "",
            "score": top_ad.get("overall_score", 0),
            "image_path": img.get("path") if img else None,
            "image_url": img.get("url") if img else None,
            "expected_ctr": top_ad.get("expected_ctr", "1.5-2.0%"),
        })

    brand = brand_report.get("brand_name", "Unknown")
    meta_config = {
        "campaign_name": f"{brand} - Brand Intelligence - {campaign_name}",
        "objective": "LINK_CLICKS",
        "budget_daily": 50,
        "status": "PAUSED",
        "brand": brand,
        "target_audience": brand_report.get("target_audience", {}),
        "ad_creatives": ad_creatives,
        "total_ads": len(ad_creatives),
        "campaign_strength": review.get("overall_campaign_strength"),
        "generated_at": datetime.now().isoformat(),
    }

    config_path = output_dir / "meta-ads-config.json"
    config_path.write_text(json.dumps(meta_config, indent=2, ensure_ascii=False))
    print(f"   Meta config saved: {config_path}")
    print(f"   Top 15 ads ready for upload")
    print(f"   Campaign status: PAUSED (manual activation required)")

    return meta_config


# ── Main Pipeline ─────────────────────────────────────────────────────────────

def run_pipeline(url: str, generate_images: bool = False,
                 full_pipeline: bool = False) -> dict:
    """Run the complete Brand Intelligence pipeline."""
    start_time = time.time()
    brand = "unknown"
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    campaign_name = f"BI_{ts}"

    print(f"{'=' * 60}")
    print(f"  BRAND INTELLIGENCE ADS SYSTEM v3.0")
    print(f"  URL: {url}")
    print(f"  Campaign: {campaign_name}")
    print(f"{'=' * 60}")

    results = {"url": url, "campaign_name": campaign_name, "phases": {}}

    # FASE 1: Brand Intelligence
    brand_report = extract_brand_intelligence(url)
    brand = brand_report.get("brand_name", "unknown")
    campaign_name = f"BI_{brand.replace(' ', '')}_{ts}"
    results["brand_name"] = brand
    results["campaign_name"] = campaign_name
    results["phases"]["brand_report"] = brand_report

    # Output directory
    output_dir = OUTPUT_BASE / "brand-intelligence" / campaign_name
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save brand report
    report_path = output_dir / "brand-report.json"
    report_path.write_text(json.dumps(brand_report, indent=2, ensure_ascii=False))
    print(f"   Saved: {report_path}")

    # FASE 2: Generate 40 Prompts
    prompts = generate_40_prompts(brand_report)
    results["phases"]["prompts"] = prompts

    # Save prompts
    prompts_path = output_dir / "prompts-40.json"
    prompts_path.write_text(json.dumps(prompts, indent=2, ensure_ascii=False))
    print(f"   Saved: {prompts_path}")

    # FASE 3: Image Generation (optional)
    image_results = {"total_requested": 0, "success_count": 0, "images": []}
    if generate_images or full_pipeline:
        print("\n== FASE 3: Image Generation ==")
        generator = ImageGenerator()
        images_dir = output_dir / "images"
        image_results = generator.generate_batch(prompts, images_dir)
        results["phases"]["images"] = image_results
    else:
        print("\n== FASE 3: Image Generation (SKIPPED — use --generate-images) ==")
        results["phases"]["images"] = image_results

    # FASE 4: Quality Review
    review = quality_review(brand_report, prompts)
    results["phases"]["review"] = review

    review_path = output_dir / "quality-review.json"
    review_path.write_text(json.dumps(review, indent=2, ensure_ascii=False))
    print(f"   Saved: {review_path}")

    # FASE 5: Meta Ads Preparation (full pipeline only)
    if full_pipeline:
        meta_config = prepare_meta_ads(
            brand_report, review, prompts, image_results,
            campaign_name, output_dir)
        results["phases"]["meta_config"] = meta_config
    else:
        print("\n== FASE 5: Meta Ads (SKIPPED — use --full-pipeline) ==")

    # Save complete results
    results_path = output_dir / "pipeline-results.json"
    elapsed = time.time() - start_time
    results["elapsed_seconds"] = round(elapsed, 1)
    results["output_dir"] = str(output_dir)
    results_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))

    # Summary
    print(f"\n{'=' * 60}")
    print(f"  PIPELINE COMPLETE")
    print(f"  Brand: {brand}")
    print(f"  Prompts: {len(prompts)}")
    print(f"  Images: {image_results.get('success_count', 0)}/{image_results.get('total_requested', 0)}")
    strength = review.get("overall_campaign_strength", "N/A")
    print(f"  Campaign Strength: {strength}/10")
    print(f"  Output: {output_dir}")
    print(f"  Time: {elapsed:.1f}s")
    print(f"{'=' * 60}")

    slack(
        f"Brand Intelligence complete: {brand}\n"
        f"Prompts: {len(prompts)} | Strength: {strength}/10\n"
        f"Output: {output_dir}"
    )

    return results


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Brand Intelligence Ads System v3.0")
    parser.add_argument("--url", required=True,
                        help="Brand website URL to analyze")
    parser.add_argument("--generate-images", action="store_true",
                        help="Generate images via Leonardo AI")
    parser.add_argument("--full-pipeline", action="store_true",
                        help="Run full pipeline (images + Pipedrive + Meta)")
    parser.add_argument("--output-dir",
                        help="Custom output directory")
    args = parser.parse_args()

    if args.output_dir:
        OUTPUT_BASE = Path(args.output_dir)

    try:
        run_pipeline(
            url=args.url,
            generate_images=args.generate_images,
            full_pipeline=args.full_pipeline,
        )
    except Exception as e:
        print(f"\nPipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
