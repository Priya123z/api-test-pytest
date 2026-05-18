import pytest


class TestUpdateUser:
    def test_put_user_returns_200(self, api):
        resp = api.put("/api/users/2", {"name": "Priya", "job": "Senior SDET"})
        assert resp.status_code == 200

    def test_put_user_echoes_updated_data(self, api):
        payload = {"name": "Priya B", "job": "QA Lead"}
        resp = api.put("/api/users/2", payload)
        body = resp.json()
        assert body["name"] == payload["name"]
        assert body["job"] == payload["job"]

    def test_put_user_returns_updatedAt_timestamp(self, api):
        resp = api.put("/api/users/2", {"name": "Test", "job": "Tester"})
        assert "updatedAt" in resp.json()

    def test_patch_user_returns_200(self, api):
        resp = api.patch("/api/users/2", {"job": "Staff Engineer"})
        assert resp.status_code == 200

    def test_patch_user_partial_update_reflected(self, api):
        payload = {"job": "Principal SDET"}
        resp = api.patch("/api/users/2", payload)
        assert resp.json()["job"] == payload["job"]


class TestDeleteUser:
    def test_delete_user_returns_204(self, api):
        resp = api.delete("/api/users/2")
        assert resp.status_code == 204

    def test_delete_user_returns_no_body(self, api):
        resp = api.delete("/api/users/3")
        assert resp.content == b""

    @pytest.mark.parametrize("user_id", [4, 5, 6])
    def test_delete_multiple_users_return_204(self, api, user_id):
        resp = api.delete(f"/api/users/{user_id}")
        assert resp.status_code == 204
