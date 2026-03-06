# CLAUDE INTEGRATION DESIGN FOR RECRUITIN

## CLAUDE PROJECTS STRUCTURE

### Recommended Projects

#### 1. **Recruitin Operations Hub**
- **Purpose**: Centralized operational excellence for daily recruitment tasks
- **Reference files**: 
  - Company handbook & processes
  - Service level agreements
  - Quality checklists
  - Communication templates
- **Custom instructions**: "You are an operations specialist at Recruitin. Prioritize efficiency, accuracy, and candidate experience. Always check against our SLAs and quality standards."
- **When to use**: Daily operational tasks, process optimization, quality checks

#### 2. **Candidate Engagement Specialist**
- **Purpose**: Personalized candidate communication and relationship management
- **Reference files**:
  - Brand voice guide
  - Email templates library
  - Candidate journey maps
  - Tone & style examples
- **Custom instructions**: "You craft engaging, personalized messages that reflect Recruitin's warm, professional brand. Focus on building genuine connections while maintaining efficiency."
- **When to use**: All candidate communications, email drafting, follow-ups

#### 3. **Search & Sourcing Assistant**
- **Purpose**: Advanced boolean search creation and sourcing strategy
- **Reference files**:
  - Boolean search library
  - Platform-specific search guides
  - Industry terminology databases
  - Successful search patterns
- **Custom instructions**: "You are a sourcing expert who creates precise, effective search strings. Consider synonyms, variations, and platform-specific syntax."
- **When to use**: Creating search queries, sourcing strategies, finding hard-to-reach talent

#### 4. **Data Analysis & Reporting**
- **Purpose**: Recruitment metrics analysis and insight generation
- **Reference files**:
  - KPI definitions
  - Report templates
  - Benchmark data
  - Visualization guidelines
- **Custom instructions**: "You analyze recruitment data to find actionable insights. Present findings clearly with context and recommendations."
- **When to use**: Weekly/monthly reporting, performance analysis, trend identification

#### 5. **Interview Intelligence**
- **Purpose**: Interview preparation, question generation, and evaluation
- **Reference files**:
  - Interview question banks
  - Competency frameworks
  - Evaluation rubrics
  - Bias prevention guidelines
- **Custom instructions**: "You help create fair, effective interviews that assess both skills and cultural fit. Always consider diversity and inclusion."
- **When to use**: Interview prep, question creation, candidate evaluation

### Reference Library Organization

```
shared_reference_library/
├── brand_voice/
│   ├── tone_guide.md
│   ├── writing_examples.md
│   └── do_dont_examples.md
├── process_templates/
│   ├── recruitment_lifecycle.md
│   ├── quality_checklists.md
│   ├── sla_requirements.md
│   └── escalation_procedures.md
├── email_templates/
│   ├── candidate_outreach/
│   ├── client_communication/
│   ├── internal_updates/
│   └── automated_responses/
├── data_structures/
│   ├── candidate_profiles.json
│   ├── job_requirements.json
│   ├── pipeline_stages.json
│   └── reporting_schemas.json
├── evaluation_rubrics/
│   ├── technical_skills.md
│   ├── soft_skills.md
│   ├── cultural_fit.md
│   └── scoring_guidelines.md
└── knowledge_base/
    ├── industry_terminology/
    ├── boolean_searches/
    ├── platform_guides/
    └── best_practices/
```

## MODEL SELECTION STRATEGY

| Task Type | Model | Why? | Interface |
|-----------|-------|------|-----------|
| CV Screening | Haiku | High volume, pattern matching | API/Batch |
| Boolean Search Generation | Haiku | Quick, formulaic task | Chat |
| Email First Drafts | Haiku | Speed for initial creation | Chat |
| Candidate Profile Analysis | Sonnet | Nuanced understanding needed | Chat |
| Personalized Outreach | Sonnet | Balance of quality & speed | Chat |
| Interview Preparation | Sonnet | Comprehensive analysis | Chat |
| Strategic Recruitment Planning | Opus | Complex strategy & insights | Chat |
| Difficult Candidate Situations | Opus | Emotional intelligence needed | Chat |
| Market Analysis & Reports | Opus | Deep analysis & synthesis | Chat |

## MCP/EXTENSION OPPORTUNITIES

### Custom MCPs to Build

#### 1. **Recruitin ATS Bridge**
- **Purpose**: Direct integration with ATS systems
- **Tools it provides**:
  - `search_candidates(criteria)`
  - `update_candidate_status(id, status)`
  - `get_pipeline_stats()`
  - `create_note(candidate_id, note)`
- **Authentication**: OAuth2 with ATS providers
- **Implementation effort**: Medium (2-3 weeks)

#### 2. **Email Automation MCP**
- **Purpose**: Smart email sending with tracking
- **Tools it provides**:
  - `send_personalized_email(template, variables)`
  - `schedule_followup(candidate_id, days)`
  - `get_email_metrics(campaign_id)`
- **Authentication**: SMTP credentials + tracking API
- **Implementation effort**: Low (1 week)

#### 3. **LinkedIn Integration MCP**
- **Purpose**: Enhanced sourcing capabilities
- **Tools it provides**:
  - `search_profiles(boolean_query)`
  - `get_profile_details(profile_url)`
  - `send_inmail(profile_id, message)`
- **Authentication**: LinkedIn API credentials
- **Implementation effort**: High (4-6 weeks)

#### 4. **Calendar & Scheduling MCP**
- **Purpose**: Interview scheduling automation
- **Tools it provides**:
  - `find_available_slots(participants, duration)`
  - `book_interview(candidate, interviewers, time)`
  - `send_calendar_invites()`
- **Authentication**: Google/Outlook OAuth
- **Implementation effort**: Medium (2-3 weeks)

## APPROVAL WORKFLOW

### Auto-Execute (No Approval Needed)
- First draft email generation
- Boolean search creation
- Data analysis & reporting
- Interview question suggestions
- Candidate profile summaries

### Manager Approval Required
- Final candidate communications (until trust established)
- Significant process changes
- Client-facing reports
- Rejection messages
- Salary negotiations content

### Executive Approval Required
- New automation workflows
- Major strategic recommendations
- Process overhauls
- New tool integrations
- Budget-impacting decisions

### Escalation Paths
1. **Operational Issues** → Team Lead → Operations Manager
2. **Quality Concerns** → QA Specialist → Head of Quality
3. **Strategic Decisions** → Department Head → CEO
4. **Technical Problems** → IT Support → CTO

## INTEGRATION ROADMAP

### Month 1: Foundation & Quick Wins
- Set up 5 core Claude Projects with reference files
- Train team on Claude best practices (2 workshops)
- Implement email template system with Claude
- Create boolean search assistant
- Establish daily Claude usage habits
- **Success Metric**: 50% reduction in email drafting time

### Month 2-3: Process Integration
- Build Email Automation MCP
- Integrate Claude into candidate screening workflow
- Develop custom prompts library
- Create automated reporting dashboards
- Implement quality check protocols
- Train advanced users as Claude champions
- **Success Metric**: 30% faster candidate processing

### Month 4-6: Advanced Automation
- Deploy ATS Bridge MCP
- Implement intelligent candidate matching
- Build predictive analytics for recruitment success
- Create automated interview scheduling
- Develop candidate engagement scoring
- **Success Metric**: 40% improvement in placement success rate

### Month 7-12: Full Integration
- LinkedIn Integration MCP
- AI-powered market intelligence system
- Automated candidate nurturing campaigns
- Predictive hiring analytics
- Complete workflow automation
- **Success Metric**: 2x consultant productivity

### Continuous Improvements
- Monthly prompt optimization sessions
- Quarterly model evaluation (Haiku vs Sonnet vs Opus)
- Bi-annual process review and updates
- Ongoing team training and certification
- Regular ROI measurement and reporting