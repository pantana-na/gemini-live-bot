# Gemini Live Bot: Technical System Architecture

> Multimodal Voice-First Intelligent Customer Service Platform with Google ADK, Gemini 3.1 Flash Preview, and Hierarchical Multi-Agent Delegation.

- **Status:** Designed & Specified
- **Target Foundation Model:** `gemini-3.1-flash-live-preview` (Gemini Multimodal Live BidiStream via Google AI Studio API Key)
- **Agent Framework:** Google Agent Development Kit (`google-adk v2.8.0`) & `agents-cli`
- **Primary Language:** Thai (ภาษาไทย)
- **Interactive Companion Diagram:** [`docs/gemini-live-bot-architecture.html`](./gemini-live-bot-architecture.html)

---

## 1. High-Level Architecture Overview

```
+----------------------------------------------------------------------------------------------------+
|                                      CUSTOMER CLIENT TIER                                          |
|                                                                                                    |
|    +----------------------------------+            +------------------------------------------+    |
|    |      Voice Input (Microphone)    |            |         Audio Output (Speaker)           |    |
|    |      16kHz / 24kHz PCM Audio     |            |         Low-latency streaming chunks     |    |
|    +-----------------+----------------+            +--------------------+---------------------+    |
+----------------------|--------------------------------------------------|--------------------------+
                       |                                                  ^
                       | WebSocket Bidirectional Audio Stream             |
                       v                                                  |
+----------------------------------------------------------------------------------------------------+
|                              ADK FASTAPI ORCHESTRATION LAYER (Port 8080)                           |
|                                                                                                    |
|    +------------------------------------------------------------------------------------------+    |
|    |  ADK Live Runner & Session Manager                                                        |    |
|    |  - Manages WebSocket lifecycle, audio frame chunking, and session context retention      |    |
|    |  - State: authenticated_user, customer_id, intent_stage, active_subagent                 |    |
|    +------------------------------------------------------------------------------------------+    |
|                                              |                                                     |
|                                              v                                                     |
|    +------------------------------------------------------------------------------------------+    |
|    |  Gemini Live Multimodal Engine (gemini-3.1-flash-live-preview via API Key)               |    |
|    |  - Real-time Audio-to-Audio reasoning & Speech-to-Speech synthesis in Thai                 |    |
|    |  - Integrated Function Calling & Tool Execution Loop                                     |    |
|    +------------------------------------------------------------------------------------------+    |
+----------------------------------------------|-----------------------------------------------------+
                                               |
                                               v
+----------------------------------------------------------------------------------------------------+
|                                    MULTI-AGENT DELEGATION TIER                                     |
|                                                                                                    |
|   +--------------------------------------------------------------------------------------------+   |
|   |  Root Orchestrator Agent (thai_customer_orchestrator)                                      |   |
|   |  - Role: Front-desk greeting & customer authentication in polite Thai                      |   |
|   |  - Verifies: Name + Birthdate against 20-profile Customer DB                               |   |
|   |  - Intent Detection: Routes to Flight Booking or Complaint Agent                          |   |
|   |  - Out-of-Scope: Politely declines, bids farewell, and executes terminate_call (hangup)   |   |
|   +-------------------+------------------------------+---------------------+-------------------+   |
|                       |                              |                     |                       |
|                       | Intent: flight_booking       | Intent: complaint   | Out-of-Scope Intent   |
|                       v                              v                     v                       |
|   +---------------------------------------+  +------------------------+  +---------------------+   |
|   | Flight Booking Agent                  |  | Complaint Agent        |  | Call Control Tool   |   |
|   | (flight_booking_agent)                |  | (complaint_agent)      |  | (terminate_call)    |   |
|   | - Collects: Origin, Dest, Dates       |  | - Genuine empathy      |  | - Polite refusal    |   |
|   | - Action: Real Google Search Grounding|  | - Situation overview   |  | - Courteous farewell|   |
|   | - Presents: Top 3 curated options     |  | - Generates Ticket ID  |  | - Hangup WebSocket  |   |
|   | - Books: Confirms & issues PNR code   |  | - SLA timeframe note   |  |                     |   |
|   +-------------------+-------------------+  +-----------+------------+  +---------------------+   |
+-----------------------|----------------------------------|-----------------------------------------+
                        |                                  |
                        v                                  v
+----------------------------------------------------------------------------------------------------+
|                                        DATA & PERSISTENCE TIER                                     |
|                                                                                                    |
|    +--------------------------+    +--------------------------+    +--------------------------+    |
|    |   Customer Mock DB       |    |   Real Google Search     |    |   Complaint Ticket DB    |    |
|    |   (20 Thai Profiles)     |    |   (Live Web Grounding)   |    |    (Issue Resolution)    |    |
|    |   - ID, Thai/EN Name     |    |   - Real-time flights    |    |   - Ticket ID            |    |
|    |   - Birthdate (B.E./C.E.)|    |   - Live schedules/fares |    |   - Category & Severity  |    |
|    |   - Loyalty Tier & Phone |    |   - Booking PNR Ledger   |    |   - Status & Timestamps  |    |
|    +--------------------------+    +--------------------------+    +--------------------------+    |
+----------------------------------------------------------------------------------------------------+
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Component Detail & Interaction Specifications

### 2.1 Audio & Streaming Protocol
- **Transport:** WebSocket over TLS (`wss://`) terminating on Cloud Run FastAPI service.
- **Payload Format:** 16,000 Hz, 16-bit linear PCM mono audio input; 24,000 Hz PCM audio output.
- **Model Endpoint:** Gemini Developer API Multimodal Live streaming endpoint using `gemini-3.1-flash-live-preview` (authenticated via `GEMINI_API_KEY` with Vertex AI toggle support).
- **Latency Optimization:** Direct streaming chunking; function calling execution happens in an asynchronous event loop without dropping the voice channel.

### 2.2 Agent Delegation & Session Transfer
- **State Preservation:** When `thai_customer_orchestrator` transfers control to `flight_booking_agent` or `complaint_agent`, customer authentication details (`customer_id`, `name_th`, `loyalty_tier`) are passed in `Session.state`.
- **Context Injection:** Sub-agents inherit the conversational memory and greeting context so the customer does not have to repeat their identity.

### 2.3 Data Stores & Search Grounding
1. **Mock Customer Store (20 Records):**
   - Realistic Thai naming distribution and Buddhist calendar birthdate conversion.
   - Dual-language matching (Thai script & English romanization).
2. **Real-Time Flight Discovery Engine:**
   - Real-world Google Search Grounding (no mock flights).
   - Dynamic schedule extraction and Top-3 selection algorithm prioritizing price and schedule convenience.
   - Confirmed bookings recorded to in-memory PNR ledger.
3. **Mock Complaint Ticket Store:**
   - Sequential ticket generation: `TKT-YYYYMMDD-XXXX`.
   - Category mapping: Flight Delay, Baggage, In-flight Service, Ticketing, Ground Staff.

---

## 3. DevOps, Observability & Cloud Deployment Topology

```mermaid
flowchart LR
    subgraph GitHub
        Repo["pantana-na/gemini-live-bot (main / prod)"]
    end

    subgraph Google Cloud Platform
        CB[Cloud Build Trigger]
        AR[Artifact Registry: cloudrun-app]
        CR[Cloud Run Service: gemini-live-bot-nonprod]
        LP["Liveness Probe (/healthz)"]
        CL[Cloud Logging: JSON Traces]
        CM[Cloud Monitoring: Latency & Errors]
        VAI[Vertex AI Gemini 3.1 Live API]
    end

    Repo -->|Commit / PR| CB
    CB -->|Build & Tag| AR
    AR -->|Deploy Revision| CR
    CR --> LP
    CR --> CL
    CR --> CM
    CR <-->|BidiStream WebSockets| VAI
```

---

## 4. Architectural Invariants
1. **Zero Unauthenticated Bookings:** `flight_booking_agent` requires a verified customer session before executing final booking.
2. **Deterministic Top 3:** Flight recommendations must return exactly 3 ranked choices when 3 or more flights are available.
3. **Universal Empathy Standard:** `complaint_agent` must acknowledge customer inconvenience in polite Thai before capturing problem taxonomy.
