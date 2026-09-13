import pytest
import httpx


@pytest.fixture
def api_client(live_server):
    """HTTP client pointed at a real running test server."""
    with httpx.Client(base_url=live_server.url, timeout=10.0) as client:
        yield client
