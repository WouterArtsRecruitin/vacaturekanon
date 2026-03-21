#!/usr/bin/env python3
"""
VACATUREKANON: 40 Image Generation via Leonardo AI API
Generates all 40 prompts in batches with error handling
"""

import requests
import time
import json
import os
from typing import List, Dict
from datetime import datetime

# API Configuration
LEONARDO_API_KEY = os.environ.get("LEONARDO_API_KEY", "")
LEONARDO_API_URL = "https://api.leonardo.ai/v1/generations"

# All 40 Vacaturekanon Prompts

VACATUREKANON_PROMPTS = [
    # STYLE 1: PRODUCT SHOWCASE (5)
    "Close-up shot of a modern laptop displaying the Vacaturekanon dashboard interface, showing recruitment metrics, automated campaign management, and candidate data streams in real-time. Soft studio lighting with subtle shadows, shot at 45-degree angle. Navy blue (#003366) and orange (#FF6B35) accent colors in the UI. Clean white background with shallow depth of field. Professional, corporate photography style. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    "Bird's eye view of a minimalist workspace with a tablet showing Vacaturekanon's AI video generation interface, surrounded by soft warm lighting from desk lamps. Candidate profiles visible on screen with orange highlight bars indicating automation status. Modern Scandinavian office aesthetic. Warm golden hour light from window. Corporate tech photography. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    "Flat lay composition featuring a smartphone displaying Vacaturekanon's mobile dashboard interface with real-time candidate notifications, nested among productivity tools—keyboard, notebook, coffee cup. Navy and orange color palette integrated into design elements. Minimalist overhead photography with soft shadows. Professional workplace aesthetic. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    "Split-screen composition showing before/after recruitment workflow—left side showing traditional manual recruitment chaos (papers, stress), right side showing Vacaturekanon's automated dashboard with clean data visualization. Navy and orange gradient transition between sides. Modern infographic style. Studio lighting. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    "Close-up macro shot of a touchscreen interface showing Vacaturekanon's algorithm optimization in real-time—orange progress bars filling, metrics updating, candidate quality scores rising. Soft LED backlight creating ambient glow. Professional tech product photography. Modern, premium aesthetic. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    # STYLE 2: LIFESTYLE (5)
    "A confident CTO or engineering manager in a modern tech office, wearing casual business attire, smiling while reviewing candidate profiles on a large monitor displaying Vacaturekanon interface. Natural daylight from large windows, warm amber tones. Moment of satisfaction and control. Modern workplace culture photography. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    "Overhead shot of a diverse technical team gathered around a table with laptops, notebooks, and coffee, celebrating a successful hire. One laptop shows Vacaturekanon dashboard with an orange success indicator. Warm, collaborative atmosphere with natural light. Authentic team dynamics. Documentary-style workplace photography. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    "A manufacturing facility manager in hard hat and professional attire, standing confidently with arms crossed, with a digital overlay showing Vacaturekanon's candidate pipeline flowing into the facility. Industrial lighting mixed with modern UI elements. Bridge between traditional industry and tech automation. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    "Young technical director in modern glass-walled office, leaning back in chair with satisfied expression, phone in hand showing Vacaturekanon notification of new qualified candidate. Soft natural light, minimalist modern interior. Moment of ease and control. Premium lifestyle photography. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    "Engineering team members in safety vests and modern tech workspace hybrid setting, pointing at a digital display showing Vacaturekanon's AI video generation of their job opening. Mixed industrial and tech aesthetics. Authentic, diverse representation. Natural light from industrial windows. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    # STYLE 3: EMOTIONAL (5)
    "Abstract visualization of speed and momentum—orange and navy streaks moving dynamically across frame, representing fast-track hiring process. Particles and light rays creating sense of energy and forward motion. Dramatic lighting. Metaphorical tech aesthetic. Cinema-grade composition. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    "Powerful image of a candidate wave or data stream flowing directly into a hiring manager's hands—represented as orange and navy light particles coalescing. Symbolic representation of 'candidates delivered directly to inbox.' Ethereal, modern, aspirational. Cinematic lighting and composition. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    "Visual metaphor of liberation—chains breaking and transforming into orange light particles representing freedom from expensive headhunters. Dark background with dramatic spot lighting on breaking point. Symbolic and powerful. Modern motion graphics aesthetic rendered as photorealistic. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    "Icon representation of dominance—a technical professional standing confidently with upward-trending charts and automation symbols in navy and orange surrounding them. Heroic, powerful composition. Cinematic uplighting. Modern professional imagery. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    "Time acceleration visual—clock hands spinning fast around a hiring manager reviewing candidates, with motion blur and orange highlights showing speed. Metaphor for rapid hiring process. Dynamic, energetic composition. Studio lighting with motion effects. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    # STYLE 4: MINIMALIST (5)
    "Large bold typography reading 'RECRUIT' in navy (#003366) on a pure white background, with a subtle orange (#FF6B35) underline accent. Minimalist layout with abundant white space. Ultra-clean, premium aesthetic. Studio lighting with precise shadows. Square format composition. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    "Centered composition: single orange vertical line on navy background, with subtle geometric shapes suggesting upward growth and automation. Minimalist, modern, high-contrast design. Sacred geometry aesthetic. Perfectly balanced. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    "The word 'AUTOMATE' in elegant sans-serif, white text, positioned in lower third of navy background. Upper two-thirds pure, clean space suggesting clarity and simplicity. Sophisticated, minimal. Photography lighting. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    "Single candidate profile silhouette in orange (#FF6B35) on navy background, with orange arrow pointing directly right, suggesting direct delivery and control. Minimalist icon-style imagery. High contrast, bold, modern. Studio lighting. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    "Three geometric shapes—square (navy), circle (orange), triangle (white)—arranged to suggest process flow and automation in minimalist composition. Balanced, modern, clean. White background with soft studio lighting. Premium tech aesthetic. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    # STYLE 5: BOLD GRAPHIC (5)
    "Explosive digital burst of orange (#FF6B35) particles and navy (#003366) geometric shapes radiating from center point, representing algorithm activation and candidate generation. High energy, dynamic composition. Bold graphic design aesthetic rendered photorealistic. Studio lighting. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    "Large overlapping geometric shapes—hexagons and circles in navy, orange, and white—creating dynamic composition suggesting interconnected automation systems. Bold, modern, tech-forward aesthetic. High contrast. Studio lighting. Vector art rendered as photorealistic. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    "Split composition: left side showing tangled chaotic lines (traditional recruitment), right side showing clean organized lines flowing right (Vacaturekanon automation). Navy to orange gradient transition between sides. High contrast, dramatic lighting. Bold infographic style. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    "Large ascending bar chart in orange rising sharply against navy background, with small human figures celebrating at top—representing hiring success metrics and growth. Bold graphic design, eye-catching, optimistic. Studio lighting. Modern infographic rendered as photorealistic imagery. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    "Layered geometric composition showing interconnected nodes and pathways in navy and orange, suggesting AI network and algorithmic matching system. Bold, modern, high-tech aesthetic. High contrast. Studio lighting. Graphic design rendered photorealistic. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    # STYLE 6: INFOGRAPHIC (5)
    "Modern dashboard-style infographic showing recruitment metrics: cost-per-hire reduction, time-to-fill improvement, candidate quality scores—all trending positively in navy and orange. Clean, professional data visualization. Studio lighting. Photorealistic render of graphic design. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    "Timeline visualization showing traditional recruitment cycle (weeks/months, expensive) vs. Vacaturekanon cycle (days, efficient) with comparative metrics and icons. Navy and orange accent colors. Clean infographic style. Professional data presentation rendered photorealistic. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    "Circular process diagram showing the 'Recruit. Automate. Dominate.' three-step flow, with icons for each stage and metric indicators in navy/orange. Clean, modern data visualization. Studio lighting. Professional infographic rendered photorealistic. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    "Network diagram showing candidate-to-company matching system—nodes in orange and navy representing different candidate profiles connecting to hiring managers. Sophisticated data visualization. Studio lighting. Modern, tech-forward aesthetic. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    "Upward-trending funnel visualization showing recruitment process improvement metrics—candidates at top in orange, companies receiving qualified hires at bottom. Data-driven, professional. Navy and orange color scheme. Studio lighting. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    # STYLE 7: CINEMATIC (5)
    "Dramatic shot of a hiring manager in modern office, bathed in blue-orange cinematic lighting (navy and orange color temperature), reviewing candidate profiles with focused intensity. Cinematic depth of field, volumetric lighting. Storytelling about control and power. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    "Cinematic wide shot of a tech manufacturing facility interior with dramatic backlighting, human figures working, overlaid with orange Vacaturekanon interface elements showing real-time team optimization. Narrative of automation transforming industry. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    "Epic cinematic shot: candidate profiles in orange light flowing through a tunnel of modern office architecture, converging at a hiring manager silhouette in dramatic backlight. Metaphor for streamlined candidate delivery. Cinema-grade composition and lighting. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    "Moody cinematic shot of a laptop screen in dark environment, face-lit by the glow of Vacaturekanon interface showing candidate data streams. Dramatic side lighting. Moment of intense focus and breakthrough. Film noir meets tech aesthetic. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    "Cinematic overhead shot of a hiring team around glowing conference table, illuminated by warm orange and cool blue light from the Vacaturekanon interface displayed on table surface. Collaborative moment, dramatic chiaroscuro lighting. Story of team success. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    # STYLE 8: DOCUMENTARY (5)
    "Candid behind-the-scenes shot of an actual technical hiring team in an engineering office, one person pointing at monitor showing Vacaturekanon candidate match notification, others reacting authentically. Natural daylight, slightly grainy documentary aesthetic. Real workplace moment captured. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    "Raw, authentic footage-style shot of a manufacturing facility floor—workers and managers collaborating, with a digital interface overlay showing Vacaturekanon's candidate profile for new position. Blend of industrial reality and tech integration. Natural lighting. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    "Authentic moment: CTO in casual work clothes, typing on keyboard, receiving Vacaturekanon notification on phone, pausing to read with genuine interest. Unpolished, real office environment. Natural lighting from windows. Documentary photography style capturing authentic reaction. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    "Real-world scenario: diverse hiring team meeting in modern office, laptops open showing various stages of recruitment process on Vacaturekanon, papers scattered, coffee cups, genuine conversation captured mid-moment. Authentic workplace culture. Natural light. Documentary photojournalism style. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    "Hands-on shot showing actual interaction with Vacaturekanon interface—someone's hands pointing at screen, another person's reaction in background, desk environment with typical office clutter, natural daylight, slightly imperfect composition. Authentic, real-world moment. Journalistic photography. 8K, hyperrealistic, square format, no text, production-ready advertising visual",
]


class LeonardoGenerator:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.results = {
            "success": [],
            "failed": [],
            "total": len(VACATUREKANON_PROMPTS),
        }

    def generate_image(self, prompt: str, prompt_num: int) -> Dict:
        """Generate single image via Leonardo API"""
        try:
            response = self.session.post(
                LEONARDO_API_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "prompt": prompt,
                    "num_images": 1,
                    "height": 1024,
                    "width": 1024,
                    "guidance_scale": 7.5,
                    "num_inference_steps": 60,
                    "seed": prompt_num,  # For reproducibility
                },
                timeout=120,
            )

            if response.status_code == 200:
                data = response.json()
                if "generations" in data and len(data["generations"]) > 0:
                    image_url = data["generations"][0].get("url")
                    if image_url:
                        result = {
                            "prompt_num": prompt_num,
                            "status": "success",
                            "url": image_url,
                            "timestamp": datetime.now().isoformat(),
                        }
                        self.results["success"].append(result)
                        return result

            # Failure handling
            error_msg = f"Status {response.status_code}"
            if response.status_code >= 400:
                try:
                    error_msg = response.json().get("message", error_msg)
                except Exception:
                    pass

            result = {
                "prompt_num": prompt_num,
                "status": "failed",
                "error": error_msg,
                "timestamp": datetime.now().isoformat(),
            }
            self.results["failed"].append(result)
            return result

        except requests.exceptions.Timeout:
            result = {
                "prompt_num": prompt_num,
                "status": "failed",
                "error": "Request timeout (120s exceeded)",
                "timestamp": datetime.now().isoformat(),
            }
            self.results["failed"].append(result)
            return result

        except Exception as e:
            result = {
                "prompt_num": prompt_num,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
            self.results["failed"].append(result)
            return result

    def generate_batch(self, batch_size: int = 5, delay_between: float = 2.0):
        """Generate all prompts in batches"""
        print("\n" + "=" * 60)
        print("VACATUREKANON: LEONARDO AI IMAGE GENERATION")
        print("=" * 60)
        print(f"Total prompts: {len(VACATUREKANON_PROMPTS)}")
        print(f"Batch size: {batch_size}")
        print(f"Estimated time: ~{(len(VACATUREKANON_PROMPTS) * 15) / 60:.0f} minutes")
        print("=" * 60 + "\n")

        for batch_idx in range(0, len(VACATUREKANON_PROMPTS), batch_size):
            batch_num = (batch_idx // batch_size) + 1
            batch = VACATUREKANON_PROMPTS[batch_idx : batch_idx + batch_size]

            total_batches = (len(VACATUREKANON_PROMPTS) - 1) // batch_size + 1
            print(f"\nBATCH {batch_num}/{total_batches}")
            print("-" * 60)

            for idx, prompt in enumerate(batch):
                prompt_num = batch_idx + idx + 1
                print(f"  [{prompt_num:2d}/40] Generating... ", end="", flush=True)

                result = self.generate_image(prompt, prompt_num)

                if result["status"] == "success":
                    print("SUCCESS")
                else:
                    print(f"FAILED: {result['error']}")

                # Rate limiting between requests
                if idx < len(batch) - 1:
                    time.sleep(1)

            # Batch delay
            if batch_idx + batch_size < len(VACATUREKANON_PROMPTS):
                print(f"\n  Batch delay: waiting {delay_between}s before next batch...")
                time.sleep(delay_between)

        return self.results

    def save_results(self, filename: str = "vacaturekanon_generation_results.json"):
        """Save results to JSON"""
        total = self.results["total"]
        successful = len(self.results["success"])
        summary = {
            "campaign": "VACATUREKANON",
            "total_prompts": total,
            "successful": successful,
            "failed": len(self.results["failed"]),
            "success_rate": f"{successful / total * 100:.1f}%" if total > 0 else "0%",
            "generated_at": datetime.now().isoformat(),
            "results": {
                "successful_images": self.results["success"],
                "failed_images": self.results["failed"],
            },
        }

        with open(filename, "w") as f:
            json.dump(summary, f, indent=2)

        print(f"\nResults saved to: {filename}")
        return summary

    def print_summary(self):
        """Print generation summary"""
        total = 40
        successful = len(self.results["success"])
        failed = len(self.results["failed"])

        print("\n" + "=" * 60)
        print("GENERATION COMPLETE")
        print("=" * 60)
        print(f"  Successful:  {successful}/{total}")
        print(f"  Failed:      {failed}/{total}")
        print(f"  Success Rate: {successful / total * 100:.1f}%")
        print("=" * 60)

        if self.results["failed"]:
            print("\nFailed prompts:")
            for item in self.results["failed"]:
                print(f"  Prompt {item['prompt_num']}: {item['error']}")

        if self.results["success"]:
            print("\nSample successful images:")
            for img in self.results["success"][:3]:
                print(f"  Prompt {img['prompt_num']}: {img['url'][:60]}...")

        print()


def main():
    api_key = LEONARDO_API_KEY
    if not api_key:
        print("Error: LEONARDO_API_KEY environment variable not set.")
        print("Set it with: export LEONARDO_API_KEY=your-key-here")
        return

    generator = LeonardoGenerator(api_key)

    # Generate all images in batches of 5
    generator.generate_batch(batch_size=5, delay_between=2.0)

    # Print summary
    generator.print_summary()

    # Save results
    generator.save_results("vacaturekanon_generation_results.json")

    print("\nNext steps:")
    print("  1. Review vacaturekanon_generation_results.json")
    print("  2. Download successful images from URLs")
    print("  3. Create Pipedrive deal")
    print("  4. Upload to Meta Ads Manager")
    print()


if __name__ == "__main__":
    main()
