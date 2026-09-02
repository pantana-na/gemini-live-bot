#!/usr/bin/env python3
"""
GCP Pricing Query Tool for Cost Estimation.

Queries Google Cloud Billing Catalog API (using active gcloud credentials)
or uses built-in reference pricing benchmarks to provide exact unit costs
for GCP services, SKUs, machine types, storage tiers, and AI models.
"""

import argparse
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

# Service mapping to Cloud Billing Service IDs
KNOWN_SERVICES = {
    "compute": "6F81-5844-456A",          # Compute Engine
    "compute engine": "6F81-5844-456A",
    "gce": "6F81-5844-456A",
    "gke": "6F81-5844-456A",
    "storage": "95FF-2EF5-5EA1",          # Cloud Storage
    "cloud storage": "95FF-2EF5-5EA1",
    "gcs": "95FF-2EF5-5EA1",
    "cloud run": "152E-C115-5142",        # Cloud Run
    "cloudrun": "152E-C115-5142",
    "bigquery": "24E6-581D-38E5",         # BigQuery
    "cloud sql": "9662-B51E-5089",        # Cloud SQL
    "cloudsql": "9662-B51E-5089",
    "vertex ai": "C7E2-9256-1C43",        # Vertex AI
    "vertex": "C7E2-9256-1C43",
    "pubsub": "A1E8-BE35-7EBC",           # Cloud Pub/Sub
    "cloud pub/sub": "A1E8-BE35-7EBC",
    "spanner": "D1A8-ED0B-CD04",          # Cloud Spanner
    "cloud spanner": "D1A8-ED0B-CD04",
    "datastream": "F7F6-DEBD-DB7B",       # Datastream
    "memorystore": "5440-F92D-6F40",      # Memorystore (Redis)
    "monitoring": "58CD-22C9-F11B",       # Cloud Monitoring
    "logging": "95FF-2EF5-5EA1",          # Cloud Logging
}

# Curated unit rates (USD) for standard regions (us-central1 baseline)
# Used as rapid reference or offline fallback
BENCHMARK_RATES = {
    # Compute Engine (us-central1, Linux on-demand)
    "compute:e2-micro": {"unit": "$/hour", "price": 0.00838, "monthly_730h": 6.12, "desc": "2 vCPU (shared), 1 GB RAM"},
    "compute:e2-small": {"unit": "$/hour", "price": 0.01676, "monthly_730h": 12.23, "desc": "2 vCPU (shared), 2 GB RAM"},
    "compute:e2-medium": {"unit": "$/hour", "price": 0.03351, "monthly_730h": 24.46, "desc": "2 vCPU (shared), 4 GB RAM"},
    "compute:e2-standard-2": {"unit": "$/hour", "price": 0.06702, "monthly_730h": 48.92, "desc": "2 vCPU, 8 GB RAM"},
    "compute:e2-standard-4": {"unit": "$/hour", "price": 0.13404, "monthly_730h": 97.85, "desc": "4 vCPU, 16 GB RAM"},
    "compute:e2-standard-8": {"unit": "$/hour", "price": 0.26808, "monthly_730h": 195.70, "desc": "8 vCPU, 32 GB RAM"},
    "compute:n2-standard-2": {"unit": "$/hour", "price": 0.0971, "monthly_730h": 70.88, "desc": "2 vCPU, 8 GB RAM"},
    "compute:n2-standard-4": {"unit": "$/hour", "price": 0.1942, "monthly_730h": 141.77, "desc": "4 vCPU, 16 GB RAM"},
    "compute:n2-standard-8": {"unit": "$/hour", "price": 0.3884, "monthly_730h": 283.53, "desc": "8 vCPU, 32 GB RAM"},
    "compute:c3-standard-4": {"unit": "$/hour", "price": 0.2088, "monthly_730h": 152.42, "desc": "4 vCPU, 16 GB RAM (Intel Emerald Rapids)"},
    "compute:pd-standard": {"unit": "$/GB-month", "price": 0.040, "desc": "Standard persistent disk"},
    "compute:pd-balanced": {"unit": "$/GB-month", "price": 0.100, "desc": "Balanced persistent disk (SSD)"},
    "compute:pd-ssd": {"unit": "$/GB-month", "price": 0.170, "desc": "SSD persistent disk"},

    # GKE Management Fee
    "gke:cluster-management": {"unit": "$/hour/cluster", "price": 0.10, "monthly_730h": 73.00, "desc": "GKE cluster fee (1 free cluster per billing account in Autopilot/Standard)"},
    "gke:autopilot-cpu": {"unit": "$/vCPU-hour", "price": 0.0445, "monthly_730h": 32.48, "desc": "GKE Autopilot vCPU allocation"},
    "gke:autopilot-memory": {"unit": "$/GB-hour", "price": 0.004925, "monthly_730h": 3.60, "desc": "GKE Autopilot Memory allocation"},

    # Cloud Run
    "cloudrun:cpu-tier1": {"unit": "$/vCPU-second", "price": 0.00002400, "unit_hour": 0.0864, "desc": "Cloud Run CPU allocation (Tier 1)"},
    "cloudrun:memory-tier1": {"unit": "$/GiB-second", "price": 0.00000250, "unit_hour": 0.0090, "desc": "Cloud Run Memory allocation (Tier 1)"},
    "cloudrun:requests": {"unit": "$/million requests", "price": 0.40, "desc": "Cloud Run Requests (2M free/mo)"},
    "cloudrun:idle-cpu-min-instances": {"unit": "$/vCPU-second", "price": 0.00000250, "unit_hour": 0.0090, "desc": "Idle CPU for min-instances (idle discount)"},

    # Cloud Storage (us-central1 regional)
    "storage:standard": {"unit": "$/GB-month", "price": 0.020, "desc": "Standard storage (regional)"},
    "storage:standard-multiregion": {"unit": "$/GB-month", "price": 0.026, "desc": "Standard storage (multi-region US)"},
    "storage:nearline": {"unit": "$/GB-month", "price": 0.010, "desc": "Nearline storage (30-day min)"},
    "storage:coldline": {"unit": "$/GB-month", "price": 0.004, "desc": "Coldline storage (90-day min)"},
    "storage:archive": {"unit": "$/GB-month", "price": 0.0012, "desc": "Archive storage (365-day min)"},
    "storage:class-a-ops": {"unit": "$/10,000 ops", "price": 0.05, "desc": "Class A operations (insert, list, update)"},
    "storage:class-b-ops": {"unit": "$/10,000 ops", "price": 0.004, "desc": "Class B operations (get, read metadata)"},

    # BigQuery
    "bigquery:analysis-on-demand": {"unit": "$/TB scanned", "price": 6.25, "desc": "On-demand query analysis (1 TB free/mo)"},
    "bigquery:storage-active": {"unit": "$/GB-month", "price": 0.020, "desc": "Active storage (10 GB free/mo)"},
    "bigquery:storage-longterm": {"unit": "$/GB-month", "price": 0.010, "desc": "Long-term storage (>90 days untouched)"},
    "bigquery:edition-standard-slot": {"unit": "$/slot-hour", "price": 0.040, "desc": "Standard edition compute autoscaling slot"},
    "bigquery:edition-enterprise-slot": {"unit": "$/slot-hour", "price": 0.060, "desc": "Enterprise edition compute slot"},

    # Cloud SQL (PostgreSQL / MySQL, db-custom)
    "cloudsql:vcpu": {"unit": "$/vCPU-hour", "price": 0.0413, "monthly_730h": 30.15, "desc": "Cloud SQL Dedicated vCPU"},
    "cloudsql:memory": {"unit": "$/GB-hour", "price": 0.0070, "monthly_730h": 5.11, "desc": "Cloud SQL Memory"},
    "cloudsql:storage-ssd": {"unit": "$/GB-month", "price": 0.170, "desc": "Cloud SQL SSD Storage"},
    "cloudsql:ha-multiplier": {"unit": "factor", "price": 2.0, "desc": "High Availability (Regional HA) doubles instance cost"},

    # Vertex AI / Generative AI
    "vertex:gemini-3.7-flash-input": {"unit": "$/1M tokens", "price": 0.75, "desc": "Gemini 3.7 Flash input (introductory rate through 2026)"},
    "vertex:gemini-3.7-flash-output": {"unit": "$/1M tokens", "price": 3.75, "desc": "Gemini 3.7 Flash output (introductory rate through 2026)"},
    "vertex:gemini-3.1-pro-input": {"unit": "$/1M tokens", "price": 2.00, "desc": "Gemini 3.1 Pro input"},
    "vertex:gemini-3.1-pro-output": {"unit": "$/1M tokens", "price": 12.00, "desc": "Gemini 3.1 Pro output"},
    "vertex:gemini-2.0-flash-input": {"unit": "$/1M tokens", "price": 0.10, "desc": "Gemini 2.0 Flash input"},
    "vertex:gemini-2.0-flash-output": {"unit": "$/1M tokens", "price": 0.40, "desc": "Gemini 2.0 Flash output"},
    "vertex:gemini-1.5-flash-input": {"unit": "$/1M tokens", "price": 0.075, "desc": "Gemini 1.5 Flash input (<=128K context)"},
    "vertex:gemini-1.5-flash-output": {"unit": "$/1M tokens", "price": 0.30, "desc": "Gemini 1.5 Flash output (<=128K context)"},
    "vertex:gemini-1.5-pro-input": {"unit": "$/1M tokens", "price": 1.25, "desc": "Gemini 1.5 Pro input (<=128K context)"},
    "vertex:gemini-1.5-pro-output": {"unit": "$/1M tokens", "price": 5.00, "desc": "Gemini 1.5 Pro output (<=128K context)"},
    "vertex:text-embedding": {"unit": "$/1M characters", "price": 0.025, "desc": "Text-Embedding-004 / 005"},
    "vertex:vector-search-standard": {"unit": "$/replica-hour", "price": 0.12, "monthly_730h": 87.60, "desc": "Vector Search Index Endpoint (small/medium)"},

    # Pub/Sub
    "pubsub:throughput": {"unit": "$/TiB ingested/delivered", "price": 40.0, "desc": "Message throughput (10 GiB free/mo)"},

    # Datastream
    "datastream:cdc-volume": {"unit": "$/GB changed data", "price": 2.00, "desc": "Datastream change data capture per GB for first 500 GB; drops at volume"},

    # Networking & Security
    "network:egress-internet-standard": {"unit": "$/GB", "price": 0.12, "desc": "Standard tier internet egress (first 10TB/mo)"},
    "network:egress-internet-premium": {"unit": "$/GB", "price": 0.12, "desc": "Premium tier internet egress (0-1 TB: $0.12, 1-10 TB: $0.11)"},
    "network:egress-inter-region": {"unit": "$/GB", "price": 0.01, "desc": "Inter-region traffic within North America ($0.01-$0.02)"},
    "network:nat-gateway": {"unit": "$/gateway-hour", "price": 0.045, "monthly_730h": 32.85, "desc": "Cloud NAT gateway hourly charge"},
    "network:nat-data-processing": {"unit": "$/GB", "price": 0.045, "desc": "Cloud NAT data processing fee"},
    "network:load-balancer-forwarding-rule": {"unit": "$/rule-hour", "price": 0.025, "monthly_730h": 18.25, "desc": "Application Load Balancer (first 5 rules $0.025/hr total)"},
    "network:load-balancer-data-processing": {"unit": "$/GB", "price": 0.008, "desc": "ALB data processed (LCU/GB)"},
}


def get_gcloud_token() -> Optional[str]:
    """Retrieve active OAuth access token from gcloud."""
    for cmd in [
        ["gcloud", "auth", "print-access-token"],
        ["gcloud", "auth", "application-default", "print-access-token"]
    ]:
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            token = res.stdout.strip()
            if token:
                return token
        except Exception:
            continue
    return None


def fetch_billing_skus(service_id: str, token: str, query: str = "", region: str = "") -> List[Dict[str, Any]]:
    """Query Cloud Billing API for SKUs belonging to a specific service."""
    url = f"https://cloudbilling.googleapis.com/v1/services/{service_id}/skus?pageSize=500"
    headers = {"Authorization": f"Bearer {token}"}

    results = []
    page_token = ""
    max_pages = 2  # limit to avoid long latency

    for _ in range(max_pages):
        page_url = url + (f"&pageToken={page_token}" if page_token else "")
        req = urllib.request.Request(page_url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                skus = data.get("skus", [])
                for sku in skus:
                    desc = sku.get("description", "")
                    service_regions = sku.get("serviceRegions", [])
                    
                    if query and query.lower() not in desc.lower():
                        continue
                    if region and region not in service_regions and "global" not in service_regions:
                        continue
                    
                    # Extract rate
                    pricing_info = sku.get("pricingInfo", [])
                    price_str = "N/A"
                    unit = ""
                    nanos = 0
                    units_val = 0
                    if pricing_info:
                        expression = pricing_info[0].get("pricingExpression", {})
                        unit = expression.get("usageUnitDescription", expression.get("usageUnit", ""))
                        tiered_rates = expression.get("tieredRates", [])
                        if tiered_rates:
                            rate = tiered_rates[0].get("unitPrice", {})
                            units_val = int(rate.get("units", 0))
                            nanos = int(rate.get("nanos", 0))
                            unit_price = units_val + (nanos / 1_000_000_000.0)
                            price_str = f"${unit_price:,.6f}".rstrip("0").rstrip(".")

                    results.append({
                        "skuId": sku.get("skuId"),
                        "description": desc,
                        "regions": service_regions[:3],
                        "unit": unit,
                        "unitPriceUSD": units_val + (nanos / 1_000_000_000.0),
                        "priceFormatted": price_str
                    })

                page_token = data.get("nextPageToken")
                if not page_token:
                    break
        except Exception as e:
            print(f"[Warning] Billing API query error: {e}", file=sys.stderr)
            break

    return results


def lookup_benchmark(pattern: str) -> List[Dict[str, Any]]:
    """Look up items in curated benchmark rates table."""
    results = []
    pattern_lower = pattern.lower()
    for key, data in BENCHMARK_RATES.items():
        if pattern_lower in key.lower() or pattern_lower in data.get("desc", "").lower():
            results.append({"resource": key, **data})
    return results


def main():
    parser = argparse.ArgumentParser(description="Query Google Cloud Pricing for Cost Estimation")
    parser.add_argument("--service", "-s", help="Service name or ID (e.g. compute, storage, cloudrun, bigquery, vertex, cloudsql)")
    parser.add_argument("--query", "-q", default="", help="Keyword filter for SKU description (e.g. 'e2-standard', 'Instance Core', 'Active')")
    parser.add_argument("--region", "-r", default="", help="GCP Region (e.g. us-central1, europe-west1)")
    parser.add_argument("--lookup", "-l", help="Direct benchmark lookup (e.g. 'e2-standard-4', 'cloudrun', 'gemini', 'storage')")
    parser.add_argument("--json", action="store_true", help="Output raw JSON format")
    parser.add_argument("--list-services", action="store_true", help="List supported common service shortcuts")

    args = parser.parse_args()

    if args.list_services:
        print(json.dumps(KNOWN_SERVICES, indent=2) if args.json else "Supported services:\n" + "\n".join(f"  - {k}: {v}" for k, v in KNOWN_SERVICES.items()))
        return

    # Benchmark quick lookup
    if args.lookup:
        results = lookup_benchmark(args.lookup)
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print(f"\n=== Benchmark Pricing Matches for '{args.lookup}' ===")
            if not results:
                print("No matches found in benchmark catalog. Try --service and --query for live API lookup.")
            for r in results:
                print(f"• {r.get('resource')}: {r.get('price')} {r.get('unit')} | {r.get('desc')}")
                if "monthly_730h" in r:
                    print(f"  └─ Full-month (730h): ${r['monthly_730h']:,.2f}/month")
            print()
        return

    # Service-based lookup
    if args.service:
        service_input = args.service.lower()
        service_id = KNOWN_SERVICES.get(service_input, args.service)
        token = get_gcloud_token()

        if token and service_id:
            skus = fetch_billing_skus(service_id, token, query=args.query, region=args.region)
            if skus:
                if args.json:
                    print(json.dumps(skus, indent=2))
                else:
                    print(f"\n=== Live Billing SKUs for '{args.service}' (Filter: '{args.query}', Region: '{args.region or 'any'}') ===")
                    print(f"{'Description':<60} | {'Unit Price':<15} | {'Unit':<20} | {'Regions'}")
                    print("-" * 115)
                    for sku in skus[:25]:
                        reg_str = ", ".join(sku['regions']) if sku['regions'] else "global"
                        print(f"{sku['description'][:58]:<60} | {sku['priceFormatted']:<15} | {sku['unit'][:18]:<20} | {reg_str}")
                    if len(skus) > 25:
                        print(f"\n... and {len(skus) - 25} more matching SKUs. Narrow search with --query.")
                    print()
                return
            else:
                print(f"[Notice] Live API returned 0 matching SKUs. Falling back to benchmark rates.", file=sys.stderr)

        # Fallback to benchmark lookup
        fallback_query = args.query or args.service
        results = lookup_benchmark(fallback_query)
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print(f"\n=== Fallback Reference Rates for '{fallback_query}' ===")
            for r in results:
                print(f"• {r.get('resource')}: {r.get('price')} {r.get('unit')} | {r.get('desc')}")
                if "monthly_730h" in r:
                    print(f"  └─ Full-month (730h): ${r['monthly_730h']:,.2f}/month")
            print()
        return

    # Default output: print quick reference
    print("Usage:")
    print("  python3 query_gcp_pricing.py --lookup <keyword>       # Fast lookup from standard benchmark pricing")
    print("  python3 query_gcp_pricing.py --service compute --query e2-standard-4 --region us-central1  # Live Cloud Billing API")
    print("  python3 query_gcp_pricing.py --list-services          # List known service identifiers")


if __name__ == "__main__":
    main()
