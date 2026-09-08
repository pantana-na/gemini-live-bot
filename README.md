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

## 🖥️ How to Run Locally

You can run the application in two ways depending on your testing needs:

### Option A: Official Google ADK Web UI (Recommended for Interactive Testing)

The ADK Web UI provides an interactive visual interface to converse with the agents, view handoffs, and inspect tool executions.

```bash
adk web --port 8000 .
```

* **Web UI URL:** [http://localhost:8000/](http://localhost:8000/) or [http://localhost:8000/dev-ui/](http://localhost:8000/dev-ui/)
* Discovered app: `app` (`thai_customer_orchestrator`)

---

### Option B: FastAPI Streaming Server (WebSocket Endpoint & Health Probes)

Runs the production-grade FastAPI server with Cloud Run health probes and bidirectional WebSocket streaming.

```bash
uvicorn app.server:app --host 0.0.0.0 --port 8080 --reload
```

* **Service Discovery:** [http://localhost:8080/api/info](http://localhost:8080/api/info)
* **Cloud Run Liveness Probe (Rule 6):** [http://localhost:8080/healthz](http://localhost:8080/healthz)
* **Readiness Probe:** [http://localhost:8080/readyz](http://localhost:8080/readyz)
* **Live WebSocket Audio Endpoint:** `ws://localhost:8080/ws/live`

---

## 🧪 Test Scenarios & Test Scripts

### Pre-Seeded Test Customers

The mock database includes 20 realistic Thai customer records in [`app/mock_data.py`](./app/mock_data.py):

| Customer ID | Name (Thai) | Date of Birth | Loyalty Tier |
| :--- | :--- | :--- | :--- |
| **`CUST-001`** | **สมชาย ใจดี** | `15 มกราคม 2533` (1990-01-15) | Gold |
| **`CUST-002`** | **สมศรี มีสุข** | `22 กุมภาพันธ์ 2538` (1995-02-22) | Platinum |
| **`CUST-003`** | **กิตติศักดิ์ รัตนดิลก** | `8 มีนาคม 2528` (1985-03-08) | Silver |
| **`CUST-004`** | **นภา พิมลวรรณ** | `14 เมษายน 2541` (1998-04-14) | Standard |

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

1. **User:** `"สวัสดีครับ ผมกิตติศักดิ์ รัตนดิลก เกิด 8 มีนาคม 2528 อยากร้องเรียนเรื่องกระเป๋าหายครับ"`
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

### Automated WebSocket Test Script

An automated Python script is provided under [`scripts/test_live_ws.py`](./scripts/test_live_ws.py) to test the live WebSocket streaming server:

```bash
# Ensure FastAPI server is running (uvicorn app.server:app --port 8080)
python scripts/test_live_ws.py
```

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

- **System Specifications:** [`specs/README.md`](./specs/README.md)
- **Baseline Architecture:** [`specs/baseline/system-overview.md`](./specs/baseline/system-overview.md)
- **Feature Specs:** [`specs/features/`](./specs/features/)
- **Living Execution Progress:** [`specs/plan/PROGRESS_REPORT_20260908.md`](./specs/plan/PROGRESS_REPORT_20260908.md)
- **Architecture Diagrams:** [`docs/gemini-live-bot-architecture.md`](./docs/gemini-live-bot-architecture.md)
