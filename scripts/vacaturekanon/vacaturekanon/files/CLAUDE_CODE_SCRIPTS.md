# CLAUDE CODE ORCHESTRATION SCRIPTS

## 🎯 WHAT YOU HAVE

Two complete orchestration scripts for Claude Code:

1. **Python version** (vacaturekanon_orchestrator.py)
   - Pure Python 3
   - Works everywhere
   - File operations
   - 400+ lines

2. **Node.js version** (vacaturekanon_orchestrator.js)
   - JavaScript/TypeScript
   - Fast execution
   - Better colors
   - 500+ lines

Both do the same thing. **Use whichever you prefer.**

---

## ⚡ QUICK START

### Python (30 seconds)

```bash
python3 /mnt/user-data/outputs/vacaturekanon_orchestrator.py
```

### Node.js (30 seconds)

```bash
node /mnt/user-data/outputs/vacaturekanon_orchestrator.js
```

### In Claude Code (online)

1. Go to https://claude.ai/chat
2. Enable Claude Code (settings)
3. Upload script or paste
4. Click "Run"

---

## 🔄 WHAT EACH SCRIPT DOES

### Loads 11 Skills
```
✅ skills-bundle-v4               (Main: marketing, tech, recruitment)
✅ kling-video-creator            (Video generation)
✅ campagne-launcher              (Meta campaigns)
✅ meta-audience-builder          (Audience targeting)
✅ vacancy-to-pipedrive           (CRM automation)
✅ recruitment-crm                (Full pipeline)
✅ recruitment-page               (Landing pages)
✅ campaign-agent                 (AI agent)
✅ high-conversion-web            (Optimization)
✅ netlify-deploy                 (Deployment)
✅ figma-import                   (Design to code)
```

### Initializes 13 MCP Servers
```
✅ Zapier              (Workflows)
✅ Jotform             (Forms)
✅ Notion              (Databases)
✅ Canva               (Design)
✅ Figma               (Design)
✅ Invideo             (Video)
✅ Apollo.io           (Leads)
✅ Gmail               (Email)
✅ Google Sheets       (Data)
✅ Google Calendar     (Calendar)
✅ Slack               (Chat)
✅ Clay                (Data)
✅ Supabase            (Database)
```

### Generates Configurations
```
✅ 25 Jotform fields (organized in 5 sections)
✅ 16 Meta audience segments
✅ 18 ad copy variants
✅ 288 possible combinations
✅ 5 email sequences
✅ 7-phase deployment plan
✅ Webhook configuration
✅ Environment validation
```

---

## 📊 OUTPUT

### Console Output
```
🎯 VACATUREKANON ORCHESTRATION ENGINE

✅ Loaded 11 skills
✅ Initialized 13 MCP servers
✅ Generated 25 Jotform fields
✅ Generated 16 audience segments
✅ Generated 5 email sequences
✅ Generated 7-phase deployment plan

📍 NEXT STEPS:
  1. Deploy to Cloudflare: wrangler deploy
  2. Create Jotform intake form
  3. Connect webhook to worker
  4. Test first vacancy submission
  5. Go live on vacaturekanon.nl
```

### JSON Export
```bash
/tmp/vacaturekanon_orchestration_status.json
# or
/tmp/vacaturekanon_status.json
```

Contains all configurations in structured JSON format.

---

## 🚀 USAGE IN CLAUDE CODE

### Method 1: Direct Paste
1. Copy script content
2. Create new Claude Code artifact
3. Paste
4. Click "Run"

### Method 2: Download + Run
```bash
# Download
curl -O https://raw.githubusercontent.com/WouterArtsRecruitin/vacaturekanon-worker/main/orchestrator.py

# Run
python3 orchestrator.py
```

### Method 3: From Files
```bash
# Python
python3 /mnt/user-data/outputs/vacaturekanon_orchestrator.py

# Node.js
node /mnt/user-data/outputs/vacaturekanon_orchestrator.js
```

---

## 🎓 FEATURES

Both scripts include:

✅ **Comprehensive Logging**
- Color-coded output
- Clear step-by-step progress
- Error reporting

✅ **Full Validation**
- Environment variable checks
- Missing secrets detection
- Status reporting

✅ **Configuration Generation**
- Jotform field schemas
- Webhook setup
- Email sequences
- Campaign templates

✅ **Deployment Planning**
- 7-phase deployment guide
- All required commands
- Step-by-step checklist

✅ **Customizable**
- Easy to modify audiences
- Add/remove email sequences
- Configure MCP servers
- Adjust audience segments

---

## 📋 ENVIRONMENT VARIABLES CHECKED

### Required (6)
- ANTHROPIC_API_KEY
- GITHUB_TOKEN
- GITHUB_REPO
- NETLIFY_TOKEN
- NETLIFY_SITE_ID
- RESEND_API_KEY

### Optional (3)
- JOTFORM_API_KEY
- PIPEDRIVE_API_KEY
- APOLLO_API_KEY

Scripts report what's missing.

---

## 🔧 CUSTOMIZATION

### Python - Edit Audiences

```python
SKILLS_TO_LOAD = [
    "your-skill",
    "another-skill",
]

META_AUDIENCES = [
    "Your audience 1",
    "Your audience 2",
]
```

### Node.js - Edit Servers

```javascript
const MCP_SERVERS = [
  { name: "Your Server", url: "https://..." },
  { name: "Another", url: "https://..." },
];
```

---

## ⏱️ EXECUTION TIME

| Action | Time |
|--------|------|
| Load skills | <1s |
| Initialize MCP | <1s |
| Validate environment | <1s |
| Generate config | <1s |
| Export JSON | <1s |
| **Total** | **<5 seconds** |

---

## 📖 DOCUMENTATION

See also:
- `ORCHESTRATOR_USAGE.md` (detailed guide)
- `GITHUB_REPO_SETUP.md` (deployment steps)
- `FINAL_HANDOVER.md` (complete overview)

---

## 🎯 NEXT STEPS

1. **Run the orchestrator**
   ```bash
   python3 /mnt/user-data/outputs/vacaturekanon_orchestrator.py
   ```

2. **Review output**
   ```bash
   cat /tmp/vacaturekanon_orchestration_status.json
   ```

3. **Deploy worker**
   ```bash
   wrangler deploy
   ```

4. **Create Jotform**
   Use generated schema

5. **Setup Netlify**
   Connect vacaturekanon-pages repo

6. **Test end-to-end**
   Submit test vacancy

7. **Go live**
   Point vacaturekanon.nl to Netlify

---

## ❓ FAQ

**Q: Which version should I use?**  
A: Python is simpler. Node.js is faster. Both work identically.

**Q: Can I modify the script?**  
A: Yes! Edit skills, MCP servers, audiences, email sequences.

**Q: What if a skill isn't found?**  
A: Script reports it and continues. Not all skills exist.

**Q: Where does the JSON go?**  
A: `/tmp/vacaturekanon_status.json` (or Python version)

**Q: Can I use in GitHub Actions?**  
A: Yes! Great for CI/CD pipelines.

**Q: How often should I run it?**  
A: Once before deployment, then as needed for updates.

---

## 🚀 ONE-LINER

```bash
python3 /mnt/user-data/outputs/vacaturekanon_orchestrator.py && cat /tmp/vacaturekanon_status.json | jq '.meta_campaigns'
```

---

## ✨ SUMMARY

| Feature | Python | Node.js |
|---------|--------|---------|
| Skills | ✅ 11 | ✅ 11 |
| MCP | ✅ 13 | ✅ 13 |
| Config | ✅ Complete | ✅ Complete |
| Speed | ✅ Fast | ✅ Faster |
| Colors | ✅ Yes | ✅ Better |
| Customizable | ✅ Easy | ✅ Easy |
| Portable | ✅ Any OS | ✅ Node required |

---

**Everything you need to orchestrate Vacaturekanon.**

Pick a script. Run it. Deploy.

🚀 Ready to go live?
