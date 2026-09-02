# Google Cloud Unit Pricing Catalog & Dimension Reference

This reference documents the pricing dimensions, formulas, and baseline unit rates (USD in `us-central1` or multi-region baseline) across core Google Cloud services.

---

## 1. Compute & Containers

### Cloud Run (2nd Gen / Standard)
Cloud Run charges only for allocated resources during request handling (or continuously if CPU is always allocated / min-instances > 0).

| Metric | Unit Rate (Tier 1) | Free Tier (per month) | Calculation Formula |
| :--- | :--- | :--- | :--- |
| **CPU** | $0.00002400 / vCPU-sec ($0.0864 / vCPU-hr) | 180,000 vCPU-seconds | `(vCPU × Active_Seconds) × $0.000024` |
| **Memory** | $0.00000250 / GiB-sec ($0.0090 / GiB-hr) | 360,000 GiB-seconds | `(GiB × Active_Seconds) × $0.0000025` |
| **Requests** | $0.40 / 1,000,000 requests | 2,000,000 requests | `max(0, Total_Reqs - 2M) × 0.40 / 1M` |
| **Min Instances (Idle)** | $0.00000250 / vCPU-sec ($0.0090 / vCPU-hr) | - | `(Min_Instances × vCPU × Idle_Seconds) × Rate` |

> [!TIP]
> **Active Seconds Approximation**: `Total_Requests × (Avg_Latency_ms / 1000) / Concurrency_Level`

---

### Compute Engine (GCE) & GKE Nodes (us-central1, Linux)

| Machine Family | Specs (vCPU / RAM) | Hourly Rate ($/hr) | Monthly Rate (730 hrs) | 1-Yr CUD (~37% off) | 3-Yr CUD (~55% off) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **e2-micro** | 2 vCPU (shared), 1 GB | $0.00838 | $6.12 | $3.86 | $2.75 |
| **e2-small** | 2 vCPU (shared), 2 GB | $0.01676 | $12.23 | $7.70 | $5.50 |
| **e2-medium** | 2 vCPU (shared), 4 GB | $0.03351 | $24.46 | $15.41 | $11.01 |
| **e2-standard-2** | 2 vCPU, 8 GB | $0.06702 | $48.92 | $30.82 | $22.01 |
| **e2-standard-4** | 4 vCPU, 16 GB | $0.13404 | $97.85 | $61.65 | $44.03 |
| **e2-standard-8** | 8 vCPU, 32 GB | $0.26808 | $195.70 | $123.29 | $88.07 |
| **n2-standard-2** | 2 vCPU, 8 GB | $0.09710 | $70.88 | $44.65 | $31.90 |
| **n2-standard-4** | 4 vCPU, 16 GB | $0.19420 | $141.77 | $89.32 | $63.80 |
| **n2-standard-8** | 8 vCPU, 32 GB | $0.38840 | $283.53 | $178.62 | $127.59 |
| **c3-standard-4** | 4 vCPU, 16 GB (Emerald Rapids) | $0.20880 | $152.42 | $96.02 | $68.59 |

#### Persistent Disks (PD)
- **Standard PD (`pd-standard`)**: $0.040 / GB-month
- **Balanced SSD (`pd-balanced`)**: $0.100 / GB-month
- **SSD Persistent Disk (`pd-ssd`)**: $0.170 / GB-month
- **Hyperdisk Balanced**: $0.090 / GB-month + $0.005/IOPS + $0.004/MBps throughput

---

### GKE (Google Kubernetes Engine)
- **Cluster Management Fee**: $0.10 / cluster-hour ($73.00 / month). One zonal/regional cluster free per billing account.
- **GKE Autopilot Workloads**:
  - Pod vCPU: $0.0445 / vCPU-hour ($32.49 / month)
  - Pod Memory: $0.004925 / GB-hour ($3.60 / month)
  - Pod Ephemeral Storage: $0.0000548 / GB-hour ($0.04 / month)

---

## 2. Databases & Storage

### Cloud SQL (PostgreSQL / MySQL)
- **Dedicated vCPU**: $0.0413 / vCPU-hour ($30.15 / month per vCPU)
- **Dedicated Memory**: $0.0070 / GB-hour ($5.11 / month per GB)
- **SSD Storage**: $0.170 / GB-month
- **High Availability (Regional HA)**: 2x multiplier on instance and storage compute (primary + standby).
- **Automated Backups**: $0.080 / GB-month (for storage exceeding provisioned DB size).

*Example*: `db-custom-2-7680` (2 vCPU, 7.5 GB RAM) Single Zone = $(2×30.15) + (7.5×5.11) + (100 GB SSD × 0.17) = $60.30 + $38.33 + $17.00 = **$115.63/month**. (With HA: ~$231.26/month).

### Cloud Spanner
- **Spanner Processing Units**: $0.099 / 100 PUs per hour ($72.27 / month per 100 PUs; 1 Node = 1,000 PUs = $722.70/month regional).
- **Spanner Storage**: $0.30 / GB-month (regional).

### Cloud Storage (GCS)
- **Standard Storage (Regional)**: $0.020 / GB-month
- **Standard Storage (Multi-Regional)**: $0.026 / GB-month
- **Nearline Storage (30-day retention)**: $0.010 / GB-month
- **Coldline Storage (90-day retention)**: $0.004 / GB-month
- **Archive Storage (365-day retention)**: $0.0012 / GB-month
- **Operations**:
  - Class A (Uploads, List, Rewrite): $0.05 per 10,000 ops
  - Class B (Downloads, Get metadata): $0.004 per 10,000 ops

---

## 3. Analytics & Streaming

### BigQuery
- **Analysis (On-Demand)**: $6.25 per TB scanned (first 1 TB/month free).
- **Active Storage**: $0.020 / GB-month (first 10 GB free).
- **Long-term Storage (>90 days untouched)**: $0.010 / GB-month.
- **BigQuery Editions (Capacity Compute)**:
  - Standard Edition: $0.040 / slot-hour ($29.20 / month per slot autoscaled).
  - Enterprise Edition: $0.060 / slot-hour ($43.80 / month per slot).

### Pub/Sub
- **Message Ingestion & Delivery**: $40.00 per TiB (first 10 GiB/month free).
- **Message Storage**: $0.27 / GB-month (for snapshot / topic retention beyond 7 days).

### Datastream (CDC)
- **Data Ingested/Processed**: $2.00 per GB (first 500 GB/month); volume discounts apply past 500 GB.

---

## 4. Generative AI & Vertex AI

### Gemini & Foundation Models (Pay-per-Token)

| Model | Input Price (<=128K context) | Output Price (<=128K context) | Typical Turn Cost (1.5K in / 500 out) |
| :--- | :--- | :--- | :--- |
| **Gemini 3.7 Flash (Introductory)** | $0.750 / 1M tokens ($0.000750/1K) | $3.750 / 1M tokens ($0.003750/1K) | $0.0030000 (~$3.00 per 1K turns) |
| **Gemini 3.7 Flash (Standard)** | $1.500 / 1M tokens ($0.001500/1K) | $7.500 / 1M tokens ($0.007500/1K) | $0.0060000 (~$6.00 per 1K turns) |
| **Gemini 3.1 Pro** | $2.000 / 1M tokens ($0.002000/1K) | $12.000 / 1M tokens ($0.012000/1K) | $0.0090000 (~$9.00 per 1K turns) |
| **Gemini 2.0 Flash** | $0.100 / 1M tokens ($0.000100/1K) | $0.400 / 1M tokens ($0.00040/1K) | $0.0003500 (~$0.35 per 1K turns) |
| **Gemini 1.5 Flash** | $0.075 / 1M tokens ($0.000075/1K) | $0.300 / 1M tokens ($0.00030/1K) | $0.0002625 (~$0.26 per 1K turns) |
| **Gemini 1.5 Pro** | $1.250 / 1M tokens ($0.001250/1K) | $5.000 / 1M tokens ($0.00500/1K) | $0.0043750 (~$4.38 per 1K turns) |
| **Text-Embedding-004** | $0.025 / 1M characters | - | $0.0000250 per 1,000 chunks (1K char/chunk) |

### Vector Search (Matching Engine)
- **Deployed Index Endpoint**: ~$0.12 / replica-hour ($87.60 / month) for standard small index (`e2-standard-2` equivalent).

---

## 5. Networking & Security

- **Internet Egress (Standard Tier)**: $0.12 / GB (0–10 TB/month).
- **Internet Egress (Premium Tier)**: $0.12 / GB (first 1 TB), $0.11 / GB (1-10 TB).
- **Inter-region Egress (within US)**: $0.01 / GB.
- **Inter-region Egress (Cross-continent)**: $0.08 - $0.12 / GB.
- **Cloud NAT**: $0.045 / gateway-hour ($32.85 / month) + $0.045 / GB processed.
- **Application Load Balancer (ALB)**: $0.025 / hour (first 5 forwarding rules = $18.25 / month) + $0.008 / GB processed (LCU).
- **Cloud Armor**: $5.00 / policy-month + $1.00 / rule-month + $0.75 / million queries.
