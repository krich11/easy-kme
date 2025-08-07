# Certificate Authority (CA) Setup for Easy-KMS

This document provides instructions for setting up a Certificate Authority (CA) and generating certificates for the Easy-KMS server and SAE clients.

## Overview

The Easy-KMS server uses mutual TLS (mTLS) authentication, requiring:
- A Certificate Authority (CA) to sign certificates
- KME server certificate and private key
- SAE client certificates and private keys

## Prerequisites

- OpenSSL (version 1.1.1 or later)
- Linux/Unix environment
- Proper file permissions for security

## Directory Structure

```
easy-kme/
├── certs/                    # Certificate storage directory
│   ├── ca/                  # CA files
│   │   ├── ca.key          # CA private key
│   │   ├── ca.crt          # CA certificate
│   │   └── ca.srl          # CA serial number file
│   ├── kme/                 # KME server certificates
│   │   ├── kme.key         # KME private key
│   │   └── kme.crt         # KME certificate
│   └── sae/                 # SAE client certificates
│       ├── sae1.key        # SAE1 private key
│       ├── sae1.crt        # SAE1 certificate
│       ├── sae2.key        # SAE2 private key
│       └── sae2.crt        # SAE2 certificate
```

## Step 1: Create Certificate Directory Structure

```bash
# Navigate to the Easy-KMS project directory
cd /home/krich/src/easy-kme

# Create certificate directories
mkdir -p certs/ca certs/kme certs/sae

# Set proper permissions
chmod 700 certs
chmod 700 certs/ca
chmod 700 certs/kme
chmod 700 certs/sae
```

## Step 2: Generate CA Private Key

```bash
# Generate CA private key (RSA 4096 bits)
openssl genrsa -out certs/ca/ca.key 4096

# Set restrictive permissions on CA private key
chmod 600 certs/ca/ca.key
```

## Step 3: Generate CA Certificate

```bash
# Create CA certificate configuration
cat > certs/ca/ca.conf << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = California
L = San Francisco
O = Easy-KMS Lab
OU = QKD Development
CN = Easy-KMS Root CA

[v3_req]
basicConstraints = CA:TRUE
keyUsage = keyCertSign, cRLSign
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer:always
EOF

# Generate CA certificate
openssl req -new -x509 -days 3650 -key certs/ca/ca.key -out certs/ca/ca.crt -config certs/ca/ca.conf

# Set proper permissions on CA certificate
chmod 644 certs/ca/ca.crt

# Create serial number file
echo "01" > certs/ca/ca.srl
chmod 644 certs/ca/ca.srl
```

## Step 4: Verify CA Certificate

```bash
# Verify CA certificate
openssl x509 -in certs/ca/ca.crt -text -noout

# Check certificate details
openssl x509 -in certs/ca/ca.crt -noout -subject -issuer -dates
```

## Step 5: Create OpenSSL Configuration for Certificate Generation

```bash
# Create main OpenSSL configuration
cat > certs/openssl.conf << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = California
L = San Francisco
O = Easy-KMS Lab
OU = QKD Development

[v3_req]
basicConstraints = CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = clientAuth, serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = *.local
IP.1 = 127.0.0.1
IP.2 = ::1

[ca]
default_ca = CA_default

[CA_default]
dir = ./ca
certs = \$dir
crl_dir = \$dir
database = \$dir/index.txt
new_certs_dir = \$dir/newcerts
certificate = \$dir/ca.crt
serial = \$dir/ca.srl
crl = \$dir/crl.pem
private_key = \$dir/ca.key
RANDFILE = \$dir/private/.rand
x509_extensions = usr_cert
name_opt = ca_default
cert_opt = ca_default
default_days = 365
default_crl_days = 30
default_md = sha256
preserve = no
policy = policy_strict

[policy_strict]
countryName = match
stateOrProvinceName = match
organizationName = match
organizationalUnitName = optional
commonName = supplied
emailAddress = optional

[usr_cert]
basicConstraints = CA:FALSE
nsCertType = client, email
nsComment = "OpenSSL Generated Certificate"
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid,issuer
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
extendedKeyUsage = clientAuth, emailProtection
EOF

# Create CA index file
touch certs/ca/index.txt
chmod 644 certs/ca/index.txt
```

## Step 6: Generate KME Server Certificate

```bash
# Generate KME private key
openssl genrsa -out certs/kme/kme.key 2048
chmod 600 certs/kme/kme.key

# Create KME certificate signing request
cat > certs/kme/kme.conf << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = California
L = San Francisco
O = Easy-KMS Lab
OU = QKD Development
CN = KME_LAB_001

[v3_req]
basicConstraints = CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = kme.local
DNS.3 = *.local
IP.1 = 127.0.0.1
IP.2 = ::1
IP.3 = 0.0.0.0
EOF

# Generate KME certificate signing request
openssl req -new -key certs/kme/kme.key -out certs/kme/kme.csr -config certs/kme/kme.conf

# Sign KME certificate with CA
openssl ca -batch -config certs/openssl.conf -in certs/kme/kme.csr -out certs/kme/kme.crt

# Set proper permissions
chmod 644 certs/kme/kme.crt

# Clean up CSR
rm certs/kme/kme.csr
```

## Step 7: Generate SAE Client Certificates

### Generate SAE1 Certificate

```bash
# Generate SAE1 private key
openssl genrsa -out certs/sae/sae1.key 2048
chmod 600 certs/sae/sae1.key

# Create SAE1 certificate signing request
cat > certs/sae/sae1.conf << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = California
L = San Francisco
O = Easy-KMS Lab
OU = QKD Development
CN = SAE_001

[v3_req]
basicConstraints = CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = clientAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = sae1.local
DNS.2 = localhost
IP.1 = 127.0.0.1
IP.2 = ::1
EOF

# Generate SAE1 certificate signing request
openssl req -new -key certs/sae/sae1.key -out certs/sae/sae1.csr -config certs/sae/sae1.conf

# Sign SAE1 certificate with CA
openssl ca -batch -config certs/openssl.conf -in certs/sae/sae1.csr -out certs/sae/sae1.crt

# Set proper permissions
chmod 644 certs/sae/sae1.crt

# Clean up CSR
rm certs/sae/sae1.csr
```

### Generate SAE2 Certificate

```bash
# Generate SAE2 private key
openssl genrsa -out certs/sae/sae2.key 2048
chmod 600 certs/sae/sae2.key

# Create SAE2 certificate signing request
cat > certs/sae/sae2.conf << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = California
L = San Francisco
O = Easy-KMS Lab
OU = QKD Development
CN = SAE_002

[v3_req]
basicConstraints = CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = clientAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = sae2.local
DNS.2 = localhost
IP.1 = 127.0.0.1
IP.2 = ::1
EOF

# Generate SAE2 certificate signing request
openssl req -new -key certs/sae/sae2.key -out certs/sae/sae2.csr -config certs/sae/sae2.conf

# Sign SAE2 certificate with CA
openssl ca -batch -config certs/openssl.conf -in certs/sae/sae2.csr -out certs/sae/sae2.crt

# Set proper permissions
chmod 644 certs/sae/sae2.crt

# Clean up CSR
rm certs/sae/sae2.csr
```

## Step 8: Verify Certificates

```bash
# Verify KME certificate
openssl verify -CAfile certs/ca/ca.crt certs/kme/kme.crt

# Verify SAE1 certificate
openssl verify -CAfile certs/ca/ca.crt certs/sae/sae1.crt

# Verify SAE2 certificate
openssl verify -CAfile certs/ca/ca.crt certs/sae/sae2.crt

# Check certificate details
echo "=== KME Certificate ==="
openssl x509 -in certs/kme/kme.crt -text -noout | grep -A 5 "Subject:"

echo "=== SAE1 Certificate ==="
openssl x509 -in certs/sae/sae1.crt -text -noout | grep -A 5 "Subject:"

echo "=== SAE2 Certificate ==="
openssl x509 -in certs/sae/sae2.crt -text -noout | grep -A 5 "Subject:"
```

## Step 9: Create Certificate Bundle for Easy-KMS

```bash
# Create symbolic links for Easy-KMS configuration
ln -sf certs/kme/kme.crt certs/kme_cert.pem
ln -sf certs/kme/kme.key certs/kme_key.pem
ln -sf certs/ca/ca.crt certs/ca_cert.pem

# Set proper permissions on symlinks
chmod 644 certs/kme_cert.pem
chmod 644 certs/ca_cert.pem
chmod 600 certs/kme_key.pem
```

## Step 10: Final Security Check

```bash
# Verify directory permissions
ls -la certs/
ls -la certs/ca/
ls -la certs/kme/
ls -la certs/sae/

# Verify file permissions
find certs/ -name "*.key" -exec ls -la {} \;
find certs/ -name "*.crt" -exec ls -la {} \;
find certs/ -name "*.pem" -exec ls -la {} \;
```

## Certificate Locations Summary

| Certificate Type | Private Key | Certificate | Default Location |
|------------------|-------------|-------------|------------------|
| CA | `certs/ca/ca.key` | `certs/ca/ca.crt` | `certs/ca/` |
| KME Server | `certs/kme/kme.key` | `certs/kme/kme.crt` | `certs/kme/` |
| SAE1 Client | `certs/sae/sae1.key` | `certs/sae/sae1.crt` | `certs/sae/` |
| SAE2 Client | `certs/sae/sae2.key` | `certs/sae/sae2.crt` | `certs/sae/` |

## Easy-KMS Configuration Paths

The Easy-KMS server expects certificates at these locations (configured in `.env`):

- **KME Certificate**: `./certs/kme_cert.pem`
- **KME Private Key**: `./certs/kme_key.pem`
- **CA Certificate**: `./certs/ca_cert.pem`

## Security Notes

1. **Private Keys**: Always set permissions to 600 (owner read/write only)
2. **Certificates**: Set permissions to 644 (owner read/write, group/others read)
3. **Directories**: Set permissions to 700 (owner read/write/execute only)
4. **CA Private Key**: Keep secure and backup - compromise affects all certificates
5. **Certificate Expiry**: Monitor certificate expiration dates
6. **Revocation**: Implement certificate revocation if needed

## Troubleshooting

### Common Issues

1. **Permission Denied**: Ensure proper file permissions
2. **Certificate Verification Failed**: Check CA certificate path and validity
3. **OpenSSL Errors**: Verify OpenSSL version and configuration syntax
4. **Path Issues**: Ensure all paths are absolute or relative to project root

### Verification Commands

```bash
# Check OpenSSL version
openssl version

# Verify certificate chain
openssl verify -CAfile certs/ca/ca.crt certs/kme/kme.crt

# Check certificate expiration
openssl x509 -in certs/kme/kme.crt -noout -dates

# Test SSL connection (if server is running)
openssl s_client -connect localhost:8443 -cert certs/sae/sae1.crt -key certs/sae/sae1.key -CAfile certs/ca/ca.crt
```

## Next Steps

After completing this CA setup:

1. Configure the Easy-KMS server using the generated certificates
2. Test the server with SAE clients
3. Refer to `README-KME.md` for server configuration
4. Refer to `README-SAE-CERT.md` for SAE client setup 