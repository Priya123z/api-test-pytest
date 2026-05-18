import json
from pathlib import Path
import jsonschema
import pytest

SCHEMAS_DIR = Path(__file__).parent.parent / "schemas"


def load_schema(name: str) -> dict:
    with open(SCHEMAS_DIR / name) as f:
        return json.load(f)


class TestCreateUser:
    def test_create_user_returns_201(self, api):
        resp = api.post("/users/add", {"firstName": "Priya", "lastName": "Bhagoriya", "email": "priya@test.com", "age": 28})
        assert resp.status_code == 201

    def test_create_user_response_matches_schema(self, api):
        resp = api.post("/users/add", {"firstName": "Priya", "lastName": "Bhagoriya", "email": "priya@test.com", "age": 28})
        schema = load_schema("create_user_response_schema.json")
        jsonschema.validate(instance=resp.json(), schema=schema)

    def test_create_user_echoes_submitted_data(self, api):
        payload = {"firstName": "Priya", "lastName": "Bhagoriya", "email": "priya@test.com", "age": 28}
        resp = api.post("/users/add", payload)
        body = resp.json()
        assert body["firstName"] == payload["firstName"]
        assert body["lastName"] == payload["lastName"]
        assert body["email"] == payload["email"]

    def test_create_user_returns_generated_id(self, api):
        resp = api.post("/users/add", {"firstName": "Test", "lastName": "User", "age": 25})
        assert "id" in resp.json()
        assert isinstance(resp.json()["id"], int)

    @pytest.mark.parametrize("first,last,email", [
        ("Alice", "Dev", "alice@test.com"),
        ("Bob", "Design", "bob@test.com"),
        ("Carol", "QA", "carol@test.com"),
    ])
    def test_create_multiple_users_parametrized(self, api, first, last, email):
        resp = api.post("/users/add", {"firstName": first, "lastName": last, "email": email, "age": 30})
        assert resp.status_code == 201
        assert resp.json()["firstName"] == first
        assert resp.json()["lastName"] == last
