# SAE Client Certificate Setup and Integration

This document provides instructions for setting up SAE (Secure Application Entity) client certificates and integrating with the Easy-KMS server according to the ETSI GS QKD 014 specification.

## Overview

SAE clients need certificates to authenticate with the KME server for:
- Key request operations (Master SAE)
- Key retrieval operations (Slave SAE)
- Status queries
- Mutual TLS authentication

## Prerequisites

- Generated CA and SAE certificates (see `README-CA.md`)
- Easy-KMS server running (see `README-KME.md`)
- Client application capable of HTTPS with client certificates
- Linux/Unix environment

## Certificate Locations

### Default Certificate Paths

After following `README-CA.md`, SAE certificates are located at:

```
easy-kme/
├── certs/
│   ├── ca/
│   │   └── ca.crt              # CA certificate
│   └── sae/
│       ├── sae1.key           # SAE1 private key
│       ├── sae1.crt           # SAE1 certificate
│       ├── sae2.key           # SAE2 private key
│       └── sae2.crt           # SAE2 certificate
```

### Certificate Details

| SAE | Common Name (CN) | Certificate | Private Key | Purpose |
|-----|------------------|-------------|-------------|---------|
| SAE1 | `SAE_001` | `certs/sae/sae1.crt` | `certs/sae/sae1.key` | Master/Slave SAE |
| SAE2 | `SAE_002` | `certs/sae/sae2.crt` | `certs/sae/sae2.key` | Master/Slave SAE |

## Certificate Verification

### Verify Certificate Chain

```bash
# Navigate to Easy-KMS directory
cd /home/krich/src/easy-kme

# Verify SAE1 certificate
openssl verify -CAfile certs/ca/ca.crt certs/sae/sae1.crt

# Verify SAE2 certificate
openssl verify -CAfile certs/ca/ca.crt certs/sae/sae2.crt

# Expected output: certs/sae/sae1.crt: OK
```

### Check Certificate Details

```bash
# View SAE1 certificate details
openssl x509 -in certs/sae/sae1.crt -text -noout | grep -A 5 "Subject:"

# View SAE2 certificate details
openssl x509 -in certs/sae/sae2.crt -text -noout | grep -A 5 "Subject:"

# Check certificate expiration
openssl x509 -in certs/sae/sae1.crt -noout -dates
```

## File Permissions

### Set Proper Permissions

```bash
# Set directory permissions
chmod 700 certs/
chmod 700 certs/sae/

# Set private key permissions (restrictive)
chmod 600 certs/sae/sae1.key
chmod 600 certs/sae/sae2.key

# Set certificate permissions (readable)
chmod 644 certs/sae/sae1.crt
chmod 644 certs/sae/sae2.crt
chmod 644 certs/ca/ca.crt

# Verify permissions
ls -la certs/sae/
ls -la certs/ca/ca.crt
```

### Security Notes

- **Private keys** must have 600 permissions (owner read/write only)
- **Certificates** should have 644 permissions (owner read/write, group/others read)
- **Directories** should have 700 permissions (owner read/write/execute only)
- Never share private keys between systems
- Backup certificates securely

## Testing SAE Certificates

### Basic Connectivity Test

```bash
# Test SAE1 connection to KME server
curl -k \
  --cert certs/sae/sae1.crt \
  --key certs/sae/sae1.key \
  --cacert certs/ca/ca.crt \
  https://localhost:8443/health

# Expected response: {"status": "healthy"}
```

### API Endpoint Testing

#### 1. Get Status Test

```bash
# Test status endpoint with SAE1
curl -k \
  --cert certs/sae/sae1.crt \
  --key certs/sae/sae1.key \
  --cacert certs/ca/ca.crt \
  https://localhost:8443/api/v1/keys/status

# Expected response:
# {
#   "status": "operational",
#   "kme_id": "KME_LAB_001",
#   "version": "1.0.0",
#   "key_pool_size": 850,
#   "max_key_pool_size": 1000
# }
```

#### 2. Get Key Test (Master SAE)

```bash
# SAE1 requests keys for SAE2 (Master SAE operation)
curl -k \
  --cert certs/sae/sae1.crt \
  --key certs/sae/sae1.key \
  --cacert certs/ca/ca.crt \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "number": 3,
    "size": 256,
    "additional_slave_sae_ids": ["SAE_003"]
  }' \
  https://localhost:8443/api/v1/keys/SAE_002/enc_keys

# Expected response:
# {
#   "keys": [
#     {
#       "key_id": "uuid-1234-5678-9abc-def0",
#       "key_material": "base64-encoded-key-material",
#       "key_size": 256
#     }
#   ],
#   "key_number": 3,
#   "key_size": 256
# }
```

#### 3. Get Key with Key IDs Test (Slave SAE)

```bash
# SAE2 retrieves keys using key IDs (Slave SAE operation)
curl -k \
  --cert certs/sae/sae2.crt \
  --key certs/sae/sae2.key \
  --cacert certs/ca/ca.crt \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "key_ids": ["uuid-1234-5678-9abc-def0", "uuid-5678-9abc-def0-1234"]
  }' \
  https://localhost:8443/api/v1/keys/SAE_001/dec_keys

# Expected response:
# {
#   "keys": [
#     {
#       "key_id": "uuid-1234-5678-9abc-def0",
#       "key_material": "base64-encoded-key-material",
#       "key_size": 256
#     }
#   ],
#   "key_number": 2,
#   "key_size": 256
# }
```

## Client Integration Examples

### Python Client Example

```python
#!/usr/bin/env python3
"""
Example SAE client for Easy-KMS server.
"""

import requests
import json
import ssl
from pathlib import Path

class SAEClient:
    def __init__(self, sae_id, cert_path, key_path, ca_path, kme_url):
        self.sae_id = sae_id
        self.cert_path = cert_path
        self.key_path = key_path
        self.ca_path = ca_path
        self.kme_url = kme_url
        
        # Configure SSL context
        self.session = requests.Session()
        self.session.verify = ca_path
        self.session.cert = (cert_path, key_path)
    
    def get_status(self):
        """Get KME status."""
        response = self.session.get(f"{self.kme_url}/api/v1/keys/status")
        response.raise_for_status()
        return response.json()
    
    def get_keys(self, slave_sae_id, number=1, size=256, additional_slave_sae_ids=None):
        """Get keys as Master SAE."""
        data = {
            "number": number,
            "size": size
        }
        if additional_slave_sae_ids:
            data["additional_slave_sae_ids"] = additional_slave_sae_ids
        
        response = self.session.post(
            f"{self.kme_url}/api/v1/keys/{slave_sae_id}/enc_keys",
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def get_keys_by_ids(self, master_sae_id, key_ids):
        """Get keys as Slave SAE using key IDs."""
        data = {"key_ids": key_ids}
        
        response = self.session.post(
            f"{self.kme_url}/api/v1/keys/{master_sae_id}/dec_keys",
            json=data
        )
        response.raise_for_status()
        return response.json()

# Usage example
if __name__ == "__main__":
    # Initialize SAE1 client (Master SAE)
    sae1_client = SAEClient(
        sae_id="SAE_001",
        cert_path="certs/sae/sae1.crt",
        key_path="certs/sae/sae1.key",
        ca_path="certs/ca/ca.crt",
        kme_url="https://localhost:8443"
    )
    
    # Initialize SAE2 client (Slave SAE)
    sae2_client = SAEClient(
        sae_id="SAE_002",
        cert_path="certs/sae/sae2.crt",
        key_path="certs/sae/sae2.key",
        ca_path="certs/ca/ca.crt",
        kme_url="https://localhost:8443"
    )
    
    try:
        # Get KME status
        status = sae1_client.get_status()
        print(f"KME Status: {status}")
        
        # SAE1 requests keys for SAE2
        key_response = sae1_client.get_keys("SAE_002", number=2, size=256)
        print(f"Keys generated: {key_response}")
        
        # Extract key IDs
        key_ids = [key["key_id"] for key in key_response["keys"]]
        
        # SAE2 retrieves keys using key IDs
        retrieved_keys = sae2_client.get_keys_by_ids("SAE_001", key_ids)
        print(f"Keys retrieved: {retrieved_keys}")
        
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
```

### Bash Script Example

```bash
#!/bin/bash
# Example SAE client script

# Configuration
KME_URL="https://localhost:8443"
SAE1_CERT="certs/sae/sae1.crt"
SAE1_KEY="certs/sae/sae1.key"
SAE2_CERT="certs/sae/sae2.crt"
SAE2_KEY="certs/sae/sae2.key"
CA_CERT="certs/ca/ca.crt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to make authenticated requests
make_request() {
    local cert=$1
    local key=$2
    local method=$3
    local endpoint=$4
    local data=$5
    
    if [ -n "$data" ]; then
        curl -k -s \
            --cert "$cert" \
            --key "$key" \
            --cacert "$CA_CERT" \
            -X "$method" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$KME_URL$endpoint"
    else
        curl -k -s \
            --cert "$cert" \
            --key "$key" \
            --cacert "$CA_CERT" \
            -X "$method" \
            "$KME_URL$endpoint"
    fi
}

# Test SAE1 as Master SAE
echo -e "${YELLOW}Testing SAE1 as Master SAE...${NC}"

# Get status
echo "Getting KME status..."
status=$(make_request "$SAE1_CERT" "$SAE1_KEY" "GET" "/api/v1/keys/status")
echo -e "${GREEN}Status: $status${NC}"

# Request keys for SAE2
echo "Requesting keys for SAE2..."
key_request='{"number": 2, "size": 256}'
key_response=$(make_request "$SAE1_CERT" "$SAE1_KEY" "POST" "/api/v1/keys/SAE_002/enc_keys" "$key_request")
echo -e "${GREEN}Key response: $key_response${NC}"

# Extract key IDs (requires jq)
if command -v jq &> /dev/null; then
    key_ids=$(echo "$key_response" | jq -r '.keys[].key_id' | tr '\n' ',' | sed 's/,$//')
    echo "Extracted key IDs: $key_ids"
else
    echo -e "${RED}jq not found. Cannot extract key IDs automatically.${NC}"
    key_ids="uuid-1234-5678-9abc-def0,uuid-5678-9abc-def0-1234"
fi

# Test SAE2 as Slave SAE
echo -e "${YELLOW}Testing SAE2 as Slave SAE...${NC}"

# Retrieve keys using key IDs
echo "Retrieving keys using key IDs..."
key_ids_request="{\"key_ids\": [\"$key_ids\"]}"
retrieved_keys=$(make_request "$SAE2_CERT" "$SAE2_KEY" "POST" "/api/v1/keys/SAE_001/dec_keys" "$key_ids_request")
echo -e "${GREEN}Retrieved keys: $retrieved_keys${NC}"

echo -e "${GREEN}All tests completed successfully!${NC}"
```

## Certificate Management

### Certificate Renewal

```bash
# Check certificate expiration
openssl x509 -in certs/sae/sae1.crt -noout -dates

# Generate new certificate (follow README-CA.md steps)
# Replace old certificate
cp certs/sae/sae1_new.crt certs/sae/sae1.crt
chmod 644 certs/sae/sae1.crt

# Restart client applications
```

### Certificate Backup

```bash
# Create backup directory
mkdir -p backup/sae_certs/$(date +%Y%m%d)

# Backup SAE certificates
cp certs/sae/sae1.* backup/sae_certs/$(date +%Y%m%d)/
cp certs/sae/sae2.* backup/sae_certs/$(date +%Y%m%d)/
cp certs/ca/ca.crt backup/sae_certs/$(date +%Y%m%d)/

# Set backup permissions
chmod 600 backup/sae_certs/$(date +%Y%m%d)/*.key
chmod 644 backup/sae_certs/$(date +%Y%m%d)/*.crt
```

### Certificate Distribution

For production environments, distribute certificates securely:

```bash
# Create secure distribution package
tar -czf sae_certs_$(date +%Y%m%d).tar.gz \
    --transform 's|certs/sae/||' \
    certs/sae/sae1.crt certs/sae/sae1.key \
    certs/sae/sae2.crt certs/sae/sae2.key \
    certs/ca/ca.crt

# Set restrictive permissions
chmod 600 sae_certs_$(date +%Y%m%d).tar.gz

# Transfer securely (example with scp)
scp sae_certs_$(date +%Y%m%d).tar.gz user@client-server:/path/to/certs/
```

## Troubleshooting

### Common Certificate Issues

1. **Certificate Verification Failed**
```bash
# Check certificate chain
openssl verify -CAfile certs/ca/ca.crt certs/sae/sae1.crt

# Check certificate details
openssl x509 -in certs/sae/sae1.crt -text -noout
```

2. **Permission Denied**
```bash
# Check file permissions
ls -la certs/sae/

# Fix permissions
chmod 600 certs/sae/sae1.key
chmod 644 certs/sae/sae1.crt
```

3. **SSL Handshake Failed**
```bash
# Test SSL connection manually
openssl s_client -connect localhost:8443 \
    -cert certs/sae/sae1.crt \
    -key certs/sae/sae1.key \
    -CAfile certs/ca/ca.crt
```

4. **Certificate Not Found**
```bash
# Verify certificate paths
find certs/ -name "*.crt" -o -name "*.key"

# Check symbolic links
ls -la certs/
```

### Debug Mode

```bash
# Enable verbose curl output
curl -v -k \
    --cert certs/sae/sae1.crt \
    --key certs/sae/sae1.key \
    --cacert certs/ca/ca.crt \
    https://localhost:8443/api/v1/keys/status

# Enable SSL debug
export SSLKEYLOGFILE=/tmp/ssl.log
# Then run client and check /tmp/ssl.log
```

### Log Analysis

```bash
# Check KME server logs for SAE activity
grep "SAE_001" logs/kme.log

# Check for authentication errors
grep "authentication" logs/kme.log

# Monitor real-time activity
tail -f logs/kme.log | grep -E "(SAE_001|SAE_002)"
```

## Security Best Practices

### Certificate Security

1. **Private Key Protection**
   - Store private keys in secure locations
   - Use hardware security modules (HSM) for production
   - Never share private keys between systems
   - Set restrictive file permissions (600)

2. **Certificate Validation**
   - Verify certificate chain before use
   - Check certificate expiration dates
   - Validate certificate purposes and extensions
   - Monitor for certificate revocation

3. **Network Security**
   - Use secure channels for certificate distribution
   - Implement certificate pinning if possible
   - Monitor for certificate misuse
   - Regular security audits

### Client Security

1. **Application Security**
   - Validate all API responses
   - Implement proper error handling
   - Use secure random number generation
   - Protect key material in memory

2. **System Security**
   - Keep systems updated
   - Use firewalls and network segmentation
   - Monitor system logs
   - Implement intrusion detection

## Integration Checklist

- [ ] Certificates generated and verified
- [ ] File permissions set correctly
- [ ] Basic connectivity test passed
- [ ] API endpoints tested
- [ ] Error handling implemented
- [ ] Logging configured
- [ ] Security measures in place
- [ ] Backup procedures established
- [ ] Monitoring configured
- [ ] Documentation updated

## Support

For SAE certificate issues:

1. Check certificate validity and permissions
2. Verify network connectivity to KME server
3. Review KME server logs for authentication errors
4. Test with provided examples
5. Check troubleshooting section above
6. Create an issue on the GitHub repository

## References

- `README-CA.md` - Certificate Authority setup
- `README-KME.md` - KME server configuration
- ETSI GS QKD 014 specification
- OpenSSL documentation
- Client application documentation 