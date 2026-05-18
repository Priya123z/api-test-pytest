import json
from pathlib import Path
import jsonschema
import pytest

SCHEMAS_DIR = Path(__file__).parent.parent / "schemas"


def load_schema(name: str) -> dict:
    with open(SCHEMAS_DIR / name) as f:
        return json.load(f)


LOGIN_URL = "/auth/login"
VALID_CREDS = {"username": "emilys", "password": "emilyspass", "expiresInMins": 30}


class TestAuth:
    def test_valid_login_returns_200(self, api):
        resp = api.post(LOGIN_URL, VALID_CREDS)
        assert resp.status_code == 200

    def test_valid_login_returns_access_token(self, api):
        resp = api.post(LOGIN_URL, VALID_CREDS)
        assert "accessToken" in resp.json()
        assert len(resp.json()["accessToken"]) > 0

    def test_valid_login_response_matches_schema(self, api):
        resp = api.post(LOGIN_URL, VALID_CREDS)
        schema = load_schema("login_response_schema.json")
        jsonschema.validate(instance=resp.json(), schema=schema)

    def test_missing_password_returns_400(self, api):
        resp = api.post(LOGIN_URL, {"username": "emilys"})
        assert resp.status_code == 400

    def test_missing_password_returns_message_key(self, api):
        resp = api.post(LOGIN_URL, {"username": "emilys"})
        assert "message" in resp.json()

    def test_invalid_credentials_return_400(self, api):
        resp = api.post(LOGIN_URL, {"username": "emilys", "password": "wrongpassword"})
        assert resp.status_code == 400

    def test_auth_token_fixture_is_string(self, auth_token):
        assert isinstance(auth_token, str)
        assert len(auth_token) > 5

    @pytest.mark.parametrize("payload,expected_status", [
        ({"username": "emilys"}, 400),
        ({"password": "emilyspass"}, 400),
        ({}, 400),
    ])
    def test_incomplete_payloads_return_error(self, api, payload, expected_status):
        resp = api.post(LOGIN_URL, payload)
        assert resp.status_code == expected_status
        assert "message" in resp.json()
