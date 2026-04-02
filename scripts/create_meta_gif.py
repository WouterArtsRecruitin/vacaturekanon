import os
import glob
from PIL import Image

def create_meta_gif(input_folder, output_filename, duration=500, loop=0):
    """
    Compileert een set van afbeeldingen (frames) naar een loopende, geoptimaliseerde GIF
    voor Meta Ads.
    
    :param input_folder: Map die de afbeeldingsframes bevat (zorg dat ze oplopend genummerd zijn: 1.png, 2.png, etc).
    :param output_filename: Pad waar de uiteindelijke .gif wordt opgeslagen.
    :param duration: Milliseconden per frame (0.5s = 500ms).
    :param loop: 0 = oneindige loop (standaard eis voor platformen zoals Facebook).
    """
    if not os.path.exists(input_folder):
        print(f"Map '{input_folder}' bestaat nog niet. Ik maak hem aan.")
        os.makedirs(input_folder, exist_ok=True)
        return

    # Zoek alle .png en .jpg/.jpeg in de geselecteerde map
    search_pattern = os.path.join(input_folder, "*.[pjPJ][nNpP][gG]*")
    image_files = sorted(glob.glob(search_pattern))

    if not image_files:
        print(f"⏳ Geen frames gevonden in {input_folder}.")
        print("Zet eerst je 5 (of meer) Canva-afbeeldingen in deze map en draai mij opnieuw!")
        return
        
    print(f"✅ {len(image_files)} frames gevonden. Bezig met assembleren...")
    
    frames = []
    for image_path in image_files:
        try:
            # We openen de afbeelding en forceren een strakke RGB-kleurprofiel conversie
            img = Image.open(image_path).convert("RGBA")
            
            # Voorkom transparantie errors op Meta (vervang onbedoelde transparantie door zwart/wit)
            bg = Image.new("RGBA", img.size, (20, 25, 45, 255)) # Dark navy base just in case
            bg.paste(img, (0, 0), img)
            img = bg.convert("RGB")
            
            frames.append(img)
            print(f" - Toegevoegd: {os.path.basename(image_path)}")
        except Exception as e:
            print(f"❌ Fout bij het inlezen van {image_path}: {e}")

    if frames:
        frames[0].save(
            output_filename,
            save_all=True,
            append_images=frames[1:],
            optimize=True,               # Probeer colorspace te comprimeren voor Meta limieten
            duration=duration,           # The 0.5 sec ritme
            loop=loop                    # 0 = infinite
        )
        print(f"\n🚀 SUCCES! De Meta GIF is weggeschreven naar:\n{output_filename}")
        print(f"↳ Specificaties: {len(frames)} frames // {duration}ms (0.5s) delay // Infinite Loop.")

if __name__ == "__main__":
    # ===== MAKKELIJKE CONFIGURATIE ===== #
    
    # 1. Hier dump jij the 5 frames (1.png, 2.png, 3.png, 4.png, 5.png) vanuit Canva
    INPUT_DIR = "/Users/wouterarts/Library/CloudStorage/OneDrive-Gedeeldebibliotheken-Recruitin/output/vacaturekanon/assets/gif_frames"
    
    # 2. Hier komt the final geanimeerde '.gif' uit rollen, klaar voor Facebook/Insta
    OUTPUT_FILE = "/Users/wouterarts/Library/CloudStorage/OneDrive-Gedeeldebibliotheken-Recruitin/output/vacaturekanon/assets/vacaturekanon_neon_pulse.gif"
    
    # Zorg dat the map bestaat
    os.makedirs(INPUT_DIR, exist_ok=True)
    
    # Draai the motor (0.5s duratie zoals besproken)
    create_meta_gif(INPUT_DIR, OUTPUT_FILE, duration=500, loop=0)
