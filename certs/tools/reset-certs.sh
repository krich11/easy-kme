#!/bin/bash

# Easy-KMS Certificate Reset Script
# Clears out all certificate directories and files

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CERT_ROOT="$(dirname "$SCRIPT_DIR")"

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to safely remove directory contents
remove_directory_contents() {
    local dir="$1"
    local dir_name="$2"
    
    if [[ -d "$dir" ]]; then
        print_warning "Clearing $dir_name directory..."
        
        # Remove all files and subdirectories
        find "$dir" -mindepth 1 -delete 2>/dev/null || true
        
        print_success "Cleared $dir_name directory"
    else
        print_warning "$dir_name directory does not exist, skipping"
    fi
}

# Function to remove specific files
remove_file() {
    local file="$1"
    local file_name="$2"
    
    if [[ -f "$file" ]]; then
        rm -f "$file"
        print_success "Removed $file_name"
    else
        print_warning "$file_name does not exist, skipping"
    fi
}

main() {
    print_header "Easy-KMS Certificate Reset"
    
    echo "This script will remove all certificates and related files."
    echo "This action cannot be undone!"
    echo
    
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Reset cancelled"
        exit 0
    fi
    
    echo
    
    # Clear CA directory
    remove_directory_contents "$CERT_ROOT/ca" "CA"
    
    # Clear KME directory
    remove_directory_contents "$CERT_ROOT/kme" "KME"
    
    # Clear SAE directory
    remove_directory_contents "$CERT_ROOT/sae" "SAE"
    
    # Remove specific files in certs root
    remove_file "$CERT_ROOT/openssl.conf" "OpenSSL configuration"
    remove_file "$CERT_ROOT/kme_cert.pem" "KME certificate symlink"
    remove_file "$CERT_ROOT/kme_key.pem" "KME private key symlink"
    remove_file "$CERT_ROOT/ca_cert.pem" "CA certificate symlink"
    
    # Remove any .pem files that might be in the root
    if [[ -d "$CERT_ROOT" ]]; then
        find "$CERT_ROOT" -maxdepth 1 -name "*.pem" -delete 2>/dev/null || true
    fi
    
    print_header "Certificate Reset Complete"
    print_success "All certificates and related files have been removed"
    echo
    print_warning "To recreate certificates, run:"
    echo "  ./certs/tools/create-ca.sh"
    echo "  ./certs/tools/create-kme.sh"
    echo "  ./certs/tools/create-sae-test-certs.sh"
    echo
}

# Run main function
main "$@"
