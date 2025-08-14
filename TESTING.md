# Easy-KME API Testing Guide

## Overview

This guide provides comprehensive testing for the Easy-KME server implementation of the ETSI GS QKD 014 specification. The test suite validates all three API methods and ensures compliance with the standard.

## ETSI GS QKD 014 Workflow

The ETSI specification defines a specific workflow for key distribution between SAEs:

### 1. **Get Status** (ETSI §5.2)
- **Purpose**: Check KME status and key pool information
- **Method**: `GET /api/v1/keys/{slave_SAE_ID}/status`
- **Use Case**: SAE checks if KME has sufficient keys available

### 2. **Get Key** (ETSI §5.3)
- **Purpose**: Master SAE requests keys for a slave SAE
- **Method**: `POST /api/v1/keys/{slave_SAE_ID}/enc_keys`
- **Use Case**: SAE_A (master) requests keys to share with SAE_B (slave)

### 3. **Get Key with Key IDs** (ETSI §5.4)
- **Purpose**: Slave SAE retrieves keys using key_IDs from master SAE
- **Method**: `POST /api/v1/keys/{master_SAE_ID}/dec_keys`
- **Use Case**: SAE_B (slave) retrieves keys using key_IDs provided by SAE_A (master)

## Correct ETSI Workflow Sequence

```
Step 1: SAE_A (Master) → KME
  POST /api/v1/keys/SAE_B/enc_keys
  → Returns Key Container with key_IDs

Step 2: SAE_A → SAE_B
  → SAE_A sends key_IDs to SAE_B (out-of-band)

Step 3: SAE_B (Slave) → KME
  POST /api/v1/keys/SAE_A/dec_keys
  → SAE_B retrieves keys using key_IDs
```

## Running the Test Suite

### Prerequisites

1. **Install jq** (JSON processor):
   ```bash
   sudo apt-get install jq
   ```

2. **Start the KME server**:
   ```bash
   source venv/bin/activate
   python run.py &
   ```

3. **Verify certificates exist**:
   ```bash
   ls -la certs/sae/sae1.crt certs/sae/sae2.crt certs/ca/ca.crt
   ```

### Using the Test Script

```bash
# Make script executable (if not already)
chmod +x test_kme_api.sh

# Run the test suite
./test_kme_api.sh
```

### Test Menu Options

The script provides a menu-driven interface with the following options:

1. **Get Status API** - Tests the status endpoint
2. **Get Key API - POST Method** - Tests key generation with POST
3. **Get Key API - GET Method** - Tests key generation with GET
4. **Complete ETSI Workflow** - Tests the full ETSI sequence
5. **Get Key with Key IDs - GET Method** - Tests single key retrieval
6. **Error Handling Tests** - Tests error conditions
7. **Advanced Features** - Tests extensions and multiple SAEs
8. **Health and Documentation** - Tests basic endpoints
9. **Run All Tests** - Executes all tests sequentially
0. **Exit** - Quit the test suite

## Individual Test Commands

If you prefer to run tests manually, here are the individual commands:

### Test 1: Get Status
```bash
curl -k \
  --cert certs/sae/sae1.crt \
  --key certs/sae/sae1.key \
  --cacert certs/ca/ca.crt \
  -H "x-sae-id: SAE_001" \
  https://localhost:8443/api/v1/keys/SAE_002/status | jq '.'
```

### Test 2: Get Key (POST)
```bash
curl -k \
  --cert certs/sae/sae1.crt \
  --key certs/sae/sae1.key \
  --cacert certs/ca/ca.crt \
  -H "x-sae-id: SAE_001" \
  -H "Content-Type: application/json" \
  -X POST \
  -d '{"number": 2, "size": 256}' \
  https://localhost:8443/api/v1/keys/SAE_002/enc_keys | jq '.'
```

### Test 3: Get Key (GET)
```bash
curl -k \
  --cert certs/sae/sae1.crt \
  --key certs/sae/sae1.key \
  --cacert certs/ca/ca.crt \
  -H "x-sae-id: SAE_001" \
  "https://localhost:8443/api/v1/keys/SAE_002/enc_keys?number=1&size=512" | jq '.'
```

### Test 4: Complete Workflow
```bash
# Step 1: Master SAE gets keys
RESPONSE=$(curl -k \
  --cert certs/sae/sae1.crt \
  --key certs/sae/sae1.key \
  --cacert certs/ca/ca.crt \
  -H "x-sae-id: SAE_001" \
  -H "Content-Type: application/json" \
  -X POST \
  -d '{"number": 2, "size": 256}' \
  https://localhost:8443/api/v1/keys/SAE_002/enc_keys)

echo "$RESPONSE" | jq '.'

# Step 2: Extract key_IDs and slave SAE retrieves keys
KEY_IDS=$(echo "$RESPONSE" | jq -r '.keys[].key_ID' | tr '\n' ',' | sed 's/,$//')
KEY_IDS_JSON=$(echo "$RESPONSE" | jq -r '.keys[] | {key_ID: .key_ID}')

curl -k \
  --cert certs/sae/sae2.crt \
  --key certs/sae/sae2.key \
  --cacert certs/ca/ca.crt \
  -H "x-sae-id: SAE_002" \
  -H "Content-Type: application/json" \
  -X POST \
  -d "{\"key_IDs\": [$KEY_IDS_JSON]}" \
  https://localhost:8443/api/v1/keys/SAE_001/dec_keys | jq '.'
```

## Expected Responses

### Get Status Response
```json
{
  "source_KME_ID": "KME_LAB_001",
  "target_KME_ID": "KME_LAB_001",
  "master_SAE_ID": "SAE_001",
  "slave_SAE_ID": "SAE_002",
  "key_size": 256,
  "stored_key_count": 985,
  "max_key_count": 1000,
  "max_key_per_request": 128,
  "max_key_size": 1024,
  "min_key_size": 8,
  "max_SAE_ID_count": 8,
  "status_extension": null
}
```

### Get Key Response
```json
{
  "keys": [
    {
      "key_ID": "550e8400-e29b-41d4-a716-446655440000",
      "key": "base64-encoded-key-material",
      "key_ID_extension": null,
      "key_extension": null
    }
  ],
  "key_container_extension": null
}
```

### Get Key with Key IDs Response
```json
{
  "keys": [
    {
      "key_ID": "550e8400-e29b-41d4-a716-446655440000",
      "key": "base64-encoded-key-material",
      "key_ID_extension": null,
      "key_extension": null
    }
  ],
  "key_container_extension": null
}
```

## Error Handling

The test suite validates proper error responses:

- **400 Bad Request**: Invalid parameters (e.g., key size not multiple of 8)
- **401 Unauthorized**: Missing or invalid certificates
- **404 Not Found**: Invalid endpoints
- **503 Service Unavailable**: Server errors

## Advanced Features

### Extensions
```json
{
  "number": 1,
  "size": 256,
  "extension_mandatory": [
    {"route_type": "direct"}
  ],
  "extension_optional": [
    {"max_age": 30000}
  ]
}
```

### Multiple Slave SAEs
```json
{
  "number": 1,
  "size": 256,
  "additional_slave_SAE_IDs": [
    "SAE_002",
    "SAE_003"
  ]
}
```

## Troubleshooting

### Common Issues

1. **Server not running**:
   ```bash
   source venv/bin/activate
   python run.py &
   ```

2. **Missing certificates**:
   ```bash
   # Follow the certificate generation guides in certs/ directory
   ls -la certs/sae/sae1.crt certs/sae/sae2.crt certs/ca/ca.crt
   ```

3. **jq not installed**:
   ```bash
   sudo apt-get install jq
   ```

4. **Permission denied**:
   ```bash
   chmod +x test_kme_api.sh
   ```

### Debug Mode

To see detailed curl commands, the script shows the exact command being executed before each API call.

## Validation Checklist

After running tests, verify:

- ✅ All API endpoints return proper ETSI data formats
- ✅ Key_IDs are valid UUIDs
- ✅ Keys are base64-encoded
- ✅ Error responses follow ETSI Error data format
- ✅ HTTP status codes match ETSI specification
- ✅ Certificate authentication works
- ✅ GET and POST methods work as specified
- ✅ Complete workflow functions correctly

## ETSI Compliance

This test suite validates compliance with:

- **ETSI GS QKD 014 v1.1.1** specification
- **Section 5.2**: Get status method
- **Section 5.3**: Get key method  
- **Section 5.4**: Get key with key IDs method
- **Section 6.1-6.5**: Data formats
- **Section 6.2**: Key request format
- **Section 6.4**: Key IDs format

The test suite ensures your Easy-KME implementation is fully compliant with the ETSI GS QKD 014 standard. 
