# GCP Cloud Cost Estimation Report Template

Use the following markdown structure when generating the cost estimation report file (saved in `docs/gcp_cost_estimate_<workload_name>.md` inside the project folder).

---

```markdown
# 💰 Google Cloud Cost Estimation: [Workload / Project Name]

**Date:** [YYYY-MM-DD]  
**Target Region:** [e.g., us-central1 / europe-west1]  
**Architecture Source:** [e.g., test-architecture-diagram.html / terraform/ / main.py]  
**Workload Profile:** [e.g., Archetype C: Mid-Scale Production (~100k MAU, ~10 RPS)]

---

## 📊 Executive Summary

| Pricing Model | Monthly Run-Rate (USD) | Annual Run-Rate (USD) | Projected Savings |
| :--- | :--- | :--- | :--- |
| **On-Demand (Pay-As-You-Go)** | **$[Total_Monthly_OnDemand]** | **$[Total_Annual_OnDemand]** | Baseline |
| **1-Year Committed Use (CUD)** | $[Monthly_1Yr_CUD] | $[Annual_1Yr_CUD] | ~25-35% on steady compute/DB |
| **3-Year Committed Use (CUD)** | $[Monthly_3Yr_CUD] | $[Annual_3Yr_CUD] | ~50-55% on steady compute/DB |

> [!NOTE]
> All unit prices are sourced dynamically from Google Cloud Billing Catalog API and current official rates in `[Target Region]`. Free tier allowances have been credited where applicable.

---

## 🧩 Cost Distribution by Service Category

```mermaid
pie title Monthly Cost by Service Category (Total: $[Total_Monthly_OnDemand])
    "Compute & Containers" : [Compute_Cost]
    "Databases & Storage" : [Database_Cost]
    "AI & Machine Learning" : [AI_Cost]
    "Analytics & Streaming" : [Analytics_Cost]
    "Networking & Security" : [Network_Cost]
```

| Category | Monthly Cost (USD) | % of Total Bill |
| :--- | :--- | :--- |
| **Compute & Containers** | $[Compute_Cost] | [Compute_Pct]% |
| **Databases & Storage** | $[Database_Cost] | [Database_Pct]% |
| **AI & Machine Learning** | $[AI_Cost] | [AI_Pct]% |
| **Analytics & Streaming** | $[Analytics_Cost] | [Analytics_Pct]% |
| **Networking & Security** | $[Network_Cost] | [Network_Pct]% |
| **Total** | **$[Total_Monthly_OnDemand]** | **100.0%** |

---

## 📋 Itemized Bill of Materials (BoM)

| Service | Resource / SKU | Specs / Sizing | Monthly Usage | Unit Rate | Monthly Cost | Cost Model & Assumptions |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cloud Run** | App Service | 2 vCPU, 4 GB RAM | 1,500 vCPU-hrs | $0.0864 / vCPU-hr | $129.60 | Min-instances=1, scaling up to 10 instances |
| **Cloud SQL** | PostgreSQL DB | `db-custom-4-16384` HA | 730 hours (HA) | $0.3200 / hr total | $233.60 | Regional HA + 100 GB SSD |
| **Cloud Storage** | GCS Bucket | Standard Storage | 250 GB-months | $0.020 / GB-mo | $5.00 | Documents & media uploads |
| **Vertex AI** | Gemini 1.5 Flash | 1.5K input / 500 out | 50,000 requests | $0.075 / 1M in, $0.30 / 1M out | $13.13 | GenAI RAG agent processing |
| **Networking** | ALB & Egress | Premium Tier Egress | 100 GB egress | $0.12 / GB + $18.25 ALB | $30.25 | Web traffic & API responses |
| **Total** | | | | | **$[Total_Monthly_OnDemand]** | |

---

## 📝 Stated Assumptions & Workload Factors

> [!IMPORTANT]
> The following assumptions were used to model variable traffic and resource utilization. If your actual traffic pattern differs, refer to the sensitivity analysis below.

### 1. User-Specified Inputs:
- **Active User Base:** [e.g., 100,000 monthly users specified by user]
- **Target Deployment Region:** [e.g., us-central1]

### 2. Standard Baseline Assumptions Applied (Where details were omitted):
- **Operating Hours:** 730 hours/month (24/7 continuous operation).
- **Traffic Profile:** Average 10 RPS, Peak 30 RPS during business hours.
- **Data Retention & Storage:** 10% month-over-month data growth.
- **Read/Write Ratio:** 80% Read queries, 20% Writes.
- **AI Turn Context:** 1,200 input tokens, 500 output tokens per LLM query.
- **Network Egress Overhead:** 15% outbound payload ratio relative to stored assets.

---

## 📈 Sensitivity & Scale Analysis

How monthly infrastructure costs change as traffic scales:

| Scale Factor | Monthly Active Users | API Requests / Month | Estimated Monthly Cost | Delta vs Baseline |
| :--- | :--- | :--- | :--- | :--- |
| **0.5× (Light / Ramp-up)** | 50,000 MAU | ~2.5M reqs | $[Cost_Half] | -40% |
| **1.0× (Baseline Estimate)** | 100,000 MAU | ~5.0M reqs | **$[Total_Monthly_OnDemand]** | **0%** |
| **2.0× (Growth Spike)** | 200,000 MAU | ~10.0M reqs | $[Cost_2x] | +65% |
| **5.0× (High Scale)** | 500,000 MAU | ~25.0M reqs | $[Cost_5x] | +220% |

---

## 💡 FinOps & Cost Optimization Recommendations

1. **Commitment Discounts (CUD):** If running steady-state databases (Cloud SQL / Compute), purchasing a 1-year or 3-year Flexible CUD can yield **28% to 55% in savings** on baseline resources.
2. **Cloud Run Concurrency & Min-Instances:** Set concurrency to 40–80 requests per instance to optimize container CPU utilization. Use `min-instances=0` in non-prod environments.
3. **Storage Lifecycle Policies:** Transition GCS objects to Nearline storage after 30 days and Coldline after 90 days to reduce storage costs by up to **80%**.
4. **BigQuery Slot vs On-Demand Optimization:** Ensure tables are partitioned by day/month and clustered by commonly filtered columns to prevent full-table scans.
```
