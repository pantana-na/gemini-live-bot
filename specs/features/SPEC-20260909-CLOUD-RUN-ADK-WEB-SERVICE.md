# Specification: SPEC-20260909-CLOUD-RUN-ADK-WEB-SERVICE

## 1. Problem Statement & Objectives

### 1.1 Context & Motivation
While the core multi-agent reasoning graph has been successfully deployed to **Google Cloud Vertex AI Agent Engine** (`reasoningEngines/7481648861434347520`) via `agents-cli deploy`, Vertex AI Agent Engine is a managed backend platform service exposing gRPC/REST APIs and the Google Cloud Console test console.

To enable stakeholders, QA testers, and developers to test the voice-first multimodal agent using a full visual web console (with live browser microphone streaming, real-time audio playback, tool call indicators, and sub-agent handoff visualization) without requiring local port forwarding or workstation setups, an enterprise-grade companion **ADK Web UI Service on Google Cloud Run** is introduced.

### 1.2 Architectural Dual-Tier Topology
1. **Core Agent Platform Runtime:** Managed by **Vertex AI Agent Engine (Gemini Enterprise Agent Platform)**.
2. **Interactive Multimodal Web Interface:** Hosted on **Google Cloud Run** running the hardened containerized Google Agent Development Kit Web Server (`adk web`).

### 1.3 Goals
- **Browser-Accessible Cloud UI:** Deploy a dedicated Cloud Run service (`gemini-live-bot-web-nonprod` / `gemini-live-bot-web-prod`) serving the ADK Web UI on public/domain HTTPS.
- **Unified Deployment Script Integration:** Extend `scripts/deploy.sh` to support `agent`, `web`, and `all` targets.
- **Environment Parameter Cohesion:** Centralize Web UI Cloud Run parameters in `.env` and `.env.example` adhering strictly to Rule 8.
- **Zero Drift Across Specs & Docs:** Update architecture diagrams, SDD baseline, feature specs, and README instructions.

---

## 2. Dual-Tier Cloud Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 USER / CLIENT BROWSER                                  │
│                                                                                        │
│   Web Browser (Microphone Audio Stream + Live Speaker + Inspection Logs)               │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ HTTPS / WSS
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                           GOOGLE CLOUD RUN (ADK WEB SERVICE)                           │
│                                                                                        │
│   Service: gemini-live-bot-web-nonprod (asia-southeast1)                               │
│   Container: Dockerfile (python:3.13-slim non-root user appuser)                       │
│   Entrypoint: adk web . --host 0.0.0.0 --port 8080 --session_service_uri memory://     │
│   Port: 8080                                                                           │
│   Health Check: /health                                                                │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                     ┌──────────────────────┴──────────────────────┐
                     ▼                                             ▼
┌──────────────────────────────────────────┐    ┌────────────────────────────────────────┐
│        SECRET MANAGER (GEMINI_API_KEY)   │    │   VERTEX AI AGENT ENGINE               │
│        (gemini-api-key:latest)           │    │   (reasoningEngines/7481648861434347520)│
└──────────────────────────────────────────┘    └────────────────────────────────────────┘
```

---

## 3. Configuration Specification (.env)

Unified parameters in `.env`:
```bash
# Non-Prod Cloud Run Web Service
NONPROD_WEB_SERVICE_NAME=gemini-live-bot-web-nonprod
NONPROD_WEB_CPU=1
NONPROD_WEB_MEMORY=2Gi
NONPROD_WEB_MIN_INSTANCES=0
NONPROD_WEB_MAX_INSTANCES=3
NONPROD_WEB_URL=

# Prod Cloud Run Web Service
PROD_WEB_SERVICE_NAME=gemini-live-bot-web-prod
PROD_WEB_CPU=1
PROD_WEB_MEMORY=2Gi
PROD_WEB_MIN_INSTANCES=1
PROD_WEB_MAX_INSTANCES=5
PROD_WEB_URL=
```

---

## 4. CLI Execution & Toolchain Contracts

### 4.1 Deployment Script (`scripts/deploy.sh`) Contract
```bash
# Deploy Web UI companion to Cloud Run (Non-Prod)
./scripts/deploy.sh nonprod web

# Deploy Agent Engine runtime (Existing)
./scripts/deploy.sh nonprod agent

# Deploy both Agent Engine and Web UI
./scripts/deploy.sh nonprod all

# Dry-run support
./scripts/deploy.sh nonprod web --dry-run
```

---

## 5. Architectural Invariants

- **Invariant 1 (Security Isolation):** Cloud Run Web service runs as non-root user `10001:10001` (`appuser`) with secrets fetched strictly from Secret Manager.
- **Invariant 2 (Dual-Tier Complementarity):** Cloud Run Web service and Vertex AI Agent Engine coexist harmoniously, using identical `.env` configurations and shared secret bindings.
- **Invariant 3 (Self-Contained Deployment Automation):** All deployment options (`agent`, `web`, `all`) must be executable through `./scripts/deploy.sh`.
