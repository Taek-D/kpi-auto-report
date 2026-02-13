# PRD: E-commerce KPI Daily Auto-Report System

**Project Code**: `ecommerce-kpi-reporter`  
**Version**: 1.0  
**Last Updated**: 2026-02-13  
**Owner**: 택  
**Status**: ✅ Completed

---

## 📋 Executive Summary

### What We're Building
A lightweight, automated daily reporting system that delivers critical e-commerce business KPIs to stakeholders via Slack every morning at 08:00. This system transforms the existing static Coupang E-commerce Dashboard into an **operational monitoring tool** by adding PostgreSQL foundation and n8n-powered automation.

### Why It Matters
**Business Problem**: Business teams manually check Tableau dashboards to monitor daily performance, leading to delayed responses to trends and missed opportunities.

**Solution**: Automated daily KPI delivery with WoW comparisons, anomaly alerts, and top product insights — delivered to stakeholders' Slack channels before they start work.

### Key Differentiators from Existing Portfolio
| Aspect | Marketing ROI Project | Finance Close Pack | **This Project** |
|--------|----------------------|-------------------|------------------|
| **Domain** | External ad platforms | Monthly finance KPIs | **Internal e-commerce KPIs** |
| **Frequency** | Daily | Monthly | **Daily** |
| **Tool** | Google Apps Script | Airflow | **n8n (lightweight)** |
| **Data Source** | Google/Facebook/Naver Ads API | MySQL transactions | **PostgreSQL (Coupang data)** |
| **Focus** | Marketing ROI optimization | Financial reporting | **Business monitoring** |

**Unique Value**: Fills the gap between static analysis (Coupang Dashboard) and external marketing automation (Marketing ROI) by automating **internal business performance monitoring**.

---

## 🎯 Background & Problem Statement

### Current State (AS-IS)

**Existing Project**: 📊 쿠팡 E-commerce Performance Dashboard
- **Strength**: Deep SQL analysis (Window Functions, CTEs), Tableau visualization
- **Weakness**: Static analysis — data loaded once, no automation, manual dashboard checks required

**Pain Points**:
1. **Delayed Insights**: Business team checks dashboard manually → trends discovered late
2. **No Proactive Alerts**: Anomalies (sudden drop in conversion rate) go unnoticed until weekly review
3. **Context Switching**: Need to open Tableau, navigate to dashboard, apply filters
4. **Limited Accessibility**: Mobile access difficult, non-technical stakeholders struggle with Tableau

### Desired State (TO-BE)

Every morning at 08:00, stakeholders receive a **Slack message** with:
- 🎯 **Core KPIs**: Revenue, Orders, Conversion Rate (yesterday vs last week)
- 📈 **Trends**: WoW % change with directional indicators (↑/↓)
- ⚠️ **Alerts**: Anomalies detected (e.g., conversion rate dropped >10%)
- 🏆 **Top 3 Products**: Best sellers by revenue (yesterday)
- 📊 **Quick Link**: Direct link to Tableau dashboard for deeper analysis

### Why Now?
- **Portfolio Gap**: No daily automation for internal e-commerce KPIs (vs Marketing ROI's external ad data)
- **At Home JD Alignment**: Demonstrates SQL + automation + Python + business impact
- **Evolution Story**: Natural progression from static analysis (Phase 1) → automated monitoring (Phase 2)

---

## 🎯 Goals & Success Metrics

### Primary Goals

| Goal | Metric | Target |
|------|--------|--------|
| **Automated Delivery** | Daily reports delivered on time | 100% (7/7 days) |
| **Data Freshness** | Data lag from source | < 1 hour |
| **Stakeholder Engagement** | Slack message open rate | > 80% |
| **Anomaly Detection Accuracy** | False positive rate | < 10% |

### Portfolio Goals

| Goal | Evidence |
|------|----------|
| **SQL Mastery** | Complex queries with Window Functions (LAG, RANK), CTEs |
| **Automation** | n8n workflow screenshot, execution logs |
| **Business Impact** | Stakeholder testimonial (simulated), response time improvement |
| **Tool Diversity** | n8n (new tool) vs Airflow/GAS (existing projects) |

### Non-Goals (Out of Scope)

- ❌ Real-time streaming (batch daily is sufficient)
- ❌ Predictive analytics (ML forecasting)
- ❌ Multi-channel integration (focus on Coupang data only)
- ❌ Custom dashboard creation (Tableau already exists)

---

## 👥 User Stories

### Persona 1: Business Manager (Primary)
**As a** business manager,  
**I want to** receive daily KPI summary in Slack before I start work,  
**So that** I can identify trends and take action without manually checking dashboards.

**Acceptance Criteria**:
- Report arrives at 08:00 KST every weekday
- Shows yesterday's performance vs last week (WoW)
- Includes top 3 products by revenue
- Highlights anomalies (>10% drop in conversion rate)

---

### Persona 2: Product Manager (Secondary)
**As a** product manager,  
**I want to** see which products are performing well daily,  
**So that** I can adjust inventory and marketing focus quickly.

**Acceptance Criteria**:
- Top 3 products ranked by revenue (yesterday)
- Shows product name, revenue, units sold
- Compares to last week's ranking

---

### Persona 3: Data Analyst (Tertiary)
**As a** data analyst,  
**I want to** verify automation quality and troubleshoot failures,  
**So that** I can maintain system reliability.

**Acceptance Criteria**:
- n8n execution logs accessible
- SQL query performance monitored
- Error notifications sent to separate admin channel

---

## 🔧 Technical Requirements

### Functional Requirements

#### FR-1: Daily Data Pipeline
- **PostgreSQL Connection**: Connect to existing Coupang database (from Phase 1)
- **Incremental Load**: Query yesterday's data only (WHERE date = CURRENT_DATE - 1)
- **WoW Comparison**: Compare to same day last week (WHERE date = CURRENT_DATE - 8)

#### FR-2: KPI Calculation
Calculate 6 core metrics:
1. **Total Revenue** (₩): SUM(order_amount)
2. **Total Orders** (#): COUNT(DISTINCT order_id)
3. **Average Order Value** (₩): Revenue / Orders
4. **Conversion Rate** (%): Orders / Visitors
5. **WoW Change** (%): ((This Week - Last Week) / Last Week) * 100
6. **Top 3 Products**: RANK() OVER (ORDER BY revenue DESC) LIMIT 3

#### FR-3: Anomaly Detection
Simple threshold-based detection:
- Conversion Rate drop > 10% → ⚠️ Alert
- Revenue drop > 20% → 🚨 Critical Alert
- Orders drop > 15% → ⚠️ Alert

#### FR-4: Slack Notification
- **Channel**: `#business-kpis` (or configurable)
- **Format**: Structured message with emoji indicators
- **Includes**: 
  - KPI table (Markdown formatting)
  - Trend indicators (↑/↓)
  - Tableau dashboard link
  - Timestamp

---

### Non-Functional Requirements

#### NFR-1: Performance
- SQL query execution: < 5 seconds
- End-to-end pipeline: < 2 minutes
- Slack API response: < 1 second

#### NFR-2: Reliability
- n8n workflow error retry: 3 attempts with exponential backoff
- Failure notification to admin channel
- Graceful degradation (skip anomaly detection if calculation fails)

#### NFR-3: Maintainability
- SQL queries externalized in separate `.sql` files
- n8n workflow exported as JSON (version controlled)
- Environment variables for secrets (DB credentials, Slack webhook)

#### NFR-4: Scalability
- Design supports adding new KPIs without code changes
- Easy to extend to multiple data sources (future: Naver, Gmarket)

---

## 🏗️ System Architecture

### High-Level Architecture (Implemented)

```
┌──────────────────────────────────────────────────────────────────────┐
│                     n8n Workflow (7 Nodes)                            │
│                                                                       │
│  ┌──────────┐   ┌──────────────┐                                    │
│  │ Schedule │──▶│ HTTP Request │──┐                                  │
│  │ Trigger  │   │ (Yesterday)  │  │                                  │
│  │ 08:00    │   └──────────────┘  │  ┌─────────┐  ┌──────────────┐ │
│  │          │──▶│ HTTP Request │──▶│  Merge   │─▶│ WoW Analysis │ │
│  │          │   │ (Last Week)  │  │  │(Append) │  │ Code Node    │ │
│  │          │   └──────────────┘  │  └─────────┘  └──────┬───────┘ │
│  │          │──▶│ HTTP Request │──┘                       │         │
│  │          │   │ (Products)   │                          ▼         │
│  └──────────┘   └──────────────┘                 ┌──────────────┐  │
│                                                   │ Slack Send   │  │
│                                                   │ Code Node    │  │
│                                                   └──────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
         │                                            │
         ▼                                            ▼
┌──────────────────┐                          ┌─────────────┐
│   Supabase       │                          │    Slack    │
│   REST API (RPC) │                          │  Workspace  │
│                  │                          │             │
│  • daily_sales   │                          │ #business-  │
│  • product_sales │                          │  kpis       │
│  • products      │                          └─────────────┘
└──────────────────┘
```

### Data Flow

```
1. Schedule Trigger (08:00 KST)
   ↓
2. Supabase RPC (3 parallel HTTP Requests)
   ├─ get_kpis_yesterday()  → Yesterday KPIs
   ├─ get_kpis_last_week()  → Last week same-day KPIs
   └─ get_top_products()    → Top 3 products by revenue
   ↓
3. Merge (Append, 3 inputs)
   ↓
4. WoW Analysis & Anomaly Detection (Code Node)
   ├─ Calculate WoW % change
   ├─ Detect anomalies (threshold-based)
   └─ Format Slack message (mrkdwn)
   ↓
5. Slack Send (Code Node)
   └─ this.helpers.httpRequest() → Webhook POST
```

---

## 📊 Data Model

### Source Tables (Existing from Phase 1)

#### Table: `orders`
```sql
CREATE TABLE orders (
    order_id VARCHAR(50) PRIMARY KEY,
    order_date DATE NOT NULL,
    product_id VARCHAR(50),
    product_name VARCHAR(200),
    quantity INTEGER,
    unit_price DECIMAL(10, 2),
    order_amount DECIMAL(12, 2),
    customer_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Table: `daily_summary` (New - Materialized for Performance)
```sql
CREATE TABLE daily_summary (
    summary_date DATE PRIMARY KEY,
    total_revenue DECIMAL(14, 2),
    total_orders INTEGER,
    total_visitors INTEGER,
    avg_order_value DECIMAL(10, 2),
    conversion_rate DECIMAL(5, 2),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Aggregation Strategy

**Option A: Real-time Aggregation** (Chosen for simplicity)
- Query raw `orders` table daily
- Calculate metrics on-the-fly
- Pros: No additional ETL, always fresh
- Cons: Slower queries (acceptable for daily batch)

**Option B: Materialized View**
- Pre-aggregate into `daily_summary`
- Query summary table only
- Pros: Faster queries
- Cons: Additional ETL step, complexity

**Decision**: Start with Option A, migrate to Option B if query time > 10 seconds.

---

## 💻 Implementation Plan

### Phase 1: PostgreSQL Setup (Day 1 - Morning)
**Duration**: 2 hours

- [x] Verify Supabase connection from Phase 1
- [x] Create `daily_summary` table (optional materialized view)
- [x] Test connection from n8n (Supabase REST API)
- [x] Write 3 core SQL queries:
  - `kpis_yesterday.sql`
  - `kpis_last_week.sql`
  - `top_products.sql`

**Deliverables**:
- `schema/daily_summary.sql`
- `queries/kpis_yesterday.sql`
- `queries/kpis_last_week.sql`
- `queries/top_products.sql`

---

### Phase 2: n8n Workflow Development (Day 1 - Afternoon)
**Duration**: 4 hours

- [x] Install n8n locally (Docker Compose)
- [x] Create workflow with 7 nodes:
  1. **Cron Trigger**: Daily at 08:00 KST
  2. **PostgreSQL Node 1**: Execute `kpis_yesterday.sql`
  3. **PostgreSQL Node 2**: Execute `kpis_last_week.sql`
  4. **PostgreSQL Node 3**: Execute `top_products.sql`
  5. **Function Node**: Python/JavaScript to calculate WoW, detect anomalies, format message
  6. **Slack Node**: Send message to `#business-kpis`
- [x] Configure Supabase RPC endpoints with API key
- [x] Test manually — E2E success

**Deliverables**:
- `n8n/workflow.json` (7-node workflow)
- `n8n/transform.js` (WoW analysis + anomaly detection)
- `n8n/slack_send.js` (Slack webhook sender)

---

### Phase 3: Slack Integration (Day 2 - Morning)
**Duration**: 2 hours

- [ ] Create Slack incoming webhook
- [ ] Design message template:
  ```
  📊 **Daily E-commerce KPI Report** | {Date}
  
  **Core Metrics (Yesterday)**
  ━━━━━━━━━━━━━━━━━━━━━
  💰 Revenue: ₩{revenue} ({wow_revenue}% ↑/↓)
  📦 Orders: {orders} ({wow_orders}% ↑/↓)
  🛒 AOV: ₩{aov} ({wow_aov}% ↑/↓)
  📈 Conv. Rate: {conv_rate}% ({wow_conv}% ↑/↓)
  
  {anomaly_alerts}
  
  **🏆 Top 3 Products**
  1. {product_1}: ₩{revenue_1} ({units_1} units)
  2. {product_2}: ₩{revenue_2} ({units_2} units)
  3. {product_3}: ₩{revenue_3} ({units_3} units)
  
  📊 View Dashboard: {tableau_link}
  ```
- [ ] Handle edge cases (no data, DB connection failure)

**Deliverables**:
- `slack_template.md` (message format)
- Test screenshots (successful + failure cases)

---

### Phase 4: Python Transform Logic (Day 2 - Afternoon)
**Duration**: 3 hours

Implement transformation logic in n8n Function Node:

```javascript
// Calculate WoW % change
const wow_revenue = ((yesterday.revenue - lastweek.revenue) / lastweek.revenue) * 100;
const wow_orders = ((yesterday.orders - lastweek.orders) / lastweek.orders) * 100;

// Anomaly detection
let alerts = [];
if (wow_revenue < -20) alerts.push("🚨 Revenue dropped >20% WoW");
if (yesterday.conv_rate - lastweek.conv_rate < -10) alerts.push("⚠️ Conversion rate dropped >10%");

// Format top products
const top3 = products.slice(0, 3).map((p, i) => 
  `${i+1}. ${p.name}: ₩${p.revenue.toLocaleString()} (${p.units} units)`
).join('\n');

return {
  revenue: yesterday.revenue.toLocaleString(),
  wow_revenue: wow_revenue.toFixed(1),
  // ... more fields
  anomaly_alerts: alerts.join('\n') || '✅ No anomalies detected',
  top3: top3
};
```

**Deliverables**:
- `transform.js` (extraction for documentation)
- Unit test cases (manual verification)

---

### Phase 5: Testing & Validation (Day 3 - Morning)
**Duration**: 2 hours

| Test Case | Expected Result | Status |
|-----------|----------------|--------|
| Normal execution | Report sent at 08:00, all KPIs populated | ⏳ |
| DB connection failure | Error notification to admin channel | ⏳ |
| No data for yesterday | Message shows "No data available for {date}" | ⏳ |
| Anomaly detected | Alert section includes warning emoji + description | ⏳ |
| WoW calculation edge case | Last week data missing → shows "N/A" | ⏳ |

**Deliverables**:
- `TEST_RESULTS.md`
- Screenshot: successful report
- Screenshot: error handling

---

### Phase 6: Documentation & GitHub (Day 3 - Afternoon)
**Duration**: 3 hours

- [ ] Write comprehensive `README.md`:
  - **Problem statement**: Why this project exists (fill portfolio gap)
  - **Architecture diagram**: Mermaid flowchart
  - **Setup guide**: How to replicate (PostgreSQL + n8n + Slack)
  - **SQL queries explained**: Breakdown of Window Functions, CTEs
  - **Differentiation**: vs Marketing ROI, vs Finance Close Pack
- [ ] Create `docs/` folder:
  - `SETUP.md`: Step-by-step installation
  - `SQL_GUIDE.md`: Query explanations for interview prep
  - `SLACK_INTEGRATION.md`: Webhook setup
- [ ] Add screenshots:
  - n8n workflow
  - Slack message examples
  - PostgreSQL schema diagram
- [ ] Push to GitHub

**Deliverables**:
- `README.md`
- `docs/SETUP.md`
- `docs/SQL_GUIDE.md`
- `docs/SLACK_INTEGRATION.md`

---

### Phase 7: Portfolio Integration (Day 4 - Morning)
**Duration**: 2 hours

- [ ] Update Notion project database entry
- [ ] Write "Evolution Story" connecting Phase 1 → Phase 2:
  ```
  Phase 1: Static Analysis (Coupang Dashboard)
  └─ CSV prototype → PostgreSQL migration → Deep SQL analysis
  
  Phase 2: Automated Monitoring (This Project)
  └─ n8n workflow → Daily Slack delivery → Proactive alerts
  
  Impact: From "pull-based" (manual checks) to "push-based" (automated delivery)
  ```
- [ ] Prepare interview talking points:
  - **Why n8n?**: Lighter than Airflow, UI-based workflow design
  - **Why daily?**: Balance between real-time (expensive) and weekly (too slow)
  - **Differentiation**: Internal KPIs (this) vs External Ads (Marketing ROI)

**Deliverables**:
- Updated Notion entry
- Interview Q&A doc

---

## 🧪 Testing Strategy

### Unit Tests (Manual)
- [ ] SQL query correctness:
  - Yesterday's data: `SELECT * FROM orders WHERE order_date = '2026-02-12'`
  - WoW data: `SELECT * FROM orders WHERE order_date = '2026-02-05'`
  - Top 3 products: Verify ranking logic
- [ ] WoW calculation:
  - Revenue: (100 - 80) / 80 * 100 = 25% ↑
  - Orders: (50 - 60) / 60 * 100 = -16.67% ↓
- [ ] Anomaly detection:
  - Conv rate: 2.5% → 2.0% → -20% change → Alert triggered
  - Revenue: ₩10M → ₩7M → -30% change → Critical alert

### Integration Tests
- [ ] End-to-end workflow:
  - Trigger manually → Verify Slack message received
  - Check execution time < 2 minutes
- [ ] Error scenarios:
  - Disconnect PostgreSQL → Verify error notification
  - Invalid Slack webhook → Verify retry logic

### Acceptance Tests
- [ ] Business validation:
  - Show sample report to simulated stakeholder
  - Verify KPIs match manual calculation
  - Confirm message format is readable

---

## ⚠️ Risks & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **PostgreSQL query timeout** | Medium | High | Add query timeout (10s), fallback to cached data |
| **Slack rate limit** | Low | Medium | Single message per day, well within limits |
| **n8n server downtime** | Low | High | Deploy on cloud (Railway/Render) with uptime monitoring |
| **Data freshness lag** | Medium | Medium | Set acceptable SLA (data from yesterday, not real-time) |
| **Coupang data schema change** | Low | Medium | Versioned SQL queries, schema validation |

---

## 🎓 Learning Objectives (For Portfolio)

### Technical Skills
- [x] **SQL Mastery**: Window Functions (LAG, RANK), CTEs, aggregations
- [x] **n8n Automation**: 7-node workflow, Code nodes, Merge node, parallel execution
- [x] **Supabase**: REST API (RPC), PostgreSQL, serverless functions
- [x] **Slack API**: Webhooks, mrkdwn formatting, this.helpers.httpRequest()

### Business Skills
- [x] **KPI Selection**: Choose metrics that matter (conversion rate > page views)
- [x] **Anomaly Detection**: Simple but effective threshold-based alerts
- [x] **Stakeholder Communication**: Non-technical message formatting

### Portfolio Value
- [ ] **At Home JD Match**: SQL ✅, Automation ✅, Python ✅, Business Impact ✅
- [ ] **Differentiation**: Fill gap between static analysis and external marketing automation
- [ ] **Evolution Story**: Phase 1 (Analysis) → Phase 2 (Automation) progression

---

## 📚 References & Resources

### Technical Documentation
- [n8n Workflow Automation](https://docs.n8n.io/)
- [PostgreSQL Window Functions](https://www.postgresql.org/docs/current/tutorial-window.html)
- [Slack Incoming Webhooks](https://api.slack.com/messaging/webhooks)
- [Supabase PostgreSQL](https://supabase.com/docs/guides/database)

### Inspiration
- Netflix Data Engineering: Daily reporting pipelines
- Airbnb Metrics Platform: Automated anomaly detection
- Uber's Data Quality: Threshold-based alerting

---

## ✅ Definition of Done

This project is considered **complete** when:

- [x] PRD approved
- [x] n8n workflow executes successfully (manual trigger) — 7-node pipeline
- [x] Slack message delivered with all KPIs populated
- [x] GitHub repository created with complete README
- [x] At least 3 SQL queries demonstrate Window Functions (RANK, COALESCE, CASE)
- [x] Anomaly detection tested (3+ edge cases)
- [x] Documentation includes setup guide + SQL explanations
- [ ] Portfolio story connects Phase 1 (Coupang Dashboard) → Phase 2 (This project)
- [ ] Interview Q&A prepared (differentiation talking points)

---

## 📅 Timeline Summary

| Phase | Duration | Deliverables |
|-------|----------|-------------|
| **Day 1 AM**: PostgreSQL Setup | 2h | SQL queries, schema |
| **Day 1 PM**: n8n Workflow | 4h | Workflow JSON, screenshot |
| **Day 2 AM**: Slack Integration | 2h | Message template, webhook |
| **Day 2 PM**: Python Transform | 3h | Transform logic, anomaly detection |
| **Day 3 AM**: Testing | 2h | Test results, edge cases |
| **Day 3 PM**: Documentation | 3h | README, SQL guide, setup docs |
| **Day 4 AM**: Portfolio Integration | 2h | Notion update, interview prep |

**Total**: 18 hours (~2.5 days with buffer)

---

## 🚀 Next Steps

1. ✅ **Approve PRD** (Review this document)
2. ⏳ **Set up environment** (Day 1 AM):
   - Install n8n (Docker or npm)
   - Verify PostgreSQL connection
   - Create Slack webhook
3. ⏳ **Start Phase 1**: Write SQL queries
4. ⏳ **Iterate**: Build → Test → Document
5. ⏳ **Publish**: Push to GitHub, update Notion

---

**Ready to proceed? Let's build this! 🚀**
