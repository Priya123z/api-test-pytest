import pytest
from utils.api_client import APIClient


@pytest.fixture(scope="session")
def api() -> APIClient:
    return APIClient()


@pytest.fixture(scope="session")
def auth_token(api: APIClient) -> str:
    resp = api.post("/api/login", {"email": "eve.holt@reqres.in", "password": "cityslicka"})
    assert resp.status_code == 200
    return resp.json()["token"]
