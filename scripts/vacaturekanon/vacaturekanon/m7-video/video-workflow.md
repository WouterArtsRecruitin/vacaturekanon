# Video Productie Workflow — Vacaturekanon

Per klant: 3 videos in ongeveer 30-45 minuten werk.

---

## Stap 1: Prompt aanpassen (5-8 min)

1. Open `video-prompts.md`
2. Kies de juiste sectie op basis van de sector van de klant
3. Pas de prompt aan:
   - Verifieer dat de industriele setting klopt (bijv. bij Constructie: bouwplaats ipv raffinaderij)
   - Voeg eventuele klant-specifieke elementen toe (logo kleur, regio-herkenbaar landschap)
   - Pas de tekst overlays aan met de juiste functietitel en bedrijfsnaam
4. Sla de aangepaste prompts op in de klantmap

**Klantmap structuur:**
```
/klanten/{{bedrijfsnaam}}/
├── video1-prompt.txt
├── video2-prompt.txt
├── video3-prompt.txt
├── video1-raw.mp4      (download van Kling)
├── video2-raw.mp4
├── video3-raw.mp4
├── video1-final-9x16.mp4
├── video1-final-1x1.mp4
└── ...
```

---

## Stap 2: Genereer in Kling AI (10-15 min)

1. Ga naar **kling.ai** en log in
2. Kies "Image to Video" of "Text to Video" (Text to Video voor deze prompts)
3. Plak de prompt in het tekstveld
4. **Settings:**
   - Duur: 5 seconden (genereer 3 clips van 5s en voeg samen in CapCut)
   - OF: 10 seconden (afhankelijk van beschikbaar in jouw tier)
   - Aspect ratio: **9:16** voor Stories/Reels primair
   - Kwaliteit: Highest beschikbaar
5. Klik "Generate"
6. Wacht: gemiddeld 2-5 minuten per generatie
7. Download de beste versie (Kling genereert 2 varianten)
8. Herhaal voor Video 2 en Video 3

**Tip:** Genereer alle 3 prompts achter elkaar (queue), dan hoef je niet te wachten.

**Fallback bij slechte output:** Gebruik de "Extend" of "Re-generate" optie. Max 2 pogingen per prompt — als het dan nog niet klopt, versimpel de prompt.

---

## Stap 3: Post-productie in CapCut (10-15 min)

### Setup
1. Download en open CapCut (desktop versie)
2. Nieuw project aanmaken: 9:16, 1080x1920, 30fps

### Stappen per video

**a) Importeer raw video**
- Sleep Kling output naar timeline
- Trim eventuele slechte frames aan begin/einde

**b) Voeg tekst overlays toe**
- Tekst tool → kies "Barlow Condensed" of dichtstbijzijnde optie
- Kleur: #FFFFFF voor hoofdtekst, #E85D04 voor accenten
- Timing: zie specificaties per video in `video-prompts.md`
- Positie: midden van het veilige gebied (niet bovenste 250px of onderste 300px)

**c) Voeg logo's toe**
- Importeer opdrachtgever logo (PNG met transparantie)
- Linksboven, 10-15% van de breedte
- Vacaturekanon badge rechtsboven (zorg dat je een klein badge-bestand hebt)

**d) Voeg muziek toe**
- Importeer royalty-free track (zie muziekbronnen hieronder)
- Fade in: 0.5s, Fade out: 0.5s
- Volume: -12dB (achtergrondmuziek, niet dominant)

**e) Kleur correctie (optioneel)**
- Exporteer naar CapCut Auto Enhance of gebruik LUT
- Match met het kleurprofiel van de sector

### Export instellingen
- **9:16 voor Stories/Reels:** 1080x1920, MP4, H.264, 30fps, 10-15 Mbps
- **1:1 voor Feed:** Export opnieuw met 1:1 format OF crop in Meta Ads Manager

---

## Stap 4: Upload naar Meta Ads Manager (5 min)

1. Ga naar ads.meta.com → Bibliotheek → Mediabibliotheek
2. Upload de 3 finale videos (zowel 9:16 als 1:1 versies)
3. Voeg een duidelijke naam toe: `VK-[SECTOR]-video[1/2/3]-[RATIO]-[bedrijfsnaam]`
4. Koppel aan de juiste advertentie in Ads Manager
5. Preview op mobile device voor publicatie
6. Controleer: thumbnail ziet er goed uit (kies zelf een frame)

---

## Muziekbronnen (royalty-free)

| Bron | Kosten | Kwaliteit | Noot |
|------|--------|-----------|------|
| YouTube Audio Library | Gratis | Goed | Geen attributie vereist voor betaalde ads |
| Pixabay Music | Gratis | Goed | CC0, volledig vrij |
| Epidemic Sound | €15/mnd | Uitstekend | Beste keuze voor professionele output |
| Artlist.io | €199/jaar | Uitstekend | Onbeperkte downloads |
| Uppbeat | Gratis/betaald | Goed | Gratis tier beschikbaar |

**Aanbevolen tracks per video type:**
- Video 1 (Probleem): Ambient, tension, instrumental — zoek op "corporate tension" of "industrial ambient"
- Video 2 (Oplossing): Upbeat corporate, optimistisch — zoek op "corporate upbeat" of "business motivation"
- Video 3 (Resultaat): Uplifting, triumphant, subtle — zoek op "corporate success" of "achievement"

---

## Bestandsnamen

```
VK-[SECTOR]-video[1/2/3]-[RATIO]-[bedrijfsnaam].mp4

Voorbeelden:
  VK-AT-video1-9x16-TechflowBV.mp4
  VK-AT-video1-1x1-TechflowBV.mp4
  VK-OG-video2-9x16-ShellNL.mp4
  VK-CI-video3-9x16-BamInfra.mp4
```

---

## Kwaliteitscheck voor publicatie

Gebruik deze checklist voor elke video:

- [ ] Video is 15 seconden (niet korter, niet langer)
- [ ] Tekst overlays zijn leesbaar op 5-inch smartphone scherm
- [ ] Logo is zichtbaar maar niet dominant
- [ ] Geen tekst in bovenste 250px of onderste 300px (veilige zone)
- [ ] Muziek is niet te luid, niet afleidend
- [ ] Branding klopt (juiste sector, juiste functietitel, juiste bedrijfsnaam)
- [ ] Video speelt smooth af (geen hakelende frames)
- [ ] Ondertitels toegevoegd (auto-genereren in CapCut, controleer op fouten)
- [ ] Preview getest op mobile
- [ ] Bestandsnaam volgt conventie
