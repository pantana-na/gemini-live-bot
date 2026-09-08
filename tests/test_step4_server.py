"""
Unit Tests for Step 4: FastAPI Server, Liveness Probe & WebSocket Audio Endpoint.
Strictly verifies Rule 6 (/healthz probe) and real-time audio WebSocket lifecycle.
"""

import json
import pytest
from starlette.testclient import TestClient
from app.server import app


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


def test_root_endpoint_metadata_and_adk_link(client):
    """Verify root landing serves service metadata and ADK Web UI pointer."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "gemini-live-bot"
    assert data["status"] == "online"
    assert data["interface"] == "adk-web"
    assert data["adk_ui_url"] == "/dev-ui/"
    assert data["orchestrator"] == "thai_customer_orchestrator"


def test_adk_health_endpoint(client):
    """Verify ADK standard /health endpoint returns 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_info_metadata(client):
    """Verify /api/info returns service metadata and multi-agent hierarchy."""
    response = client.get("/api/info")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "gemini-live-bot"
    assert data["status"] == "online"
    assert data["orchestrator"] == "thai_customer_orchestrator"
    assert len(data["sub_agents"]) == 2


def test_healthz_liveness_probe_rule_6(client):
    """Verify Rule 6: Cloud Run liveness probe returns HTTP 200 and healthy JSON payload."""
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "gemini-live-bot"
    assert "timestamp" in data


def test_readyz_probe(client):
    """Verify readiness probe returns 200 OK."""
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_websocket_live_handshake_and_ping_pong(client):
    """Verify WebSocket connection, initialization message, and ping-pong roundtrip."""
    with client.websocket_connect("/ws/live") as websocket:
        init_msg = websocket.receive_text()
        init_data = json.loads(init_msg)
        assert init_data["type"] == "SESSION_INIT"
        assert init_data["status"] == "READY"

        # Send PING
        websocket.send_text(json.dumps({"type": "PING"}))
        pong_msg = websocket.receive_text()
        pong_data = json.loads(pong_msg)
        assert pong_data["type"] == "PONG"


def test_websocket_live_terminate_call(client):
    """Verify call termination control frame closes WebSocket connection with clean code."""
    with client.websocket_connect("/ws/live") as websocket:
        # Consume init message
        websocket.receive_text()

        # Send termination frame
        websocket.send_text(json.dumps({
            "type": "TERMINATE_CALL",
            "reason": "OUT_OF_SCOPE_INTENT",
            "farewell_message": "ขออภัยครับ สายการบินไม่รองรับบริการนี้ ขอบคุณครับ"
        }))

        term_msg = websocket.receive_text()
        term_data = json.loads(term_msg)
        assert term_data["type"] == "CALL_TERMINATED"
        assert term_data["reason"] == "OUT_OF_SCOPE_INTENT"
