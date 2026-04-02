# 🎯 MASTER PROMPT: DYNAMISCHE VACATURELANDINGSPAGINAS
## Recruitin B.V. | Vacature Kanon Systeem
**Version:** 1.0  
**Status:** DRAFT → REVIEW → PRODUCTION  
**Owner:** Wouter Arts  
**Tech Stack:** Jotform → Figma → Claude Code → GitHub → Netlify  

---

## 📋 OPDRACHT SCOPE

**Doel:** Bouwen van een **modulair framework** voor vacaturelandingspaginas die:
- ✅ Identieke opbouw (header, hero, value props, form, FAQ, footer)
- ✅ Variabel design (kleuren, fonts, toon, voice, images/videos)
- ✅ Klantspecifieke content (contactgegevens, company info, vacancy details)
- ✅ Jotform integration (intake form → module-driven design)
- ✅ Claude Code automation (perfect HTML/CSS/JS + GA4 + tracking)
- ✅ Git + Netlify deployment (automatic versioning & live)

**Niet:** Copy-paste templates. **Wel:** Intelligent system met één prompt.

---

## 🏗️ HUIDIGE ARCHITECTUUR (jdejonge-voorman)

### Folder Structure
```
/vacaturekanon-landing-pages
  /pages
    /jdejonge-voorman
      index.html          (Main page - 200+ lines)
      (CSS/JS embedded)
      
Observations:
- Single HTML file (no external CSS/JS)
- Vite bundled (index-BQDAIptF.css reference)
- Sonner toast library (notifications)
- Lovable badge component
- React/TypeScript likely (based on imports)
```

### Current Page Structure (MODULES)
1. **Head** - Meta, title, fonts, styles
2. **Badge** - Lovable fixed badge (bottom-right)
3. **Body Content** - (Unknown, needs full content review)
4. **Toaster** - Sonner notifications
5. **Scripts** - React app hydration

### Current Issues
- ❌ No modular component exports
- ❌ No dynamic configuration
- ❌ No Jotform integration visible
- ❌ No GA4/tracking setup
- ❌ Single-file monolith

---

## 🎨 REQUIRED MODULES (Template Architecture)

### Module 1: HEADER
- Logo + nav (optional)
- Sticky/fixed behavior
- Company branding

### Module 2: HERO
- Large headline
- Subheadline
- Background (image or video)
- CTA button

### Module 3: VALUE PROPS (3-5 items)
- Icon + headline + description
- Grid layout
- Alternating left/right (optional)

### Module 4: JOB REQUIREMENTS
- Requirements list
- Benefits list
- Responsibilities section
- (From Jotform data)

### Module 5: ABOUT COMPANY
- Description
- Company image
- Stats (optional)

### Module 6: FORM/CTA
- Embedded Jotform OR
- Custom form with Jotform webhook

### Module 7: FAQ
- Accordion component
- 5-10 items

### Module 8: FOOTER
- Contact info
- Social links
- Copyright

### Module 9: TRACKING/ANALYTICS
- GA4 gtag integration
- Jotform submission tracking
- Custom events
- Conversion pixel (Meta/LinkedIn)

---

## 📊 JOTFORM INPUT SCHEMA

The master prompt should accept Jotform data in this structure:

```json
{
  "company": {
    "name": "J de Jonge",
    "description": "...",
    "logo_url": "...",
    "website": "https://...",
    "color_primary": "#...",
    "color_secondary": "#...",
    "font_heading": "Poppins|Montserrat|custom",
    "font_body": "Inter|Open Sans|custom",
    "tone": "professional|casual|energetic",
    "target_audience": "blue_collar|white_collar|mix"
  },
  "vacancy": {
    "title": "Voorman Wegen",
    "description": "...",
    "location": "Zuidwest, NL",
    "salary_range": "€3000 - €3500/month",
    "employment_type": "Full-time|Contract",
    "requirements": ["...", "..."],
    "benefits": ["...", "..."],
    "responsibilities": ["...", "..."]
  },
  "contact": {
    "name": "Fabienne",
    "email": "fabienne@...",
    "phone": "+31 ...",
    "form_url": "https://jotform.com/..."
  },
  "design": {
    "hero_image": "url|video_url",
    "include_video": true|false,
    "images_style": "realistic|illustrated|minimal",
    "cta_text": "Apply Now|Get in Touch|Custom"
  },
  "tracking": {
    "ga4_id": "G-...",
    "meta_pixel_id": "...",
    "conversion_event": "lead|application|contact"
  }
}
```

---

## 🚀 PROCESS FLOW

### Step 1: Jotform Intake (Client fills form)
- Company name, colors, fonts
- Vacancy details
- Contact info
- Design preferences

### Step 2: Master Prompt (Claude processes)
- Reads Jotform JSON
- Maps to module system
- Generates HTML/CSS/JS
- Adds GA4 + tracking

### Step 3: Figma Design (Visual review)
- Create template with actual design
- Lock framework, allow customization
- Share with client

### Step 4: Claude Code (Perfection)
- HTML/CSS/JS output from prompt
- Linting, optimization, accessibility
- GA4 implementation verification
- Responsive design check

### Step 5: GitHub Push (Version control)
- Create `/pages/{company-slug}/` folder
- Push HTML + manifest.json
- Tag with company + date

### Step 6: Netlify Deploy (Live)
- Auto-deploy on push
- SSL certificate
- CDN + caching
- Custom domain (if provided)

### Step 7: Monitoring (Tracking)
- GA4 reports dashboard
- Form submission tracking
- Conversion monitoring
- A/B test ready

---

## 🛠️ SKILLS & TOOLS REQUIRED

| Layer | Skill/Tool | Purpose |
|-------|-----------|---------|
| **Data Input** | Jotform | Client intake |
| **Orchestration** | Master Claude Prompt | Logic + routing |
| **Design** | Figma | Visual template |
| **Code Generation** | Claude Code | HTML/CSS/JS output |
| **Version Control** | GitHub | Repository management |
| **Deployment** | Netlify | Hosting + auto-deploy |
| **Tracking** | GA4 + Meta Pixel | Conversion tracking |
| **Analytics** | Google Analytics | Performance monitoring |

---

## 📝 MASTER PROMPT STRUCTURE

The master prompt should:

1. **Parse Input** - Accept Jotform JSON
2. **Validate Data** - Check required fields
3. **Route Modules** - Determine which modules to include
4. **Generate Template** - Output HTML/CSS/JS skeleton
5. **Inject Dynamic Content** - Fill with company/vacancy data
6. **Add Analytics** - GA4 + pixel tracking
7. **Optimize** - Minify, check performance
8. **Quality Check** - Linting, accessibility audit
9. **Output** - Deployable code ready for GitHub

---

## ⚠️ KNOWN ISSUES TO FIX

1. **Current jdejonge-voorman issues:**
   - No visible content structure (need full HTML body)
   - CSS bundled (need modular approach)
   - No configuration system
   - No Jotform integration
   - No GA4 setup
   - Hard-coded company info

2. **Framework issues to solve:**
   - Avoid monolithic files
   - Component modularity
   - Config-driven design
   - Dynamic imports
   - Accessibility compliance (WCAG 2.1)
   - Performance targets (Lighthouse >90)
   - Mobile-first responsive

---

## 📊 SUCCESS CRITERIA

✅ **Deliverables:**
- [ ] Master prompt documented (this file)
- [ ] Figma template created (8 core modules)
- [ ] Claude Code script ready
- [ ] GitHub action for auto-deploy
- [ ] Sample vacancy page generated (test case)
- [ ] GA4 tracking verified
- [ ] Netlify live (test deployment)
- [ ] README + docs

✅ **Quality Gates:**
- [ ] Lighthouse score >90 (performance)
- [ ] Accessibility audit pass (WCAG 2.1)
- [ ] Mobile responsive (tested on 3+ devices)
- [ ] Form submission working
- [ ] GA4 events firing
- [ ] Meta pixel tracking verified
- [ ] Load time <2.5s (3G)

---

## 🔄 NEXT STEPS

**Phase 1: Analysis & Design (THIS WEEK)**
1. Review full jdejonge-voorman code
2. Identify exact module structure
3. Create Figma template with real design
4. Write detailed configuration schema

**Phase 2: Master Prompt (NEXT WEEK)**
1. Build comprehensive Claude prompt
2. Test with sample Jotform input
3. Generate first test page
4. Code review + bug fixes

**Phase 3: Automation (WEEK 3)**
1. Create GitHub action
2. Netlify integration
3. GA4 setup
4. Deployment pipeline

**Phase 4: Production (WEEK 4)**
1. Client testing
2. Performance optimization
3. Go-live ready
4. Documentation

---

## 📎 APPENDIX: CURRENT CODE SNIPPET

```html
<!DOCTYPE html>
<html lang="nl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>J de Jonge - Voorman Vacature</title>
  <link rel="stylesheet" href="/assets/index-BQDAIptF.css">
  <!-- Fonts, styles, badge styles embedded -->
</head>
<body>
  <!-- Content TBD - need full review -->
</body>
</html>
```

---

## 🎯 EXEC SUMMARY FOR STAKEHOLDERS

**What:** Templated vacancy landing page system  
**Why:** Volume + customization + quality at scale  
**How:** Jotform → Claude prompt → Figma → Code → GitHub → Netlify  
**Timeline:** 4 weeks  
**Budget:** Manageable (mostly automation)  
**ROI:** 10x faster page creation, 100% consistent quality  

---

**END OF MASTER PROMPT DRAFT**  
**Status:** Ready for code review & stakeholder sign-off
