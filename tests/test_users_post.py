import json
from pathlib import Path
import jsonschema
import pytest



class TestCreateUser:
    @pytest.mark.users
    @pytest.mark.smoke
    def test_create_user_returns_201(self, api):
        resp = api.post("/users/add", {"firstName": "Priya", "lastName": "Bhagoriya", "email": "priya@test.com", "age": 28})
        assert resp.status_code == 201

    @pytest.mark.users
    def test_create_user_response_matches_schema(self, api, load_schema):
        resp = api.post("/users/add", {"firstName": "Priya", "lastName": "Bhagoriya", "email": "priya@test.com", "age": 28})
        schema = load_schema("create_user_response_schema.json")
        jsonschema.validate(instance=resp.json(), schema=schema)

    @pytest.mark.users
    def test_create_user_echoes_submitted_data(self, api):
        payload = {"firstName": "Priya", "lastName": "Bhagoriya", "email": "priya@test.com", "age": 28}
        resp = api.post("/users/add", payload)
        body = resp.json()
        assert body["firstName"] == payload["firstName"]
        assert body["lastName"] == payload["lastName"]
        assert body["email"] == payload["email"]

    @pytest.mark.users
    def test_create_user_returns_generated_id(self, api):
        resp = api.post("/users/add", {"firstName": "Test", "lastName": "User", "age": 25})
        assert "id" in resp.json()
        assert isinstance(resp.json()["id"], int)

    @pytest.mark.parametrize("first,last,email", [
        ("Alice", "Dev", "alice@test.com"),
        ("Bob", "Design", "bob@test.com"),
        ("Carol", "QA", "carol@test.com"),
    ])
    @pytest.mark.users
    def test_create_multiple_users_parametrized(self, api, first, last, email):
        resp = api.post("/users/add", {"firstName": first, "lastName": last, "email": email, "age": 30})
        assert resp.status_code == 201
        assert resp.json()["firstName"] == first
        assert resp.json()["lastName"] == last
