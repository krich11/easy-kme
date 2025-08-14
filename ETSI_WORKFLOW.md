# ETSI GS QKD 014 Workflow Reference

## 🔄 **Correct ETSI Workflow Sequence**

The ETSI GS QKD 014 specification defines a specific sequence for key distribution between SAEs. Here's the **correct** workflow:

### **Step 1: Master SAE Requests Keys**
```
SAE_A (Master) → KME
POST /api/v1/keys/SAE_B/enc_keys
{
  "number": 2,
  "size": 256
}

Response:
{
  "keys": [
    {
      "key_ID": "550e8400-e29b-41d4-a716-446655440000",
      "key": "base64-encoded-key-material"
    },
    {
      "key_ID": "bc490419-7d60-487f-adc1-4ddcc177c139", 
      "key": "base64-encoded-key-material"
    }
  ]
}
```

### **Step 2: Master SAE Sends Key IDs to Slave SAE**
```
SAE_A (Master) → SAE_B (Slave)
[Out-of-band communication]
→ SAE_A sends key_IDs to SAE_B
```

### **Step 3: Slave SAE Retrieves Keys Using Key IDs**
```
SAE_B (Slave) → KME
POST /api/v1/keys/SAE_A/dec_keys
{
  "key_IDs": [
    {
      "key_ID": "550e8400-e29b-41d4-a716-446655440000"
    },
    {
      "key_ID": "bc490419-7d60-487f-adc1-4ddcc177c139"
    }
  ]
}

Response:
{
  "keys": [
    {
      "key_ID": "550e8400-e29b-41d4-a716-446655440000",
      "key": "base64-encoded-key-material"
    },
    {
      "key_ID": "bc490419-7d60-487f-adc1-4ddcc177c139",
      "key": "base64-encoded-key-material"
    }
  ]
}
```

## 🎯 **Key Points**

1. **Master SAE** calls "Get key" with **slave SAE ID** in URL
2. **Slave SAE** calls "Get key with key IDs" with **master SAE ID** in URL
3. The **key_IDs** are used to retrieve the **same keys** that were generated for the master
4. Both SAEs end up with **identical key material** for secure communication

## ❌ **Common Misconception**

**Incorrect**: Thinking that the slave SAE ID in "Get key with key IDs" refers to the slave SAE making the request.

**Correct**: The SAE ID in "Get key with key IDs" refers to the **master SAE** who originally requested the keys.

## 📋 **Test Script Usage**

The `test_kme_api.sh` script includes a **"Complete ETSI Workflow"** test that demonstrates this correct sequence:

```bash
./test_kme_api.sh
# Select option 4: Complete ETSI Workflow
```

This test will:
1. Have SAE_001 (master) request keys for SAE_002 (slave)
2. Extract the key_IDs from the response
3. Have SAE_002 (slave) retrieve the same keys using those key_IDs

## 🔍 **Why This Matters**

This workflow ensures:
- **Key synchronization**: Both SAEs get identical keys
- **Security**: Keys are only accessible to authorized SAEs
- **Compliance**: Follows ETSI GS QKD 014 specification exactly
- **Interoperability**: Works with other ETSI-compliant implementations

The test script validates that your Easy-KME implementation correctly follows this ETSI workflow. 
