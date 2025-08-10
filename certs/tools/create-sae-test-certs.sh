#!/bin/bash

cd ../..

openssl genrsa -out certs/sae/sae1.key 2048
chmod 600 certs/sae/sae1.key

openssl genrsa -out certs/sae/sae2.key 2048
chmod 600 certs/sae/sae2.key

openssl genrsa -out certs/sae/sae3.key 2048
chmod 600 certs/sae/sae3.key

openssl genrsa -out certs/sae/sae4.key 2048
chmod 600 certs/sae/sae4.key

cat > certs/sae/sae1.conf << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = TX
L = Burnet
O = HPE-Networking
OU = Easy-KMS Lab
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

cat > certs/sae/sae2.conf << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = TX
L = Burnet
O = HPE-Networking
OU = Easy-KMS Lab
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

cat > certs/sae/sae3.conf << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = TX
L = Burnet
O = HPE-Networking
OU = Easy-KMS Lab
CN = SAE_003

[v3_req]
basicConstraints = CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = clientAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = sae3.local
DNS.2 = localhost
IP.1 = 127.0.0.1
IP.2 = ::1
EOF

cat > certs/sae/sae4.conf << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = TX
L = Burnet
O = HPE-Networking
OU = Easy-KMS Lab
CN = SAE_004

[v3_req]
basicConstraints = CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = clientAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = sae3.local
DNS.2 = localhost
IP.1 = 127.0.0.1
IP.2 = ::1
EOF

openssl req -new -key certs/sae/sae1.key -out certs/sae/sae1.csr -config certs/sae/sae1.conf
openssl req -new -key certs/sae/sae2.key -out certs/sae/sae2.csr -config certs/sae/sae2.conf
openssl req -new -key certs/sae/sae3.key -out certs/sae/sae3.csr -config certs/sae/sae3.conf
openssl req -new -key certs/sae/sae4.key -out certs/sae/sae4.csr -config certs/sae/sae4.conf
openssl ca -batch -config certs/openssl.conf -in certs/sae/sae1.csr -out certs/sae/sae1.crt
openssl ca -batch -config certs/openssl.conf -in certs/sae/sae2.csr -out certs/sae/sae2.crt
openssl ca -batch -config certs/openssl.conf -in certs/sae/sae3.csr -out certs/sae/sae3.crt
openssl ca -batch -config certs/openssl.conf -in certs/sae/sae4.csr -out certs/sae/sae4.crt
chmod 644 certs/sae/sae1.crt
chmod 644 certs/sae/sae2.crt
chmod 644 certs/sae/sae3.crt
chmod 644 certs/sae/sae4.crt
rm certs/sae/sae1.csr
rm certs/sae/sae2.csr
rm certs/sae/sae3.csr
rm certs/sae/sae4.csr

