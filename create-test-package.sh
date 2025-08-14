#!/bin/bash

# Easy-KMS Test Package Creator - Bare Bones Version
# Creates a simple tar.gz with test files

set -e

# Configuration
PACKAGE_NAME="easy-kms-test-package"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
ARCHIVE_NAME="${PACKAGE_NAME}-${TIMESTAMP}.tar.gz"

echo "Creating test package: $ARCHIVE_NAME"

# Create tar.gz with test files only
tar -czf "$ARCHIVE_NAME" \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='venv' \
    --exclude='.git' \
    --exclude='logs' \
    --exclude='.pytest_cache' \
    --exclude='certs/ca/ca.conf' \
    --exclude='certs/ca/ca.srl' \
    --exclude='certs/ca/ca.srl.old' \
    --exclude='certs/ca/index.txt' \
    --exclude='certs/ca/index.txt.old' \
    --exclude='certs/ca/index.txt.attr' \
    --exclude='certs/ca/index.txt.attr.old' \
    test_kme_api.sh \
    certs/ \
    TESTING.md \
    ETSI_WORKFLOW.md

echo "Package created: $ARCHIVE_NAME"
echo "Size: $(du -h "$ARCHIVE_NAME" | cut -f1)"
