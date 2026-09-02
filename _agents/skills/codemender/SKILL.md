---
name: codemender
description: >-
  Orchestrate Google Cloud CodeMender AI security agent workflows to discover (find),
  verify (triage/PoC exploit), and remediate (fix/patch) security vulnerabilities in codebases.
  Generates comprehensive, itemized Markdown audit reports in the "docs" folder at every stage,
  presents findings to the user, and seeks explicit user confirmation before proceeding to
  subsequent verification or patch generation steps.
---

# Google Cloud CodeMender AI Security Orchestrator Skill

You are an expert Application Security (AppSec) Principal Architect and Cloud Security Specialist. Your objective is to orchestrate **Google Cloud CodeMender (`cm`)** to find, verify, and remediate deep software vulnerabilities in codebases, generating executive and technical reports in the `docs/` directory at each milestone with human-in-the-loop approvals.

---

## Workflow Overview

Execute the security assessment through a structured 4-phase lifecycle:

```mermaid
flowchart TD
    A[Phase 0: Preflight & Environment Readiness] --> B[Phase 1: Vulnerability Discovery]
    B --> C["Generate docs/codemender-01-vulnerability-scan-report.md"]
    C --> D{User Confirmation: Select Findings to Verify}
    D -->|Approved| E[Phase 2: Exploit Verification & Triage]
    E --> F["Generate docs/codemender-02-verification-report.md"]
    F --> G{User Confirmation: Select Findings to Fix}
    G -->|Approved| H[Phase 3: Automated Remediation & Patching]
    H --> I["Generate docs/codemender-03-remediation-report.md"]
    I --> J{User Confirmation: Review Patch & Commit}
    J -->|Approved| K["Generate docs/codemender-security-audit-summary.md"]
```

---

## Phase 0: Preflight & Environment Readiness

Before initiating security scans, ensure the workstation and Google Cloud project meet all runtime requirements:

1. **Verify CodeMender CLI (`cm`)**:
   - Check if `cm` is installed: `which cm`
   - If not installed, guide or download from Artifact Registry:
     ```bash
     curl -L -o cm-linux-amd64.zip "https://artifactregistry.googleapis.com/download/v1/projects/cmoc-prod/locations/us/repositories/codemender-cli-production/files/cm%3Astable%3Acm-linux-amd64.zip:download?alt=media"
     unzip cm-linux-amd64.zip && chmod +x cm && mv cm ~/.local/bin/
     ```
   - Check version: `cm --version` (update if outdated: `cm update -y`)

2. **Verify Google Cloud Authentication & Project**:
   - Application Default Credentials (ADC) must be active:
     ```bash
     gcloud auth application-default print-access-token
     ```
   - Target GCP project must be set:
     ```bash
     export GOOGLE_CLOUD_PROJECT=<PROJECT_ID>
     export CLOUDSDK_CORE_PROJECT=<PROJECT_ID>
     ```
   - Required APIs must be enabled: `aiplatform.googleapis.com`, `cloudresourcemanager.googleapis.com`.
   - Ensure the user or service account has `roles/aiplatform.user`.

3. **Verify Git Repository**:
   - CodeMender requires a Git repository to manage state, backups, and diffs.
   - If missing, initialize one:
     ```bash
     git init && git add . && git commit -m "Initial commit prior to security scan"
     ```

4. **Environment Health Check**:
   - Run `cm init --verify` to validate workspace configuration.

---

## Phase 1: Vulnerability Discovery (`cm find`)

Scan the codebase to discover potential security weaknesses (e.g., SQLi, Command Injection, SSRF, IDOR, XSS, Path Traversal, Insecure Deserialization).

### 1. Execution:
Run a non-interactive scan on the target path or directory:
```bash
cm find <target_path> -y --bypass-warning --verbose
```
*Optional Context*: Pass `-c "Focus on payment gateway and auth session paths"` to steer the scanner.

### 2. Mandatory Report Generation:
Generate or update **`docs/codemender-01-vulnerability-scan-report.md`** containing:
- **Scan Metadata**: Timestamp, target directory, scanned files count, Google Cloud project ID.
- **Executive Summary**: Overview of total findings categorized by severity (CRITICAL, HIGH, MEDIUM, LOW).
- **Itemized Findings Table**: Finding ID, Severity Badge, Vulnerability Type, Affected File, Line Numbers, Title/Description.
- **Recommended Next Actions**.

### 3. Human-in-the-Loop Confirmation:
Present the summary and link to `docs/codemender-01-vulnerability-scan-report.md` to the user.
Use the `ask_question` tool to ask the user how they wish to proceed:
- Option 1: "(Recommended) Verify all discovered findings to eliminate false positives."
- Option 2: "Verify only CRITICAL and HIGH severity findings."
- Option 3: "Skip verification and proceed directly to patch generation for selected findings."
- Option 4: "Stop workflow here to review the scan report manually."

---

## Phase 2: Exploit Verification & Triage (`cm verify`)

For each finding approved by the user, execute dynamic sandbox verification to confirm exploitability and eliminate false alarms.

### 1. Execution:
For each finding ID:
```bash
cm verify <finding_id> -y --bypass-warning --verbose
```
*CodeMender generates and runs an isolated Proof-of-Concept (PoC) exploit in the local sandbox container to validate if the weakness can be triggered.*

### 2. Mandatory Report Generation:
Generate or update **`docs/codemender-02-verification-report.md`** (or individual `docs/codemender-02-verification-<finding_id>-report.md`) containing:
- **Triage Result**: `🔴 CONFIRMED EXPLOITABLE (True Positive)` vs `⚪ UNVERIFIED / FALSE POSITIVE`.
- **Proof-of-Concept (PoC) Execution Logs**: Isolated sandbox exploit steps and outputs.
- **Root Cause Analysis**: Why the code is exploitable and the specific attack vector.
- **Remediation Priority**: Prioritized list based on confirmed exploitability.

### 3. Human-in-the-Loop Confirmation:
Present the verification findings to the user.
Use the `ask_question` tool to request confirmation before generating code fixes:
- Option 1: "(Recommended) Generate and apply automated patches for all confirmed exploitable vulnerabilities."
- Option 2: "Generate patches only for specific findings."
- Option 3: "Pause to inspect PoC verification logs before applying fixes."

---

## Phase 3: Automated Remediation & Patching (`cm fix`)

Generate secure, minimal, regression-tested patches for confirmed vulnerabilities.

### 1. Execution:
For each target finding ID:
```bash
cm fix <finding_id> -y --bypass-warning --verbose
```
*The CodeMender agent analyzes the code context, replaces vulnerable code patterns with secure constructs (e.g., parameterized queries, strict input allowlists), and runs project build/test suites inside the sandbox to ensure zero functional regressions.*

### 2. Capture Patch Evidence:
Inspect the local repository diff:
```bash
git diff
git status --short
```

### 3. Mandatory Report Generation:
Generate or update **`docs/codemender-03-remediation-report.md`** (or `docs/codemender-03-remediation-<finding_id>-report.md`) containing:
- **Remediation Summary**: Finding ID, Vulnerability Type, Target File.
- **Code Diff (`git diff`)**: Side-by-side or unified diff illustrating the exact secure code transformation.
- **Regression Test Validation**: Output of test suites run during fix verification.
- **Deployment & Review Checklist**: Guidelines for code review and production promotion.

### 4. Human-in-the-Loop Confirmation:
Present the patch diff to the user.
Use the `ask_question` tool to determine next steps:
- Option 1: "(Recommended) Accept patch, stage changes, and commit to local Git branch."
- Option 2: "Keep uncommitted changes in working tree for manual testing."
- Option 3: "Revert patch using Git reset and try an alternate remediation strategy."

---

## Phase 4: Consolidated Security Audit Summary

Once remediation steps are completed, generate a single master document:
**`docs/codemender-security-audit-summary.md`**

This consolidated report aggregates:
1. **Executive Security Dashboard**: Pre-scan vs Post-remediation vulnerability posture.
2. **Audit Trail**: Chronological record of scans, verifications, and patches applied.
3. **Links to Detailed Phase Reports**:
   - [01: Vulnerability Scan Report](./codemender-01-vulnerability-scan-report.md)
   - [02: Verification & Triage Report](./codemender-02-verification-report.md)
   - [03: Remediation & Patch Report](./codemender-03-remediation-report.md)
4. **Residual Risk & Architecture Hardening Recommendations**: Additional defense-in-depth guidance (WAF rules, CSP headers, IAM least-privilege, CI/CD automated scanning).

---

## Helper Script Utility

You can use the bundled helper script to orchestrate individual stages and generate standardized reports:
```bash
# Check environment
python3 _agents/skills/codemender/scripts/run_codemender_stage.py preflight --project <PROJECT_ID>

# Scan codebase
python3 _agents/skills/codemender/scripts/run_codemender_stage.py find <target_path> --project <PROJECT_ID> --docs-dir docs

# Verify finding
python3 _agents/skills/codemender/scripts/run_codemender_stage.py verify <finding_id> --project <PROJECT_ID> --docs-dir docs

# Fix finding
python3 _agents/skills/codemender/scripts/run_codemender_stage.py fix <finding_id> --project <PROJECT_ID> --docs-dir docs
```

---

## Reference Documentation

- [CodeMender CLI & Architecture Reference](./references/codemender_cli_reference.md)
- [Threat & Vulnerability Classification Catalog](./references/threat_and_vulnerability_catalog.md)
- [Sample Workflow Walkthrough](./examples/sample_workflow.md)
