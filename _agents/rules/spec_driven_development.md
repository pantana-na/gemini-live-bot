---
trigger: always_on
description: "Strictly enforce Spec-Driven Development (SDD) with mandatory brownfield baseline, detailed implementation plans, unit + property-based testing at every step, and continuous plan progress tracking in specs/plan/."
---

# Rule: Spec-Driven Development (SDD), Brownfield Protocol & Plan Progress Tracking

## Core Mandate
This project operates strictly under the **Spec-Driven Development (SDD)** process.
**Code is a downstream artifact derived from specification documents.** No feature implementation, architectural change, major refactoring, or API modification may begin without:
1. An approved, up-to-date Specification Document (SDD) stored under `specs/`.
2. A detailed **Implementation Plan** breaking down changes into concrete steps.
3. Dedicated **Unit Tests** and **Property-Based Tests (PBT)** defined for every implementation step.
4. Continuous **Plan Progress Tracking** documented under `specs/plan/`.

---

## 1. Brownfield Development Protocol (Mandatory Baseline First)

When working on an existing (brownfield) codebase or modifying any existing subsystem:

1. **Check for Baseline SDD:**
   - Before writing or modifying any code, verify if a comprehensive Baseline SDD exists in `specs/baseline/` for the targeted component/system.
2. **Reverse-Engineer / Generate Baseline SDD First:**
   - If no Baseline SDD exists (or if it is out-of-date), you **MUST** inspect the existing code, dependencies, data contracts, and APIs to generate a complete Baseline SDD first.
   - The Baseline SDD must accurately document the "as-is" state:
     - Architecture and subsystem boundaries
     - Data models and TypeScript / Python types / schemas
     - API endpoints, payloads, headers, and error behaviors
     - Business logic, algorithms, and domain constraints
     - UI/UX workflows and component hierarchy
     - External service integrations (e.g., Gemini API, Vertex AI, Google Cloud)
     - Core system invariants to be protected by property tests
3. **Establish Baseline Before Delta:**
   - Only after the baseline state is codified into `specs/baseline/` can feature specs or modification plans (`specs/features/`) be drafted against it.

---

## 2. SDD Workflow Lifecycle

Every development task must progress through these sequential phases:

```
[Phase 0: Baseline Discovery (Brownfield only)]
               │
               ▼
[Phase 1: Specification Authoring (SDD)]
               │
               ▼
[Phase 2: Detailed Implementation Plan + Test Strategy]
               │
               ▼
[Phase 3: Review & Alignment]
               │
               ▼
[Phase 4: Step-by-Step Implementation + Unit & Property Tests]
               │
               ▼
[Phase 5: Verification, Living Spec Sync & Plan Progress Tracking]
```

### Phase 0: Baseline Discovery (Brownfield only)
- Inspect existing files, configuration, models, and tests.
- Document current behavior, contracts, and invariants in `specs/baseline/`.

### Phase 1: Specification Authoring
- Create or update the relevant spec under `specs/features/` or `specs/` using `specs/templates/sdd-template.md`.
- Required sections:
  1. Problem Statement & Goals / Non-Goals
  2. System Architecture & Component Interactions
  3. Data Models & Schema Definitions (Single source of truth)
  4. API Contracts & Integrations (Request/Response, status codes, error shapes)
  5. UI/UX & Behavioral Specifications (State machines, edge cases, validation)
  6. Security, Privacy & Non-Functional Requirements

### Phase 2: Detailed Implementation Plan & Test Design
Before writing production code, author a granular **Implementation Plan** in the SDD with:
- **Sequential Step Breakdown:** Clear, manageable steps from foundational models/types to backend APIs, UI components, and integrations.
- **Unit Tests for Every Step:** Specific, deterministic test cases covering expected behavior, edge cases, and error paths.
- **Property-Based Tests (PBT) for Every Step:** Formal mathematical/logical invariants tested across randomized, fuzzed, or generative inputs (e.g. with `fast-check` in TS/JS or `hypothesis` in Python).
- **Completion Criteria:** Definition of Done for each individual step.

### Phase 3: Review & Alignment
- Review the proposed specification, step-by-step implementation plan, and test designs with the user/stakeholders.
- Resolve ambiguities, edge cases, and design trade-offs *in the document* before writing code.

### Phase 4: Step-by-Step Implementation
- Execute the implementation plan step-by-step.
- For each step:
  1. Implement the step code and its required types/contracts.
  2. Implement the accompanying Unit Tests.
  3. Implement the accompanying Property-Based Tests.
  4. Run and verify that all tests pass before proceeding to the next step.

### Phase 5: Verification, Living Spec Sync & Plan Progress Tracking
- Run the complete test suite (all unit tests, property tests, and evaluation benchmarks).
- Verify against every Acceptance Criterion in the SDD.
- Synchronize any spec modifications to prevent spec drift.
- **Update Plan Progress:** Author or update the execution progress report in `specs/plan/` documenting completed milestones, test metrics, and next steps.

---

## 3. Plan Progress Tracking Protocol (`specs/plan/`)

All execution progress must be continuously recorded in the `specs/plan/` directory:

1. **Progress Report Requirements:**
   - **Specification Linkage:** State the associated SDD document ID (e.g., `SPEC-20260824-MULTI-AGENT-CLOUD-ARCHITECTURE.md`).
   - **Step-by-Step Progress Matrix:** Detailed table tracking completed vs pending steps, implemented files, and test suites.
   - **Quality & Test Metrics:** Up-to-date summary of test pass rates (Unit, PBT, Golden Benchmarks), execution latency, and invariant verification.
   - **Delivered Capabilities:** Non-obvious architectural decisions, model integrations, security guardrails, and UI enhancements.
   - **Roadmap & Next Actions:** Concrete, actionable next steps when resuming development.
2. **Milestone & Pause Synchronization:**
   - Whenever development is paused, handed off, or a major phase completes, the agent **MUST** update `specs/plan/` and synchronize `specs/README.md` before concluding the session.

---

## 4. Mandatory Testing Standards for Every Step

For **every step** in the implementation plan:

### 4.1 Unit Testing Requirements
- **Deterministic Examples:** Test concrete inputs and verified expected outputs.
- **Boundary & Edge Conditions:** Empty sets, max limits, malformed payloads, network timeout errors.
- **Mocking & Isolation:** Isolate external services to ensure fast, reliable test execution.

### 4.2 Property-Based Testing (PBT) Requirements
- **Universal Invariants:** Formulate properties that must hold true for *all* valid inputs (e.g., "Severity ordering is monotonic", "Blocked injections never invoke database tools", "Clarification depth is strictly bounded at <= 3").
- **Generative Arbitraries:** Use generators (`st.text()`, `st.integers()`, `st.sampled_from()`) to produce hundreds of permutations.
- **Shrinking & Counterexamples:** Ensure failing properties produce minimal failing examples to quickly diagnose edge bugs.
- **Idempotence & Round-tripping:** Test serialization/deserialization, normalizer idempotence.

---

## 5. Directory Structure & Document Organization

This project maintains a strict separation between **Spec-Driven Development artifacts (`specs/`)** and **Skill-Generated documentation & operational reports (`docs/`)**:

### 5.1 SDD Specifications (`specs/`)
All formal specifications, baseline models, feature designs, and implementation progress tracking must reside in the `specs/` directory:

```
specs/
├── README.md                      # Index of all specifications and progress reports
├── templates/
│   └── sdd-template.md            # Standardized template with Implementation Plan & Testing sections
├── baseline/                      # Baseline SDDs for existing/brownfield code
│   └── system-overview.md         # Full system architecture, stack & invariants
├── features/                      # Feature specifications and enhancement proposals
│   └── <feature-id>-<title>.md
└── plan/                          # Living implementation progress reports and milestone tracking
    └── PROGRESS_REPORT_<DATE>.md
```

### 5.2 Skill-Generated Documentation & Reports (`docs/`)
All operational reports, security assessment logs, cloud cost models, and standalone visual assets produced by agent skills must reside in the `docs/` directory:
- Architecture Diagrams & HTML: `docs/*-architecture.md`, `docs/*-architecture.html`
- CodeMender Security Reports: `docs/codemender-*.md`
- GCP Cost Estimations: `docs/gcp_cost_estimate_*.md`

---

## 6. Hard Enforcement Rules

1. **No Code Without Spec & Plan:** Reject or pause direct coding requests until the SDD, detailed implementation plan, and test designs are established.
2. **Unit & Property Tests Required at Every Step:** Code without corresponding unit tests and property-based tests is strictly prohibited.
3. **Strict Schema Fidelity:** API responses, frontend types, and backend validation schemas must be exact matches to the SDD contracts.
4. **Zero Spec Drift:** If code changes behavior, the SDD must be updated in the same commit/change.
5. **Living Plan Progress Tracking:** Never pause development or complete a milestone without recording full progress, test metrics, and next steps in `specs/plan/`.
