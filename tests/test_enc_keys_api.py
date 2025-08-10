#!/usr/bin/env python3
import base64
from fastapi.testclient import TestClient
import pytest

from src.main import app


def test_enc_keys_post_and_get(monkeypatch):
    client = TestClient(app)

    # Fake auth
    def fake_authenticate(request):
        return request.headers.get("x-sae-id", "SAE_001")

    from src.api import middleware
    monkeypatch.setattr(middleware, "authenticate_client", fake_authenticate)

    # POST spec request
    req = {
        "number": 2,
        "size": 256,
        "additional_slave_SAE_IDs": ["SAE_003"],
    }
    r = client.post("/api/v1/keys/SAE_002/enc_keys", json=req, headers={"x-sae-id": "SAE_001"})
    assert r.status_code == 200
    body = r.json()
    assert "keys" in body and isinstance(body["keys"], list)
    assert len(body["keys"]) == 2
    for k in body["keys"]:
        assert "key_ID" in k and "key" in k
        # validate base64
        base64.b64decode(k["key"], validate=True)

    # GET simple case
    r2 = client.get("/api/v1/keys/SAE_002/enc_keys?number=1&size=256", headers={"x-sae-id": "SAE_001"})
    assert r2.status_code == 200
    body2 = r2.json()
    assert len(body2["keys"]) == 1
