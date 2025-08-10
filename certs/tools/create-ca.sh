#!/bin/bash

cd ../..
mkdir -p certs/ca certs/kme certs/sae
chmod 700 certs certs/ca certs/kme certs/sae
openssl genrsa -out certs/ca/ca.key 4096
chmod 600 certs/ca/ca.key
cat > certs/ca/ca.conf << EOF
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
CN = Easy-KMS Root CA1

[v3_req]
basicConstraints = CA:TRUE
keyUsage = keyCertSign, cRLSign
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer:always
EOF

openssl req -new -x509 -days 3650 -key certs/ca/ca.key -out certs/ca/ca.crt -config certs/ca/ca.conf
chmod 644 certs/ca/ca.crt
echo "01" > certs/ca/ca.srl
openssl x509 -in certs/ca/ca.crt -text -noout
openssl x509 -in certs/ca/ca.crt -noout -subject -issuer -dates

ln -sf certs/ca/ca.crt certs/ca_cert.pem

