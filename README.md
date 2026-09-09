# ✈️ Gemini Live Thai Voice Agent Platform

A multimodal, voice-first airline customer service platform built on the **Google Agent Development Kit (ADK)** and the **Google Gemini Multimodal Live API** (`gemini-3.1-flash-live-preview`).

The platform provides end-to-end conversational customer journeys in natural Thai, featuring specialized multi-agent orchestration, deterministic state machine guardrails, and real-time bidirectional audio streaming.

---

## 🏛️ System Architecture & Multi-Agent Structure

The system is organized into a 3-tier multi-agent hierarchy with distinct personas, dedicated prebuilt voices, and decentralized coordination:

```
                          ┌────────────────────────────────┐
                          │    thai_customer_orchestrator  │
                          │   (Front Desk Concierge - ฝน)  │
                          │        Voice: Aoede            │
                          └───────────────┬────────────────┘
                                          │
                  ┌───────────────────────┴───────────────────────┐
                  ▼                                               ▼
   ┌─────────────────────────────┐                 ┌─────────────────────────────┐
   │    flight_booking_agent     │                 │       complaint_agent       │
   │ (Booking Specialist - ก้อย) │ ◄─────────────► │ (Grievance Specialist - ไอติม)│
   │        Voice: Kore          │  Peer Transfer  │        Voice: Charon        │
   └─────────────────────────────┘                 └─────────────────────────────┘
```

### Agent Roles & Voice Personas

| Agent Name | Role | Persona & Tone | Prebuilt Voice | Tools |
| :--- | :--- | :--- | :--- | :--- |
| **`thai_customer_orchestrator`** | Front Desk Concierge | **"ฝน"** — Warm, courteous, welcoming | `Aoede` | `authenticate_customer`, `check_customer_status`, `terminate_call` |
| **`flight_booking_agent`** | Booking Specialist | **"ก้อย"** — Energetic, professional, concise | `Kore` | `search_real_flights`, `confirm_flight_booking`, `route_customer_followup`, `terminate_call` |
| **`complaint_agent`** | Resolution Specialist | **"ไอติม"** — Calm, empathetic, reassuring | `Charon` | `record_customer_complaint`, `query_complaint_status`, `route_customer_followup`, `terminate_call` |

### Key Architectural Highlights
- **Decentralized Coordination:** After completing a domain task (booking or complaint), sub-agents do *not* force an unnecessary handoff back to the orchestrator. They directly ask what else the customer needs and laterally route to peer agents or terminate politely.
- **Deterministic Follow-Up Intent Routing (`route_customer_followup`):** Eliminates LLM transfer hallucinations by programmatically setting `tool_context.actions.transfer_to_agent`.
- **`ToolContext` State Determinism:** Enforces a strict 3-attempt authentication lockout (`auth_fail_count`), automatic session profile injection (`customer_id`, `customer_name`), and lifecycle state tracking (`session_stage`).
- **Canonical Intent Lexicon (`app/intent_lexicon.py`):** Shared keyword dictionary guaranteeing 100% classification parity across all tools.

---

## 🚀 Quickstart & Local Setup

### 1. Prerequisites
- Python 3.11+
- Google Gemini API Key ([Get one at Google AI Studio](https://aistudio.google.com/))

### 2. Clone Repository & Setup Virtual Environment

```bash
git clone https://github.com/pantana-na/gemini-live-bot.git
cd gemini-live-bot

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .
```

### 3. Environment Configuration

Copy the template `.env.example` to `.env` and fill in your Gemini API Key:

```bash
cp .env.example .env
```

Edit `.env`:
```ini
GEMINI_API_KEY=your_actual_gemini_api_key_here
GOOGLE_GENAI_USE_VERTEXAI=FALSE
LIVE_API_MODEL=gemini-3.1-flash-live-preview
```

---

## 🖥️ How to Test App Locally

### 1. Start the Interactive ADK Web Interface
The application runs on the official **Google Agent Development Kit (ADK) Web Server**, which manages multimodal session state, audio streaming, and multi-agent handoffs:

```bash
# Start the ADK Web Server on port 8000
adk web --port 8000 .
```

* **Interactive Web Console:** [http://localhost:8000/dev-ui/](http://localhost:8000/dev-ui/) (or [http://localhost:8000/](http://localhost:8000/))
* **Discovered Application:** `app` ([`thai_customer_orchestrator`](./app/agent.py) / Voice persona: **ฝน**)
* **Health Endpoint:** [http://localhost:8000/health](http://localhost:8000/health) (`{"status": "ok"}`)
* **App Metadata:** [http://localhost:8000/apps/app/app-info](http://localhost:8000/apps/app/app-info)

### 2. Alternative: Command-Line Single Prompt Run
You can also run direct prompts via ADK CLI:
```bash
adk run app "สวัสดีครับ ผมสมชาย ใจดี เกิด 15 มกราคม 2533 อยากเช็คเที่ยวบินไปเชียงใหม่ครับ"
```

### 3. Run the Automated Test Suite
The repository includes **67 automated unit and property-based tests** (Hypothesis generative testing):
```bash
pytest -v
```

---

## 🚀 How to Deploy to Cloud

The platform architecture provides a **dual-tier cloud topology**:
1. **Core Agent Intelligence:** Deployed to **Vertex AI Agent Engine** (`reasoningEngines`) via `agents-cli`.
2. **Interactive Multimodal Testing UI:** Deployed to **Google Cloud Run** running the containerized ADK Web UI (`/dev-ui/`) with public/domain unauthenticated ingress (Rule 10 Pattern 3).

### 1. Automated Deployment via `scripts/deploy.sh` (Recommended)

The [`scripts/deploy.sh`](./scripts/deploy.sh) script automatically extracts and validates configuration parameters directly from your unified [`.env`](./.env) file:

```bash
# Preview deployment without modifying cloud resources (Dry-Run)
./scripts/deploy.sh nonprod web --dry-run
./scripts/deploy.sh nonprod agent --dry-run

# Deploy the Interactive Web UI Companion to Cloud Run (Browser Access)
./scripts/deploy.sh nonprod web

# Deploy the Multi-Agent Engine to Vertex AI Agent Engine
./scripts/deploy.sh nonprod agent

# Deploy both Vertex AI Agent Engine & Cloud Run Web UI
./scripts/deploy.sh nonprod all

# Check status of deployed Vertex AI Agent Engine
./scripts/deploy.sh --status
```

### 2. Live Cloud Access Links (Non-Prod)

* **🌐 Interactive Browser Web Console (ADK Web on Cloud Run):**
  👉 **[https://gemini-live-bot-web-nonprod-cwmwtobz3a-as.a.run.app/dev-ui/](https://gemini-live-bot-web-nonprod-cwmwtobz3a-as.a.run.app/dev-ui/)**
  *(Direct browser microphone streaming, real-time audio playback, sub-agent handoffs & inspector)*
* **🩺 Public Health Endpoint:**
  👉 **[https://gemini-live-bot-web-nonprod-cwmwtobz3a-as.a.run.app/health](https://gemini-live-bot-web-nonprod-cwmwtobz3a-as.a.run.app/health)** (`{"status": "ok"}`)
* **⚙️ Vertex AI Agent Engine Console:**
  👉 **[Vertex AI Reasoning Engine Console](https://console.cloud.google.com/vertex-ai/agents/agent-engines/locations/asia-southeast1/agent-engines/7481648861434347520?project=cs-poc-y03r7kmfyov4kilzg50fd7s)**

---

### 3. Manual Deployment via Google Agents CLI (`agents-cli`)

You can also invoke `agents-cli` directly:

```bash
# 1. Inspect Project Metadata & Manifest
agents-cli info

# 2. Preview deployment
agents-cli deploy --dry-run

# 3. Deploy to Vertex AI Agent Engine
agents-cli deploy \
  --deployment-target agent_runtime \
  --project=your-gcp-project-id \
  --region=asia-southeast1 \
  --service-name=gemini-live-bot-nonprod \
  --cpu=1 \
  --memory=4Gi \
  --min-instances=0 \
  --max-instances=5 \
  --secrets=GEMINI_API_KEY=gemini-api-key:latest \
  --update-env-vars=ENVIRONMENT=nonprod,LIVE_API_MODEL=gemini-3.1-flash-live-preview,GOOGLE_GENAI_USE_VERTEXAI=TRUE

# 4. Check deployment status
agents-cli deploy --status
```

* **Project Manifest:** [`agents-cli-manifest.yaml`](./agents-cli-manifest.yaml)
* **Agent Platform Config:** [`.agent_engine_config.json`](./.agent_engine_config.json)

---

### 3. Native ADK CLI Alternative

You can also deploy directly using native Google ADK CLI:
```bash
adk deploy agent_engine \
  --project=your-gcp-project-id \
  --region=asia-southeast1 \
  --service_name=gemini-live-bot \
  app
```

---

### 4. Continuous Deployment via Cloud Build (CI/CD)

The repository provides [`cloudbuild.yaml`](./cloudbuild.yaml) which automatically runs tests, invokes `agents-cli deploy`, and verifies post-deployment status upon Git pushes to `main` (Non-Prod) and `prod` (Prod).

## 🧪 Test Scenarios & Test Scripts

### Pre-Seeded Test Customers

The mock database includes 20 realistic Thai customer records in [`app/mock_data.py`](./app/mock_data.py):

| Customer ID | Name (Thai) | Date of Birth | Loyalty Tier |
| :--- | :--- | :--- | :--- |
| **`CUST-001`** | **สมชาย ใจดี** | `15 มกราคม 2533` (1990-01-15) | Gold |
| **`CUST-002`** | **วรรณภา สุขสมบูรณ์** | `20 พฤษภาคม 2528` (1985-05-20) | Platinum |
| **`CUST-003`** | **กิตติศักดิ์ รัตนดิลก** | `8 พฤศจิกายน 2535` (1992-11-08) | Silver |
| **`CUST-004`** | **ชลธิชา พงษ์ไพโรจน์** | `25 มีนาคม 2541` (1998-03-25) | Standard |

---

### Scenario 1: Flight Booking & Session Completion

1. **User:** `"สวัสดีครับ ผมสมชาย ใจดี เกิด 15 มกราคม 2533 อยากจองตั๋วเครื่องบินไปเชียงใหม่ครับ"`
   - **Agent (`ฝน` - Orchestrator):** Authenticates customer $\to$ triggers immediate transfer to Flight Booking Specialist (`ก้อย`).
2. **Agent (`ก้อย` - Flight Booking):** Introduces herself as "ก้อย" and asks for departure dates.
3. **User:** `"เดินทางวันที่ 20 กันยายนนี้ครับ ขอช่วงเช้า"`
   - **Agent (`ก้อย`):** Calls `search_real_flights` and presents top-3 flight options with flight numbers and prices.
4. **User:** `"เลือกเที่ยวบิน TG102 ครับ ยืนยันการจอง"`
   - **Agent (`ก้อย`):** Calls `confirm_flight_booking`, verbally confirms 6-character PNR booking reference, and asks: *"มีบริการอื่นใดให้ก้อยช่วยดูแลเพิ่มเติมอีกไหมคะ?"*
5. **User:** `"ไม่มีเรื่องอื่นแล้วครับ ขอบคุณมากครับ"`
   - **Agent (`ก้อย`):** Calls `route_customer_followup`, recognizes completion intent, gives warm farewell, and terminates call.

---

### Scenario 2: Complaint Filing & Lateral Peer Transfer

1. **User:** `"สวัสดีครับ ผมกิตติศักดิ์ รัตนดิลก เกิด 8 พฤศจิกายน 2535 อยากร้องเรียนเรื่องกระเป๋าหายครับ"`
   - **Agent (`ฝน` - Orchestrator):** Authenticates customer $\to$ triggers immediate transfer to Complaint Specialist (`ไอติม`).
2. **Agent (`ไอติม` - Complaint):** Introduces himself empathetically, asks for incident details in 2–3 question sets.
3. **User:** `"บินมาจากโตเกียวเมื่อวาน กระเป๋าไม่มากับเที่ยวบิน ต้องการให้ช่วยติดตามด่วนครับ"`
   - **Agent (`ไอติม`):** Calls `record_customer_complaint`, confirms Ticket ID (`TKT-YYYYMMDD-XXXX`) and 24–48hr SLA, then asks: *"มีบริการอื่นใดให้ไอติมช่วยดูแลเพิ่มเติมอีกไหมครับ?"*
4. **User:** `"อยากจองตั๋วเครื่องบินไปภูเก็ตต่อเลยครับ"`
   - **Agent (`ไอติม`):** Calls `route_customer_followup`, detects flight booking intent, and **laterally hands off to `flight_booking_agent` (`ก้อย`)** without going back to root.
5. **Agent (`ก้อย`):** Takes over and assists with booking Phuket flight.

---

### Scenario 3: Authentication Security Lockout (3 Strikes)

1. **User:** `"ผมสมชาย ใจดี เกิด 1 มกราคม 2540"` (Incorrect DOB)
   - **System:** Auth failure count = 1. Prompts for correct credentials.
2. **User:** `"เกิด 1 มกราคม 2535"` (Incorrect DOB)
   - **System:** Auth failure count = 2. Prompts for correct credentials.
3. **User:** `"เกิด 1 มกราคม 2530"` (Incorrect DOB)
   - **System:** Auth failure count = 3. **Guardrail 1A triggers:** Calls `terminate_call(reason='AUTH_FAILURE_EXCEEDED')`, delivers polite security notice, and disconnects.

---

### Scenario 4: Out-of-Scope Intent Guardrail

1. **User:** `"ช่วยแนะนำร้านอาหารอร่อยๆ แถวสยาม หรือแนะนำหุ้นหน่อย"`
   - **System:** **Guardrail 1B triggers:** Calls `terminate_call(reason='OUT_OF_SCOPE_INTENT')`, explains services are restricted to flight reservations and complaints, and terminates call.

---

## 🔬 Running Automated Test Suite

The project includes **67 automated tests** (deterministic unit tests + Hypothesis property-based fuzzing tests):

```bash
pytest -v
```

### Test Breakdown
- **Step 1 Models & Invariants:** PNR validation, Thai Buddhist Era (พ.ศ.) $\leftrightarrow$ Common Era (ค.ศ.) conversion, lossless roundtrips.
- **Step 2 Domain Tools & PBT:** Top-3 flight price monotonicity, ticket uniqueness, 3-strike auth lockout, identity fallback, follow-up routing.
- **Step 3 Multi-Agent Orchestration & Prompts:** Hierarchy structure, peer transfers, voice profiles, Thai name greetings, and concise dialogue directives.
- **Step 4 Server & Cloud Probes:** Healthz liveness probe invariance, readiness probe, WebSocket handshake, and call termination.

---

## 📚 Governance & Documentation

- **System Specifications Index:** [`specs/README.md`](./specs/README.md)
- **Canonical Unified Specification:** [`specs/features/SPEC-SYSTEM-UNIFIED.md`](./specs/features/SPEC-SYSTEM-UNIFIED.md)
- **Baseline Architecture:** [`specs/baseline/system-overview.md`](./specs/baseline/system-overview.md)
- **Living Execution Progress:** [`specs/plan/PROGRESS_REPORT_20260909.md`](./specs/plan/PROGRESS_REPORT_20260909.md)
- **Architecture Diagrams & Topology:** [`docs/gemini-live-bot-architecture.md`](./docs/gemini-live-bot-architecture.md)
