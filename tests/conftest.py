import json
from pathlib import Path

import pytest

from utils.api_client import APIClient

SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"


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


@pytest.fixture(scope="session")
def load_schema():
    """Reads a schema from schemas/. Was copy-pasted into three test modules."""
    def _load(name: str) -> dict:
        with open(SCHEMAS_DIR / name) as f:
            return json.load(f)
    return _load
