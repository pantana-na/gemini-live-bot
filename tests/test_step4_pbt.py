"""
Property-Based Tests (PBT) for Step 4: Server Health & Invariant Testing.
Guarantees Rule 6 (/healthz probe) invariance across randomized queries and headers.
"""

import string
from starlette.testclient import TestClient
from hypothesis import given, strategies as st, settings
from app.server import app

client = TestClient(app)

ascii_chars = string.ascii_letters + string.digits

st_query_params = st.dictionaries(
    keys=st.text(min_size=1, max_size=20, alphabet=ascii_chars),
    values=st.text(min_size=0, max_size=50, alphabet=ascii_chars + " "),
    max_size=5
)

st_headers = st.dictionaries(
    keys=st.text(min_size=1, max_size=15, alphabet=string.ascii_letters).map(lambda s: f"X-{s}"),
    values=st.text(min_size=1, max_size=30, alphabet=ascii_chars),
    max_size=3
)


@settings(max_examples=30)
@given(st_query_params, st_headers)
def test_invariant_10_health_probe_invariance(params, headers):
    """
    Invariant 10 (Health Probe Invariance):
    GET /healthz strictly returns HTTP 200 with status='healthy'
    regardless of arbitrary query parameters or valid HTTP client request headers.
    """
    response = client.get("/healthz", params=params, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "gemini-live-bot"
