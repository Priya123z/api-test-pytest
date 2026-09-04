import jsonschema
import pytest

RESPONSE_TIME_CEILING_SECONDS = 5.0


class TestGetUsers:
    @pytest.mark.users
    @pytest.mark.smoke
    def test_list_users_returns_200(self, api):
        resp = api.get("/users", params={"limit": 6, "skip": 0})
        assert resp.status_code == 200

    @pytest.mark.users
    def test_list_users_responds_within_the_agreed_ceiling(self, api):
        # A wall-clock assertion against a public API from a shared runner. Two seconds
        # was tight enough to fail on a slow runner rather than on a real regression,
        # which trains people to ignore the suite. This is a smoke-alarm ceiling, not
        # a performance test; do that separately with percentiles over many samples.
        resp = api.get("/users", params={"limit": 6, "skip": 0})
        assert resp.status_code == 200
        assert resp.elapsed.total_seconds() < RESPONSE_TIME_CEILING_SECONDS

    @pytest.mark.users
    def test_list_users_matches_schema(self, api, load_schema):
        resp = api.get("/users", params={"limit": 6, "skip": 0})
        schema = load_schema("user_list_schema.json")
        jsonschema.validate(instance=resp.json(), schema=schema)

    @pytest.mark.users
    def test_list_users_returns_six_per_page(self, api):
        resp = api.get("/users", params={"limit": 6, "skip": 0})
        data = resp.json()
        assert data["limit"] == 6
        assert len(data["users"]) == 6

    @pytest.mark.users
    def test_list_users_page2_has_different_users(self, api):
        page1 = api.get("/users", params={"limit": 6, "skip": 0}).json()["users"]
        page2 = api.get("/users", params={"limit": 6, "skip": 6}).json()["users"]
        ids_p1 = {u["id"] for u in page1}
        ids_p2 = {u["id"] for u in page2}
        assert ids_p1.isdisjoint(ids_p2)

    @pytest.mark.users
    @pytest.mark.smoke
    def test_single_user_returns_200(self, api):
        resp = api.get("/users/1")
        assert resp.status_code == 200

    @pytest.mark.users
    def test_single_user_matches_schema(self, api, load_schema):
        resp = api.get("/users/1")
        schema = load_schema("user_schema.json")
        jsonschema.validate(instance=resp.json(), schema=schema)

    @pytest.mark.users
    def test_single_user_id_matches_request(self, api):
        resp = api.get("/users/2")
        assert resp.json()["id"] == 2

    @pytest.mark.users
    @pytest.mark.smoke
    def test_nonexistent_user_returns_404(self, api):
        resp = api.get("/users/999")
        assert resp.status_code == 404

    @pytest.mark.users
    def test_nonexistent_user_returns_error_message(self, api):
        resp = api.get("/users/999")
        assert "message" in resp.json()

    @pytest.mark.parametrize("user_id", [1, 2, 3, 4, 5, 6])
    @pytest.mark.users
    def test_valid_user_ids_return_200(self, api, user_id):
        resp = api.get(f"/users/{user_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == user_id
