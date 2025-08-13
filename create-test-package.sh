#!/bin/bash

# Easy-KMS Test Package Creator
# Creates a portable test package with all necessary components

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
PACKAGE_NAME="easy-kms-test-package"
PACKAGE_VERSION="1.0"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
PACKAGE_DIR="${PACKAGE_NAME}-${PACKAGE_VERSION}-${TIMESTAMP}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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

# Function to check if required tools are available
check_requirements() {
    print_info "Checking requirements..."
    
    local missing_tools=()
    
    # Check for required commands
    command -v tar >/dev/null 2>&1 || missing_tools+=("tar")
    command -v gzip >/dev/null 2>&1 || missing_tools+=("gzip")
    command -v jq >/dev/null 2>&1 || missing_tools+=("jq")
    command -v curl >/dev/null 2>&1 || missing_tools+=("curl")
    command -v openssl >/dev/null 2>&1 || missing_tools+=("openssl")
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        print_error "Missing required tools:"
        for tool in "${missing_tools[@]}"; do
            echo -e "  ${RED}- $tool${NC}"
        done
        print_info "Please install missing tools and try again"
        exit 1
    fi
    
    print_success "All required tools are available"
}

# Function to check if certificates exist
check_certificates() {
    print_info "Checking certificates..."
    
    local missing_certs=()
    
    # Check for required certificates
    [[ ! -f "certs/ca/ca.crt" ]] && missing_certs+=("CA certificate")
    [[ ! -f "certs/kme/kme.crt" ]] && missing_certs+=("KME certificate")
    [[ ! -f "certs/kme/kme.key" ]] && missing_certs+=("KME private key")
    [[ ! -f "certs/sae/sae1.crt" ]] && missing_certs+=("SAE1 certificate")
    [[ ! -f "certs/sae/sae1.key" ]] && missing_certs+=("SAE1 private key")
    [[ ! -f "certs/sae/sae2.crt" ]] && missing_certs+=("SAE2 certificate")
    [[ ! -f "certs/sae/sae2.key" ]] && missing_certs+=("SAE2 private key")
    [[ ! -f "certs/sae/sae3.crt" ]] && missing_certs+=("SAE3 certificate")
    [[ ! -f "certs/sae/sae3.key" ]] && missing_certs+=("SAE3 private key")
    
    if [[ ${#missing_certs[@]} -gt 0 ]]; then
        print_error "Missing certificates:"
        for cert in "${missing_certs[@]}"; do
            echo -e "  ${RED}- $cert${NC}"
        done
        print_info "Please generate certificates first using:"
        echo "  ./certs/tools/create-ca.sh"
        echo "  ./certs/tools/create-kme.sh"
        echo "  ./certs/tools/create-sae-test-certs.sh"
        exit 1
    fi
    
    print_success "All required certificates found"
}

# Function to create package directory structure
create_package_structure() {
    print_info "Creating package directory structure..."
    
    # Create main package directory
    mkdir -p "$PACKAGE_DIR"
    
    # Create subdirectories
    mkdir -p "$PACKAGE_DIR/certs"
    mkdir -p "$PACKAGE_DIR/certs/ca"
    mkdir -p "$PACKAGE_DIR/certs/kme"
    mkdir -p "$PACKAGE_DIR/certs/sae"
    mkdir -p "$PACKAGE_DIR/certs/tools"
    mkdir -p "$PACKAGE_DIR/src"
    mkdir -p "$PACKAGE_DIR/src/api"
    mkdir -p "$PACKAGE_DIR/src/models"
    mkdir -p "$PACKAGE_DIR/src/services"
    mkdir -p "$PACKAGE_DIR/src/utils"
    mkdir -p "$PACKAGE_DIR/data"
    mkdir -p "$PACKAGE_DIR/logs"
    mkdir -p "$PACKAGE_DIR/tests"
    
    print_success "Package directory structure created"
}

# Function to copy certificates
copy_certificates() {
    print_info "Copying certificates..."
    
    # Copy CA certificates
    cp certs/ca/ca.crt "$PACKAGE_DIR/certs/ca/"
    cp certs/ca/ca.key "$PACKAGE_DIR/certs/ca/"
    cp certs/ca/ca.srl "$PACKAGE_DIR/certs/ca/" 2>/dev/null || true
    cp certs/ca/index.txt "$PACKAGE_DIR/certs/ca/" 2>/dev/null || true
    cp certs/ca/index.txt.attr "$PACKAGE_DIR/certs/ca/" 2>/dev/null || true
    
    # Copy KME certificates
    cp certs/kme/kme.crt "$PACKAGE_DIR/certs/kme/"
    cp certs/kme/kme.key "$PACKAGE_DIR/certs/kme/"
    cp certs/kme/kme.conf "$PACKAGE_DIR/certs/kme/" 2>/dev/null || true
    
    # Copy SAE certificates
    cp certs/sae/sae1.crt "$PACKAGE_DIR/certs/sae/"
    cp certs/sae/sae1.key "$PACKAGE_DIR/certs/sae/"
    cp certs/sae/sae2.crt "$PACKAGE_DIR/certs/sae/"
    cp certs/sae/sae2.key "$PACKAGE_DIR/certs/sae/"
    cp certs/sae/sae3.crt "$PACKAGE_DIR/certs/sae/"
    cp certs/sae/sae3.key "$PACKAGE_DIR/certs/sae/"
    cp certs/sae/sae1.conf "$PACKAGE_DIR/certs/sae/" 2>/dev/null || true
    cp certs/sae/sae2.conf "$PACKAGE_DIR/certs/sae/" 2>/dev/null || true
    cp certs/sae/sae3.conf "$PACKAGE_DIR/certs/sae/" 2>/dev/null || true
    
    # Copy OpenSSL configuration
    cp certs/openssl.conf "$PACKAGE_DIR/certs/"
    
    # Copy certificate tools
    cp certs/tools/create-ca.sh "$PACKAGE_DIR/certs/tools/"
    cp certs/tools/create-kme.sh "$PACKAGE_DIR/certs/tools/"
    cp certs/tools/create-sae-test-certs.sh "$PACKAGE_DIR/certs/tools/"
    cp certs/tools/reset-certs.sh "$PACKAGE_DIR/certs/tools/"
    
    # Make tools executable
    chmod +x "$PACKAGE_DIR/certs/tools/"*.sh
    
    print_success "Certificates copied"
}

# Function to copy source code
copy_source_code() {
    print_info "Copying source code..."
    
    # Copy main application files
    cp run.py "$PACKAGE_DIR/"
    cp requirements.txt "$PACKAGE_DIR/"
    cp env.example "$PACKAGE_DIR/"
    
    # Copy source code (excluding cache files)
    rsync -av --exclude='__pycache__' --exclude='*.pyc' src/ "$PACKAGE_DIR/src/" 2>/dev/null || cp -r src/* "$PACKAGE_DIR/src/"
    
    # Copy configuration
    cp nginx.conf "$PACKAGE_DIR/"
    cp start_kme.sh "$PACKAGE_DIR/"
    cp setup_nginx.sh "$PACKAGE_DIR/"
    
    # Make scripts executable
    chmod +x "$PACKAGE_DIR/start_kme.sh"
    chmod +x "$PACKAGE_DIR/setup_nginx.sh"
    
    print_success "Source code copied"
}

# Function to copy test files
copy_test_files() {
    print_info "Copying test files..."
    
    # Copy main test script
    cp test_kme_api.sh "$PACKAGE_DIR/"
    chmod +x "$PACKAGE_DIR/test_kme_api.sh"
    
    # Copy test documentation
    cp TESTING.md "$PACKAGE_DIR/"
    cp ETSI_WORKFLOW.md "$PACKAGE_DIR/"
    
    # Copy test data
    cp -r data/* "$PACKAGE_DIR/data/" 2>/dev/null || true
    
    # Copy test scripts (excluding cache files)
    rsync -av --exclude='__pycache__' --exclude='*.pyc' tests/ "$PACKAGE_DIR/tests/" 2>/dev/null || cp -r tests/* "$PACKAGE_DIR/tests/" 2>/dev/null || true
    
    print_success "Test files copied"
}

# Function to create package documentation
create_package_docs() {
    print_info "Creating package documentation..."
    
    cat > "$PACKAGE_DIR/README-TEST-PACKAGE.md" << 'EOF'
# Easy-KMS Test Package

This package contains all necessary components to run Easy-KMS tests on a target machine.

## Package Contents

- **Certificates**: CA, KME, and SAE certificates for mTLS testing
- **Source Code**: Complete Easy-KMS application
- **Test Scripts**: API testing tools and documentation
- **Configuration**: Nginx and application configuration files

## Quick Start

1. **Extract the package**:
   ```bash
   tar -xzf easy-kms-test-package-*.tar.gz
   cd easy-kms-test-package-*
   ```

2. **Set up Python environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

4. **Set up Nginx** (if using mTLS termination):
   ```bash
   sudo ./setup_nginx.sh
   ```

5. **Start the KME server**:
   ```bash
   ./start_kme.sh
   ```

6. **Run tests**:
   ```bash
   # Test local server
   ./test_kme_api.sh
   
   # Test remote server
   ./test_kme_api.sh --host <target-host> --port <target-port>
   ```

## Certificate Management

- **View certificates**: Check `certs/` directory
- **Reset certificates**: `./certs/tools/reset-certs.sh`
- **Regenerate certificates**: Use scripts in `certs/tools/`

## Test Options

The test script supports various options:
- `--host HOST`: Target KME server hostname/IP
- `--port PORT`: Target KME server port
- `--help`: Show help information

## Troubleshooting

1. **Certificate errors**: Ensure certificates are valid and have correct permissions
2. **Connection errors**: Check if target KME server is running and accessible
3. **Permission errors**: Ensure scripts have execute permissions

## Package Information

- **Created**: $(date)
- **Version**: $PACKAGE_VERSION
- **Source**: Easy-KMS $(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
EOF

    print_success "Package documentation created"
}

# Function to create installation script
create_install_script() {
    print_info "Creating installation script..."
    
    cat > "$PACKAGE_DIR/install.sh" << 'EOF'
#!/bin/bash

# Easy-KMS Test Package Installer

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

main() {
    print_header "Easy-KMS Test Package Installation"
    
    # Check if running as root for nginx setup
    if [[ $EUID -eq 0 ]]; then
        print_warning "Running as root - will set up nginx configuration"
        SETUP_NGINX=true
    else
        print_info "Running as user - nginx setup will be skipped"
        SETUP_NGINX=false
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    print_success "Python 3 found"
    
    # Create virtual environment
    print_info "Creating Python virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
    
    # Activate virtual environment and install dependencies
    print_info "Installing Python dependencies..."
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    print_success "Dependencies installed"
    
    # Set up environment file
    if [[ ! -f .env ]]; then
        print_info "Creating environment configuration..."
        cp env.example .env
        print_warning "Please edit .env file with your configuration"
    else
        print_info "Environment file already exists"
    fi
    
    # Set up nginx if running as root
    if [[ "$SETUP_NGINX" == "true" ]]; then
        print_info "Setting up nginx configuration..."
        ./setup_nginx.sh
        print_success "Nginx configuration set up"
    fi
    
    # Set permissions on certificates
    print_info "Setting certificate permissions..."
    chmod 600 certs/ca/ca.key
    chmod 600 certs/kme/kme.key
    chmod 600 certs/sae/*.key
    chmod 644 certs/ca/ca.crt
    chmod 644 certs/kme/kme.crt
    chmod 644 certs/sae/*.crt
    print_success "Certificate permissions set"
    
    print_header "Installation Complete"
    print_success "Easy-KMS test package is ready to use"
    echo
    print_info "Next steps:"
    echo "1. Edit .env file with your configuration"
    echo "2. Start the server: ./start_kme.sh"
    echo "3. Run tests: ./test_kme_api.sh"
    echo
    print_warning "If you need nginx setup, run: sudo ./setup_nginx.sh"
}

main "$@"
EOF

    chmod +x "$PACKAGE_DIR/install.sh"
    print_success "Installation script created"
}

# Function to create package archive
create_archive() {
    print_info "Creating package archive..."
    
    local archive_name="${PACKAGE_DIR}.tar.gz"
    
    # Create tar.gz archive
    tar -czf "$archive_name" "$PACKAGE_DIR"
    
    # Get archive size
    local archive_size=$(du -h "$archive_name" | cut -f1)
    
    print_success "Package archive created: $archive_name ($archive_size)"
    
    # Clean up package directory
    rm -rf "$PACKAGE_DIR"
    
    print_info "Package directory cleaned up"
    
    echo
    print_header "Package Creation Complete"
    print_success "Test package: $archive_name"
    print_info "Size: $archive_size"
    echo
    print_info "To deploy on target machine:"
    echo "1. Copy $archive_name to target machine"
    echo "2. Extract: tar -xzf $archive_name"
    echo "3. Run: cd $PACKAGE_DIR && ./install.sh"
    echo "4. Start testing: ./test_kme_api.sh"
}

# Main function
main() {
    print_header "Easy-KMS Test Package Creator"
    
    echo "This script will create a portable test package with all necessary components."
    echo "Package will include:"
    echo "  - All certificates (CA, KME, SAE)"
    echo "  - Source code and configuration"
    echo "  - Test scripts and documentation"
    echo "  - Installation and setup scripts"
    echo
    
    # Check requirements
    check_requirements
    
    # Check certificates
    check_certificates
    
    # Create package
    create_package_structure
    copy_certificates
    copy_source_code
    copy_test_files
    create_package_docs
    create_install_script
    create_archive
    
    print_header "Package Creation Complete"
    print_success "Test package is ready for deployment!"
}

# Run main function
main "$@"
