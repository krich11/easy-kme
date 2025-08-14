#!/bin/bash

# Easy-KME Startup Script
# Starts nginx (mTLS termination) and FastAPI application

set -e

echo "=== Starting Easy-KME with nginx mTLS termination ==="

# Check if nginx is installed
if ! command -v nginx &> /dev/null; then
    echo "ERROR: nginx is not installed. Please install nginx first."
    exit 1
fi

# Check if certificates exist
if [ ! -f "./certs/kme_cert.pem" ] || [ ! -f "./certs/kme_key.pem" ] || [ ! -f "./certs/ca_cert.pem" ]; then
    echo "ERROR: Required certificates not found in ./certs/"
    echo "Please ensure the following files exist:"
    echo "  - ./certs/kme_cert.pem"
    echo "  - ./certs/kme_key.pem" 
    echo "  - ./certs/ca_cert.pem"
    exit 1
fi

# Check if nginx site is configured
if [ ! -L "/etc/nginx/sites-enabled/easy-kme" ]; then
    echo "ERROR: nginx site not configured. Please run ./setup_nginx.sh first"
    exit 1
fi

# Test nginx configuration
echo "Testing nginx configuration..."
if ! sudo nginx -t; then
    echo "ERROR: nginx configuration test failed"
    exit 1
fi

# Kill any existing processes
echo "Stopping any existing processes..."
pkill -f "python run.py" || true
sudo systemctl stop nginx || true
sleep 2

# Start FastAPI application
echo "Starting FastAPI application on port 8000..."
source venv/bin/activate
python run.py &
FASTAPI_PID=$!

# Wait for FastAPI to start
echo "Waiting for FastAPI to start..."
sleep 3

# Test if FastAPI is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "ERROR: FastAPI failed to start"
    kill $FASTAPI_PID 2>/dev/null || true
    exit 1
fi

echo "FastAPI is running on port 8000"

# Start nginx
echo "Starting nginx with mTLS on port 8443..."
sudo systemctl start nginx

# Wait for nginx to start
sleep 2

# Test if nginx is running
if ! curl -k -s https://localhost:8443/health > /dev/null; then
    echo "ERROR: nginx failed to start"
    kill $FASTAPI_PID 2>/dev/null || true
    sudo systemctl stop nginx || true
    exit 1
fi

echo "nginx is running on port 8443"

echo "=== Easy-KME is ready ==="
echo "  - FastAPI: http://localhost:8000"
echo "  - nginx (mTLS): https://localhost:8443"
echo ""
echo "Press Ctrl+C to stop"

# Wait for interrupt
trap 'echo "Shutting down..."; kill $FASTAPI_PID 2>/dev/null || true; sudo systemctl stop nginx || true; exit 0' INT
wait 
