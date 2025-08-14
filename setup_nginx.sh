#!/bin/bash

# Easy-KME Nginx Setup Script
# Sets up nginx site configuration for Easy-KME

set -e

echo "=== Setting up nginx site configuration for Easy-KME ==="

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo "This script needs to be run with sudo"
    exit 1
fi

# Check if nginx is installed
if ! command -v nginx &> /dev/null; then
    echo "ERROR: nginx is not installed. Please install nginx first:"
    echo "  sudo apt update && sudo apt install nginx"
    exit 1
fi

# Check if nginx.conf exists
if [ ! -f "./nginx.conf" ]; then
    echo "ERROR: nginx.conf not found in current directory"
    exit 1
fi

# Backup existing configuration if it exists
if [ -f "/etc/nginx/sites-available/easy-kme" ]; then
    echo "Backing up existing easy-kme configuration..."
    cp /etc/nginx/sites-available/easy-kme /etc/nginx/sites-available/easy-kme.backup.$(date +%Y%m%d_%H%M%S)
fi

# Copy nginx config to sites-available
echo "Installing nginx site configuration..."
cp nginx.conf /etc/nginx/sites-available/easy-kme

# Remove existing symlink if present
if [ -L "/etc/nginx/sites-enabled/easy-kme" ]; then
    echo "Removing existing symlink..."
    rm /etc/nginx/sites-enabled/easy-kme
fi

# Create symlink in sites-enabled
echo "Creating symlink in sites-enabled..."
ln -s /etc/nginx/sites-available/easy-kme /etc/nginx/sites-enabled/

# Test nginx configuration
echo "Testing nginx configuration..."
if nginx -t; then
    echo "✓ nginx configuration test passed"
else
    echo "✗ nginx configuration test failed"
    echo "Removing problematic configuration..."
    rm -f /etc/nginx/sites-enabled/easy-kme
    exit 1
fi

echo ""
echo "=== nginx site configuration installed successfully ==="
echo "Site configuration: /etc/nginx/sites-available/easy-kme"
echo "Symlink: /etc/nginx/sites-enabled/easy-kme"
echo ""
echo "To enable the site, run: sudo systemctl reload nginx"
echo "To disable the site, run: sudo rm /etc/nginx/sites-enabled/easy-kme && sudo systemctl reload nginx" 
