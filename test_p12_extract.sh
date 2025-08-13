#!/bin/bash

# Test script for P12 extraction functionality
# This script tests the P12 extraction logic used in setup_kme.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to extract P12 file (copied from setup_kme.sh)
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

# Test the extraction function
echo "=========================================="
echo "        P12 Extraction Test"
echo "=========================================="
echo ""

# Check if we have any P12 files to test with
p12_files=$(find . -name "*.p12" 2>/dev/null | head -5)

if [ -z "$p12_files" ]; then
    print_status "No P12 files found for testing"
    print_status "To test P12 extraction, place a P12 file in the current directory"
    print_status "Then run this script again"
    exit 0
fi

echo "Found P12 files:"
echo "$p12_files" | while read -r file; do
    echo "  - $file"
done
echo ""

# Create test directory
test_dir="test_p12_extract"
mkdir -p "$test_dir"

print_status "Testing P12 extraction functionality..."
print_status "This will extract certificates to: $test_dir/"
echo ""

# Test with first P12 file found
first_p12=$(echo "$p12_files" | head -1)
print_status "Testing with: $first_p12"

if extract_p12 "$first_p12" "$test_dir" "test_cert"; then
    print_success "P12 extraction test completed successfully!"
    
    # Show extracted files
    echo ""
    print_status "Extracted files:"
    ls -la "$test_dir/"
    
    # Clean up
    echo ""
    read -p "Remove test files? (y/n): " cleanup
    if [ "$cleanup" = "y" ] || [ "$cleanup" = "Y" ]; then
        rm -rf "$test_dir"
        print_success "Test files removed"
    fi
else
    print_error "P12 extraction test failed"
    exit 1
fi
