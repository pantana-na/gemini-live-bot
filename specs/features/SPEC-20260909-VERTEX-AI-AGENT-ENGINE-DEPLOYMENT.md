# Specification: SPEC-20260909-VERTEX-AI-AGENT-ENGINE-DEPLOYMENT

## 1. Problem Statement & Objectives

### 1.1 Context & Motivation
Previously, the Gemini Live Bot application relied on custom Docker container packaging and manual deployment to Google Cloud Run via `gcloud run deploy`. While functional, this introduced unnecessary infrastructure maintenance overhead:
1. Managing Dockerfiles, OS base package CVE patches, and multi-stage container builds.
2. Manually wiring Cloud Run liveness probes, port bindings, and custom WebSocket bridging.
3. Managing session persistence and agent runtime context without platform-native Agent Engine support.

Google Cloud's **Vertex AI Agent Engine** (the Gemini Enterprise Agent Platform runtime, exposed via `reasoningEngines`) provides a fully managed, serverless execution environment designed specifically for Agent Development Kit (ADK) multi-agent graphs. The **Google Agents CLI (`agents-cli`)** streamlines the development lifecycle, allowing declarative deployment (`agents-cli deploy --deployment-target agent_runtime` / `adk deploy agent_engine`) directly from project manifests.

### 1.2 Goals
- **Native Platform Runtime:** Transition deployment target from standalone Cloud Run containers to **Vertex AI Agent Engine (Gemini Enterprise Agent Platform)**.
- **Unified Toolchain Automation:** Mandate **Google Agents CLI (`agents-cli`)** for build, deployment, and verification workflows.
- **Declarative Manifest Governance:** Codify deployment specifications in `agents-cli-manifest.yaml` and `.agent_engine_config.json`.
- **Built-in Enterprise Observability:** Enable native OpenTelemetry and Cloud Trace instrumentation (`GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true`).
- **Seamless Local Development:** Preserve local testing and rapid iteration via `adk web` and `agents-cli playground` without cloud dependencies.

### 1.3 Non-Goals
- Modifying the core conversational multi-agent logic (`thai_customer_orchestrator`, `flight_booking_agent`, `complaint_agent`).
- Altering the 20 pre-seeded Thai customer mock records or domain tool behavior.

---

## 2. System Architecture & Component Interaction

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               DEVELOPMENT & CI/CD PIPELINE                              │
│                                                                                        │
│   ┌────────────────────┐          ┌────────────────────────────────────────────────┐   │
│   │   GitHub Repo      │          │            Google Cloud Build                  │   │
│   │   (main / prod)    │─────────►│  - Run linting & unit/PBT tests                │   │
│   │                    │          │  - Execute: agents-cli deploy                  │   │
│   └────────────────────┘          │    --deployment-target agent_runtime           │   │
│                                   └───────────────────────┬────────────────────────┘   │
└───────────────────────────────────────────────────────────┼────────────────────────────┘
                                                            │ Deploys to
                                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│               VERTEX AI AGENT ENGINE (GEMINI ENTERPRISE AGENT PLATFORM)                 │
│                                                                                        │
│   Resource: projects/{project}/locations/{region}/reasoningEngines/{engine_id}         │
│                                                                                        │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                     Managed Agent Engine Runtime Container                     │   │
│   │                                                                                │   │
│   │   ┌────────────────────────────────────────────────────────────────────────┐   │   │
│   │   │                     thai_customer_orchestrator (ฝน)                    │   │   │
│   │   │                           Voice: Aoede                                 │   │   │
│   │   └───────────────────┬────────────────────────────────┬───────────────────┘   │   │
│   │                       │                                │                       │   │
│   │                       ▼                                ▼                       │   │
│   │   ┌───────────────────────────────┐        ┌───────────────────────────────┐   │   │
│   │   │     flight_booking_agent      │◄──────►│        complaint_agent        │   │   │
│   │   │         (ก้อย - Kore)          │  Peer  │        (ไอติม - Charon)        │   │   │
│   │   └───────────────────────────────┘ Transfer└───────────────────────────────┘   │   │
│   │                                                                                │   │
│   │   ┌────────────────────────────────────────────────────────────────────────┐   │   │
│   │   │     Built-in OpenTelemetry & Google Cloud Trace Instrumentation        │   │   │
│   │   └────────────────────────────────────────────────────────────────────────┘   │   │
│   └────────────────────────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Telemetry & Secret Bindings
                    ┌───────────────────────┴───────────────────────┐
                    ▼                                               ▼
     ┌─────────────────────────────┐                 ┌─────────────────────────────┐
     │      Cloud Trace &          │                 │        Secret Manager       │
     │      Cloud Logging          │                 │      (GEMINI_API_KEY)       │
     └─────────────────────────────┘                 └─────────────────────────────┘
```

---

## 3. Configuration Contracts & Data Models

### 3.1 `agents-cli-manifest.yaml` (Single Source of Truth)
```yaml
name: gemini-live-bot
agent_directory: app
region: asia-southeast1
base_template: adk
language: python
version: 1.0.0
create_params:
  deployment_target: agent_runtime
  session_type: memory
  cicd_runner: cloud_build
  agent_guidance_filename: GEMINI.md
  is_a2a: false
```

### 3.2 `.agent_engine_config.json`
```json
{
  "display_name": "gemini-live-bot",
  "description": "Multimodal Voice-First Thai Airline Customer Service Platform on Gemini Enterprise Agent Platform",
  "location": "asia-southeast1",
  "agent_directory": "app",
  "deployment_target": "agent_runtime",
  "min_instances": 1,
  "max_instances": 10,
  "cpu": 1,
  "memory": "4Gi",
  "telemetry": {
    "enable_cloud_trace": true,
    "enable_open_telemetry": true
  }
}
```

### 3.3 Multi-Environment `.env` Parameters
```ini
# Shared Configuration
GCP_PROJECT=your-gcp-project-id
GCP_REGION=asia-southeast1
AGENT_DEPLOYMENT_TARGET=agent_runtime
LIVE_API_MODEL=gemini-3.1-flash-live-preview
GOOGLE_GENAI_USE_VERTEXAI=TRUE

# Non-Prod Configuration Block
NONPROD_ENVIRONMENT_NAME=development
NONPROD_AGENT_ENGINE_ID=
NONPROD_SERVICE_NAME=gemini-live-bot-nonprod
NONPROD_MIN_INSTANCES=0
NONPROD_MAX_INSTANCES=5

# Prod Configuration Block
PROD_ENVIRONMENT_NAME=production
PROD_AGENT_ENGINE_ID=
PROD_SERVICE_NAME=gemini-live-bot-prod
PROD_MIN_INSTANCES=1
PROD_MAX_INSTANCES=10
```

---

## 4. CLI Execution & API Contracts

### 4.1 Deployment Command
```bash
# Deployment via Agents CLI to Vertex AI Agent Engine
agents-cli deploy \
  --deployment-target agent_runtime \
  --project=${PROJECT_ID} \
  --region=asia-southeast1 \
  --service-name=gemini-live-bot \
  --secrets=GEMINI_API_KEY=gemini-api-key:latest \
  --update-env-vars=GOOGLE_GENAI_USE_VERTEXAI=TRUE,LIVE_API_MODEL=gemini-3.1-flash-live-preview
```

### 4.2 Post-Deployment Status Verification
```bash
agents-cli deploy --status
```

---

## 5. Architectural Invariants

- **Invariant 1 (Target Integrity):** All cloud deployments must target `agent_runtime` (Vertex AI Agent Engine) rather than unmanaged container runtimes.
- **Invariant 2 (Manifest Synchronization):** `agents-cli-manifest.yaml` and `.agent_engine_config.json` must be version-controlled and synchronized in the project root.
- **Invariant 3 (Telemetry Mandate):** `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true` and `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true` must be enabled in the deployed runtime.
- **Invariant 4 (Local/Cloud Parity):** Agents running locally via `adk web` or `agents-cli playground` execute the exact same multi-agent class definitions (`app.agent:root_agent`) deployed to Vertex AI Agent Engine.

---

## 6. Implementation Plan & Test Matrix

### Step 1: Governance & Rules Synchronization
- Update `GEMINI.md` and `_agents/rules/devops_security_and_quality_standards.md` to establish the Agent CLI and Vertex AI Agent Engine mandate.
- **Completion Criteria:** Rules 5, 6, 7, and 9 codified and aligned.

### Step 2: Manifest & Configuration Scaffolding
- Implement `agents-cli-manifest.yaml` and `.agent_engine_config.json`.
- Update `.env` and `.env.example` with Vertex AI parameters.
- **Unit & PBT Tests:** Verify YAML/JSON parse validity and environment resolution.
- **Completion Criteria:** Manifests present and valid.

### Step 3: CI/CD Cloud Build Pipeline Adaptation
- Update `cloudbuild.yaml` to install `google-agents-cli` and run `agents-cli deploy --deployment-target agent_runtime`.
- **Completion Criteria:** Pipeline definition valid.

### Step 4: Documentation, Architecture Diagrams & Living Sync
- Synchronize `specs/baseline/system-overview.md`, `specs/README.md`, and `docs/gemini-live-bot-architecture.md`.
- Record execution progress report under `specs/plan/`.
- **Completion Criteria:** Zero spec drift across all markdown artifacts.
