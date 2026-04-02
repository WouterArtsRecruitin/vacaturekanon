import asyncio
from playwright.async_api import async_playwright
import os

async def record_meta_ads():
    print("🎥 Start Schermopname van de Meta Ads via Chromium...")
    async with async_playwright() as p:
        # Start browser met video opname in de huidige map
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            record_video_dir="/Users/wouterarts/Library/CloudStorage/OneDrive-Gedeeldebibliotheken-Recruitin/output/vacaturekanon/sales-website/",
            record_video_size={"width": 1280, "height": 800}
        )
        
        page = await context.new_page()
        
        # Gebruik de file protocol URL voor je locale bestand
        html_path = "file:///Users/wouterarts/Library/CloudStorage/OneDrive-Gedeeldebibliotheken-Recruitin/output/vacaturekanon/sales-website/meta_ads_visuals.html"
        await page.goto(html_path)
        
        # Wacht exact 10 seconden zodat de neon-blob smooth kan bewegen
        print("⏳ Animatie loopt... bezig met opnemen (10s)...")
        await page.wait_for_timeout(10000)
        
        # Stop de opname door het pad op te slaan
        video_path = await page.video.path()
        await context.close()
        await browser.close()
        
        # Hernoem webm file
        final_video = "/Users/wouterarts/Library/CloudStorage/OneDrive-Gedeeldebibliotheken-Recruitin/output/vacaturekanon/sales-website/vacaturekanon_meta_ads.webm"
        if os.path.exists(final_video):
            os.remove(final_video)
        os.rename(video_path, final_video)
        
        print(f"✅ Schermopname voltooid! Video opgeslagen als:\n{final_video}")

if __name__ == "__main__":
    asyncio.run(record_meta_ads())
