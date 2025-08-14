#!/bin/bash

cd ../..

mkdir certs/ca/newcerts

cat > certs/openssl.conf << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = TX
L = Burnet
O = HPE-Networking
OU = Easy-KME Lab

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
dir = ./certs/ca
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

touch certs/ca/index.txt
chmod 644 certs/ca/index.txt
openssl genrsa -out certs/kme/kme.key 2048
chmod 600 certs/kme/kme.key
cat > certs/kme/kme.conf << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = TX
L = Burnet
O = HPE-Networking
OU = Easy-KME Lab
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

openssl req -new -key certs/kme/kme.key -out certs/kme/kme.csr -config certs/kme/kme.conf
openssl ca -batch -config certs/openssl.conf -in certs/kme/kme.csr -out certs/kme/kme.crt
chmod 644 certs/kme/kme.crt
rm certs/kme/kme.csr

ln -sf ./kme/kme.crt certs/kme_cert.pem
ln -sf ./kme/kme.key certs/kme_key.pem

