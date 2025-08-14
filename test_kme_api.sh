#!/bin/bash

# Easy-KME ETSI GS QKD 014 API Test Script
# Tests all three API methods according to ETSI specification

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
# Default values - can be overridden by command line arguments
KME_HOST="localhost"
KME_PORT="8443"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --host)
            KME_HOST="$2"
            shift 2
            ;;
        --port)
            KME_PORT="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [--host HOST] [--port PORT]"
            echo "  --host HOST    Target KME server hostname/IP (default: localhost)"
            echo "  --port PORT    Target KME server port (default: 8443)"
            echo "  --help, -h     Show this help message"
            echo
            echo "Examples:"
            echo "  $0                    # Test localhost:8443"
            echo "  $0 --host 192.168.1.100 --port 8443"
            echo "  $0 --host kme.example.com"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

BASE_URL="https://${KME_HOST}:${KME_PORT}"
CERT_DIR="./certs"
SAE1_CERT="${CERT_DIR}/sae/sae1.crt"
SAE1_KEY="${CERT_DIR}/sae/sae1.key"
SAE2_CERT="${CERT_DIR}/sae/sae2.crt"
SAE2_KEY="${CERT_DIR}/sae/sae2.key"
SAE3_CERT="${CERT_DIR}/sae/sae3.crt"
SAE3_KEY="${CERT_DIR}/sae/sae3.key"
CA_CERT="${CERT_DIR}/ca/ca.crt"

# SAE IDs for testing
MASTER_SAE_ID="SAE_001"
SLAVE_SAE_ID="SAE_002"

# Function to print colored output
print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Function to make API calls with proper formatting
api_call() {
    local method="$1"
    local endpoint="$2"
    local data="$3"
    local sae_id="$4"
    local cert_file="$5"
    local key_file="$6"
    
    local url="${BASE_URL}${endpoint}"
    local headers="-H 'x-sae-id: ${sae_id}'"
    
    if [[ -n "$data" ]]; then
        headers="${headers} -H 'Content-Type: application/json'"
    fi
    
    local curl_cmd="curl -k --cert ${cert_file} --key ${key_file} --cacert ${CA_CERT} ${headers}"
    
    if [[ "$method" == "GET" ]]; then
        curl_cmd="${curl_cmd} -X GET"
    elif [[ "$method" == "POST" ]]; then
        curl_cmd="${curl_cmd} -X POST"
        if [[ -n "$data" ]]; then
            curl_cmd="${curl_cmd} -d '${data}'"
        fi
    fi
    
    curl_cmd="${curl_cmd} '${url}'"
    
    echo -e "${PURPLE}Executing:${NC} $curl_cmd"
    echo
    
    # Execute and format JSON output
    local response
    response=$(eval "$curl_cmd" 2>/dev/null)
    
    if [[ $? -eq 0 ]]; then
        echo -e "${GREEN}Response:${NC}"
        echo "$response" | jq '.' 2>/dev/null || echo "$response"
    else
        echo -e "${RED}Request failed${NC}"
        echo "$response"
    fi
    echo
}

# Function to check if server is running
check_server() {
    print_info "Target KME Server: ${KME_HOST}:${KME_PORT}"
    print_info "Base URL: ${BASE_URL}"
    echo
    
    print_info "Checking if KME server is running..."
    if curl -k -s "${BASE_URL}/health" >/dev/null 2>&1; then
        print_success "KME server is running"
        return 0
    else
        print_error "KME server is not running"
        print_info "Please start the server with: source venv/bin/activate && python run.py &"
        return 1
    fi
}

# Function to check certificates
check_certificates() {
    print_info "Checking certificates..."
    
    local missing_certs=()
    
    [[ ! -f "$SAE1_CERT" ]] && missing_certs+=("SAE1 certificate")
    [[ ! -f "$SAE1_KEY" ]] && missing_certs+=("SAE1 private key")
    [[ ! -f "$SAE2_CERT" ]] && missing_certs+=("SAE2 certificate")
    [[ ! -f "$SAE2_KEY" ]] && missing_certs+=("SAE2 private key")
    [[ ! -f "$SAE3_CERT" ]] && missing_certs+=("SAE3 certificate")
    [[ ! -f "$SAE3_KEY" ]] && missing_certs+=("SAE3 private key")
    [[ ! -f "$CA_CERT" ]] && missing_certs+=("CA certificate")
    
    if [[ ${#missing_certs[@]} -eq 0 ]]; then
        print_success "All certificates found"
    else
        print_error "Missing certificates:"
        for cert in "${missing_certs[@]}"; do
            echo -e "  ${RED}- $cert${NC}"
        done
        print_info "Please generate certificates using the README files in certs/ directory"
        return 1
    fi
}

# Test 1: Get Status API
test_get_status() {
    print_header "Test 1: Get Status API (ETSI §5.2)"
    print_info "Testing Get status for ${SLAVE_SAE_ID} (slave SAE)"
    
    api_call "GET" "/api/v1/keys/${SLAVE_SAE_ID}/status" "" "$MASTER_SAE_ID" "$SAE1_CERT" "$SAE1_KEY"
}

# Test 2: Get Key API - POST Method
test_get_key_post() {
    print_header "Test 2: Get Key API - POST Method (ETSI §5.3)"
    print_info "Testing Get key with Key request data format (ETSI §6.2)"
    print_info "Master SAE ${MASTER_SAE_ID} requesting keys for slave SAE ${SLAVE_SAE_ID}"
    
    local key_request='{
        "number": 2,
        "size": 256
    }'
    
    api_call "POST" "/api/v1/keys/${SLAVE_SAE_ID}/enc_keys" "$key_request" "$MASTER_SAE_ID" "$SAE1_CERT" "$SAE1_KEY"
}

# Test 3: Get Key API - GET Method
test_get_key_get() {
    print_header "Test 3: Get Key API - GET Method (ETSI §6.2)"
    print_info "Testing Get key using GET method with query parameters"
    
    api_call "GET" "/api/v1/keys/${SLAVE_SAE_ID}/enc_keys?number=1&size=512" "" "$MASTER_SAE_ID" "$SAE1_CERT" "$SAE1_KEY"
}

# Test 4: Complete ETSI Workflow
test_complete_workflow() {
    print_header "Test 4: Complete ETSI Workflow"
    print_info "Step 1: Master SAE gets keys for slave SAE"
    
    # Step 1: Master SAE gets keys
    local key_request='{
        "number": 2,
        "size": 256
    }'
    
    print_info "Master SAE ${MASTER_SAE_ID} requesting keys for slave SAE ${SLAVE_SAE_ID}..."
    
    # Use api_call function to ensure command is printed
    local curl_cmd="curl -k --cert $SAE1_CERT --key $SAE1_KEY --cacert $CA_CERT -H 'x-sae-id: $MASTER_SAE_ID' -H 'Content-Type: application/json' -X POST -d '$key_request' '${BASE_URL}/api/v1/keys/${SLAVE_SAE_ID}/enc_keys'"
    echo -e "${PURPLE}Executing:${NC} $curl_cmd"
    echo
    
    local response
    response=$(eval "$curl_cmd" 2>/dev/null)
    
    if [[ $? -eq 0 ]]; then
        print_success "Keys obtained successfully"
        echo -e "${GREEN}Response:${NC}"
        echo "$response" | jq '.' 2>/dev/null || echo "$response"
        echo
        
        # Extract key IDs for step 2
        local key_ids
        key_ids=$(echo "$response" | jq -r '.keys[].key_ID' 2>/dev/null)
        
        if [[ -n "$key_ids" ]]; then
            print_info "Step 2: Slave SAE retrieves keys using key_IDs"
            
            # Create key IDs request
            local key_ids_request='{
                "key_IDs": ['
            
            local first=true
            while IFS= read -r key_id; do
                if [[ -n "$key_id" ]]; then
                    if [[ "$first" == "true" ]]; then
                        first=false
                    else
                        key_ids_request="${key_ids_request},"
                    fi
                    key_ids_request="${key_ids_request}
                    {
                        \"key_ID\": \"${key_id}\"
                    }"
                fi
            done <<< "$key_ids"
            
            key_ids_request="${key_ids_request}
                ]
            }"
            
            print_info "Slave SAE ${SLAVE_SAE_ID} retrieving keys using key_IDs from master SAE ${MASTER_SAE_ID}..."
            
            api_call "POST" "/api/v1/keys/${MASTER_SAE_ID}/dec_keys" "$key_ids_request" "$SLAVE_SAE_ID" "$SAE2_CERT" "$SAE2_KEY"
        else
            print_error "Failed to extract key_IDs from response"
        fi
    else
        print_error "Failed to get keys in step 1"
    fi
}

# Test 5: Get Key with Key IDs API - GET Method
test_get_key_with_ids_get() {
    print_header "Test 5: Get Key with Key IDs API - GET Method (ETSI §6.4)"
    print_info "Testing single key ID retrieval using GET method"
    
    # First get a key to obtain a key_ID
    print_info "Getting a key to obtain key_ID..."
    local response
    response=$(curl -k --cert "$SAE1_CERT" --key "$SAE1_KEY" --cacert "$CA_CERT" \
        -H "x-sae-id: $MASTER_SAE_ID" \
        -H "Content-Type: application/json" \
        -X POST \
        -d '{"number": 1, "size": 256}' \
        "${BASE_URL}/api/v1/keys/${SLAVE_SAE_ID}/enc_keys" 2>/dev/null)
    
    if [[ $? -eq 0 ]]; then
        local key_id
        key_id=$(echo "$response" | jq -r '.keys[0].key_ID' 2>/dev/null)
        
        if [[ -n "$key_id" && "$key_id" != "null" ]]; then
            print_info "Retrieved key_ID: $key_id"
            api_call "GET" "/api/v1/keys/${MASTER_SAE_ID}/dec_keys?key_ID=${key_id}" "" "$SLAVE_SAE_ID" "$SAE2_CERT" "$SAE2_KEY"
        else
            print_error "Failed to extract key_ID from response"
        fi
    else
        print_error "Failed to get key for key_ID extraction"
    fi
}

# Test 6: Error Handling
test_error_handling() {
    print_header "Test 6: Error Handling (ETSI §5.2-5.4)"
    
    print_info "Test 1: 400 Bad Request - Invalid key size (not multiple of 8)"
    api_call "POST" "/api/v1/keys/${SLAVE_SAE_ID}/enc_keys" '{"number": 1, "size": 255}' "$MASTER_SAE_ID" "$SAE1_CERT" "$SAE1_KEY"
    
    print_info "Test 2: 401 Unauthorized - Missing certificate"
    curl -k "${BASE_URL}/api/v1/keys/${SLAVE_SAE_ID}/status" 2>/dev/null | jq '.' 2>/dev/null || echo "Request failed as expected"
    echo
    
    print_info "Test 3: 404 Not Found - Invalid endpoint"
    curl -k --cert "$SAE1_CERT" --key "$SAE1_KEY" --cacert "$CA_CERT" \
        -H "x-sae-id: $MASTER_SAE_ID" \
        "${BASE_URL}/api/v1/keys/invalid/status" 2>/dev/null | jq '.' 2>/dev/null || echo "Request failed as expected"
    echo
    
    print_info "Test 4: 401 Unauthorized - Unauthorized SAE trying to retrieve keys"
    # First get some keys with authorized SAE
    local auth_response
    auth_response=$(curl -k --cert "$SAE1_CERT" --key "$SAE1_KEY" --cacert "$CA_CERT" \
        -H "x-sae-id: $MASTER_SAE_ID" \
        -H "Content-Type: application/json" \
        -X POST \
        -d '{"number": 1, "size": 256}' \
        "${BASE_URL}/api/v1/keys/${SLAVE_SAE_ID}/enc_keys" 2>/dev/null)
    
    if [[ $? -eq 0 ]]; then
        local key_id
        key_id=$(echo "$auth_response" | jq -r '.keys[0].key_ID' 2>/dev/null)
        
        if [[ -n "$key_id" && "$key_id" != "null" ]]; then
            print_info "Testing unauthorized access with key_ID: $key_id"
            # Try to retrieve the same key with an unauthorized SAE (SAE_003)
            curl -k --cert "$SAE3_CERT" --key "$SAE3_KEY" --cacert "$CA_CERT" \
                -H "x-sae-id: SAE_003" \
                -H "Content-Type: application/json" \
                -X POST \
                -d "{\"key_IDs\": [{\"key_ID\": \"$key_id\"}]}" \
                "${BASE_URL}/api/v1/keys/${MASTER_SAE_ID}/dec_keys" 2>/dev/null | jq '.' 2>/dev/null || echo "Request failed as expected"
        else
            print_error "Failed to extract key_ID for unauthorized test"
        fi
    else
        print_error "Failed to get key for unauthorized test"
    fi
    echo
}

# Test 7: Advanced Features
test_advanced_features() {
    print_header "Test 7: Advanced Features"
    
    print_info "Test 1: Key request with extensions"
    local advanced_request='{
        "number": 1,
        "size": 256,
        "extension_mandatory": [
            {
                "route_type": "direct"
            }
        ],
        "extension_optional": [
            {
                "max_age": 30000
            }
        ]
    }'
    
    api_call "POST" "/api/v1/keys/${SLAVE_SAE_ID}/enc_keys" "$advanced_request" "$MASTER_SAE_ID" "$SAE1_CERT" "$SAE1_KEY"
    
    print_info "Test 2: Multiple slave SAEs"
    local multiple_slaves_request='{
        "number": 1,
        "size": 256,
        "additional_slave_SAE_IDs": [
            "SAE_002",
            "SAE_003"
        ]
    }'
    
    api_call "POST" "/api/v1/keys/${SLAVE_SAE_ID}/enc_keys" "$multiple_slaves_request" "$MASTER_SAE_ID" "$SAE1_CERT" "$SAE1_KEY"
}

# Test 8: Health and Documentation
test_health_and_docs() {
    print_header "Test 8: Health and Documentation"
    
    print_info "Health check endpoint"
    curl -k "${BASE_URL}/health" 2>/dev/null | jq '.' 2>/dev/null || echo "Health check response"
    echo
    
    print_info "Root endpoint"
    curl -k "${BASE_URL}/" 2>/dev/null | jq '.' 2>/dev/null || echo "Root endpoint response"
    echo
    
    print_info "API Documentation available at: ${BASE_URL}/docs"
    print_info "OpenAPI specification available at: ${BASE_URL}/openapi.json"
}

# Main menu
show_menu() {
    clear
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  Easy-KME API Test Suite${NC}"
    echo -e "${BLUE}  ETSI GS QKD 014 Compliant${NC}"
    echo -e "${BLUE}================================${NC}"
    echo
    echo -e "${CYAN}Available Tests:${NC}"
    echo -e "  ${GREEN}1${NC}) Get Status API"
    echo -e "  ${GREEN}2${NC}) Get Key API - POST Method"
    echo -e "  ${GREEN}3${NC}) Get Key API - GET Method"
    echo -e "  ${GREEN}4${NC}) Complete ETSI Workflow"
    echo -e "  ${GREEN}5${NC}) Get Key with Key IDs - GET Method"
    echo -e "  ${GREEN}6${NC}) Error Handling Tests"
    echo -e "  ${GREEN}7${NC}) Advanced Features"
    echo -e "  ${GREEN}8${NC}) Health and Documentation"
    echo -e "  ${GREEN}9${NC}) Run All Tests"
    echo -e "  ${GREEN}0${NC}) Exit"
    echo
    echo -e "${YELLOW}Note:${NC} Make sure the KME server is running before testing"
    echo
}

# Main function
main() {
    # Check dependencies
    if ! command -v jq &> /dev/null; then
        print_error "jq is required but not installed. Please install jq: sudo apt-get install jq"
        exit 1
    fi
    
    # Check server and certificates
    if ! check_server; then
        exit 1
    fi
    
    if ! check_certificates; then
        exit 1
    fi
    
    while true; do
        show_menu
        read -p "Select a test (0-9): " choice
        
        case $choice in
            1)
                test_get_status
                ;;
            2)
                test_get_key_post
                ;;
            3)
                test_get_key_get
                ;;
            4)
                test_complete_workflow
                ;;
            5)
                test_get_key_with_ids_get
                ;;
            6)
                test_error_handling
                ;;
            7)
                test_advanced_features
                ;;
            8)
                test_health_and_docs
                ;;
            9)
                print_header "Running All Tests"
                test_get_status
                test_get_key_post
                test_get_key_get
                test_complete_workflow
                test_get_key_with_ids_get
                test_error_handling
                test_advanced_features
                test_health_and_docs
                print_success "All tests completed!"
                ;;
            0)
                print_info "Exiting..."
                exit 0
                ;;
            *)
                print_error "Invalid choice. Please select 0-9."
                ;;
        esac
        
        echo
        read -p "Press Enter to continue..."
    done
}

# Run main function
main "$@" 
