import os
from PIL import Image
import glob

# Map met de gedownloade AI vierluiken (Zet je originele plaatjes hierin)
IN_DIR = "/Users/wouterarts/Library/CloudStorage/OneDrive-Gedeeldebibliotheken-Recruitin/output/vacaturekanon/assets/grids_to_split"
# Map waar de losse plaatjes belanden
OUT_DIR = "/Users/wouterarts/Library/CloudStorage/OneDrive-Gedeeldebibliotheken-Recruitin/output/vacaturekanon/assets/grids_split_output"

os.makedirs(IN_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

image_files = glob.glob(os.path.join(IN_DIR, "*.png")) + glob.glob(os.path.join(IN_DIR, "*.jpg")) + glob.glob(os.path.join(IN_DIR, "*.jpeg"))

if not image_files:
    print(f"Geen afbeeldingen gevonden in {IN_DIR}. Zet je AI vierluiken in deze map!")
    exit(0)

print(f"Gevonden: {len(image_files)} afbeeldingen om the splitten...")

for img_path in image_files:
    filename = os.path.basename(img_path)
    name, ext = os.path.splitext(filename)
    
    try:
        with Image.open(img_path) as img:
            width, height = img.size
            # We gaan iteratief uit van een 2x2 grid (linksboven, rechtsboven, linksonder, rechtsonder)
            half_w = width // 2
            half_h = height // 2
            
            # Crop secties (left, upper, right, lower)
            top_left = img.crop((0, 0, half_w, half_h))
            top_right = img.crop((half_w, 0, width, half_h))
            bottom_left = img.crop((0, half_h, half_w, height))
            bottom_right = img.crop((half_w, half_h, width, height))
            
            # Opslaan
            top_left.save(os.path.join(OUT_DIR, f"{name}_TL{ext}"))
            top_right.save(os.path.join(OUT_DIR, f"{name}_TR{ext}"))
            bottom_left.save(os.path.join(OUT_DIR, f"{name}_BL{ext}"))
            bottom_right.save(os.path.join(OUT_DIR, f"{name}_BR{ext}"))
            
            print(f"✅ {filename} succesvol in 4'en gesneden!")
    except Exception as e:
        print(f"❌ Fout bij {filename}: {e}")

print(f"\nKlaar! Al je losse beelden staan nu loeistrak uitgesneden in: {OUT_DIR}")
