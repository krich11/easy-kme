#!/usr/bin/env python3
import base64
from fastapi.testclient import TestClient

from src.main import app


def test_dec_keys_post_and_get_authorization(monkeypatch):
    client = TestClient(app)

    # Fake auth
    def fake_authenticate(request):
        return request.headers.get("x-sae-id", "SAE_001")

    from src.api import middleware
    monkeypatch.setattr(middleware, "authenticate_client", fake_authenticate)

    # First, SAE_001 requests keys for SAE_002
    r = client.post(
        "/api/v1/keys/SAE_002/enc_keys",
        json={"number": 2, "size": 256},
        headers={"x-sae-id": "SAE_001"},
    )
    assert r.status_code == 200
    keys = [k["key_ID"] for k in r.json()["keys"]]

    # Unauthorized: master trying to dec_keys should be rejected
    r_unauth = client.post(
        "/api/v1/keys/SAE_001/dec_keys",
        json={"key_IDs": [{"key_ID": keys[0]}]},
        headers={"x-sae-id": "SAE_001"},
    )
    assert r_unauth.status_code == 401

    # Authorized: slave SAE_002 retrieves by POST
    def auth_sae2(request):
        return "SAE_002"

    monkeypatch.setattr(middleware, "authenticate_client", auth_sae2)

    r_ok = client.post(
        "/api/v1/keys/SAE_001/dec_keys",
        json={"key_IDs": [{"key_ID": k} for k in keys]},
    )
    assert r_ok.status_code == 200
    for k in r_ok.json()["keys"]:
        base64.b64decode(k["key"], validate=True)

    # GET simple case with one key_ID
    r_get = client.get(f"/api/v1/keys/SAE_001/dec_keys?key_ID={keys[0]}")
    assert r_get.status_code == 200
