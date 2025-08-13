#!/bin/bash

# Easy-KMS CA Manager Launcher

echo "Easy-KMS CA Manager"
echo "=================="

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed"
    exit 1
fi

# Check if cryptography is installed
if ! python3 -c "import cryptography" &> /dev/null; then
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
fi

# Run the CA manager
python3 ca_manager.py
