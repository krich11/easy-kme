#!/usr/bin/env python3
import os
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.config import get_settings


def with_env(env):
    return pytest.mark.usefixtures()(lambda f: f)


def test_get_status_spec(monkeypatch):
    client = TestClient(app)

    # Monkeypatch authenticate_client to accept header SAE ID
    def fake_authenticate(request):
        return request.headers.get("x-sae-id", "SAE_001")

    # Inject fake authenticator
    from src.api import middleware
    monkeypatch.setattr(middleware, "authenticate_client", fake_authenticate)

    # Call status for a target slave SAE
    resp = client.get("/api/v1/keys/SAE_002/status", headers={"x-sae-id": "SAE_001"})
    assert resp.status_code == 200
    body = resp.json()

    # ETSI StatusSpec fields
    for field in [
        "source_KME_ID",
        "target_KME_ID",
        "master_SAE_ID",
        "slave_SAE_ID",
        "key_size",
        "stored_key_count",
        "max_key_count",
        "max_key_per_request",
        "max_key_size",
        "min_key_size",
        "max_SAE_ID_count",
    ]:
        assert field in body, f"missing field {field}"

    assert isinstance(body["stored_key_count"], int)
    assert body["slave_SAE_ID"] == "SAE_002"
    assert body["master_SAE_ID"] == "SAE_001"
