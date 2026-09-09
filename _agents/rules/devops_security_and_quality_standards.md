# Rule: DevOps, Quality, Security & Cloud Architecture Standards

## Core Mandate
In addition to Spec-Driven Development (SDD), all software engineering, repository management, CI/CD pipeline automation, and cloud deployments must strictly adhere to the following 10 fundamental rules:

---

## Rule 1: Repository Management & Multi-Branch Environment Strategy
1. **Mandatory Single SCM Repository:** All source code, specifications, tests, configuration templates, and pipeline definitions must be version-controlled in a single **GitHub** repository.
2. **Branch-Based Multi-Environment Separation:**
   - The application manages **Non-Production (Non-Prod / Dev)** and **Production (Prod)** environments within the same repository using dedicated Git branches:
     - **Non-Prod Branch (`main` / `develop`):** Houses active development, feature integration, and continuous deployment to the Non-Prod environment.
     - **Prod Branch (`prod` / `release`):** Dedicated to stable, customer-facing production releases. Code is promoted to `prod` strictly via reviewed Pull Requests from the Non-Prod branch.
   - Commits must follow conventional commit standards with clear, descriptive scopes.
3. **Environment Promotion & Quality Gate:** No code may be merged to the `prod` branch without passing static code quality analysis, SAST, unit & property tests, and non-prod post-deployment verification.
4. **No Unversioned Artifacts:** No deployment or release shall occur from uncommitted or untracked local changes.

---

## Rule 2: Post-Commit Static Code Quality Analysis
1. **Automated Quality Inspection:** Automated static code quality analysis must run automatically on commits and pull requests.
2. **Detection Scope:**
   - Identification of bugs, logic flaws, and dead code.
   - Code smells, complexity thresholds, and maintainability issues.
   - Code duplication and styling conformance.
   - TypeScript / JavaScript type checking and strict linting.
3. **Quality Gate:** Code that fails static analysis quality gates or introduces critical code smells must be remediated prior to merge.

---

## Rule 3: Pre-Build & Pre-Deploy SAST (Static Application Security Testing via CodeMender)
1. **Mandatory SAST & Vulnerability Lifecycle:** Static Application Security Testing and vulnerability remediation must be executed prior to build and deployment using the **CodeMender skill** (`_agents/skills/codemender/SKILL.md`).
2. **Tooling & CodeMender (`cm` CLI) Workflow:**
   - **Discovery (`cm find`):** Scan source files and configs for software weaknesses (`cm find <target_path> -y --bypass-warning`), generating `docs/codemender-01-vulnerability-scan-report.md`.
   - **Verification & Triage (`cm verify`):** Synthesize and run isolated PoC exploits in local sandboxes to eliminate false positives (`cm verify <finding_id> -y --bypass-warning`), generating `docs/codemender-02-verification-report.md`.
   - **Automated Remediation (`cm fix`):** Refactor vulnerable code constructs and validate regression test suites (`cm fix <finding_id> -y --bypass-warning`), generating `docs/codemender-03-remediation-report.md`.
3. **Zero High/Critical Vulnerabilities:** Builds and deployments must fail if unaddressed High or Critical security vulnerabilities are detected in application code. Master security summary reports must be published to `docs/codemender-security-audit-summary.md`.

---

## Rule 4: Artifact Analysis & Open-Source Dependency Security
1. **Automated Vulnerability & License Compliance:** Use **Google Cloud Artifact Analysis** (Container Analysis) to scan all container images stored in Artifact Registry.
2. **Dependency Risk Management:**
   - Automatically analyze open-source packages (npm packages, Python libraries, OS base packages) for known CVEs (Common Vulnerabilities and Exposures).
   - Verify license compliance across all third-party dependencies to eliminate restrictive or incompatible licenses.
3. **Continuous Monitoring:** Container images in Artifact Registry must be continuously scanned for newly published vulnerabilities.

---

## Rule 5: Multi-Environment Agent CLI Pipeline Automation & Vertex AI Agent Engine Deployment
1. **Deployment Mandate via Agent CLI:**
   - All AI agent deployments targeting cloud environments must be executed using the unified **Google Agents CLI** (`agents-cli deploy --deployment-target agent_runtime` or `adk deploy agent_engine`), deploying natively onto **Vertex AI Agent Engine** (the Gemini Enterprise Agent Platform runtime, `projects/{project}/locations/{region}/reasoningEngines/{id}`).
   - Custom, unmanaged container orchestration is replaced by the managed Agent Engine runtime, providing native session state, multimodal live streaming, and secure tool execution.
2. **Manifest-Driven Deployment Configuration:**
   - Deployment parameters, agent source directory (`app`), target region, session backend, and CI/CD runner are declaratively configured in `agents-cli-manifest.yaml` (with `.agent_engine_config.json`).
3. **Multi-Environment Branch Strategy:**
   - Commits to the **Non-Prod branch** trigger automated Cloud Build pipelines deploying the agent runtime targeting the **Non-Prod Agent Engine instance** (`gemini-live-bot-nonprod`).
   - Pull requests to the **Prod branch** promote validated agent configurations to the **Production Agent Engine instance** (`gemini-live-bot-prod`).
4. **Isolated & Reproducible Packaging:**
   - Agent dependencies, environment specifications, and secrets from Google Secret Manager (`--secrets=GEMINI_API_KEY=gemini-api-key:latest`) are staged and deployed securely via Agents CLI without local environment leakage.

---

## Rule 6: Vertex AI Agent Engine Observability, Telemetry & Cloud Trace
1. **Native OpenTelemetry & Cloud Trace Integration:**
   - Agent deployments to Vertex AI Agent Engine must enable Cloud Trace and GenAI span telemetry (`GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true`, `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true`).
   - All user conversation turns, multi-agent lateral transfers, tool calls, and LLM completions must be automatically captured in Google Cloud Trace and Cloud Logging.
2. **Health & Lifecycle Probes:**
   - Agent runtime operational state must be verified via the Vertex AI Agent Engine API (`api_resource.state == ACTIVE`), validating reasoning engine instance readiness and multimodal socket availability.
3. **Cloud Monitoring:**
   - Configure Cloud Monitoring dashboards and alert policies for Agent Engine inference latencies (p95/p99), quota utilization, tool execution error rates, and connection lifecycles.

---

## Rule 7: Post-Deployment Verification & Smoke Testing via Agent CLI
1. **Automated Post-Deploy Verification:** Immediately after deploying an Agent Engine revision via `agents-cli deploy`, automated smoke tests must run against the deployed Vertex AI Agent Engine resource (`agents-cli deploy --status` and live agent test inference).
2. **Verification Scope:**
   - Agent instance operational status verification (`api_resource.state == ACTIVE`).
   - Core multi-agent turn execution (greeting, authentication, tool invocation).
   - Live session connectivity and error-free response streaming.
3. **Automated Rollback on Failure:** If post-deployment smoke tests fail, deployment notifications must alert the team, and previous stable revision pointers restored.

---

## Rule 8: Centralized Multi-Environment `.env` Parameter Management (Unified Single File)
1. **Zero Hardcoding:** No configurable parameters may be hardcoded in application source code, Dockerfiles, or client-side scripts.
2. **Unified Multi-Environment Configuration File:**
   - Parameters for **both Non-Prod and Prod environments** must be maintained in the **same unified `.env` file** (with a documented template in `.env.example`).
   - The `.env` file structure organizes variables into:
     - **Shared / Core Section:** Base settings common to all environments (e.g., `GCP_PROJECT`, `GCP_REGION`, `GENAI_LOCATION`, `DEFAULT_MODEL`, `AGENT_DEPLOYMENT_TARGET`, `GITHUB_REPO`).
     - **Non-Prod Configuration Block (`NONPROD_*`):** Non-prod specific values (e.g., `NONPROD_ENVIRONMENT_NAME=development`, `NONPROD_AGENT_ENGINE_ID`, `NONPROD_SERVICE_NAME`, `NONPROD_MIN_INSTANCES=0`, `NONPROD_MAX_INSTANCES=5`, service accounts).
     - **Prod Configuration Block (`PROD_*`):** Prod specific values (e.g., `PROD_ENVIRONMENT_NAME=production`, `PROD_AGENT_ENGINE_ID`, `PROD_SERVICE_NAME`, `PROD_MIN_INSTANCES=1`, `PROD_MAX_INSTANCES=10`, service accounts).
   - CI/CD pipelines, build scripts, and local runners resolve the appropriate configuration block dynamically based on the active Git branch or target environment selection.
3. **Secret Isolation:**
   - Sensitive credentials (e.g., API keys, service account keys) must NEVER be committed to GitHub.
   - Local development uses `.env` (ignored by `.gitignore`).
   - Cloud environments supply configuration via Cloud Build substitutions, Agent Engine deployment parameters, or Google Cloud Secret Manager.

---

## Rule 9: Multi-Environment IaC & Deployment via Terraform & Google Cloud Infrastructure Manager
1. **Infrastructure as Code (IaC):**
   - Cloud infrastructure resources (Vertex AI PSC Network Attachments, IAM roles, service accounts, Secret Manager secrets) are declaratively codified in **Terraform** (`terraform/` directory), parameterized to support multiple environment deployments from a single codebase.
2. **Independent Infrastructure Manager Deployments:**
   - Non-Prod and Prod environments are provisioned as independent **Google Cloud Infrastructure Manager** deployments (e.g., `gemini-live-bot-infra-nonprod` vs `gemini-live-bot-infra-prod`), ensuring complete isolation of Terraform state, service lifecycle, and scaling profiles.
3. **Reproducible & Tracked Deployments:**
   - Infrastructure Manager deployment revisions must be tied to specific Git commits/SHAs, branch names, and Cloud Build runs.
   - Drift detection and automated rollbacks must be supported through Infrastructure Manager deployment manifests.

---

## Rule 10: IAM Domain Restricted Sharing & Authentication Architecture Standards
1. **Organization Policy Constraint (Domain Restricted Sharing):**
   - The GCP organization enforces `constraints/iam.allowedPolicyMemberDomains`, which strictly forbids adding `allUsers`, `allAuthenticatedUsers`, or identities outside the permitted customer domains to IAM policies.
   - Agents and developers **MUST NEVER** attempt to write `allUsers` or `allAuthenticatedUsers` to Terraform `google_cloud_run_v2_service_iam_member` resources or GCP IAM policy bindings.
2. **Mandatory Authentication & Ingress Recommendations:**
   When designing, configuring, or reviewing authentication and ingress for applications, the agent must recommend the appropriate compliant architectural pattern:
   - **Pattern 1: Identity-Aware Proxy (IAP) (Recommended for Production-Grade Enterprise External Apps):**
     - Deploy Cloud Run behind an External HTTPS Application Load Balancer with Serverless Network Endpoint Group (Serverless NEG).
     - Restrict Cloud Run ingress to `INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER`.
     - Enforce Google OAuth 2.0 and central IAM / Google Workspace group authorization at the IAP gateway edge. Zero `allUsers` IAM binding required.
   - **Pattern 2: App-Level Google OAuth 2.0 (Recommended for Internal Apps / PoCs requiring Google User Context):**
     - Deploy Cloud Run with direct ingress and annotation `run.googleapis.com/invoker-iam-disabled = "true"` (empty IAM policy, zero Org Policy violations).
     - Embed Google Identity Services (Sign in with Google) / OAuth 2.0 Client ID in the web frontend, and verify user ID tokens inside the backend application code.
   - **Pattern 3: Direct Unauthenticated Ingress (Recommended for Public / Friction-Free Internal Web Tools):**
     - Deploy Cloud Run frontend service with `annotations = { "run.googleapis.com/invoker-iam-disabled" = "true" }` and `ingress = "INGRESS_TRAFFIC_ALL"`.
     - Zero IAM policy member bindings on the public frontend service (100% Org Policy compliant).
     - Backend API services remain strictly private (`roles/run.invoker` granted exclusively to the frontend Service Account).
