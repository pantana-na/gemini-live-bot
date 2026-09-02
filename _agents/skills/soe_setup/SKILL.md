---
name: soe-setup
description: Automates internal Google Cloud developer environment setup for CEs and Solution Architects on Cloudtop. Handles LOAS (gcert), Corp Airlock (uv/PyPI), MCP proxy wiring (Buganizer/Workspace), toolchain installation, and Gemini model preflight probes.
---

<!-- disableFinding(LINE_OVER_80) -->
<!-- disableFinding(WHITESPACE_TRAILING) -->

# SOE Cloudtop Environment Setup & Preflight Skill

You are an expert AI platform engineer configuring a gLinux Cloudtop workstation for a Google Cloud Customer Engineer (CE) or Solution Architect (SOE). Execute the following steps sequentially, explaining your actions clearly, and report progress.

## Step 1: Corporate LOAS & Airlock Setup (uv)
1. **Verify LOAS Certificate:** Run `gcertstatus`. If expired or missing, instruct the user to run `gcert` in their terminal and pause execution until verified.
2. **Configure Python Toolchain with uv (Zero Venv Bloat):**
   * If `uv` is not installed, install it: `curl -LsSf https://astral.sh/uv/install.sh | sh` and source the environment.
   * Run `gpkg setup` to initialize Artifact Registry authentication for corporate devices.
   * Ensure `~/.config/uv/uv.toml` exists and directs all PyPI traffic through Corp Airlock:
     ```bash
     mkdir -p ~/.config/uv
     cat << 'EOF' > ~/.config/uv/uv.toml
     # Prevent disk bloat by cloning/hardlinking cached wheels into venvs
     link-mode = "clone"
     cache-dir = "~/.cache/uv"

     [[index]]
     name = "airlock"
     url = "https://us-python.pkg.dev/artifact-foundry-prod/python-3p-trusted/simple/"
     default = true
     EOF
     ```
3. **Install Core Developer CLIs:** Install `google-adk` (Agent Development Kit) and `google-agents-cli` (Agents CLI) globally via `uv tool`, and configure the `jetski` CLI:
   ```bash
   uv tool install google-adk
   uv tool install google-agents-cli
   if [[ -x "/google/bin/releases/jetski-devs/tools/cli" ]]; then
       /google/bin/releases/jetski-devs/tools/cli install
   else
       curl -fsSL https://jetski.google/cli/install.sh | bash
   fi
   ```

4. **(Optional) Configure Jetski Hub (Web UI):** If you prefer using the browser-based Agent Manager interface instead of the terminal CLI, initialize the Jetski Web daemon on your Cloudtop:
   ```bash
   /google/bin/releases/jetski-devs/tools/cli web install
   ```
   * Open Chrome on your laptop and navigate to **[http://jetski/](http://jetski/)** (or `http://<username>.c.googlers.com:5387/` directly).
   * Enter your Cloudtop hostname (`<username>.c.googlers.com`) when prompted.

## Step 2: MCP Server Proxy Wiring
Configure the user's local MCP client (`~/.gemini/jetski/mcp_config.json`) to include corporate endpoints for Buganizer and Google Workspace using official internal release binaries:
```bash
python3 -c '
import json, os, pathlib
config_path = pathlib.Path.home() / ".gemini/jetski/mcp_config.json"
config_path.parent.mkdir(parents=True, exist_ok=True)
data = json.loads(config_path.read_text()) if config_path.exists() else {"mcpServers": {}}

data["mcpServers"]["buganizer"] = {
    "command": "/google/bin/releases/corp-mcp-proxy/server.par",
    "args": ["--use_loas_transact_dat=True", "--mcp_server=blade:devtools.buganizer.mcpservice-prod"]
}
data["mcpServers"]["workspace"] = {
    "command": "/google/bin/releases/codemind-mcp-servers/workspace_server.par"
}
data["mcpServers"]["duckie"] = {
    "command": "/google/bin/releases/duckie-eng-policy/duckie_server.par"
}
config_path.write_text(json.dumps(data, indent=2))
print("Successfully wired Buganizer, Workspace, & Duckie MCP proxies.")
'
```

### 2.5 Verify MCP Server Proxy Connectivity
After wiring `~/.gemini/jetski/mcp_config.json`, verify that the MCP proxies are responsive by making lightweight, non-destructive read-only test calls using your available MCP tools:
1. **Buganizer MCP:** Verify bug access (e.g., call `get_user_access` or check metadata for bug `1` via Buganizer MCP).
2. **Workspace MCP:** Verify Workspace API connectivity (e.g., query `list_drive_files` with a limit of 1).
3. **Duckie MCP:** Verify policy/eng tool response (e.g., send a test greeting or check tool status via `ask_duckie`).
* For each MCP server that responds cleanly, mark it as **[✔ LIVE & OPERATIONAL]** in your summary banner.
* If any MCP test fails (e.g., due to an expired LOAS ticket), explain: *"The `<ServerName>` MCP proxy connection failed. Ensure your `gcert` LOAS ticket is active."*

## Step 3: gcloud & Argolis Project Wiring
1. **Ensure gcloud CLI is installed:** If `gcloud` is not in PATH, install it:
   ```bash
   if ! command -v gcloud &> /dev/null; then
       curl -fsSL https://sdk.cloud.google.com | bash
       source ~/.bashrc 2>/dev/null || source ~/.zshrc 2>/dev/null || true
   fi
   ```
2. **Resolve GCP Project ID & Location:**
   * Prompt the user for their assigned **Argolis or GCP Project ID** if the environment variable `GOOGLE_CLOUD_PROJECT` is unset, `(unset)`, or points to an internal pool project (`cloudtop-prod-*`).
   * Prompt the user for their preferred **GCP Location** (defaulting to `global` if unspecified).
3. **Set & Export Baseline Environment Variables:**
   Write required baseline environment variables to `.env` and `~/.bashrc` (or `~/.zshrc`):
   ```env
   GOOGLE_CLOUD_PROJECT=<PROJECT_ID>
   GOOGLE_CLOUD_LOCATION=<LOCATION>
   GOOGLE_GENAI_USE_VERTEXAI=TRUE
   ```
   *(Note: Setting `GOOGLE_CLOUD_LOCATION=global` by default prevents region-routing 404 errors during preview model testing in Argolis sandbox tiers).*
4. **Set Active Project & Quota Project in gcloud:**
   ```bash
   gcloud config set project $GOOGLE_CLOUD_PROJECT
   gcloud auth application-default set-quota-project $GOOGLE_CLOUD_PROJECT
   ```
5. **Verify & Ensure Application Default Credentials (ADC) is Active:**
   Test token generation quietly:
   ```bash
   gcloud auth application-default print-access-token >/dev/null 2>&1
   ```
   * If token generation succeeds, confirm ADC is active **[✔ ADC Active]**.
   * If token generation fails, initiate `gcloud auth application-default login` or ask the user to complete login in their browser.
   * *If authentication fails or is blocked by Context Aware Access (CAA/mTLS) restrictions:* Do not loop repeatedly. Explain to the user: *"Your gcloud authentication is restricted by Context Aware Access (mTLS). Please open the Chrome browser **inside your Cloudtop desktop session** so the SecureConnect extension syncs device posture, then run `gcloud auth application-default login`."*

## Step 4: Summary & Handoff to Antigravity (`agy`)
When all checks pass, display a polished markdown summary table confirming active LOAS status, uv/Airlock mirror configuration, active MCP server proxies, active GCP project & location, and verified ADC token:
1. Confirm that their workstation is 100% configured for Google Cloud Elevate and CE agentic curriculum labs.
2. Instruct them to launch the Antigravity CLI (`agy`) or Jetski CLI (`jetski`) for their daily training and lab work:
   ```bash
   agy
   ```
3. Inform them that upon starting `agy`, they will log in once via browser OAuth to begin Module 0-1 of the Elevate curriculum.
