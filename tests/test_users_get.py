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
        resp = api.get("/api/users", params={"page": 1})
        assert resp.status_code == 200

    def test_list_users_response_time_under_2s(self, api):
        resp = api.get("/api/users", params={"page": 1})
        assert resp.elapsed.total_seconds() < 2.0

    def test_list_users_matches_schema(self, api):
        resp = api.get("/api/users", params={"page": 1})
        schema = load_schema("user_list_schema.json")
        jsonschema.validate(instance=resp.json(), schema=schema)

    def test_list_users_returns_six_per_page(self, api):
        resp = api.get("/api/users", params={"page": 1})
        data = resp.json()
        assert data["per_page"] == 6
        assert len(data["data"]) == 6

    def test_list_users_page2_has_different_users(self, api):
        page1 = api.get("/api/users", params={"page": 1}).json()["data"]
        page2 = api.get("/api/users", params={"page": 2}).json()["data"]
        ids_p1 = {u["id"] for u in page1}
        ids_p2 = {u["id"] for u in page2}
        assert ids_p1.isdisjoint(ids_p2)

    def test_single_user_returns_200(self, api):
        resp = api.get("/api/users/1")
        assert resp.status_code == 200

    def test_single_user_matches_schema(self, api):
        resp = api.get("/api/users/1")
        schema = load_schema("user_schema.json")
        jsonschema.validate(instance=resp.json()["data"], schema=schema)

    def test_single_user_id_matches_request(self, api):
        resp = api.get("/api/users/2")
        assert resp.json()["data"]["id"] == 2

    def test_nonexistent_user_returns_404(self, api):
        resp = api.get("/api/users/999")
        assert resp.status_code == 404

    def test_nonexistent_user_returns_empty_body(self, api):
        resp = api.get("/api/users/999")
        assert resp.json() == {}

    @pytest.mark.parametrize("user_id", [1, 2, 3, 4, 5, 6])
    def test_valid_user_ids_return_200(self, api, user_id):
        resp = api.get(f"/api/users/{user_id}")
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == user_id
