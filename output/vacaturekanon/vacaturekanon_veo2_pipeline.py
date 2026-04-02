import json
import os

# VACATUREKANON SHOWCASE - AI VIDEO PIPELINE
# Doel: Genereer de 5 SaaS Motion Graphics scenes met AI.
# Workflow: 
# 1. Genereer Startframe & Endframe via Nano Banana 2 (Image Tool)
# 2. Voed beide frames aan de Kling API / Veo 2 als interpolatie-video.

pipeline_scenes = {
    "scene_1_intake": {
        "description": "De Hook - Formulier typing",
        "nano_banana_startframe": "A highly cinematic, extremely high quality 3D isometric render of an elegant, dark-mode glassmorphism UI job application form floating in a vast dark glowing void. The fields are empty. Neon orange and blue accent lighting, soft volumetric fog. Rendered in Unreal Engine 5, Octane render, SaaS dashboard style.",
        "nano_banana_endframe": "A highly cinematic 3D isometric render of the exact same dark-mode glassmorphism UI form floating in a dark void, but now fully filled out. The central field brightly glows with neon orange text: 'Monteur'. Tech motion graphic style, Octane render.",
        "kling_video_prompt": "Smooth fast 3D camera pan. The dark empty glassmorphism UI form magically types out glowing text. Floating UI components snap into place with satisfying kinetic motion. High-end SaaS motion graphics, smooth 60fps."
    },
    
    "scene_2_engine": {
        "description": "Engine Compileert - Data naar Landing page",
        "nano_banana_startframe": "A cinematic 3D isometric render of a glowing 'LANCEREN' UI button being pressed on a glass panel, emitting a massive shockwave of neon orange and blue data particles in a dark void. Tech dashboard, Octane Render.",
        "nano_banana_endframe": "A highly cinematic 3D render of a completed, stunning modern recruitment web landing page floating in the dark void, assembled entirely from glowing data lines and glassmorphism cards. Sleek, glowing, 8k.",
        "kling_video_prompt": "The glowing launch button explodes into thousands of energetic neon data particles that aggressively weave together through the dark space to instantly form a beautiful floating web UI landing page. Fast paced motion graphics, seamless transition."
    },
    
    "scene_3_ai_media": {
        "description": "Genereer AI Media",
        "nano_banana_startframe": "A 3D isometric view of the floating glassmorphism landing page emitting vertical orange light beams upwards into three floating transparent tech containers.",
        "nano_banana_endframe": "Inside the three floating glass tech containers, high quality realistic photos of a heavy machinery mechanic working in an industrial workshop are displayed. The UI containers glow with success indicators. Overlaid abstract tech HUD.",
        "kling_video_prompt": "The glass UI page fires light beams upwards. The empty transparent containers catch the light and smoothly liquid-morph into hyper-realistic video feeds of industrial mechanics. Sleek 3D holographic interface animations."
    },
    
    "scene_4_meta": {
        "description": "Meta Autopilot Dashboard",
        "nano_banana_startframe": "A complex, incredibly beautiful dark-mode Meta Ads Manager 3D UI dashboard floating in space. It has several glowing sliders and three glowing advertisement nodes labeled A, B, and C.",
        "nano_banana_endframe": "The same dark-mode Meta Ads 3D UI, but nodes B and C are greyed out and dissolving, while node A is glowing intensely green and firing thousands of bright light-pulses outward like a massive network tree.",
        "kling_video_prompt": "Fast UI animation. The sliders on the 3D dashboard move automatically. The UI branches out. Two advertisement nodes shatter into digital dust, while the winning green node violently expands into a massive, glowing network tree spreading across the screen."
    },
    
    "scene_5_hires": {
        "description": "The Hires - Inbox",
        "nano_banana_startframe": "Thousands of green glowing data particles from the network tree converging into physical floating glass 'Lead Cards' with profile silhouettes.",
        "nano_banana_endframe": "A sleek 3D isometric render of an email inbox UI floating in a dark void, absolutely overflowing with glowing 'New Lead' notifications stacked on top of each other. A glowing 'Recruitin' checkmark hovers above.",
        "kling_video_prompt": "The floating glass lead cards swiftly fly forward and stack themselves aggressively into a sleek 3D email UI. The inbox counter rapidly counts up to 99+. Deep cinematic zoom out showing the final automated pipeline."
    }
}

def create_pipeline_dirs():
    base_dir = "/Users/wouterarts/Library/CloudStorage/OneDrive-Gedeeldebibliotheken-Recruitin/output/vacaturekanon/showcase_video_pipeline"
    os.makedirs(base_dir, exist_ok=True)
    
    for scene_id, data in pipeline_scenes.items():
        scene_dir = os.path.join(base_dir, scene_id)
        os.makedirs(scene_dir, exist_ok=True)
        
        # Save prompt data locally per scene
        with open(os.path.join(scene_dir, "prompts.json"), "w") as f:
            json.dump(data, f, indent=4)
            
    print(f"✅ Pipeline mappenstructuur en prompts aangemaakt in {base_dir}")

if __name__ == "__main__":
    create_pipeline_dirs()
