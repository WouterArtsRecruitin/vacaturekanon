#!/usr/bin/env python3
"""
VACATUREKANON: Premium Image Generation via Kling AI 2.1
Top 15 prompts for cinematic recruitment ads
"""

import requests
import time
import json
from typing import List, Dict
from datetime import datetime

KLING_API_KEY = "AkQh9hA3YCCPTLeaE8tRbtbrfgygdCJk"  # JE KEY HERE
KLING_API_URL = "https://api.klingai.com/v1/image/generation"

# TOP 15 PROMPTS (Best performers from quality review)
TOP_15_PROMPTS = [
    # Rank 1: Diverse team celebration (Prompt 7)
    "Overhead shot of a diverse technical team gathered around a table with laptops, notebooks, and coffee, celebrating a successful hire. One laptop shows Vacaturekanon dashboard with an orange success indicator. Warm, collaborative atmosphere with natural light. Authentic team dynamics. Documentary-style workplace photography. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    # Rank 2: Manufacturing facility cinematic (Prompt 32)
    "Cinematic wide shot of a tech manufacturing facility interior with dramatic backlighting, human figures working, overlaid with orange Vacaturekanon interface elements showing real-time team optimization. Narrative of automation transforming industry. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    # Rank 3: Documentary real moment (Prompt 37)
    "Raw, authentic footage-style shot of a manufacturing facility floor—workers and managers collaborating, with a digital interface overlay showing Vacaturekanon's candidate profile for new position. Blend of industrial reality and tech integration. Natural lighting. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    # Rank 4: Metrics infographic (Prompt 26)
    "Modern dashboard-style infographic showing recruitment metrics: cost-per-hire reduction, time-to-fill improvement, candidate quality scores—all trending positively in navy and orange. Clean, professional data visualization. Studio lighting. Photorealistic render of graphic design. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    # Rank 5: Dashboard close-up (Prompt 1)
    "Close-up shot of a modern laptop displaying the Vacaturekanon dashboard interface, showing recruitment metrics, automated campaign management, and candidate data streams in real-time. Soft studio lighting with subtle shadows, shot at 45-degree angle. Navy blue (#003366) and orange (#FF6B35) accent colors in the UI. Clean white background with shallow depth of field. Professional, corporate photography style. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    # Rank 6: Cinematic CTO (Prompt 31)
    "Dramatic shot of a hiring manager in modern office, bathed in blue-orange cinematic lighting (navy and orange color temperature), reviewing candidate profiles with focused intensity. Cinematic depth of field, volumetric lighting. Storytelling about control and power. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    # Rank 7: Before/After graphic (Prompt 23)
    "Split composition: left side showing tangled chaotic lines (traditional recruitment), right side showing clean organized lines flowing right (Vacaturekanon automation). Navy to orange gradient transition between sides. High contrast, dramatic lighting. Bold infographic style. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    # Rank 8: Authentic team meeting (Prompt 39)
    "Real-world scenario: diverse hiring team meeting in modern office, laptops open showing various stages of recruitment process on Vacaturekanon, papers scattered, coffee cups, genuine conversation captured mid-moment. Authentic workplace culture. Natural light. Documentary photojournalism style. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    # Rank 9: Speed momentum (Prompt 11)
    "Abstract visualization of speed and momentum—orange and navy streaks moving dynamically across frame, representing fast-track hiring process. Particles and light rays creating sense of energy and forward motion. Dramatic lighting. Metaphorical tech aesthetic. Cinema-grade composition. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    # Rank 10: Three-step cycle (Prompt 28)
    "Circular process diagram showing the 'Recruit. Automate. Dominate.' three-step flow, with icons for each stage and metric indicators in navy/orange. Clean, modern data visualization. Studio lighting. Professional infographic rendered photorealistic. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    # Rank 11: Collaborative glow (Prompt 35)
    "Cinematic overhead shot of a hiring team around glowing conference table, illuminated by warm orange and cool blue light from the Vacaturekanon interface displayed on table surface. Collaborative moment, dramatic chiaroscuro lighting. Story of team success. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    # Rank 12: Confident CTO (Prompt 6)
    "A confident CTO or engineering manager in a modern tech office, wearing casual business attire, smiling while reviewing candidate profiles on a large monitor displaying Vacaturekanon interface. Natural daylight from large windows, warm amber tones. Moment of satisfaction and control. Modern workplace culture photography. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    # Rank 13: Ascending success (Prompt 24)
    "Large ascending bar chart in orange rising sharply against navy background, with small human figures celebrating at top—representing hiring success metrics and growth. Bold graphic design, eye-catching, optimistic. Studio lighting. Modern infographic rendered as photorealistic imagery. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    # Rank 14: CTO authentic (Prompt 38)
    "Authentic moment: CTO in casual work clothes, typing on keyboard, receiving Vacaturekanon notification on phone, pausing to read with genuine interest. Unpolished, real office environment. Natural lighting from windows. Documentary photography style capturing authentic reaction. 8K, hyperrealistic, square format, no text, production-ready advertising visual",

    # Rank 15: Timeline comparison (Prompt 27)
    "Timeline visualization showing traditional recruitment cycle (weeks/months, expensive) vs. Vacaturekanon cycle (days, efficient) with comparative metrics and icons. Navy and orange accent colors. Clean infographic style. Professional data presentation rendered photorealistic. 8K, hyperrealistic, square format, no text, production-ready advertising visual"
]

class KlingGenerator:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.results = {
            "success": [],
            "failed": [],
            "total": len(TOP_15_PROMPTS)
        }

    def generate_image(self, prompt: str, prompt_num: int) -> Dict:
        """Generate single image via Kling API"""
        try:
            response = self.session.post(
                KLING_API_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "prompt": prompt,
                    "model": "kling-2.1",
                    "size": "1024:1024",
                    "num_images": 1,
                    "quality": "high",
                    "cfg_scale": 7.5
                },
                timeout=180  # Kling slower, needs longer timeout
            )

            if response.status_code == 200:
                data = response.json()
                if "results" in data and len(data["results"]) > 0:
                    image_url = data["results"][0].get("url")
                    if image_url:
                        result = {
                            "rank": prompt_num,
                            "status": "success",
                            "url": image_url,
                            "timestamp": datetime.now().isoformat()
                        }
                        self.results["success"].append(result)
                        return result

            error_msg = f"Status {response.status_code}"
            if response.status_code >= 400:
                try:
                    error_msg = response.json().get("message", error_msg)
                except:
                    pass

            result = {
                "rank": prompt_num,
                "status": "failed",
                "error": error_msg,
                "timestamp": datetime.now().isoformat()
            }
            self.results["failed"].append(result)
            return result

        except Exception as e:
            result = {
                "rank": prompt_num,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.results["failed"].append(result)
            return result

    def generate_batch(self, batch_size: int = 3, delay_between: float = 5.0):
        """Generate top 15 in batches"""
        print("\n" + "="*70)
        print("VACATUREKANON: KLING AI 2.1 PREMIUM GENERATION (TOP 15)")
        print("="*70)
        print(f"Total prompts: {len(TOP_15_PROMPTS)}")
        print(f"Batch size: {batch_size}")
        print(f"Estimated time: ~{(len(TOP_15_PROMPTS) * 45) / 60:.0f} minutes (Kling slower)")
        print("="*70 + "\n")

        for batch_idx in range(0, len(TOP_15_PROMPTS), batch_size):
            batch_num = (batch_idx // batch_size) + 1
            batch = TOP_15_PROMPTS[batch_idx:batch_idx + batch_size]

            print(f"\n BATCH {batch_num}/{(len(TOP_15_PROMPTS) - 1) // batch_size + 1}")
            print("-" * 70)

            for idx, prompt in enumerate(batch):
                rank_num = batch_idx + idx + 1
                print(f"  [Rank {rank_num:2d}/15] Generating via Kling... ", end="", flush=True)

                result = self.generate_image(prompt, rank_num)

                if result["status"] == "success":
                    print(f"SUCCESS")
                else:
                    print(f"FAILED: {result['error']}")

                # Rate limiting (Kling slower)
                if idx < len(batch) - 1:
                    time.sleep(2)

            # Batch delay (Kling needs more breathing room)
            if batch_idx + batch_size < len(TOP_15_PROMPTS):
                print(f"\n  Batch delay: waiting {delay_between}s before next batch...")
                time.sleep(delay_between)

        return self.results

    def save_results(self, filename: str = "vacaturekanon_kling_results.json"):
        """Save results"""
        summary = {
            "campaign": "VACATUREKANON - KLING PREMIUM",
            "model": "kling-2.1",
            "total_prompts": self.results["total"],
            "successful": len(self.results["success"]),
            "failed": len(self.results["failed"]),
            "success_rate": f"{len(self.results['success']) / self.results['total'] * 100:.1f}%",
            "quality_level": "premium (cinematic, high detail)",
            "generated_at": datetime.now().isoformat(),
            "results": {
                "successful_images": self.results["success"],
                "failed_images": self.results["failed"]
            }
        }

        with open(filename, "w") as f:
            json.dump(summary, f, indent=2)

        print(f"\nResults saved to: {filename}")
        return summary

    def print_summary(self):
        """Print summary"""
        print("\n" + "="*70)
        print("KLING GENERATION COMPLETE")
        print("="*70)
        print(f"Successful:  {len(self.results['success'])}/15")
        print(f"Failed:      {len(self.results['failed'])}/15")
        print(f"Success Rate:  {len(self.results['success'])/15*100:.1f}%")
        print(f"Quality:       Premium cinematic (Kling 2.1)")
        print("="*70)

        if self.results["failed"]:
            print("\nFailed prompts:")
            for failed in self.results["failed"]:
                print(f"  Rank {failed['rank']}: {failed['error']}")

        if self.results["success"]:
            print("\nGenerated images (top 5):")
            for img in self.results["success"][:5]:
                print(f"  Rank {img['rank']}: {img['url'][:65]}...")

        print()

def main():
    generator = KlingGenerator(KLING_API_KEY)
    generator.generate_batch(batch_size=3, delay_between=5.0)
    generator.print_summary()
    generator.save_results("vacaturekanon_kling_results.json")

    print("\nNext steps:")
    print("  1. Download Kling images from results JSON")
    print("  2. Generate Leonardo batch for remaining 25 prompts")
    print("  3. Merge both sets (15 Kling premium + 25 Leonardo)")
    print("  4. Create Pipedrive deal")
    print("  5. Upload to Meta Ads Manager")
    print()

if __name__ == "__main__":
    main()
