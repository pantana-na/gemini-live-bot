# Specification: [SPEC-YYYYMMDD-TITLE]

## 1. Problem Statement & Objectives
- **Context & Motivation:** Describe the background, current pain points, and business/technical driver.
- **Goals:** Measurable, concrete outcomes expected from this implementation.
- **Non-Goals:** Explicitly out-of-scope items to prevent scope creep.

---

## 2. System Architecture & Component Interaction
- **Component Breakdown:** Identify affected services, UI modules, backend handlers, databases, and pipelines.
- **Sequence / Flow Diagram:**
  ```mermaid
  sequenceDiagram
      actor User
      participant Frontend as Web Client (React)
      participant Gateway as API / Proxy (Cloud Run)
      participant Service as Backend Service
      participant Model as Vertex AI (Gemini 3.7 Flash)
      participant DB as Database (Cloud SQL)

      User->>Frontend: Trigger action
      Frontend->>Gateway: REST API Request
      Gateway->>Service: Authenticated dispatch
      Service->>Model: Invoke GenAI reasoning
      Model-->>Service: Structured JSON response
      Service->>DB: Persist state
      Service-->>Frontend: Response payload
  ```

---

## 3. Data Models & Type Contracts
Single source of truth schemas (TypeScript types, Pydantic models, SQL DDL):

```typescript
export interface ExampleDataModel {
  id: string;
  name: string;
  createdAt: string;
  updatedAt: string;
}
```

---

## 4. API Contracts & External Integrations
- **Endpoint:** `POST /api/v1/example`
- **Headers:** `Authorization: Bearer <token>`, `Content-Type: application/json`
- **Request Payload:**
  ```json
  {
    "name": "example_name"
  }
  ```
- **Response Payload (200 OK):**
  ```json
  {
    "id": "item-123",
    "status": "SUCCESS"
  }
  ```
- **Error Responses:** 400 Bad Request, 401 Unauthorized, 403 Forbidden, 500 Internal Error.

---

## 5. UI/UX & Behavioral Specifications
- **State Machine / User Journey:** States (Idle, Loading, Success, Error).
- **Edge Cases & Failure Modes:** Offline mode, retry backoff, validation error rendering.

---

## 6. DevOps, Security & Cloud Governance Checklist
Ensure alignment with the 10 fundamental engineering standards:

| Rule | Area | Requirement / Architecture Specification |
| :--- | :--- | :--- |
| **Rule 1** | **SCM & Multi-Branch** | Single GitHub repository; Non-Prod (`main`/`develop`) vs Prod (`prod`/`release`). |
| **Rule 2** | **Code Quality** | Automated static analysis, TypeScript strict type-checking, zero critical code smells. |
| **Rule 3** | **SAST & CodeMender** | Pre-build vulnerability scan, triage, and patching via CodeMender (`cm find`, `cm verify`, `cm fix`). Reports in `docs/`. |
| **Rule 4** | **Artifact Analysis** | Automated Container Analysis CVE scanning and license compliance for dependencies. |
| **Rule 5** | **Cloud Build** | Automated multi-environment builds in Google Cloud Build; container tags: `${_ENVIRONMENT}-${SHORT_SHA}`. |
| **Rule 6** | **Cloud Run Observability**| Liveness Probe configured at `/healthz`; structured JSON logs to Cloud Logging; latency alerts. |
| **Rule 7** | **Post-Deploy Smoke Test** | Automated integration/smoke test against live Cloud Run URL; auto-rollback on failure. |
| **Rule 8** | **Unified `.env` Management**| Single unified `.env` file with base shared variables, `NONPROD_*` block, and `PROD_*` block. Zero hardcoding. |
| **Rule 9** | **Terraform & Infra Manager** | Declarative IaC under `terraform/`; isolated Infrastructure Manager deployments (`phenol-container-nonprod` vs `phenol-container-prod`). |
| **Rule 10**| **IAM & Ingress** | Zero `allUsers` bindings; Pattern 3 (invoker-iam-disabled: true) / Pattern 1 (IAP) / Pattern 2 (App-level OAuth 2.0). |

---

## 7. Step-by-Step Implementation Plan & Test Design

> [!IMPORTANT]
> Every step MUST define both deterministic Unit Tests and generative Property-Based Tests (PBT) before writing production code.

### Step 1: Core Data Models, Type Contracts & Validation Schemas
- **Implementation:** Codify foundational domain models, schema validators, and data contracts.
- **Unit Tests:** Deterministic boundary tests verifying parsing of valid payloads and rejection of malformed or missing fields.
- **Property-Based Tests (PBT):** Invariant testing with `fast-check` (TS) or `hypothesis` (Python) verifying serialization round-tripping and schema validity across generated permutations.
- **Completion Criteria:** All data models exported with 100% unit and property test pass rate.

### Step 2: Backend Business Logic, API Endpoints & Health Check
- **Implementation:** Implement API route handlers, service controllers, Gemini 3.7 Flash invocations, and `/healthz` liveness probe endpoint (Rule 6).
- **Unit Tests:** Mock Vertex AI and database calls, test standard request flows, error status codes (4xx/5xx), and `/healthz` probe response.
- **Property-Based Tests (PBT):** Universal invariants (e.g. rate limiters monotonically increment, error handlers never leak unhandled stack traces).
- **Completion Criteria:** Endpoints and health probes verified with tests passing.

### Step 3: Frontend User Interface, State Machines & Forms
- **Implementation:** Implement UI components, forms, client state transitions, loading indicators, and error banners.
- **Unit Tests:** Component rendering, form input validations, accessibility checks, and API error state rendering.
- **Property-Based Tests (PBT):** UI state reducer transition invariants (valid state transitions hold across random action sequences).
- **Completion Criteria:** Frontend components interactive, responsive, and covered by tests.

### Step 4: Security Gates, SAST Scanning & Code Quality
- **Implementation:** Execute static code quality analysis (Rule 2) and CodeMender security workflow (`cm find`, `cm verify`, `cm fix`) (Rule 3).
- **Unit Tests:** Regression tests for remediated vulnerability patches.
- **Property-Based Tests (PBT):** Input sanitizer invariants (e.g. SQL/command injection payloads are safely sanitized/parameterized across arbitrary fuzzed inputs).
- **Completion Criteria:** Zero High/Critical security vulnerabilities; audit reports generated in `docs/codemender-*.md`.

### Step 5: Multi-Environment IaC, Cloud Build CI/CD & Deployment Verification
- **Implementation:** Parameterize Terraform configs (`terraform/`) for Infrastructure Manager (Rule 9), configure Cloud Build triggers (`cloudbuild.yaml`) (Rule 5), and populate unified environment parameters (Rule 8).
- **Unit Tests:** Terraform plan validation, linting (`tflint`), and post-deployment smoke test scripts (`GET /healthz`, API ping) (Rule 7).
- **Property-Based Tests (PBT):** Configuration parser invariants (dynamic environment variable resolver produces correct mappings for both Non-Prod and Prod blocks).
- **Completion Criteria:** Successful deployment to Non-Prod Cloud Run; post-deployment smoke tests passing.

---

## 8. Plan Progress Tracking & Living Spec Synchronization
- **Progress Report:** Update execution metrics, test pass rates, and milestone statuses in `specs/plan/PROGRESS_REPORT_<DATE>.md`.
- **Living Spec Sync:** Update this specification document if any API contracts, data models, or behavioral logic changed during implementation.
