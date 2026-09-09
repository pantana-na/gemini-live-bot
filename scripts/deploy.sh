#!/usr/bin/env bash
# ==============================================================================
# Vertex AI Agent Engine Deployment Script for Gemini Live Bot
# Conforms to Rules 5, 6, 7 & 8 in GEMINI.md & devops_security_and_quality_standards.md
# Extracts deployment configuration dynamically from the unified .env file.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${PROJECT_ROOT}/.env"

# Color formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

print_usage() {
    echo -e "${BOLD}Usage:${NC}"
    echo -e "  ./scripts/deploy.sh [ENVIRONMENT] [TARGET] [OPTIONS]"
    echo
    echo -e "${BOLD}Environments:${NC}"
    echo -e "  nonprod    Deploy to Non-Production (default)"
    echo -e "  prod       Deploy to Production"
    echo
    echo -e "${BOLD}Targets:${NC}"
    echo -e "  web        Deploy ADK Web UI Companion to Google Cloud Run (Browser Access)"
    echo -e "  agent      Deploy Multi-Agent Reasoning Engine to Vertex AI Agent Engine (default)"
    echo -e "  all        Deploy both Vertex AI Agent Engine and Cloud Run Web UI"
    echo
    echo -e "${BOLD}Options:${NC}"
    echo -e "  --dry-run, -n     Preview deployment configuration without deploying"
    echo -e "  --status          Check status of the deployed Agent Engine service"
    echo -e "  --help, -h        Show this help message"
    echo
    echo -e "${BOLD}Examples:${NC}"
    echo -e "  ./scripts/deploy.sh nonprod web          # Deploy Cloud Run Web UI for browser test"
    echo -e "  ./scripts/deploy.sh nonprod agent        # Deploy Vertex AI Agent Engine"
    echo -e "  ./scripts/deploy.sh nonprod all          # Deploy both Agent Engine & Web UI"
    echo -e "  ./scripts/deploy.sh prod web --dry-run   # Preview Prod Web UI deployment"
    echo -e "  ./scripts/deploy.sh --status             # Check Agent Engine status"
}

# Ensure .env exists
if [[ ! -f "${ENV_FILE}" ]]; then
    echo -e "${RED}Error: Configuration file '${ENV_FILE}' not found.${NC}"
    echo -e "${YELLOW}Please create one by copying .env.example:${NC}"
    echo "  cp .env.example .env"
    exit 1
fi

# Load variables from .env file safely
load_env_var() {
    local var_name="$1"
    local default_val="${2:-}"
    # Extract variable value, removing surrounding quotes and inline comments
    local val
    val=$(grep -E "^${var_name}=" "${ENV_FILE}" 2>/dev/null | tail -n 1 | cut -d '=' -f 2- | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e 's/^"\(.*\)"$/\1/' -e "s/^'\(.*\)'$/\1/" -e 's/[[:space:]]*#.*$//')
    if [[ -n "${val}" ]]; then
        echo "${val}"
    else
        echo "${default_val}"
    fi
}

# Parse command-line arguments
TARGET_ENV="nonprod"
DEPLOY_COMPONENT="agent" # "agent", "web", or "all"
DRY_RUN=false
CHECK_STATUS=false

for arg in "$@"; do
    case "${arg}" in
        nonprod|dev|development)
            TARGET_ENV="nonprod"
            ;;
        prod|production)
            TARGET_ENV="prod"
            ;;
        agent|engine|backend)
            DEPLOY_COMPONENT="agent"
            ;;
        web|frontend|ui)
            DEPLOY_COMPONENT="web"
            ;;
        all)
            DEPLOY_COMPONENT="all"
            ;;
        --dry-run|-n)
            DRY_RUN=true
            ;;
        --status)
            CHECK_STATUS=true
            ;;
        --help|-h)
            print_usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown argument: ${arg}${NC}"
            print_usage
            exit 1
            ;;
    esac
done

# Resolve CLI executable: check agents-cli in PATH, uv, or venv
CLI_CMD="agents-cli"
if ! command -v "${CLI_CMD}" &>/dev/null; then
    if [[ -x "${HOME}/.local/bin/agents-cli" ]]; then
        CLI_CMD="${HOME}/.local/bin/agents-cli"
    elif [[ -x "${PROJECT_ROOT}/.venv/bin/agents-cli" ]]; then
        CLI_CMD="${PROJECT_ROOT}/.venv/bin/agents-cli"
    else
        CLI_CMD="agents-cli"
    fi
fi

# If checking status only
if [[ "${CHECK_STATUS}" == true ]]; then
    echo -e "${CYAN}Checking deployment status via ${CLI_CMD}...${NC}"
    cd "${PROJECT_ROOT}"
    "${CLI_CMD}" deploy --status
    exit $?
fi

# ------------------------------------------------------------------------------
# Extract Parameters from .env
# ------------------------------------------------------------------------------
GCP_PROJECT=$(load_env_var "GCP_PROJECT" "$(load_env_var "GOOGLE_CLOUD_PROJECT")")
GCP_REGION=$(load_env_var "GCP_REGION" "$(load_env_var "GOOGLE_CLOUD_LOCATION" "asia-southeast1")")
DEPLOYMENT_TARGET=$(load_env_var "AGENT_DEPLOYMENT_TARGET" "agent_runtime")
LIVE_MODEL=$(load_env_var "LIVE_API_MODEL" "gemini-3.1-flash-live-preview")
USE_VERTEXAI=$(load_env_var "GOOGLE_GENAI_USE_VERTEXAI" "TRUE")
SECRET_NAME=$(load_env_var "GEMINI_SECRET_NAME" "gemini-api-key:latest")

if [[ -z "${GCP_PROJECT}" ]]; then
    echo -e "${RED}Error: GCP_PROJECT is not set in .env.${NC}"
    exit 1
fi

if [[ "${TARGET_ENV}" == "prod" ]]; then
    ENV_NAME=$(load_env_var "PROD_ENVIRONMENT_NAME" "production")
    SERVICE_NAME=$(load_env_var "PROD_SERVICE_NAME" "gemini-live-bot-prod")
    CPU=$(load_env_var "PROD_CPU" "1")
    MEMORY=$(load_env_var "PROD_MEMORY" "4Gi")
    MIN_INSTANCES=$(load_env_var "PROD_MIN_INSTANCES" "1")
    MAX_INSTANCES=$(load_env_var "PROD_MAX_INSTANCES" "10")
    CONCURRENCY=$(load_env_var "PROD_CONCURRENCY" "8")
    SERVICE_ACCOUNT=$(load_env_var "PROD_SERVICE_ACCOUNT_NAME" "")
    
    WEB_SERVICE_NAME=$(load_env_var "PROD_WEB_SERVICE_NAME" "gemini-live-bot-web-prod")
    WEB_CPU=$(load_env_var "PROD_WEB_CPU" "1")
    WEB_MEMORY=$(load_env_var "PROD_WEB_MEMORY" "2Gi")
    WEB_MIN_INSTANCES=$(load_env_var "PROD_WEB_MIN_INSTANCES" "1")
    WEB_MAX_INSTANCES=$(load_env_var "PROD_WEB_MAX_INSTANCES" "5")
else
    ENV_NAME=$(load_env_var "NONPROD_ENVIRONMENT_NAME" "development")
    SERVICE_NAME=$(load_env_var "NONPROD_SERVICE_NAME" "gemini-live-bot-nonprod")
    CPU=$(load_env_var "NONPROD_CPU" "1")
    MEMORY=$(load_env_var "NONPROD_MEMORY" "4Gi")
    MIN_INSTANCES=$(load_env_var "NONPROD_MIN_INSTANCES" "0")
    MAX_INSTANCES=$(load_env_var "NONPROD_MAX_INSTANCES" "5")
    CONCURRENCY=$(load_env_var "NONPROD_CONCURRENCY" "8")
    SERVICE_ACCOUNT=$(load_env_var "NONPROD_SERVICE_ACCOUNT_NAME" "")

    WEB_SERVICE_NAME=$(load_env_var "NONPROD_WEB_SERVICE_NAME" "gemini-live-bot-web-nonprod")
    WEB_CPU=$(load_env_var "NONPROD_WEB_CPU" "1")
    WEB_MEMORY=$(load_env_var "NONPROD_WEB_MEMORY" "2Gi")
    WEB_MIN_INSTANCES=$(load_env_var "NONPROD_WEB_MIN_INSTANCES" "0")
    WEB_MAX_INSTANCES=$(load_env_var "NONPROD_WEB_MAX_INSTANCES" "3")
fi

# ==============================================================================
# Deploy Function 1: Vertex AI Agent Engine
# ==============================================================================
deploy_agent_engine() {
    echo -e "${BOLD}${CYAN}============================================================${NC}"
    echo -e "${BOLD}${CYAN}   🚀 Gemini Live Bot: Vertex AI Agent Engine Deployment   ${NC}"
    echo -e "${BOLD}${CYAN}============================================================${NC}"
    echo -e "  ${BOLD}Target Environment:${NC}  ${YELLOW}${TARGET_ENV} (${ENV_NAME})${NC}"
    echo -e "  ${BOLD}GCP Project:${NC}         ${GREEN}${GCP_PROJECT}${NC}"
    echo -e "  ${BOLD}GCP Region:${NC}          ${GREEN}${GCP_REGION}${NC}"
    echo -e "  ${BOLD}Service Name:${NC}        ${GREEN}${SERVICE_NAME}${NC}"
    echo -e "  ${BOLD}Deployment Target:${NC}   ${GREEN}${DEPLOYMENT_TARGET}${NC} (Vertex AI Agent Engine)"
    echo -e "  ${BOLD}Resources:${NC}           CPU: ${CPU}, Memory: ${MEMORY}, Concurrency: ${CONCURRENCY}"
    echo -e "  ${BOLD}Scaling Bounds:${NC}      Min: ${MIN_INSTANCES}, Max: ${MAX_INSTANCES}"
    echo -e "  ${BOLD}Live Model:${NC}          ${LIVE_MODEL}"
    echo -e "  ${BOLD}Vertex AI Mode:${NC}      ${USE_VERTEXAI}"
    if [[ -n "${SERVICE_ACCOUNT}" ]]; then
        echo -e "  ${BOLD}Service Account:${NC}    ${SERVICE_ACCOUNT}"
    fi
    echo -e "${BOLD}${CYAN}============================================================${NC}"
    echo

    DEPLOY_ARGS=(
        deploy
        --deployment-target "${DEPLOYMENT_TARGET}"
        --project "${GCP_PROJECT}"
        --region "${GCP_REGION}"
        --service-name "${SERVICE_NAME}"
        --cpu "${CPU}"
        --memory "${MEMORY}"
        --min-instances "${MIN_INSTANCES}"
        --max-instances "${MAX_INSTANCES}"
        --concurrency "${CONCURRENCY}"
        --secrets "GEMINI_API_KEY=${SECRET_NAME}"
        --update-env-vars "ENVIRONMENT=${TARGET_ENV},LIVE_API_MODEL=${LIVE_MODEL},GOOGLE_GENAI_USE_VERTEXAI=${USE_VERTEXAI},GOOGLE_CLOUD_LOCATION=${GCP_REGION}"
    )

    if [[ -n "${SERVICE_ACCOUNT}" ]]; then
        DEPLOY_ARGS+=(--service-account "${SERVICE_ACCOUNT}")
    fi

    if [[ "${DRY_RUN}" == true ]]; then
        DEPLOY_ARGS+=(--dry-run)
        echo -e "${YELLOW}Running in DRY-RUN mode (no cloud resources modified):${NC}"
    fi

    cd "${PROJECT_ROOT}"
    echo -e "${BLUE}Executing: ${CLI_CMD} ${DEPLOY_ARGS[*]}${NC}"
    echo

    "${CLI_CMD}" "${DEPLOY_ARGS[@]}"

    echo
    if [[ "${DRY_RUN}" == true ]]; then
        echo -e "${GREEN}✅ Agent Engine dry-run completed successfully!${NC}"
    else
        echo -e "${GREEN}✅ Agent Engine deployment completed!${NC}"
    fi
}

# ==============================================================================
# Deploy Function 2: Cloud Run ADK Web UI Companion
# ==============================================================================
deploy_cloud_run_web() {
    echo -e "${BOLD}${CYAN}============================================================${NC}"
    echo -e "${BOLD}${CYAN}   🌐 Gemini Live Bot: Cloud Run ADK Web UI Deployment     ${NC}"
    echo -e "${BOLD}${CYAN}============================================================${NC}"
    echo -e "  ${BOLD}Target Environment:${NC}  ${YELLOW}${TARGET_ENV} (${ENV_NAME})${NC}"
    echo -e "  ${BOLD}GCP Project:${NC}         ${GREEN}${GCP_PROJECT}${NC}"
    echo -e "  ${BOLD}GCP Region:${NC}          ${GREEN}${GCP_REGION}${NC}"
    echo -e "  ${BOLD}Web Service Name:${NC}    ${GREEN}${WEB_SERVICE_NAME}${NC}"
    echo -e "  ${BOLD}Resources:${NC}           CPU: ${WEB_CPU}, Memory: ${WEB_MEMORY}"
    echo -e "  ${BOLD}Scaling Bounds:${NC}      Min: ${WEB_MIN_INSTANCES}, Max: ${WEB_MAX_INSTANCES}"
    echo -e "  ${BOLD}Live Model:${NC}          ${LIVE_MODEL}"
    echo -e "  ${BOLD}Port & Probe:${NC}        Port 8080, Health: /health"
    if [[ -n "${SERVICE_ACCOUNT}" ]]; then
        echo -e "  ${BOLD}Service Account:${NC}    ${SERVICE_ACCOUNT}"
    fi
    echo -e "${BOLD}${CYAN}============================================================${NC}"
    echo

    RUN_ARGS=(
        run deploy "${WEB_SERVICE_NAME}"
        --source "${PROJECT_ROOT}"
        --project "${GCP_PROJECT}"
        --region "${GCP_REGION}"
        --platform managed
        --allow-unauthenticated
        --cpu "${WEB_CPU}"
        --memory "${WEB_MEMORY}"
        --min-instances "${WEB_MIN_INSTANCES}"
        --max-instances "${WEB_MAX_INSTANCES}"
        --port 8080
        --set-secrets "GEMINI_API_KEY=${SECRET_NAME}"
        --set-env-vars "ENVIRONMENT=${TARGET_ENV},LIVE_API_MODEL=${LIVE_MODEL},GOOGLE_GENAI_USE_VERTEXAI=${USE_VERTEXAI},GOOGLE_CLOUD_LOCATION=${GCP_REGION}"
        --set-annotations "run.googleapis.com/invoker-iam-disabled=true"
        --ingress all
        --quiet
    )

    if [[ -n "${SERVICE_ACCOUNT}" ]]; then
        RUN_ARGS+=(--service-account "${SERVICE_ACCOUNT}")
    fi

    if [[ "${DRY_RUN}" == true ]]; then
        echo -e "${YELLOW}Running in DRY-RUN mode (gcloud run deploy command preview):${NC}"
        echo -e "${BLUE}gcloud ${RUN_ARGS[*]}${NC}"
        echo
        echo -e "${GREEN}✅ Cloud Run Web UI dry-run completed!${NC}"
        return 0
    fi

    echo -e "${BLUE}Executing: gcloud ${RUN_ARGS[*]}${NC}"
    echo

    # Extract active ADC token to guarantee non-interactive execution
    local adc_token
    adc_token=$("${PROJECT_ROOT}/.venv/bin/python" -c "
import google.auth, google.auth.transport.requests
creds, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
creds.refresh(google.auth.transport.requests.Request())
print(creds.token)
" 2>/dev/null || true)

    if [[ -n "${adc_token}" ]]; then
        CLOUDSDK_AUTH_ACCESS_TOKEN="${adc_token}" CLOUDSDK_CORE_DISABLE_PROMPTS=1 gcloud "${RUN_ARGS[@]}"
    else
        gcloud "${RUN_ARGS[@]}"
    fi

    # Retrieve and display Service URL
    local web_url
    if [[ -n "${adc_token}" ]]; then
        web_url=$(CLOUDSDK_AUTH_ACCESS_TOKEN="${adc_token}" CLOUDSDK_CORE_DISABLE_PROMPTS=1 gcloud run services describe "${WEB_SERVICE_NAME}" --project "${GCP_PROJECT}" --region "${GCP_REGION}" --format="value(status.url)" 2>/dev/null || true)
    else
        web_url=$(gcloud run services describe "${WEB_SERVICE_NAME}" --project "${GCP_PROJECT}" --region "${GCP_REGION}" --format="value(status.url)" 2>/dev/null || true)
    fi

    echo
    echo -e "${GREEN}✅ Cloud Run Web UI deployed successfully!${NC}"
    if [[ -n "${web_url}" ]]; then
        echo -e "${BOLD}🔗 Access the Web UI in your browser:${NC} ${CYAN}${web_url}${NC}"
        echo -e "${BOLD}📱 Dev-UI Path:${NC} ${CYAN}${web_url}/dev-ui/${NC}"
    fi
}

# ------------------------------------------------------------------------------
# Main Dispatch
# ------------------------------------------------------------------------------
case "${DEPLOY_COMPONENT}" in
    agent)
        deploy_agent_engine
        ;;
    web)
        deploy_cloud_run_web
        ;;
    all)
        deploy_agent_engine
        echo
        deploy_cloud_run_web
        ;;
esac

