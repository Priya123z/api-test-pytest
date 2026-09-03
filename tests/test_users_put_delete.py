import pytest


class TestUpdateUser:
    @pytest.mark.users
    @pytest.mark.smoke
    def test_put_user_returns_200(self, api):
        resp = api.put("/users/2", {"firstName": "Priya", "lastName": "Bhagoriya"})
        assert resp.status_code == 200

    @pytest.mark.users
    def test_put_user_echoes_updated_data(self, api):
        payload = {"firstName": "Priya", "lastName": "Bhagoriya"}
        resp = api.put("/users/2", payload)
        body = resp.json()
        assert body["firstName"] == payload["firstName"]
        assert body["lastName"] == payload["lastName"]

    @pytest.mark.users
    def test_put_user_preserves_id(self, api):
        resp = api.put("/users/2", {"firstName": "Updated"})
        assert resp.json()["id"] == 2

    @pytest.mark.users
    def test_patch_user_returns_200(self, api):
        resp = api.patch("/users/2", {"lastName": "SDET"})
        assert resp.status_code == 200

    @pytest.mark.users
    def test_patch_user_partial_update_reflected(self, api):
        payload = {"lastName": "PrincipalSDE"}
        resp = api.patch("/users/2", payload)
        assert resp.json()["lastName"] == payload["lastName"]


class TestDeleteUser:
    @pytest.mark.users
    @pytest.mark.smoke
    def test_delete_user_returns_200(self, api):
        resp = api.delete("/users/1")
        assert resp.status_code == 200

    @pytest.mark.users
    def test_delete_user_returns_deleted_flag(self, api):
        resp = api.delete("/users/3")
        body = resp.json()
        assert body.get("isDeleted") is True

    @pytest.mark.parametrize("user_id", [4, 5, 6])
    @pytest.mark.users
    def test_delete_multiple_users_return_200(self, api, user_id):
        resp = api.delete(f"/users/{user_id}")
        assert resp.status_code == 200
        assert resp.json().get("isDeleted") is True
