#!/bin/bash

# Easy-KMS Test Package Creator - Bare Bones Version
# Creates a simple tar.gz with test files

set -e

# Configuration
PACKAGE_NAME="easy-kms-test-package"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
ARCHIVE_NAME="${PACKAGE_NAME}-${TIMESTAMP}.tar.gz"

echo "Creating test package: $ARCHIVE_NAME"

# Create tar.gz with necessary files
tar -czf "$ARCHIVE_NAME" \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='venv' \
    --exclude='.git' \
    --exclude='logs' \
    --exclude='.pytest_cache' \
    test_kme_api.sh \
    certs/ \
    src/ \
    requirements.txt \
    env.example \
    nginx.conf \
    start_kme.sh \
    setup_nginx.sh \
    TESTING.md \
    ETSI_WORKFLOW.md \
    data/ \
    tests/

echo "Package created: $ARCHIVE_NAME"
echo "Size: $(du -h "$ARCHIVE_NAME" | cut -f1)"
