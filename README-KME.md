# Easy-KMS Server Setup and Configuration

This document provides instructions for setting up, configuring, and running the Easy-KMS server according to the ETSI GS QKD 014 specification.

## Overview

The Easy-KMS server implements the ETSI GS QKD 014 Key Management Entity (KME) with:
- Three REST API endpoints for key delivery
- Mutual TLS (mTLS) authentication
- File-based key storage
- Certificate-based SAE authentication

## Prerequisites

- Python 3.8 or higher
- OpenSSL for certificate management
- Generated certificates (see `README-CA.md`)
- Linux/Unix environment

## Installation

### Step 1: Clone and Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/easy-kms.git
cd easy-kms

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Certificate Setup

Follow the instructions in `README-CA.md` to generate the required certificates:

- CA certificate and private key
- KME server certificate and private key
- SAE client certificates and private keys

### Step 3: Environment Configuration

```bash
# Copy environment template
cp env.example .env

# Edit configuration
nano .env
```

## Configuration

### Environment Variables (.env file)

```bash
# KME Server Configuration
KME_HOST=0.0.0.0
KME_PORT=8443
KME_ID=KME_LAB_001

# Certificate Configuration
KME_CERT_PATH=./certs/kme_cert.pem
KME_KEY_PATH=./certs/kme_key.pem
CA_CERT_PATH=./certs/ca_cert.pem

# Storage Configuration
DATA_DIR=./data
KEY_POOL_SIZE=1000
KEY_SIZE=256

# Security Settings
REQUIRE_CLIENT_CERT=true
VERIFY_CA=true

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=./logs/kme.log

# API Configuration
API_VERSION=v1
API_PREFIX=/api
```

### Configuration Details

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `KME_HOST` | Server bind address | `0.0.0.0` | Yes |
| `KME_PORT` | Server port | `8443` | Yes |
| `KME_ID` | KME identifier | `KME_LAB_001` | Yes |
| `KME_CERT_PATH` | KME certificate path | `./certs/kme_cert.pem` | Yes |
| `KME_KEY_PATH` | KME private key path | `./certs/kme_key.pem` | Yes |
| `CA_CERT_PATH` | CA certificate path | `./certs/ca_cert.pem` | Yes |
| `DATA_DIR` | Data storage directory | `./data` | Yes |
| `KEY_POOL_SIZE` | Maximum key pool size | `1000` | Yes |
| `KEY_SIZE` | Default key size (bits) | `256` | Yes |
| `REQUIRE_CLIENT_CERT` | Require client certificates | `true` | Yes |
| `VERIFY_CA` | Verify CA certificate | `true` | Yes |
| `LOG_LEVEL` | Logging level | `INFO` | No |
| `LOG_FILE` | Log file path | `./logs/kme.log` | No |

## Directory Structure

```
easy-kme/
├── .env                      # Environment configuration
├── certs/                    # Certificate storage
│   ├── kme_cert.pem         # KME certificate (symlink)
│   ├── kme_key.pem          # KME private key (symlink)
│   └── ca_cert.pem          # CA certificate (symlink)
├── data/                     # File-based storage
│   ├── keys.json            # Key pool storage
│   ├── sessions.json        # Active sessions
│   ├── sae_registry.json    # SAE registry
│   └── key_pool.json        # Key pool status
├── logs/                     # Log files
│   └── kme.log              # Server logs
├── src/                      # Source code
└── run.py                   # Server launcher
```

## Running the Server

### Development Mode

```bash
# Activate virtual environment
source venv/bin/activate

# Run server
python run.py
```

### Production Mode

```bash
# Create systemd service (optional)
sudo nano /etc/systemd/system/easy-kms.service
```

```ini
[Unit]
Description=Easy-KMS Server
After=network.target

[Service]
Type=simple
User=krich
WorkingDirectory=/home/krich/src/easy-kme
Environment=PATH=/home/krich/src/easy-kme/venv/bin
ExecStart=/home/krich/src/easy-kme/venv/bin/python run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable easy-kms
sudo systemctl start easy-kms
sudo systemctl status easy-kms
```

## API Endpoints

The Easy-KMS server implements three ETSI GS QKD 014 endpoints:

### 1. Get Status
```
GET /api/v1/keys/status
```

**Response:**
```json
{
  "status": "operational",
  "kme_id": "KME_LAB_001",
  "version": "1.0.0",
  "key_pool_size": 850,
  "max_key_pool_size": 1000
}
```

### 2. Get Key (Master SAE)
```
POST /api/v1/keys/{slave_sae_id}/enc_keys
```

**Request Body:**
```json
{
  "number": 5,
  "size": 256,
  "additional_slave_sae_ids": ["SAE_003"]
}
```

**Response:**
```json
{
  "keys": [
    {
      "key_id": "uuid-1234-5678-9abc-def0",
      "key_material": "base64-encoded-key-material",
      "key_size": 256
    }
  ],
  "key_number": 5,
  "key_size": 256
}
```

### 3. Get Key with Key IDs (Slave SAE)
```
POST /api/v1/keys/{master_sae_id}/dec_keys
```

**Request Body:**
```json
{
  "key_ids": ["uuid-1234-5678-9abc-def0", "uuid-5678-9abc-def0-1234"]
}
```

**Response:**
```json
{
  "keys": [
    {
      "key_id": "uuid-1234-5678-9abc-def0",
      "key_material": "base64-encoded-key-material",
      "key_size": 256
    }
  ],
  "key_number": 2,
  "key_size": 256
}
```

## Testing the Server

### Health Check

```bash
# Test basic connectivity (without mTLS)
curl -k https://localhost:8443/health
```

### API Documentation

Access the interactive API documentation:
- Swagger UI: https://localhost:8443/docs
- ReDoc: https://localhost:8443/redoc

### Certificate Testing

```bash
# Test with SAE1 certificate
curl -k \
  --cert certs/sae/sae1.crt \
  --key certs/sae/sae1.key \
  --cacert certs/ca/ca.crt \
  https://localhost:8443/api/v1/keys/status

# Test key generation (Master SAE)
curl -k \
  --cert certs/sae/sae1.crt \
  --key certs/sae/sae1.key \
  --cacert certs/ca/ca.crt \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"number": 2, "size": 256}' \
  https://localhost:8443/api/v1/keys/SAE_002/enc_keys
```

## Monitoring and Logging

### Log Files

```bash
# View server logs
tail -f logs/kme.log

# View system logs (if using systemd)
sudo journalctl -u easy-kms -f
```

### Key Pool Monitoring

```bash
# Check key pool status
cat data/key_pool.json

# Check registered SAEs
cat data/sae_registry.json

# Check active sessions
cat data/sessions.json
```

### Performance Monitoring

```bash
# Monitor server process
ps aux | grep easy-kms

# Monitor network connections
netstat -tlnp | grep 8443

# Monitor disk usage
du -sh data/
```

## Security Considerations

### File Permissions

```bash
# Set proper permissions
chmod 700 certs/
chmod 600 certs/kme_key.pem
chmod 644 certs/kme_cert.pem certs/ca_cert.pem
chmod 700 data/
chmod 600 data/*.json
chmod 755 logs/
chmod 644 logs/kme.log
```

### Network Security

1. **Firewall Configuration**
```bash
# Allow HTTPS traffic
sudo ufw allow 8443/tcp

# Restrict access to specific IPs (if needed)
sudo ufw allow from 192.168.1.0/24 to any port 8443
```

2. **SSL/TLS Configuration**
- Server uses TLS 1.2/1.3
- Mutual authentication required
- Certificate verification enabled

### Access Control

1. **SAE Registration**: SAEs are automatically registered on first connection
2. **Key Authorization**: Only authorized SAEs can access specific keys
3. **Session Management**: Keys are tied to specific master-slave SAE pairs

## Troubleshooting

### Common Issues

1. **Certificate Errors**
```bash
# Verify certificate paths
ls -la certs/

# Check certificate validity
openssl verify -CAfile certs/ca_cert.pem certs/kme_cert.pem

# Test SSL connection
openssl s_client -connect localhost:8443 -cert certs/sae/sae1.crt -key certs/sae/sae1.key -CAfile certs/ca_cert.pem
```

2. **Permission Errors**
```bash
# Check file permissions
find certs/ data/ -type f -exec ls -la {} \;

# Fix permissions if needed
chmod 600 certs/kme_key.pem
chmod 644 certs/kme_cert.pem certs/ca_cert.pem
```

3. **Port Already in Use**
```bash
# Check what's using the port
sudo netstat -tlnp | grep 8443

# Kill process if needed
sudo kill -9 <PID>
```

4. **Key Pool Issues**
```bash
# Check key pool status
cat data/key_pool.json

# Reset key pool if needed
rm data/keys.json data/key_pool.json
# Restart server to regenerate
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with debug output
python run.py
```

### Log Analysis

```bash
# Search for errors
grep ERROR logs/kme.log

# Search for specific SAE activity
grep "SAE_001" logs/kme.log

# Monitor real-time activity
tail -f logs/kme.log | grep -E "(INFO|ERROR|WARNING)"
```

## Backup and Recovery

### Data Backup

```bash
# Create backup directory
mkdir -p backup/$(date +%Y%m%d)

# Backup certificates
cp -r certs/ backup/$(date +%Y%m%d)/

# Backup data
cp -r data/ backup/$(date +%Y%m%d)/

# Backup configuration
cp .env backup/$(date +%Y%m%d)/
```

### Recovery

```bash
# Restore from backup
cp -r backup/20231201/certs/ ./
cp -r backup/20231201/data/ ./
cp backup/20231201/.env ./

# Set proper permissions
chmod 600 certs/kme_key.pem
chmod 644 certs/kme_cert.pem certs/ca_cert.pem
chmod 600 data/*.json
```

## Performance Tuning

### Key Pool Optimization

```bash
# Increase key pool size for high throughput
KEY_POOL_SIZE=5000

# Adjust key size based on requirements
KEY_SIZE=128  # For faster generation
KEY_SIZE=512  # For higher security
```

### Server Optimization

```bash
# Increase worker processes (if using gunicorn)
gunicorn --workers 4 --worker-class uvicorn.workers.UvicornWorker src.main:app

# Enable connection pooling
# Add to .env: CONNECTION_POOL_SIZE=100
```

## Integration with SAE Clients

For information on integrating SAE clients with the KME server, see:
- `README-SAE-CERT.md` - SAE client certificate setup
- API documentation at `/docs` endpoint
- Example client implementations in the `examples/` directory

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review server logs in `logs/kme.log`
3. Check certificate validity and permissions
4. Verify network connectivity and firewall settings
5. Create an issue on the GitHub repository 