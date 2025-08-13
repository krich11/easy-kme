#!/bin/bash

# Easy-KMS Setup Script
# This script sets up the KME server from scratch, including all prerequisites

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a file exists
file_exists() {
    [ -f "$1" ]
}

# Function to check if a directory exists
dir_exists() {
    [ -d "$1" ]
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    local missing_deps=()
    
    # Check for Python 3.8+
    if command_exists python3; then
        python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
            print_success "Python 3.8+ found: $(python3 --version)"
        else
            missing_deps+=("Python 3.8+ (found: $python_version)")
        fi
    else
        missing_deps+=("Python 3.8+")
    fi
    
    # Check for pip
    if command_exists pip3; then
        print_success "pip3 found"
    else
        missing_deps+=("pip3")
    fi
    
    # Check for git
    if command_exists git; then
        print_success "git found"
    else
        missing_deps+=("git")
    fi
    
    # Check for openssl
    if command_exists openssl; then
        print_success "OpenSSL found"
    else
        missing_deps+=("OpenSSL")
    fi
    
    # Check for nginx
    if command_exists nginx; then
        print_success "Nginx found"
    else
        missing_deps+=("Nginx")
    fi
    
    # Check for curl
    if command_exists curl; then
        print_success "curl found"
    else
        missing_deps+=("curl")
    fi
    
    # Check for jq
    if command_exists jq; then
        print_success "jq found"
    else
        missing_deps+=("jq")
    fi
    
    if [ ${#missing_deps[@]} -eq 0 ]; then
        print_success "All prerequisites are satisfied!"
        return 0
    else
        print_error "Missing prerequisites:"
        for dep in "${missing_deps[@]}"; do
            echo "  - $dep"
        done
        return 1
    fi
}

# Function to install missing prerequisites
install_prerequisites() {
    print_status "Installing missing prerequisites..."
    
    if command_exists apt-get; then
        print_status "Using apt package manager"
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip python3-venv git openssl nginx curl jq
    elif command_exists yum; then
        print_status "Using yum package manager"
        sudo yum install -y python3 python3-pip git openssl nginx curl jq
    elif command_exists dnf; then
        print_status "Using dnf package manager"
        sudo dnf install -y python3 python3-pip git openssl nginx curl jq
    else
        print_error "Unsupported package manager. Please install prerequisites manually."
        return 1
    fi
    
    print_success "Prerequisites installed successfully!"
}

# Function to setup Python virtual environment
setup_virtual_environment() {
    print_status "Setting up Python virtual environment..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_success "Virtual environment already exists"
    fi
    
    # Activate virtual environment and install requirements
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    print_success "Python dependencies installed"
}

# Function to create directory structure
create_directory_structure() {
    print_status "Creating directory structure..."
    
    local dirs=("data" "logs" "certs/ca" "certs/kme" "certs/sae")
    
    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_success "Created directory: $dir"
        else
            print_success "Directory already exists: $dir"
        fi
    done
    
    # Set proper permissions
    chmod 755 data logs
    chmod 700 certs/ca certs/kme certs/sae
    
    print_success "Directory structure created with proper permissions"
}

# Function to create .env file
create_env_file() {
    print_status "Creating .env file..."
    
    if [ -f ".env" ]; then
        print_warning ".env file already exists. Backing up to .env.backup"
        cp .env .env.backup
    fi
    
    cat > .env << 'EOF'
# KME Server Configuration
KME_HOST=0.0.0.0
KME_PORT=8443
KME_ID=KME_LAB_001

# Certificate Configuration
KME_CERT_PATH=./certs/kme/kme.crt
KME_KEY_PATH=./certs/kme/kme.key
CA_CERT_PATH=./certs/ca/ca.crt

# Storage Configuration
DATA_DIR=./data
KEY_POOL_SIZE=1000
KEY_SIZE=256

# Security Settings
REQUIRE_CLIENT_CERT=true
VERIFY_CA=true
ALLOW_HEADER_AUTH=false

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=./logs/kme.log

# API Configuration
API_VERSION=v1
API_PREFIX=/api
EOF
    
    print_success ".env file created"
}

# Function to extract P12 file
extract_p12() {
    local p12_file="$1"
    local output_dir="$2"
    local cert_name="$3"
    
    print_status "Extracting P12 file: $p12_file"
    
    if [ ! -f "$p12_file" ]; then
        print_error "P12 file not found: $p12_file"
        return 1
    fi
    
    # Prompt for password
    read -s -p "Enter P12 password: " p12_password
    echo
    
    # Extract certificate and private key
    openssl pkcs12 -in "$p12_file" -out "$output_dir/${cert_name}.crt" -clcerts -nokeys -passin pass:"$p12_password" 2>/dev/null || {
        print_error "Failed to extract certificate from P12 file"
        return 1
    }
    
    openssl pkcs12 -in "$p12_file" -out "$output_dir/${cert_name}.key" -nocerts -nodes -passin pass:"$p12_password" 2>/dev/null || {
        print_error "Failed to extract private key from P12 file"
        return 1
    }
    
    # Set proper permissions
    chmod 644 "$output_dir/${cert_name}.crt"
    chmod 600 "$output_dir/${cert_name}.key"
    
    print_success "P12 file extracted successfully"
    print_success "Certificate: $output_dir/${cert_name}.crt"
    print_success "Private key: $output_dir/${cert_name}.key"
}

# Function to import KME certificate
import_kme_certificate() {
    print_status "Importing KME certificate..."
    
    read -p "Enter path to KME P12 file: " kme_p12_file
    
    if [ -z "$kme_p12_file" ]; then
        print_warning "No P12 file specified, skipping KME certificate import"
        return 0
    fi
    
    extract_p12 "$kme_p12_file" "certs/kme" "kme"
    
    # Update .env file with correct paths
    sed -i 's|KME_CERT_PATH=.*|KME_CERT_PATH=./certs/kme/kme.crt|' .env
    sed -i 's|KME_KEY_PATH=.*|KME_KEY_PATH=./certs/kme/kme.key|' .env
    
    print_success "KME certificate imported and .env updated"
}

# Function to import CA certificate
import_ca_certificate() {
    print_status "Importing CA certificate..."
    
    read -p "Enter path to CA certificate file (PEM format): " ca_cert_file
    
    if [ -z "$ca_cert_file" ]; then
        print_warning "No CA certificate specified, skipping CA import"
        return 0
    fi
    
    if [ ! -f "$ca_cert_file" ]; then
        print_error "CA certificate file not found: $ca_cert_file"
        return 1
    fi
    
    cp "$ca_cert_file" "certs/ca/ca.crt"
    chmod 644 "certs/ca/ca.crt"
    
    # Update .env file
    sed -i 's|CA_CERT_PATH=.*|CA_CERT_PATH=./certs/ca/ca.crt|' .env
    
    print_success "CA certificate imported and .env updated"
}

# Function to import SAE certificates
import_sae_certificates() {
    print_status "Importing SAE certificates..."
    
    while true; do
        read -p "Enter path to SAE P12 file (or 'done' to finish): " sae_p12_file
        
        if [ "$sae_p12_file" = "done" ]; then
            break
        fi
        
        if [ -z "$sae_p12_file" ]; then
            continue
        fi
        
        read -p "Enter SAE name (e.g., SAE_001): " sae_name
        
        if [ -z "$sae_name" ]; then
            print_error "SAE name is required"
            continue
        fi
        
        extract_p12 "$sae_p12_file" "certs/sae" "$sae_name"
    done
    
    print_success "SAE certificate import completed"
}

# Function to setup Nginx
setup_nginx() {
    print_status "Setting up Nginx configuration..."
    
    if [ ! -f "nginx.conf" ]; then
        print_error "nginx.conf not found in current directory"
        return 1
    fi
    
    # Check if nginx is running
    if systemctl is-active --quiet nginx; then
        print_success "Nginx is running"
    else
        print_warning "Nginx is not running. Starting Nginx..."
        sudo systemctl start nginx
        sudo systemctl enable nginx
    fi
    
    # Copy nginx configuration
    sudo cp nginx.conf /etc/nginx/sites-available/easy-kms
    sudo ln -sf /etc/nginx/sites-available/easy-kms /etc/nginx/sites-enabled/
    
    # Test nginx configuration
    if sudo nginx -t; then
        sudo systemctl reload nginx
        print_success "Nginx configuration updated"
    else
        print_error "Nginx configuration test failed"
        return 1
    fi
}

# Function to verify setup
verify_setup() {
    print_status "Verifying setup..."
    
    local issues=()
    
    # Check .env file
    if [ ! -f ".env" ]; then
        issues+=("Missing .env file")
    else
        print_success ".env file exists"
    fi
    
    # Check virtual environment
    if [ ! -d "venv" ]; then
        issues+=("Missing virtual environment")
    else
        print_success "Virtual environment exists"
    fi
    
    # Check certificate files
    if [ ! -f "certs/kme/kme.crt" ]; then
        issues+=("Missing KME certificate")
    else
        print_success "KME certificate exists"
    fi
    
    if [ ! -f "certs/kme/kme.key" ]; then
        issues+=("Missing KME private key")
    else
        print_success "KME private key exists"
    fi
    
    if [ ! -f "certs/ca/ca.crt" ]; then
        issues+=("Missing CA certificate")
    else
        print_success "CA certificate exists"
    fi
    
    # Check SAE certificates
    sae_count=$(find certs/sae -name "*.crt" 2>/dev/null | wc -l)
    if [ "$sae_count" -eq 0 ]; then
        issues+=("No SAE certificates found")
    else
        print_success "Found $sae_count SAE certificate(s)"
    fi
    
    # Check nginx configuration
    if [ ! -f "/etc/nginx/sites-enabled/easy-kms" ]; then
        issues+=("Nginx configuration not linked")
    else
        print_success "Nginx configuration linked"
    fi
    
    if [ ${#issues[@]} -eq 0 ]; then
        print_success "Setup verification completed successfully!"
        return 0
    else
        print_warning "Setup verification found issues:"
        for issue in "${issues[@]}"; do
            echo "  - $issue"
        done
        return 1
    fi
}

# Function to show main menu
show_menu() {
    clear
    echo "=========================================="
    echo "        Easy-KMS Setup Menu"
    echo "=========================================="
    echo ""
    
    # Show status indicators
    echo "Status:"
    if command_exists python3 && command_exists pip3 && command_exists git && command_exists openssl && command_exists nginx && command_exists curl && command_exists jq; then
        echo -e "  ${GREEN}✓${NC} Prerequisites"
    else
        echo -e "  ${RED}✗${NC} Prerequisites"
    fi
    
    if [ -d "venv" ]; then
        echo -e "  ${GREEN}✓${NC} Virtual Environment"
    else
        echo -e "  ${RED}✗${NC} Virtual Environment"
    fi
    
    if [ -f ".env" ]; then
        echo -e "  ${GREEN}✓${NC} Environment Configuration"
    else
        echo -e "  ${RED}✗${NC} Environment Configuration"
    fi
    
    if [ -f "certs/kme/kme.crt" ] && [ -f "certs/kme/kme.key" ]; then
        echo -e "  ${GREEN}✓${NC} KME Certificates"
    else
        echo -e "  ${RED}✗${NC} KME Certificates"
    fi
    
    if [ -f "certs/ca/ca.crt" ]; then
        echo -e "  ${GREEN}✓${NC} CA Certificate"
    else
        echo -e "  ${RED}✗${NC} CA Certificate"
    fi
    
    sae_count=$(find certs/sae -name "*.crt" 2>/dev/null | wc -l)
    if [ "$sae_count" -gt 0 ]; then
        echo -e "  ${GREEN}✓${NC} SAE Certificates ($sae_count found)"
    else
        echo -e "  ${RED}✗${NC} SAE Certificates"
    fi
    
    if [ -f "/etc/nginx/sites-enabled/easy-kms" ]; then
        echo -e "  ${GREEN}✓${NC} Nginx Configuration"
    else
        echo -e "  ${RED}✗${NC} Nginx Configuration"
    fi
    
    echo ""
    echo "Options:"
    echo "  1) Check/Install Prerequisites"
    echo "  2) Setup Virtual Environment"
    echo "  3) Create Directory Structure"
    echo "  4) Create Environment Configuration"
    echo "  5) Import KME Certificate (P12)"
    echo "  6) Import CA Certificate"
    echo "  7) Import SAE Certificates (P12)"
    echo "  8) Setup Nginx Configuration"
    echo "  9) Verify Complete Setup"
    echo "  10) Run Complete Setup (All Steps)"
    echo "  q) Quit"
    echo ""
}

# Function to run complete setup
run_complete_setup() {
    print_status "Running complete setup..."
    
    # Check prerequisites
    if ! check_prerequisites; then
        print_status "Installing missing prerequisites..."
        install_prerequisites
    fi
    
    # Setup virtual environment
    setup_virtual_environment
    
    # Create directory structure
    create_directory_structure
    
    # Create .env file
    create_env_file
    
    # Import certificates (optional)
    echo ""
    read -p "Do you want to import certificates now? (y/n): " import_certs
    if [ "$import_certs" = "y" ] || [ "$import_certs" = "Y" ]; then
        import_kme_certificate
        import_ca_certificate
        import_sae_certificates
    fi
    
    # Setup nginx
    setup_nginx
    
    # Verify setup
    verify_setup
    
    print_success "Complete setup finished!"
    echo ""
    print_status "Next steps:"
    echo "  1. Import certificates if not done already"
    echo "  2. Run: ./start_kme.sh"
    echo "  3. Test with: ./test_kme_api.sh"
}

# Main menu loop
while true; do
    show_menu
    read -p "Select option: " choice
    
    case $choice in
        1)
            if check_prerequisites; then
                print_success "All prerequisites are satisfied!"
            else
                read -p "Install missing prerequisites? (y/n): " install_choice
                if [ "$install_choice" = "y" ] || [ "$install_choice" = "Y" ]; then
                    install_prerequisites
                fi
            fi
            ;;
        2)
            setup_virtual_environment
            ;;
        3)
            create_directory_structure
            ;;
        4)
            create_env_file
            ;;
        5)
            import_kme_certificate
            ;;
        6)
            import_ca_certificate
            ;;
        7)
            import_sae_certificates
            ;;
        8)
            setup_nginx
            ;;
        9)
            verify_setup
            ;;
        10)
            run_complete_setup
            ;;
        q|Q)
            print_status "Exiting setup menu"
            exit 0
            ;;
        *)
            print_error "Invalid option. Please try again."
            ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
done
