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
        resp = api.post("/api/users", {"name": "Priya", "job": "QA Engineer"})
        assert resp.status_code == 201

    def test_create_user_response_matches_schema(self, api):
        resp = api.post("/api/users", {"name": "Priya", "job": "QA Engineer"})
        schema = load_schema("create_user_response_schema.json")
        jsonschema.validate(instance=resp.json(), schema=schema)

    def test_create_user_echoes_submitted_data(self, api):
        payload = {"name": "Priya Bhagoriya", "job": "SDET"}
        resp = api.post("/api/users", payload)
        body = resp.json()
        assert body["name"] == payload["name"]
        assert body["job"] == payload["job"]

    def test_create_user_returns_generated_id(self, api):
        resp = api.post("/api/users", {"name": "Test", "job": "Tester"})
        assert "id" in resp.json()
        assert len(resp.json()["id"]) > 0

    def test_create_user_returns_timestamp(self, api):
        resp = api.post("/api/users", {"name": "Test", "job": "Tester"})
        assert "createdAt" in resp.json()

    @pytest.mark.parametrize("name,job", [
        ("Alice", "Developer"),
        ("Bob", "Designer"),
        ("Carol", "QA Lead"),
    ])
    def test_create_multiple_users_parametrized(self, api, name, job):
        resp = api.post("/api/users", {"name": name, "job": job})
        assert resp.status_code == 201
        assert resp.json()["name"] == name
        assert resp.json()["job"] == job
