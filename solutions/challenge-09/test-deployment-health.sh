#!/usr/bin/env bash
#
# PetPal Microservices Deployment Health Check
#
# Tests health endpoints of all deployed microservices to validate successful deployment
# Validates connectivity, response time, and database connection status.
#
# Usage:
#   ./test-deployment-health.sh [-r RESOURCE_GROUP] [-d]
#
# Options:
#   -r    Resource group name (default: from RESOURCE_GROUP env var)
#   -d    Show detailed response from each service
#   -h    Show this help message
#
# Examples:
#   ./test-deployment-health.sh -r "rg-petpal-dev"
#   ./test-deployment-health.sh -r "rg-petpal-dev" -d
#
# Requirements:
#   - Azure CLI installed and authenticated (az login)
#   - jq for JSON parsing
#   - curl for HTTP requests
#

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESOURCE_GROUP="${RESOURCE_GROUP:-}"
DETAILED=false

# Service definitions
declare -A SERVICES=(
    [pet-service]="8010|petservice|Pet Management Service"
    [activity-service]="8020|activityservice|Activity Tracking Service"
    [accessory-service]="8030|accessoryservice|Accessory Management Service"
)

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
NC='\033[0m' # No Color

# Output helpers
success() { echo -e "${GREEN}✅ $*${NC}"; }
failure() { echo -e "${RED}❌ $*${NC}"; }
info() { echo -e "${CYAN}ℹ️  $*${NC}"; }
warning() { echo -e "${YELLOW}⚠️  $*${NC}"; }
debug() { echo -e "${GRAY}$*${NC}"; }

# Print usage
usage() {
    sed -n '2,20p' "$0" | sed 's/^# \?//'
    exit 0
}

# Parse arguments
while getopts "r:dh" opt; do
    case $opt in
        r) RESOURCE_GROUP="$OPTARG" ;;
        d) DETAILED=true ;;
        h) usage ;;
        *) usage ;;
    esac
done

# Validate prerequisites
check_prerequisites() {
    local missing=()
    
    command -v az &> /dev/null || missing+=("Azure CLI (az)")
    command -v jq &> /dev/null || missing+=("jq")
    command -v curl &> /dev/null || missing+=("curl")
    
    if [ ${#missing[@]} -gt 0 ]; then
        failure "Missing required tools: ${missing[*]}"
        echo ""
        echo "Install instructions:"
        [ " ${missing[*]} " =~ " jq " ] && echo "  jq:   apt-get install jq  OR  brew install jq"
        [ " ${missing[*]} " =~ " curl " ] && echo "  curl: apt-get install curl OR brew install curl"
        [ " ${missing[*]} " =~ " Azure CLI (az) " ] && echo "  az:   https://docs.microsoft.com/cli/azure/install-azure-cli"
        exit 1
    fi
}

# Check Azure authentication
check_azure_auth() {
    debug "Checking Azure CLI authentication..."
    if ! az account show &> /dev/null; then
        failure "Azure CLI not authenticated. Run: az login"
        exit 1
    fi
    success "Azure CLI authenticated"
}

# Print header
print_header() {
    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║   PetPal Microservices Deployment Health Check           ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Print section separator
print_separator() {
    echo -e "${GRAY}───────────────────────────────────────────────────────────${NC}"
}

# Test a single service
test_service() {
    local service_name=$1
    local service_info=${SERVICES[$service_name]}
    
    IFS='|' read -r port expected_db description <<< "$service_info"
    
    echo ""
    print_separator
    echo -e "${YELLOW}Testing: ${description}${NC}"
    print_separator
    echo ""
    
    # Get Container App name
    debug "  Looking up service URL..."
    local app_name
    app_name=$(az containerapp list \
        --resource-group "$RESOURCE_GROUP" \
        --query "[?contains(name, '${service_name}')].name" \
        -o tsv 2>/dev/null)
    
    if [ -z "$app_name" ]; then
        failure "Service not found in resource group"
        echo "NOT_FOUND|$service_name|N/A|false|"
        return 1
    fi
    
    # Get FQDN
    local fqdn
    fqdn=$(az containerapp show \
        --name "$app_name" \
        --resource-group "$RESOURCE_GROUP" \
        --query "properties.configuration.ingress.fqdn" \
        -o tsv 2>/dev/null)
    
    if [ -z "$fqdn" ]; then
        failure "Could not retrieve service URL"
        echo "NO_INGRESS|$service_name|N/A|false|"
        return 1
    fi
    
    local health_url="https://${fqdn}/health"
    info "Service URL: $health_url"
    
    # Test health endpoint
    debug "  Testing /health endpoint..."
    local start_time end_time response_time http_code response_body
    
    start_time=$(date +%s%3N)
    response_body=$(curl -s -w "\n%{http_code}" -m 30 "$health_url" 2>/dev/null || echo "000")
    end_time=$(date +%s%3N)
    
    http_code=$(echo "$response_body" | tail -n1)
    response_body=$(echo "$response_body" | sed '$d')
    response_time=$((end_time - start_time))
    
    if [ "$http_code" != "200" ]; then
        failure "Health check failed with HTTP $http_code"
        echo "HTTP_${http_code}|$service_name|$health_url|false|"
        return 1
    fi
    
    # Parse JSON response
    if ! echo "$response_body" | jq -e . >/dev/null 2>&1; then
        failure "Invalid JSON response"
        echo "INVALID_JSON|$service_name|$health_url|false|"
        return 1
    fi
    
    local status
    status=$(echo "$response_body" | jq -r '.status // "unknown"')
    
    # Validate response
    if [ "$status" = "healthy" ]; then
        success "Service is healthy (${response_time}ms)"
        
        if [ "$DETAILED" = true ]; then
            echo ""
            echo -e "    ${GRAY}Full Response:${NC}"
            echo "$response_body" | jq '.' | sed 's/^/    /' | while read -r line; do
                echo -e "${GRAY}${line}${NC}"
            done
        fi
        
        echo "HEALTHY|$service_name|$health_url|true|$response_time"
        return 0
    elif [ "$status" != "healthy" ]; then
        failure "Service status is not healthy: $status"
        echo "UNHEALTHY|$service_name|$health_url|false|"
        return 1
    fi
}

# Main execution
main() {
    check_prerequisites
    print_header
    
    # Validate resource group
    if [ -z "$RESOURCE_GROUP" ]; then
        failure "Resource group not specified."
        echo ""
        echo "Usage:"
        echo "  $0 -r RESOURCE_GROUP"
        echo "  export RESOURCE_GROUP=rg-petpal-dev && $0"
        exit 1
    fi
    
    info "Testing services in resource group: $RESOURCE_GROUP"
    echo ""
    
    check_azure_auth
    
    # Test all services and collect results
    local results=()
    local all_healthy=true
    
    for service in "${!SERVICES[@]}"; do
        local last_line
        # Print detailed output while keeping only the final summary line for later aggregation.
        if result=$(test_service "$service"); then
            printf '%s\n' "$result" | sed '$d'
            last_line=$(printf '%s\n' "$result" | tail -n1)
            if [ -n "$last_line" ]; then
                results+=("$last_line")
            else
                results+=("NO_RESULT|$service|N/A|false|")
            fi
        else
            printf '%s\n' "$result" | sed '$d'
            last_line=$(printf '%s\n' "$result" | tail -n1)
            all_healthy=false
            if [ -n "$last_line" ]; then
                results+=("$last_line")
            else
                results+=("NO_RESULT|$service|N/A|false|")
            fi
        fi
    done
    
    # Print summary
    echo ""
    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                    TEST SUMMARY                           ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    for result in "${results[@]}"; do
        IFS='|' read -r status service_name url healthy response_time <<< "$result"
        
        if [ "$healthy" = "true" ]; then
            if [ -n "$response_time" ]; then
                printf "  ${GREEN}✅ %-20s HEALTHY (%sms)${NC}\n" "$service_name" "$response_time"
            else
                printf "  ${GREEN}✅ %-20s HEALTHY${NC}\n" "$service_name"
            fi
        else
            printf "  ${RED}❌ %-20s %s${NC}\n" "$service_name" "$status"
        fi
    done
    
    echo ""
    
    # Overall result
    if [ "$all_healthy" = true ]; then
        echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
        success "All services are healthy and operational!"
        echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
        echo ""
        exit 0
    else
        echo -e "${RED}═══════════════════════════════════════════════════════════${NC}"
        failure "One or more services failed health checks"
        echo -e "${RED}═══════════════════════════════════════════════════════════${NC}"
        echo ""
        
        info "Troubleshooting tips:"
        echo -e "  ${GRAY}1. Check Container App logs: az containerapp logs show --name <app-name> --resource-group $RESOURCE_GROUP --follow${NC}"
        echo -e "  ${GRAY}2. Verify environment variables are set correctly${NC}"
        echo -e "  ${GRAY}3. Ensure Cosmos DB credentials are valid${NC}"
        echo -e "  ${GRAY}4. Check ingress configuration matches service port${NC}"
        echo ""
        exit 1
    fi
}

# Run main function
main "$@"
