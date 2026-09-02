# Example: End-to-End Cost Estimation Walkthrough

This example demonstrates how the `gcp-cost-estimator` skill analyzes an architecture document and codebase, queries live pricing, queries user inputs or applies baseline assumptions, and generates an itemized cost estimate.

---

## Scenario: Real-time CDC & GenAI Analytics Architecture

### Architecture Discovered from Design Doc / Codebase:
1. **Source OLTP Database:** Cloud SQL for PostgreSQL (`db-custom-4-16384` HA)
2. **Change Data Capture:** Datastream streaming CDC events from PostgreSQL to Cloud Storage.
3. **Data Lake & Warehouse:** Cloud Storage (Standard Bucket) + BigQuery (Data analytics & continuous queries).
4. **Agentic API & Frontend:** Cloud Run (2 vCPU, 4 GB RAM, container running FastAPI + LangChain).
5. **AI Inference:** Vertex AI Gemini 1.5 Flash for summarizing change data and answering queries.
6. **Network & Ingress:** Cloud Application Load Balancer with SSL termination.

---

### Step 1: Parameter Elicitation & Stated Assumptions

**Agent prompts user:**
> *"I identified the 6 key GCP components in your CDC & GenAI pipeline. To calibrate the monthly cost estimate, please choose your anticipated monthly workload profile:"*
> 1. (Recommended) Mid-Scale Production: ~50k-100k MAU, ~50 GB CDC changes/month, ~50k LLM turns/month.
> 2. Dev / POC Tier: <1k users, <5 GB CDC changes, <5k LLM turns/month.
> 3. Enterprise High-Scale: 1M+ users, 500 GB CDC changes/month, 500k LLM turns/month.

**User selects / assumes:** Option 1 (Mid-Scale Production).

**Agent notes stated assumptions:**
- Operating region: `us-central1`
- Cloud Run: 15,000,000 requests/month, 100ms avg execution time, concurrency=40 => ~1,040 vCPU-hours/month.
- Cloud SQL: 730 hours/month running `db-custom-4-16384` HA (4 vCPU, 16 GB RAM) + 200 GB SSD.
- Datastream: 50 GB CDC changed data/month.
- Cloud Storage: 500 GB-months Standard storage + 50,000 Class A ops.
- BigQuery: 2 TB scanned queries/month (on-demand) + 200 GB active storage.
- Vertex AI: 50,000 Gemini 1.5 Flash turns/month (1,500 input tokens / 500 output tokens per turn).
- Load Balancer & Egress: 1 ALB forwarding rule + 150 GB Premium internet egress.

---

### Step 2: Live Price Lookups via `query_gcp_pricing.py`

```bash
python3 scripts/query_gcp_pricing.py --lookup cloudrun
python3 scripts/query_gcp_pricing.py --lookup gemini
python3 scripts/query_gcp_pricing.py --lookup cloudsql
python3 scripts/query_gcp_pricing.py --lookup datastream
```

---

### Step 3: Calculation & BoM Breakdown

```json
{
  "project_name": "CDC & GenAI Analytics Pipeline",
  "currency": "USD",
  "items": [
    {
      "name": "Cloud Run API Service",
      "service": "Cloud Run",
      "category": "Compute",
      "sku": "2 vCPU / 4 GB container",
      "quantity": 1040,
      "unit": "vCPU-hours",
      "unit_price": 0.0864,
      "usage_per_month": 1040,
      "notes": "15M reqs, 100ms latency, concurrency 40"
    },
    {
      "name": "Cloud SQL PostgreSQL HA",
      "service": "Cloud SQL",
      "category": "Database",
      "sku": "db-custom-4-16384 (HA + 200GB SSD)",
      "quantity": 730,
      "unit": "hours",
      "unit_price": 0.3876,
      "usage_per_month": 730,
      "notes": "Primary + Standby HA replica in us-central1"
    },
    {
      "name": "Datastream CDC Stream",
      "service": "Datastream",
      "category": "Analytics",
      "sku": "CDC Data Ingestion",
      "quantity": 50,
      "unit": "GB",
      "unit_price": 2.00,
      "usage_per_month": 50,
      "notes": "50 GB CDC changed records processed"
    },
    {
      "name": "BigQuery Analysis & Storage",
      "service": "BigQuery",
      "category": "Analytics",
      "sku": "On-Demand Queries & Active Storage",
      "quantity": 1,
      "unit": "TB-scanned (net of free tier)",
      "unit_price": 6.25,
      "usage_per_month": 1.0,
      "notes": "2 TB queries (1 TB free tier) + $4.00 active storage"
    },
    {
      "name": "Vertex AI Gemini 1.5 Flash",
      "service": "Vertex AI",
      "category": "AI/ML",
      "sku": "Prompt & Response Tokens",
      "quantity": 50000,
      "unit": "turns",
      "unit_price": 0.0002625,
      "usage_per_month": 50000,
      "notes": "75M input tokens ($5.63) + 25M output tokens ($7.50)"
    },
    {
      "name": "Cloud Storage Data Lake",
      "service": "Cloud Storage",
      "category": "Storage",
      "sku": "Standard Regional GCS",
      "quantity": 500,
      "unit": "GB-month",
      "unit_price": 0.020,
      "usage_per_month": 500,
      "notes": "Raw CDC staging bucket"
    },
    {
      "name": "Load Balancer & Egress",
      "service": "Networking",
      "category": "Networking",
      "sku": "ALB Forwarding Rule + Egress",
      "quantity": 1,
      "unit": "month",
      "unit_price": 36.25,
      "usage_per_month": 1,
      "notes": "$18.25 ALB + 150 GB Premium egress ($18.00)"
    }
  ]
}
```

---

### Step 4: Final Estimated Output & Markdown Report

Save the generated markdown report to `docs/gcp_cost_estimate_cdc_genai_pipeline.md` in the project folder:

- **Saved Location:** `docs/gcp_cost_estimate_cdc_genai_pipeline.md`
- **Monthly On-Demand Total:** ~$548.74 / month
- **Annual On-Demand Total:** ~$6,584.88 / year
- **1-Year CUD Projected Total:** ~$445.00 / month (~19% total bill reduction, ~30% off database/compute)
- **3-Year CUD Projected Total:** ~$360.00 / month (~34% total bill reduction, ~55% off database/compute)
