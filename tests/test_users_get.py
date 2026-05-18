import json
from pathlib import Path
import jsonschema
import pytest

SCHEMAS_DIR = Path(__file__).parent.parent / "schemas"


def load_schema(name: str) -> dict:
    with open(SCHEMAS_DIR / name) as f:
        return json.load(f)


class TestGetUsers:
    def test_list_users_returns_200(self, api):
        resp = api.get("/users", params={"limit": 6, "skip": 0})
        assert resp.status_code == 200

    def test_list_users_response_time_under_2s(self, api):
        resp = api.get("/users", params={"limit": 6, "skip": 0})
        assert resp.elapsed.total_seconds() < 2.0

    def test_list_users_matches_schema(self, api):
        resp = api.get("/users", params={"limit": 6, "skip": 0})
        schema = load_schema("user_list_schema.json")
        jsonschema.validate(instance=resp.json(), schema=schema)

    def test_list_users_returns_six_per_page(self, api):
        resp = api.get("/users", params={"limit": 6, "skip": 0})
        data = resp.json()
        assert data["limit"] == 6
        assert len(data["users"]) == 6

    def test_list_users_page2_has_different_users(self, api):
        page1 = api.get("/users", params={"limit": 6, "skip": 0}).json()["users"]
        page2 = api.get("/users", params={"limit": 6, "skip": 6}).json()["users"]
        ids_p1 = {u["id"] for u in page1}
        ids_p2 = {u["id"] for u in page2}
        assert ids_p1.isdisjoint(ids_p2)

    def test_single_user_returns_200(self, api):
        resp = api.get("/users/1")
        assert resp.status_code == 200

    def test_single_user_matches_schema(self, api):
        resp = api.get("/users/1")
        schema = load_schema("user_schema.json")
        jsonschema.validate(instance=resp.json(), schema=schema)

    def test_single_user_id_matches_request(self, api):
        resp = api.get("/users/2")
        assert resp.json()["id"] == 2

    def test_nonexistent_user_returns_404(self, api):
        resp = api.get("/users/999")
        assert resp.status_code == 404

    def test_nonexistent_user_returns_error_message(self, api):
        resp = api.get("/users/999")
        assert "message" in resp.json()

    @pytest.mark.parametrize("user_id", [1, 2, 3, 4, 5, 6])
    def test_valid_user_ids_return_200(self, api, user_id):
        resp = api.get(f"/users/{user_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == user_id
