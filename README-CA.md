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

First, navigate to the Easy-KMS project directory:

```bash
cd /home/krich/src/easy-kme
```

Create the certificate directory structure. This organizes certificates by type (CA, KME, SAE):

```bash
mkdir -p certs/ca certs/kme certs/sae
```

Set restrictive permissions on all certificate directories. This ensures only the owner can access these directories:

```bash
chmod 700 certs
chmod 700 certs/ca
chmod 700 certs/kme
chmod 700 certs/sae
```

**What this does:** Creates a secure directory structure where:
- `certs/ca/` stores the Certificate Authority files
- `certs/kme/` stores the KME server certificates
- `certs/sae/` stores the SAE client certificates
- All directories have 700 permissions (owner read/write/execute only)

## Step 2: Generate CA Private Key

Generate a 4096-bit RSA private key for the Certificate Authority. This is the root key that will be used to sign all other certificates:

```bash
openssl genrsa -out certs/ca/ca.key 4096
```

**What this does:** Creates a cryptographically secure RSA private key with 4096 bits of entropy. This key will be used to sign all certificates in the PKI hierarchy.

Set restrictive permissions on the CA private key. This is critical for security - only the owner should be able to read or write this file:

```bash
chmod 600 certs/ca/ca.key
```

**What this does:** Sets file permissions to 600 (owner read/write only). This prevents other users from accessing the private key, which would compromise the entire certificate hierarchy.

## Step 3: Generate CA Certificate

Create a configuration file for the CA certificate. This defines the certificate's identity and extensions:

```bash
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
```

**What this does:** Creates a configuration file that defines:
- The CA's identity (country, state, organization, etc.)
- Certificate extensions that mark this as a CA certificate
- Key usage constraints (can only sign other certificates)
- Subject and authority key identifiers for certificate chaining

Generate the CA certificate using the private key and configuration:

```bash
openssl req -new -x509 -days 3650 -key certs/ca/ca.key -out certs/ca/ca.crt -config certs/ca/ca.conf
```

**What this does:** Creates a self-signed CA certificate valid for 10 years (3650 days). This certificate will be used to verify all other certificates in the system.

Set readable permissions on the CA certificate since it needs to be distributed to clients:

```bash
chmod 644 certs/ca/ca.crt
```

**What this does:** Sets file permissions to 644 (owner read/write, group/others read). The CA certificate is public and needs to be readable by clients.

Create a serial number file for certificate numbering:

```bash
echo "01" > certs/ca/ca.srl
chmod 644 certs/ca/ca.srl
```

**What this does:** Initializes the serial number counter starting at 01. Each certificate signed by this CA will get a unique serial number.

## Step 4: Verify CA Certificate

Display the full certificate details to verify it was created correctly:

```bash
openssl x509 -in certs/ca/ca.crt -text -noout
```

**What this does:** Shows the complete certificate including all extensions, validity periods, and key information. This helps verify the certificate was generated with the correct parameters.

Check the essential certificate information (subject, issuer, and validity dates):

```bash
openssl x509 -in certs/ca/ca.crt -noout -subject -issuer -dates
```

**What this does:** Displays a concise summary showing:
- Subject: The CA's identity
- Issuer: Should be the same as subject (self-signed)
- Dates: Certificate validity period (notBefore and notAfter)

## Step 5: Create OpenSSL Configuration for Certificate Generation

Create a comprehensive OpenSSL configuration file that will be used for generating all certificates:

```bash
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
```

**What this does:** Creates a master configuration file that defines:
- Default certificate parameters (country, organization, etc.)
- Certificate extensions for client and server authentication
- Subject Alternative Names for localhost and local domains
- CA configuration for signing certificates
- Strict policy for certificate generation
- Standard certificate extensions for end-entity certificates

Create the CA database file to track issued certificates:

```bash
touch certs/ca/index.txt
chmod 644 certs/ca/index.txt
```

**What this does:** Creates an empty database file that OpenSSL will use to track all certificates issued by this CA. This is required for the CA operations.

## Step 6: Generate KME Server Certificate

Generate a 2048-bit RSA private key for the KME server:

```bash
openssl genrsa -out certs/kme/kme.key 2048
chmod 600 certs/kme/kme.key
```

**What this does:** Creates a private key for the KME server and sets restrictive permissions. The KME server will use this key for TLS connections.

Create a configuration file specific to the KME server certificate:

```bash
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
```

**What this does:** Creates a configuration file that defines:
- The KME server's identity (Common Name: KME_LAB_001)
- Certificate extensions for server authentication
- Subject Alternative Names for various ways to access the server

Generate a Certificate Signing Request (CSR) for the KME server:

```bash
openssl req -new -key certs/kme/kme.key -out certs/kme/kme.csr -config certs/kme/kme.conf
```

**What this does:** Creates a CSR that contains the KME server's public key and identity information. This will be signed by the CA to create the final certificate.

Sign the KME certificate using the CA:

```bash
openssl ca -batch -config certs/openssl.conf -in certs/kme/kme.csr -out certs/kme/kme.crt
```

**What this does:** Uses the CA to sign the KME server's CSR, creating a valid certificate that clients can trust.

Set proper permissions on the KME certificate:

```bash
chmod 644 certs/kme/kme.crt
```

**What this does:** Makes the certificate readable by the KME server process while maintaining security.

Remove the temporary CSR file:

```bash
rm certs/kme/kme.csr
```

**What this does:** Cleans up the temporary CSR file since it's no longer needed after the certificate is signed.

## Step 7: Generate SAE Client Certificates

### Generate SAE1 Certificate

Generate a 2048-bit RSA private key for SAE1:

```bash
openssl genrsa -out certs/sae/sae1.key 2048
chmod 600 certs/sae/sae1.key
```

**What this does:** Creates a private key for SAE1 client and sets restrictive permissions. SAE1 will use this key for client authentication.

Create a configuration file specific to SAE1:

```bash
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
```

**What this does:** Creates a configuration file that defines:
- SAE1's identity (Common Name: SAE_001)
- Certificate extensions for client authentication only
- Subject Alternative Names for local access

Generate a Certificate Signing Request for SAE1:

```bash
openssl req -new -key certs/sae/sae1.key -out certs/sae/sae1.csr -config certs/sae/sae1.conf
```

**What this does:** Creates a CSR containing SAE1's public key and identity information.

Sign SAE1's certificate using the CA:

```bash
openssl ca -batch -config certs/openssl.conf -in certs/sae/sae1.csr -out certs/sae/sae1.crt
```

**What this does:** Uses the CA to sign SAE1's CSR, creating a valid client certificate.

Set proper permissions on SAE1's certificate:

```bash
chmod 644 certs/sae/sae1.crt
```

**What this does:** Makes the certificate readable by SAE1 client applications.

Remove the temporary CSR file:

```bash
rm certs/sae/sae1.csr
```

**What this does:** Cleans up the temporary CSR file.

### Generate SAE2 Certificate

Generate a 2048-bit RSA private key for SAE2:

```bash
openssl genrsa -out certs/sae/sae2.key 2048
chmod 600 certs/sae/sae2.key
```

**What this does:** Creates a private key for SAE2 client and sets restrictive permissions. SAE2 will use this key for client authentication.

Create a configuration file specific to SAE2:

```bash
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
```

**What this does:** Creates a configuration file that defines:
- SAE2's identity (Common Name: SAE_002)
- Certificate extensions for client authentication only
- Subject Alternative Names for local access

Generate a Certificate Signing Request for SAE2:

```bash
openssl req -new -key certs/sae/sae2.key -out certs/sae/sae2.csr -config certs/sae/sae2.conf
```

**What this does:** Creates a CSR containing SAE2's public key and identity information.

Sign SAE2's certificate using the CA:

```bash
openssl ca -batch -config certs/openssl.conf -in certs/sae/sae2.csr -out certs/sae/sae2.crt
```

**What this does:** Uses the CA to sign SAE2's CSR, creating a valid client certificate.

Set proper permissions on SAE2's certificate:

```bash
chmod 644 certs/sae/sae2.crt
```

**What this does:** Makes the certificate readable by SAE2 client applications.

Remove the temporary CSR file:

```bash
rm certs/sae/sae2.csr
```

**What this does:** Cleans up the temporary CSR file.

## Step 8: Verify Certificates

Verify that the KME certificate is properly signed by the CA:

```bash
openssl verify -CAfile certs/ca/ca.crt certs/kme/kme.crt
```

**What this does:** Checks that the KME certificate was signed by our CA and is valid. Should return "certs/kme/kme.crt: OK".

Verify that SAE1's certificate is properly signed by the CA:

```bash
openssl verify -CAfile certs/ca/ca.crt certs/sae/sae1.crt
```

**What this does:** Checks that SAE1's certificate was signed by our CA and is valid. Should return "certs/sae/sae1.crt: OK".

Verify that SAE2's certificate is properly signed by the CA:

```bash
openssl verify -CAfile certs/ca/ca.crt certs/sae/sae2.crt
```

**What this does:** Checks that SAE2's certificate was signed by our CA and is valid. Should return "certs/sae/sae2.crt: OK".

Display the subject information for each certificate to verify their identities:

```bash
echo "=== KME Certificate ==="
openssl x509 -in certs/kme/kme.crt -text -noout | grep -A 5 "Subject:"

echo "=== SAE1 Certificate ==="
openssl x509 -in certs/sae/sae1.crt -text -noout | grep -A 5 "Subject:"

echo "=== SAE2 Certificate ==="
openssl x509 -in certs/sae/sae2.crt -text -noout | grep -A 5 "Subject:"
```

**What this does:** Shows the subject (identity) of each certificate to confirm they have the correct Common Names (KME_LAB_001, SAE_001, SAE_002).

## Step 9: Create Certificate Bundle for Easy-KMS

Create symbolic links that point to the actual certificate files. This allows the Easy-KMS server to use standardized paths:

```bash
ln -sf certs/kme/kme.crt certs/kme_cert.pem
ln -sf certs/kme/kme.key certs/kme_key.pem
ln -sf certs/ca/ca.crt certs/ca_cert.pem
```

**What this does:** Creates symbolic links that the Easy-KMS server expects:
- `certs/kme_cert.pem` → points to the KME server certificate
- `certs/kme_key.pem` → points to the KME server private key
- `certs/ca_cert.pem` → points to the CA certificate

Set proper permissions on the symbolic links:

```bash
chmod 644 certs/kme_cert.pem
chmod 644 certs/ca_cert.pem
chmod 600 certs/kme_key.pem
```

**What this does:** Ensures the symbolic links have the correct permissions:
- Certificates (644): readable by the server process
- Private key (600): only readable by the owner

## Step 10: Final Security Check

Verify that all directories have the correct permissions:

```bash
ls -la certs/
ls -la certs/ca/
ls -la certs/kme/
ls -la certs/sae/
```

**What this does:** Shows the permissions on all certificate directories. They should all show `drwx------` (700 permissions).

Check that all private key files have restrictive permissions:

```bash
find certs/ -name "*.key" -exec ls -la {} \;
```

**What this does:** Lists all private key files and their permissions. They should all show `-rw-------` (600 permissions).

Check that all certificate files have readable permissions:

```bash
find certs/ -name "*.crt" -exec ls -la {} \;
find certs/ -name "*.pem" -exec ls -la {} \;
```

**What this does:** Lists all certificate files and their permissions. They should show `-rw-r--r--` (644 permissions).

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