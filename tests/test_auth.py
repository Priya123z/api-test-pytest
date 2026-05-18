import json
from pathlib import Path
import jsonschema
import pytest

SCHEMAS_DIR = Path(__file__).parent.parent / "schemas"


def load_schema(name: str) -> dict:
    with open(SCHEMAS_DIR / name) as f:
        return json.load(f)


class TestAuth:
    def test_valid_login_returns_200(self, api):
        resp = api.post("/api/login", {
            "email": "eve.holt@reqres.in",
            "password": "cityslicka",
        })
        assert resp.status_code == 200

    def test_valid_login_returns_token(self, api):
        resp = api.post("/api/login", {
            "email": "eve.holt@reqres.in",
            "password": "cityslicka",
        })
        assert "token" in resp.json()
        assert len(resp.json()["token"]) > 0

    def test_valid_login_response_matches_schema(self, api):
        resp = api.post("/api/login", {
            "email": "eve.holt@reqres.in",
            "password": "cityslicka",
        })
        schema = load_schema("login_response_schema.json")
        jsonschema.validate(instance=resp.json(), schema=schema)

    def test_missing_password_returns_400(self, api):
        resp = api.post("/api/login", {"email": "eve.holt@reqres.in"})
        assert resp.status_code == 400

    def test_missing_password_returns_error_key(self, api):
        resp = api.post("/api/login", {"email": "eve.holt@reqres.in"})
        assert "error" in resp.json()
        assert resp.json()["error"] == "Missing password"

    def test_missing_email_returns_400(self, api):
        resp = api.post("/api/login", {"password": "cityslicka"})
        assert resp.status_code == 400

    def test_auth_token_fixture_is_string(self, auth_token):
        assert isinstance(auth_token, str)
        assert len(auth_token) > 5

    @pytest.mark.parametrize("payload,expected_error", [
        ({"email": "peter@klaven.com"}, "Missing password"),
        ({"password": "cityslicka"}, "Missing email or username"),
    ])
    def test_incomplete_payloads_return_error(self, api, payload, expected_error):
        resp = api.post("/api/login", payload)
        assert resp.status_code == 400
        assert "error" in resp.json()
