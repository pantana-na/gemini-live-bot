# Project Guidelines & Agent Instructions

## Spec-Driven Development (SDD) & Engineering Mandate

This project strictly follows the **Spec-Driven Development (SDD)** process alongside enterprise DevOps, Security, and Cloud Architecture standards.

### Primary SDD Directives:
1. **Spec First, Code Second:** All development (features, bug fixes, refactoring, API changes) must be preceded by a formal Specification Document in `specs/`.
2. **Brownfield Baseline Requirement:** In brownfield development (such as working on this existing codebase), an accurate **Baseline SDD** reflecting the existing code, architecture, data models, and API contracts must be generated under `specs/baseline/` before making modifications.
3. **Implementation Plan with Step-by-Step Breakdown:** Every spec MUST include a granular, step-by-step Implementation Plan before coding begins.
4. **Mandatory Unit & Property-Based Testing at Every Step:** For *every* step in the implementation plan, developers/agents must implement:
   - **Unit Tests:** Deterministic, example-based tests verifying happy paths, edge cases, and error boundaries.
   - **Property-Based Tests (PBT):** Mathematical/logical invariant tests across generative/fuzzed input spaces (e.g. `fast-check` in TS/JS or `hypothesis` in Python).
5. **Spec Rule Reference:** Read and strictly comply with the rules in `_agents/rules/spec_driven_development.md` and `_agents/rules/devops_security_and_quality_standards.md`.
6. **Living Specs:** When any code or behavior changes, the corresponding SDD in `specs/` must be synchronized in the same change to prevent spec drift.
7. **Living Plan Progress Tracking:** Maintain continuous, up-to-date execution reports, test verification metrics, and milestone statuses under `specs/plan/` whenever development pauses or major phases complete.

---

### Mandatory Engineering, Quality, Security & Cloud Rules:
1. **GitHub Repository Management & Multi-Branch Environment Strategy:** Single repository in GitHub managing Non-Prod (e.g. `main` / `develop`) and Prod (`prod` / `release`) on separate branches. Code promotion to production follows reviewed Pull Requests with passing quality and security gates.
2. **Static Code Quality Analysis:** Perform static code quality analysis to identify bugs, code smells, duplication, and maintainability issues after code commits.
3. **Pre-Build Static Application Security Testing (SAST):** Conduct static application security testing and vulnerability remediation (find, verify, fix) before build and deployment using the **CodeMender skill** (`_agents/skills/codemender/SKILL.md`).
4. **Artifact Analysis & Dependency Scanning:** Use Google Cloud Artifact Analysis (if applicable) to analyze open-source libraries and third-party dependencies for vulnerability and license compliance risks.
5. **Cloud Build & Artifact Registry:** Use Google Cloud Build to build the solution and store container images in Google Cloud Artifact Registry, mapping triggers and image tags to the target environment (`nonprod` vs `prod`).
6. **Cloud Run Observability & Liveness Probe:** Configure Cloud Run Liveness Probe, Cloud Monitoring, and Cloud Logging for the application.
7. **Post-Deployment Integration Testing:** Run integration tests after deployment against the live deployed service.
8. **Centralized Multi-Environment Parameter Management (Unified Single File):** All configurable parameters for **both Non-Prod and Prod environments** must be maintained in the **same unified `.env` file** (documented in `.env.example`), structured into shared core variables and distinct environment-specific blocks (`NONPROD_*` and `PROD_*`).
9. **Terraform & Google Cloud Infrastructure Manager:** Deployment must be managed by Terraform using Google Cloud Infrastructure Manager with isolated deployment instances per environment (e.g., `phenol-container-nonprod` vs `phenol-container-prod`).
10. **IAM Domain Restricted Sharing & Authentication Recommendations:** Organization policy strictly prohibits `allUsers` and non-domain members in IAM policies. Agents must proactively recommend compliant authentication and ingress options: **Identity-Aware Proxy (IAP)** for production external apps, **App-level Google OAuth 2.0** for internal apps requiring user identity, or **Direct Unauthenticated Ingress (`invoker-iam-disabled: 'true'`)** for friction-free public/internal tools.

---

## Project Structure Overview

- `specs/`: Single source of truth for Spec-Driven Development (SDD) specifications, baseline docs, feature designs, and progress tracking.
  - `specs/baseline/`: Current as-is specifications reverse-engineered from existing code.
  - `specs/features/`: Proposed feature specifications with step-by-step plans & test matrices.
  - `specs/plan/`: Implementation progress reports, milestone execution tracking, and verification metrics.
  - `specs/templates/`: Reusable SDD templates.
- `docs/`: Generated documentation and reports from skills (e.g., CodeMender security audit reports, GCP cost estimates, and interactive architecture diagrams/assets).
- `src/`: Frontend React + Vite + TypeScript + Tailwind CSS application.
- `server/`: Backend Node.js + Express / FastAPI proxy integrating with the Gemini API.
- `terraform/`: Declarative Infrastructure as Code for Cloud Run, Artifact Registry, IAM, and observability managed via Infrastructure Manager.
- `_agents/rules/`: Agent behavioral rules, SDD standards, and DevOps/Security governance.
