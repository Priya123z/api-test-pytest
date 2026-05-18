import pytest
from utils.api_client import APIClient


@pytest.fixture(scope="session")
def api() -> APIClient:
    return APIClient()


@pytest.fixture(scope="session")
def auth_token(api: APIClient) -> str:
    resp = api.post("/auth/login", {
        "username": "emilys",
        "password": "emilyspass",
        "expiresInMins": 30,
    })
    assert resp.status_code == 200
    return resp.json()["accessToken"]
