---
name: gcp-cost-estimator
description: >-
  Estimate running Google Cloud Platform (GCP) cloud infrastructure costs by analyzing
  architecture design documents, diagrams, and codebase implementations. Queries real-time
  unit pricing from Google Cloud Billing API or public pricing endpoints, elicits unknown
  workload variables (users, RPS, queries, token counts) from the user, applies explicit
  baseline assumptions for missing or overly granular inputs, and generates itemized markdown cost reports
  in the "docs" folder inside the project folder with Committed Use Discount (CUD) and FinOps optimization recommendations.
---

# Google Cloud Platform (GCP) Cost Estimation Skill

You are an expert Google Cloud Principal Architect and FinOps Specialist. Your objective is to analyze technical design documents, architecture diagrams, Infrastructure-as-Code (Terraform, Pulumi, K8s), and application code to produce an accurate, transparent, and actionable running cost estimate for Google Cloud workloads.

---

## Workflow Overview

Execute the cost estimation process across 6 structured phases:

```mermaid
flowchart LR
    A[1. Architecture & Code Discovery] --> B[2. Component Inventory BoM]
    B --> C[3. Parameter Elicitation]
    C --> D[4. Stated Assumptions]
    D --> E[5. Dynamic Pricing Query]
    E --> F[6. Markdown Cost Report in docs/]
```

---

## Phase 1: Architecture & Codebase Discovery

Scan the project workspace to identify all provisioned and planned GCP services:
1. **Design Documents & Diagrams**: Read `.md`, `.html`, `.png`, `.pdf`, RFCs, and PRDs (e.g., architecture topologies, data flow diagrams).
2. **Infrastructure-as-Code (IaC)**: Search for Terraform files (`*.tf`, `*.tfvars`), OpenTofu, Pulumi, Kubernetes manifests (`*.yaml`, Helm charts), Cloud Run service definitions (`service.yaml`), Dockerfiles, and Cloud Build configs.
3. **Application Code**: Inspect client initializations, database connection pools, messaging brokers (Pub/Sub topics/subscriptions), storage bucket interactions, and AI model invocations (Vertex AI, Gemini SDK, LangChain, LlamaIndex).

---

## Phase 2: Component Inventory & Bill of Materials (BoM) Mapping

Categorize every discovered component into primary GCP service domains:

- **Compute & Containers**: Cloud Run (vCPU, memory, min/max instances, concurrency), GKE (Standard vs Autopilot, node machine types, cluster fees), Compute Engine (machine family, vCPU, RAM, boot disk size/type).
- **Databases & Caching**: Cloud SQL (engine, tier, dedicated vCPU/RAM, HA multi-zone, storage size, backups), Cloud Spanner (PUs/nodes, storage), Bigtable, Firestore, Memorystore for Redis/Memcached.
- **Storage**: Cloud Storage buckets (Standard, Nearline, Coldline, Archive), Persistent Disks (`pd-standard`, `pd-balanced`, `pd-ssd`, `hyperdisk`).
- **Analytics & Event Streaming**: BigQuery (on-demand vs capacity slots, active vs long-term storage), Pub/Sub (ingestion throughput, retention), Datastream (CDC volume), Dataflow (vCPU/GB workers).
- **Generative AI & Vertex AI**: Gemini models (Gemini 3.7 Flash, Gemini 3.1 Pro, Gemini 1.5 Flash/Pro: input/output token volume), Text Embeddings, Vector Search (Index endpoints, replica count), Vertex Feature Store.
- **Networking & Ingress**: Cloud Application Load Balancer (forwarding rules, data processed), Cloud NAT (gateways, egress throughput), Cloud Armor, Cloud CDN, Internet Egress (Standard vs Premium tier), Inter-region traffic.

---

## Phase 3: Workload Parameter Elicitation

Identify unknown runtime variables that cannot be inferred solely from static code or diagrams.

### Variables to Clarify:
1. **Scale & User Base**: Daily / Monthly Active Users (DAU / MAU) or queries per second (QPS / RPS).
2. **Data & Storage Volume**: Initial database size, monthly ingestion/change rate (GB/month), asset storage size.
3. **GenAI / LLM Volume**: Anticipated prompts/turns per day or month, average context length.
4. **Target Region**: Primary deployment region (default: `us-central1` if unspecified).

### How to Enquire the User:
- Use `ask_question` with 2–3 clear, high-level multiple-choice options corresponding to workload tiers (e.g., Dev/POC vs Mid-Scale Production vs Enterprise High-Scale).
- Keep questions high-level. Do not interrogate the user for dozens of low-level technical parameters.

---

## Phase 4: Stated Assumption Heuristics

If the user does not provide exact workload metrics, answers "not sure", skips the questionnaire, or if the system dynamics are too detailed to calibrate manually:

1. **Adopt a Baseline Sizing Archetype**:
   - **Archetype A: Dev / Sandbox / POC** (<1k users, scale-to-zero compute, single-zone DB, minimal egress).
   - **Archetype B: MVP / Low-Traffic App** (1k–10k MAU, avg 0.5 RPS, 50 GB DB, ~10k AI turns/mo).
   - **Archetype C: Mid-Scale Production (Default)** (50k–250k MAU, avg 6 RPS, peak 35 RPS, Cloud SQL HA 4 vCPU/16 GB, 500 GB storage, 100k AI turns/mo).
   - **Archetype D: Enterprise / High-Throughput Tier** (1M+ MAU, 500+ RPS, Spanner/GKE, multi-TB streaming).
2. **Apply Universal Standard Defaults**:
   - **Operating Hours**: `730 hours/month` (24/7 continuous operation).
   - **Read / Write Ratio**: `80% Read / 20% Write`.
   - **Network Egress**: `15%` of total transferred/stored data.
   - **GenAI Prompt Context**: `1,200 input tokens / 500 output tokens` per turn.
   - **Storage Growth**: `10%` month-over-month.
   - **Database Backups**: `100%` of primary disk size.
   - **Cloud Monitoring / Logging**: `2%` operational overhead.
3. **Explicitly Document Every Assumption**: In the generated report, clearly list all assumed values under a dedicated **"Stated Assumptions"** section so stakeholders understand the foundation of the estimate.

For full baseline details, refer to:
[standard_assumptions.md](./references/standard_assumptions.md)

---

## Phase 5: Dynamic Unit Pricing Resolution

Retrieve current unit costs using the built-in pricing scripts and live Google Cloud APIs:

### 1. Fast CLI Lookup & Billing API Query:
Run the pricing helper script located in `scripts/query_gcp_pricing.py`:

```bash
# Direct benchmark lookup for common resources:
python3 _agents/skills/gcp_cost_estimator/scripts/query_gcp_pricing.py --lookup cloudrun
python3 _agents/skills/gcp_cost_estimator/scripts/query_gcp_pricing.py --lookup gemini
python3 _agents/skills/gcp_cost_estimator/scripts/query_gcp_pricing.py --lookup e2-standard-4

# Query live Cloud Billing API (uses active gcloud credentials / ADC):
python3 _agents/skills/gcp_cost_estimator/scripts/query_gcp_pricing.py --service compute --query "n2-standard-4" --region us-central1
python3 _agents/skills/gcp_cost_estimator/scripts/query_gcp_pricing.py --service storage --region us-central1
```

### 2. Live Web Search Fallback:
If an emerging product SKU or promotional rate is needed, use `search_web` to verify official pricing on `cloud.google.com/<product>/pricing`.

### 3. Pricing Reference Catalog:
Consult the curated pricing matrix for rapid formula calculation:
[gcp_pricing_catalog.md](./references/gcp_pricing_catalog.md)

---

## Phase 6: Cost Modeling & Markdown Report Generation

### 1. Deterministic Calculation:
Calculate the itemized costs using the BoM calculator script:
```bash
python3 _agents/skills/gcp_cost_estimator/scripts/calculate_bom_cost.py <bom_file.json>
```

### 2. Generate Cost Estimation Markdown Report in docs/:
**CRITICAL**: Output and save the itemized cost report directly as a markdown (`.md`) file inside the `docs/` folder of the project workspace:
`docs/gcp_cost_estimate_<project_name>.md` (or `docs/gcp_cost_estimate.md`).
Ensure the `docs/` directory is created if it does not already exist.

Follow the template structure in:
[cost_report_template.md](./references/cost_report_template.md)

### Required Report Sections:
1. **Executive Summary Table**: Monthly & Annual Run-Rates for On-Demand, 1-Year CUD (~28% discount), and 3-Year CUD (~52% discount).
2. **Visual Cost Distribution**: Mermaid pie chart and percentage breakdown by category (Compute, Database, Storage, AI/ML, Analytics, Networking).
3. **Itemized Bill of Materials (BoM)**: Service name, SKU, configuration, monthly quantity, unit rate, monthly cost, and rationale.
4. **Stated Assumptions & Workload Factors**: Clear distinction between user-provided inputs and assumed default values.
5. **Sensitivity & Scale Analysis**: Cost progression at 0.5×, 1.0×, 2.0×, and 5.0× traffic.
6. **FinOps & Cost Optimization Recommendations**: Actionable architectural recommendations (CUD commitments, Spot/Preemptible, Cloud Run concurrency tuning, GCS lifecycle rules, BigQuery clustering).

---

## Examples

To inspect a complete end-to-end example walkthrough:
[sample_cost_analysis.md](./examples/sample_cost_analysis.md)
