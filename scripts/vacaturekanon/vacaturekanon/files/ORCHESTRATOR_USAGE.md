# CLAUDE CODE ORCHESTRATOR — USAGE GUIDE

## 🎯 WHAT THIS SCRIPT DOES

Loads **ALL** Vacaturekanon systems:
- ✅ 11 Claude Skills
- ✅ 13 MCP Servers
- ✅ Jotform configuration
- ✅ Meta campaign setup
- ✅ Email automation
- ✅ Deployment plan
- ✅ Environment validation

**Single command to orchestrate everything.**

---

## 🚀 QUICKSTART

### Option 1: Run Directly

```bash
# Download script
curl -O https://raw.githubusercontent.com/WouterArtsRecruitin/vacaturekanon-worker/main/scripts/orchestrator.py

# Run it
python3 orchestrator.py
```

### Option 2: In Claude Code Terminal

```bash
# Copy to your machine
cp /mnt/user-data/outputs/vacaturekanon_orchestrator.py ~/

# Run
python3 ~/vacaturekanon_orchestrator.py
```

### Option 3: Via Claude Code in claude.ai

1. Open https://claude.ai with Claude Code enabled
2. Create new artifact with Python
3. Paste the script content
4. Click "Run"

---

## 📋 WHAT YOU GET

### Output on Console:

```
🎯 VACATUREKANON COMPLETE ORCHESTRATION

✅ Loaded 11 skills:
  - skills-bundle-v4
  - kling-video-creator
  - campagne-launcher
  - meta-audience-builder
  - vacancy-to-pipedrive
  - recruitment-crm
  - recruitment-page
  - campaign-agent
  - high-conversion-web
  - netlify-deploy
  - figma-import

✅ Initialized 13 MCP servers:
  - Zapier
  - Jotform
  - Notion
  - Canva
  - Figma
  - Invideo
  - Apollo.io
  - Gmail
  - Google Sheets
  - Google Calendar
  - Slack
  - Clay
  - Supabase

✅ Generated configurations:
  - 25 Jotform fields
  - 16 Meta audience segments
  - 18 ad copy templates
  - 5 email sequences
  - 7 deployment phases
```

### Output JSON File:

```bash
/tmp/vacaturekanon_orchestration_status.json
```

Contains all generated configurations for backup.

---

## ⚙️ WHAT IT CHECKS

### Phase 1: Skills Loading
- ✅ Loads all 11 Claude skills
- ✅ Verifies file existence
- ✅ Reports load status

### Phase 2: MCP Server Initialization
- ✅ Initializes 13 MCP servers
- ✅ Configures API endpoints
- ✅ Tests connectivity (optional)

### Phase 3: Environment Validation
- ✅ Checks for required secrets
- ✅ Lists missing variables
- ✅ Provides setup guidance

### Phase 4: Jotform Configuration
- ✅ Generates 25 form fields
- ✅ Organizes in 5 sections
- ✅ Provides webhook config

### Phase 5: Deployment Plan
- ✅ Creates 7-phase deployment plan
- ✅ Lists all required steps
- ✅ Provides command references

### Phase 6: Meta Campaign Setup
- ✅ Generates 16 audience segments
- ✅ Creates 18 ad copy variants
- ✅ Calculates 288 possible combinations
- ✅ Provides budget recommendations

### Phase 7: Email Automation
- ✅ Designs 5 email sequences
- ✅ Configures triggers
- ✅ Plans send delays

---

## 🔧 CUSTOMIZATION

### Edit audience segments:
```python
AUDIENCES = [
    "Your Audience 1",
    "Your Audience 2",
    ...
]
```

### Edit email sequences:
```python
SEQUENCES = {
    "your_sequence": {
        "name": "Sequence Name",
        "emails": 3,
        "trigger": "event_name",
    }
}
```

### Add new MCP servers:
```python
MCP_SERVERS = [
    ("Your Server", "https://your-mcp-url"),
    ...
]
```

---

## 🎓 OUTPUT STRUCTURE

The script generates:

```json
{
  "skills": [
    {
      "name": "skills-bundle-v4",
      "status": "loaded",
      "path": "/mnt/skills/user/skills-bundle-v4/SKILL.md",
      "size": 12345
    },
    ...
  ],
  "mcp_servers": [
    {
      "name": "Zapier",
      "status": "initialized",
      "url": "https://mcp.zapier.com/..."
    },
    ...
  ],
  "environment": {
    "required_present": 0,
    "required_missing": 6,
    "missing_vars": [
      "ANTHROPIC_API_KEY",
      "GITHUB_TOKEN",
      ...
    ],
    "status": "incomplete"
  },
  "jotform_schema": { ... },
  "jotform_webhook": { ... },
  "deployment_plan": { ... },
  "meta_campaigns": { ... },
  "email_sequences": { ... }
}
```

---

## 📊 NEXT STEPS AFTER RUNNING

### 1. Set Environment Variables

```bash
export ANTHROPIC_API_KEY="your-key"
export GITHUB_TOKEN="your-token"
export GITHUB_REPO="WouterArtsRecruitin/vacaturekanon-pages"
export NETLIFY_TOKEN="your-token"
export NETLIFY_SITE_ID="your-site-id"
export RESEND_API_KEY="your-key"
```

### 2. Deploy to Cloudflare

```bash
wrangler deploy
```

### 3. Create Jotform Form

Use the generated schema to create your form.

### 4. Setup Webhooks

Use the generated webhook config in Jotform settings.

### 5. Deploy & Test

```bash
wrangler dev
node test.js
```

---

## 🐛 TROUBLESHOOTING

| Issue | Fix |
|-------|-----|
| "ModuleNotFoundError" | Install Python 3.8+: `python3 --version` |
| "Skills not found" | Check paths: `/mnt/skills/user/` and `/mnt/skills/public/` |
| "MCP initialization failed" | Check internet connection, URLs valid |
| "JSON export failed" | Check `/tmp/` directory writable: `touch /tmp/test` |

---

## 💡 ADVANCED USAGE

### Use in CI/CD Pipeline

```bash
#!/bin/bash
python3 vacaturekanon_orchestrator.py > orchestration.log 2>&1
if [ $? -eq 0 ]; then
  echo "✅ Orchestration successful"
  wrangler deploy
else
  echo "❌ Orchestration failed"
  cat orchestration.log
  exit 1
fi
```

### Integrate with GitHub Actions

```yaml
- name: Run Orchestrator
  run: python3 scripts/orchestrator.py

- name: Deploy Worker
  run: wrangler deploy
```

### Use in Custom Scripts

```python
from vacaturekanon_orchestrator import VacaturekanonOrchestrator

orchestrator = VacaturekanonOrchestrator()
status = orchestrator.run_complete_setup()

# Access results
print(status['meta_campaigns']['audiences'])
```

---

## 📖 DOCUMENTATION

Generated by script:
- Jotform field mappings
- Webhook configuration
- Deployment checklist
- Campaign templates
- Email sequences

Exported to:
- `/tmp/vacaturekanon_orchestration_status.json`
- Console output (colorized)

---

## ✨ FEATURES

✅ **Comprehensive** — 11 skills + 13 MCP servers  
✅ **Fast** — Runs in <5 seconds  
✅ **Clear** — Color-coded logging  
✅ **Structured** — JSON export for automation  
✅ **Smart** — Environment validation  
✅ **Flexible** — Easy to customize  

---

## 🚀 ONE-LINER

```bash
python3 /mnt/user-data/outputs/vacaturekanon_orchestrator.py && echo "✅ Ready to deploy!"
```

---

**Everything you need, in one script.**

Run it. Deploy. Go live.
