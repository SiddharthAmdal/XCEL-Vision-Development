import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app
import json
import hmac
import hashlib
from xsc_lib.xsc_lib_common.config import settings

client = TestClient(app)

def generate_signature(payload_bytes: bytes) -> str:
    hmac_secret = settings.RING_HMAC_SECRET.encode('utf-8')
    calculated_hmac = hmac.new(
        hmac_secret,
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    return f"sha256={calculated_hmac}"

def test_webhook_missing_signature():
    response = client.post("/api/v1/ring/webhook", json={"test": "data"})
    assert response.status_code == 401
    assert "Missing signature" in response.json()["detail"]

def test_webhook_invalid_signature():
    headers = {"x-signature": "sha256=invalid"}
    response = client.post("/api/v1/ring/webhook", json={"test": "data"}, headers=headers)
    assert response.status_code == 401
    assert "Invalid signature" in response.json()["detail"]

def test_webhook_missing_event_id():
    payload = {"data": {"id": "123"}}
    payload_bytes = json.dumps(payload).encode('utf-8')
    headers = {"x-signature": generate_signature(payload_bytes)}
    
    response = client.post("/api/v1/ring/webhook", content=payload_bytes, headers=headers)
    assert response.status_code == 400
    assert "Missing request_id" in response.json()["detail"]

def test_webhook_idempotency():
    import uuid
    req_id = str(uuid.uuid4())
    payload = {
        "meta": {
            "request_id": req_id,
            "account_id": "acc_1"
        },
        "data": {
            "id": "evt_123",
            "type": "button_press",
            "attributes": {
                "source": "cam_1",
                "timestamp": 1699457230000
            }
        }
    }
    payload_bytes = json.dumps(payload).encode('utf-8')
    headers = {"x-signature": generate_signature(payload_bytes)}
    
    # First delivery
    response1 = client.post("/api/v1/ring/webhook", content=payload_bytes, headers=headers)
    assert response1.status_code == 200
    assert response1.json() == {"status": "acknowledged"}
    
    # Duplicate delivery
    response2 = client.post("/api/v1/ring/webhook", content=payload_bytes, headers=headers)
    assert response2.status_code == 200
    assert response2.json() == {"status": "acknowledged", "detail": "duplicate"}
