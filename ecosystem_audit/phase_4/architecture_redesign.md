# RECRUITIN ARCHITECTURE DESIGN

## PROPOSED ARCHITECTURE

### High-Level Architecture Overview

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│   PRESENTATION      │     │   ORCHESTRATION     │     │    INTEGRATION      │
│                     │     │                     │     │                     │
│ • Web Dashboard     │────▶│ • Workflow Engine   │────▶│ • Pipedrive API     │
│ • Chrome Extension  │     │ • Event Bus         │     │ • LinkedIn API      │
│ • Email Interface   │     │ • Job Queue         │     │ • Email Services    │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘
           │                           │                           │
           ▼                           ▼                           ▼
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│   LOCAL AGENTS      │     │   CLOUD SERVICES   │     │   DATA LAYER        │
│                     │     │                     │     │                     │
│ • CV Parser         │     │ • Lead Scoring API  │     │ • PostgreSQL        │
│ • Email Monitor     │     │ • AI Processing     │     │ • Redis Cache       │
│ • Browser Automator │     │ • Template Engine   │     │ • S3 Storage        │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘
```

### Component Placement

**LOCAL (Mac) Components:**
- **CV Parser Agent**: Privacy-sensitive document processing
- **Email Monitor**: Direct access to local mail client
- **Browser Automation**: LinkedIn scraping, requires browser context
- **Desktop Notifier**: Real-time alerts for urgent actions

**CLOUD Components:**
- **API Gateway**: Central entry point (AWS API Gateway)
- **Workflow Orchestrator**: State management (AWS Step Functions)
- **Lead Scoring Service**: ML models (AWS Lambda + SageMaker)
- **Template Engine**: Document generation (AWS Lambda)

**MANAGED SERVICES:**
- **Database**: AWS RDS PostgreSQL (multi-AZ)
- **Cache**: AWS ElastiCache Redis
- **Queue**: AWS SQS for async processing
- **Storage**: AWS S3 for documents/attachments

**WHY These Choices:**
- Local agents for privacy/compliance (CV data stays local)
- Cloud for scalability and availability
- Managed services to minimize ops overhead
- AWS ecosystem for integrated monitoring/scaling

### Data Flows

#### Vacancy Processing Flow
```
[Pipedrive]                [Local Agent]              [Cloud Services]
     │                           │                           │
     ├──webhook─────────────────▶├──parse CV──────────────▶│
     │                           │                           │
     │                           ├──extract skills─────────▶├──enrich data───┐
     │                           │                           │                │
     │◀──update status───────────┤◀──scoring result─────────┤◀───────────────┘
     │                           │                           │
```

#### Lead Generation Flow
```
[LinkedIn]              [Orchestrator]             [Scoring Engine]
     │                        │                           │
     ├──scrape profile───────▶├──validate lead─────────▶│
     │                        │                           ├──score lead───┐
     │                        │◀──enriched profile───────┤               │
     │                        │                           │◀──────────────┘
     │                        ├──queue outreach─────────▶[Email Service]
     │                        │
```

### Integration Points

**Real-time Integrations:**
- Pipedrive webhooks → API Gateway (< 100ms)
- Chrome Extension → Local Agent (WebSocket)
- Email notifications → SMTP relay

**Batch Processing:**
- LinkedIn scraping: Every 2 hours (rate limit friendly)
- Lead enrichment: Nightly batch (00:00 - 06:00)
- Analytics aggregation: Hourly

**Event-Driven Triggers:**
```
Event Bus (AWS EventBridge)
├── vacancy.created → start_cv_screening
├── candidate.matched → notify_recruiter
├── interview.scheduled → send_calendar_invite
└── pipeline.stalled → escalate_to_manager
```

### Scalability Strategy

**Current Capacity:**
- 100 vacancies/day
- 1,000 CV scans/day
- 500 outreach emails/day

**2x Volume:** No changes needed (current design handles)

**5x Volume:** 
- Add read replicas for database
- Scale Lambda concurrent executions
- Implement request throttling

**10x Volume:**
- Partition database by client
- Multi-region deployment
- Dedicated LinkedIn scraping fleet

**Bottlenecks & Limits:**
- LinkedIn API: 100 requests/day (use caching)
- Email sending: 500/hour (use queue + retry)
- CV parsing: CPU intensive (scale horizontally)

### Resilience & Monitoring

**Failure Scenarios:**

| Component | Impact | Fallback | Recovery |
|-----------|--------|----------|----------|
| Pipedrive API | No new vacancies | Queue webhooks | Auto-retry with backoff |
| CV Parser | Can't process applications | Manual review queue | Alert + manual takeover |
| Email Service | Outreach stops | Secondary SMTP | Automatic failover |
| Database | Complete outage | Read from cache | Multi-AZ failover |

**Monitoring Stack:**
- **Metrics**: CloudWatch (latency, errors, throughput)
- **Logs**: CloudWatch Logs with structured logging
- **Traces**: AWS X-Ray for request tracking
- **Alerts**: PagerDuty integration

```
Alert Hierarchy:
├── P1: Database down, API gateway error > 10%
├── P2: Queue depth > 1000, Lambda errors > 5%
└── P3: Slow queries, cache misses > 20%
```

## KEY ARCHITECTURAL DECISIONS

### Decision 1: Hybrid Architecture (Local + Cloud)
- **Options:** 
  - A) Full local (Python on Mac)
  - B) Full cloud (100% AWS)
  - C) Hybrid (sensitive local, scale cloud)
- **Recommendation:** C - Hybrid
- **Reasoning:** 
  - GDPR compliance for CV data
  - Leverage cloud scalability
  - Keep browser automation local (anti-bot measures)

### Decision 2: Event-Driven vs Request-Response
- **Options:**
  - A) Synchronous REST APIs
  - B) Event-driven with queues
  - C) GraphQL with subscriptions
- **Recommendation:** B - Event-driven
- **Reasoning:**
  - Handles spiky loads (Monday morning rush)
  - Natural retry mechanism
  - Decouples components

### Decision 3: AI/ML Processing Location
- **Options:**
  - A) Local Claude/GPT calls
  - B) Cloud-hosted models
  - C) Hybrid with caching
- **Recommendation:** C - Hybrid with caching
- **Reasoning:**
  - Cache common patterns (skills extraction)
  - Use cloud for heavy lifting
  - Local for quick decisions

### Decision 4: Data Storage Strategy
- **Options:**
  - A) Single PostgreSQL database
  - B) Polyglot (PostgreSQL + MongoDB + Redis)
  - C) Data lake approach
- **Recommendation:** B - Polyglot
- **Reasoning:**
  - PostgreSQL for transactional data
  - MongoDB for unstructured CV data
  - Redis for real-time scoring cache

## MIGRATION STRATEGY

### Current State → Target State

**Phase 1: Foundation (Week 1-2)**
- Set up AWS infrastructure (Terraform)
- Deploy API Gateway + Lambda skeleton
- Configure Pipedrive webhooks
- Implement basic monitoring

**Phase 2: Core Services (Week 3-4)**
- Deploy CV parser as local agent
- Build lead scoring service
- Integrate email automation
- Set up event bus

**Phase 3: Migration (Week 5-6)**
- Migrate existing templates
- Import historical data
- Parallel run (old vs new)
- Train users on new UI

**Phase 4: Optimization (Week 7-8)**
- Performance tuning
- Add caching layers
- Implement advanced features
- Decommission old system

### Rollback Plan

```
Rollback Decision Tree:
├── Data corruption? → Restore from snapshot (RTO: 1 hour)
├── Performance issues? → Scale down features (RTO: 30 min)
├── Integration broken? → Switch to manual mode (RTO: 5 min)
└── Complete failure? → Full rollback to v1 (RTO: 2 hours)
```

**Data Safety:**
- Hourly snapshots during migration
- Blue-green deployment for zero downtime
- Feature flags for gradual rollout
- Audit trail for all operations

**Success Criteria:**
- 99.9% uptime in first month
- < 2 second response time (p95)
- Zero data loss incidents
- 80% automation achieved