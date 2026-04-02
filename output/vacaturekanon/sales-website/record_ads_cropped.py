import asyncio
from playwright.async_api import async_playwright
import os
import subprocess

ADS = [
    {
        "name": "Instagram_Feed",
        "viewport": {"width": 1080, "height": 1080},
        "selector": ".grid > div:nth-child(1) .ad-container",
        "scale": "2.16" # 1080 / 500 = 2.16
    },
    {
        "name": "Facebook_Feed",
        "viewport": {"width": 1200, "height": 628},
        "selector": ".grid > div:nth-child(2) .ad-container",
        "scale": "2.0" # 1200 / 600 = 2.0
    }
]

html_path = "file:///Users/wouterarts/Library/CloudStorage/OneDrive-Gedeeldebibliotheken-Recruitin/output/vacaturekanon/sales-website/meta_ads_visuals.html"
output_dir = "/Users/wouterarts/Library/CloudStorage/OneDrive-Gedeeldebibliotheken-Recruitin/output/vacaturekanon/sales-website"

async def record_ad(p, ad):
    print(f"🎥 Start opname voor: {ad['name']} ({ad['viewport']['width']}x{ad['viewport']['height']})")
    browser = await p.chromium.launch(headless=True)
    
    # Maak een nieuwe context met het exacte viewport formaat
    context = await browser.new_context(
        record_video_dir=output_dir,
        record_video_size=ad["viewport"],
        viewport=ad["viewport"]
    )
    
    page = await context.new_page()
    await page.goto(html_path)
    
    # Isoleer de specifieke ad en schaal deze op naar de volledige viewport
    await page.evaluate(f"""() => {{
        // Reset de body
        document.body.style.margin = '0';
        document.body.style.padding = '0';
        document.body.style.overflow = 'hidden';
        document.body.style.backgroundColor = '#0a0a14';
        
        // Zoek de specifieke ad container
        const adElement = document.querySelector('{ad["selector"]}');
        
        // Verwijder alles in de body en stop alleen de ad terug
        document.body.innerHTML = '';
        document.body.appendChild(adElement);
        
        // Schaal het element exact naar de viewport grootte!
        adElement.style.position = 'absolute';
        adElement.style.top = '0';
        adElement.style.left = '0';
        adElement.style.transform = 'scale({ad["scale"]})';
        adElement.style.transformOrigin = 'top left';
        adElement.style.margin = '0';
    }}""")
    
    # Wacht exact 10 seconden voor een mooie loop
    await page.wait_for_timeout(10000)
    
    video_path = await page.video.path()
    await context.close()
    await browser.close()
    
    final_webm = os.path.join(output_dir, f"VK_Waitlist_{ad['name']}.webm")
    final_mp4 = os.path.join(output_dir, f"VK_Waitlist_{ad['name']}.mp4")
    
    if os.path.exists(final_webm):
        os.remove(final_webm)
    os.rename(video_path, final_webm)
    
    # Converteer meteen naar MP4 voor Meta!
    print(f"🔄 Converteren naar MP4 voor {ad['name']}...")
    subprocess.run([
        "ffmpeg", "-y", "-i", final_webm,
        "-c:v", "libx264", "-preset", "fast", "-crf", "22", "-pix_fmt", "yuv420p",
        final_mp4
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Cleanup webm
    os.remove(final_webm)
    print(f"✅ Klaar! Opgeslagen als {final_mp4}")

async def main():
    async with async_playwright() as p:
        for ad in ADS:
            await record_ad(p, ad)

if __name__ == "__main__":
    asyncio.run(main())
