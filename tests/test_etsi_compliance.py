#!/usr/bin/env python3
"""
Test ETSI GS QKD 014 compliance for enc_keys route.
"""

import base64
import json
from fastapi.testclient import TestClient
import pytest

from src.main import app


def test_etsi_enc_keys_compliance(monkeypatch):
    """Test that enc_keys route returns data in exact ETSI format."""
    client = TestClient(app)

    # Fake auth
    def fake_authenticate(request):
        return request.headers.get("x-sae-id", "SAE_001")

    from src.api import middleware
    monkeypatch.setattr(middleware, "authenticate_client", fake_authenticate)

    # Test POST with ETSI-compliant request
    request_data = {
        "number": 2,
        "size": 256,
        "additional_slave_SAE_IDs": ["SAE_003"],
        "extension_mandatory": [],
        "extension_optional": []
    }
    
    response = client.post(
        "/api/v1/keys/SAE_002/enc_keys", 
        json=request_data, 
        headers={"x-sae-id": "SAE_001"}
    )
    
    assert response.status_code == 200
    body = response.json()
    
    # Verify ETSI-compliant response structure
    assert "keys" in body
    assert isinstance(body["keys"], list)
    assert len(body["keys"]) == 2
    
    # Verify each key object has required ETSI fields
    for key_obj in body["keys"]:
        assert "key_ID" in key_obj
        assert "key" in key_obj
        assert isinstance(key_obj["key_ID"], str)
        assert isinstance(key_obj["key"], str)
        
        # Verify key_ID is UUID format
        assert len(key_obj["key_ID"]) == 36  # UUID length
        assert key_obj["key_ID"].count("-") == 4  # UUID format
        
        # Verify key is valid base64
        try:
            decoded_key = base64.b64decode(key_obj["key"], validate=True)
            assert len(decoded_key) == 32  # 256 bits = 32 bytes
        except Exception as e:
            pytest.fail(f"Invalid base64 key: {e}")
    
    # Verify optional fields are present (even if None)
    assert "key_container_extension" in body
    assert "easy_kme_certificate_extension" in body


def test_etsi_enc_keys_validation(monkeypatch):
    """Test ETSI validation requirements."""
    client = TestClient(app)

    # Fake auth
    def fake_authenticate(request):
        return request.headers.get("x-sae-id", "SAE_001")

    from src.api import middleware
    monkeypatch.setattr(middleware, "authenticate_client", fake_authenticate)

    # Test key size not multiple of 8 (should fail)
    request_data = {
        "number": 1,
        "size": 255,  # Not multiple of 8
    }
    
    response = client.post(
        "/api/v1/keys/SAE_002/enc_keys", 
        json=request_data, 
        headers={"x-sae-id": "SAE_001"}
    )
    
    assert response.status_code == 400
    assert "size shall be a multiple of 8" in response.json()["detail"]

    # Test extension_mandatory (should fail as we don't support any)
    request_data = {
        "number": 1,
        "size": 256,
        "extension_mandatory": [{"test_extension": "value"}]
    }
    
    response = client.post(
        "/api/v1/keys/SAE_002/enc_keys", 
        json=request_data, 
        headers={"x-sae-id": "SAE_001"}
    )
    
    assert response.status_code == 400
    assert "not all extension_mandatory parameters are supported" in response.json()["detail"]


def test_etsi_enc_keys_get_variant(monkeypatch):
    """Test GET variant for simple cases."""
    client = TestClient(app)

    # Fake auth
    def fake_authenticate(request):
        return request.headers.get("x-sae-id", "SAE_001")

    from src.api import middleware
    monkeypatch.setattr(middleware, "authenticate_client", fake_authenticate)

    # Test GET with query parameters
    response = client.get(
        "/api/v1/keys/SAE_002/enc_keys?number=1&size=256", 
        headers={"x-sae-id": "SAE_001"}
    )
    
    assert response.status_code == 200
    body = response.json()
    
    # Verify same ETSI structure
    assert "keys" in body
    assert len(body["keys"]) == 1
    
    key_obj = body["keys"][0]
    assert "key_ID" in key_obj
    assert "key" in key_obj
    
    # Verify key size
    decoded_key = base64.b64decode(key_obj["key"], validate=True)
    assert len(decoded_key) == 32  # 256 bits = 32 bytes


def test_etsi_enc_keys_default_values(monkeypatch):
    """Test that default values work correctly."""
    client = TestClient(app)

    # Fake auth
    def fake_authenticate(request):
        return request.headers.get("x-sae-id", "SAE_001")

    from src.api import middleware
    monkeypatch.setattr(middleware, "authenticate_client", fake_authenticate)

    # Test with empty request (should use defaults)
    response = client.post(
        "/api/v1/keys/SAE_002/enc_keys", 
        json={}, 
        headers={"x-sae-id": "SAE_001"}
    )
    
    assert response.status_code == 200
    body = response.json()
    
    # Should return 1 key with default size
    assert len(body["keys"]) == 1
    
    key_obj = body["keys"][0]
    decoded_key = base64.b64decode(key_obj["key"], validate=True)
    # Default key size should be 256 bits (32 bytes)
    assert len(decoded_key) == 32
