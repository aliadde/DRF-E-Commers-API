import pytest


@pytest.fixture
def user() -> dict[str, str]:
    return {
        "username": "tester",
        "password": "testpass123",
        "email": "tester@gmail.com",
    }


@pytest.fixture
def register_user(user, api_client) -> dict[str, int | str]:

    resp_register = api_client.post(
        "/user/register/",
        json=user,
    )
    assert resp_register.status_code == 201
    assert resp_register.json().get("username") == "tester"
    assert resp_register.json().get("email") == "tester@gmail.com"

    return user


@pytest.mark.django_db
class TestLoginUpdateE2E:
    """User register, login, then update its own data."""

    def test_login_then_update_email(self, register_user, api_client):
        user = register_user

        login_data = {
            "username": user["username"],
            "password": user["password"],
        }

        resp_login = api_client.post("/user/login/", json=login_data)
        assert resp_login.status_code == 200

        access_token = resp_login.json().get("access")
        assert access_token

        new_email = "updated@gmail.com"

        api_client.headers = {"Authorization": f"Bearer {access_token}"}

        resp_patch = api_client.patch(
            "/user/me/",
            json={"email": new_email},
        )

        assert resp_patch.status_code == 200
        assert resp_patch.json().get("username") == user["username"]
        assert resp_patch.json().get("email") == new_email
        assert "last_login" in resp_patch.json()

    def test_login_then_update_username_and_email(self, register_user, api_client):
        user = register_user

        resp_login = api_client.post(
            "/user/login/",
            json={
                "username": user["username"],
                "password": user["password"],
            },
        )
        assert resp_login.status_code == 200

        access_token = resp_login.json().get("access")
        assert access_token

        new_username = "updated_tester"
        new_email = "updated@gmail.com"

        api_client.headers = {"Authorization": f"Bearer {access_token}"}

        resp_patch = api_client.patch(
            "/user/me/",
            json={
                "username": new_username,
                "email": new_email,
            },
        )

        assert resp_patch.status_code == 200
        assert resp_patch.json().get("username") == new_username
        assert resp_patch.json().get("email") == new_email
        assert "last_login" in resp_patch.json()

    def test_login_then_patch_only_allowed_fields(self, register_user, api_client):
        user = register_user

        resp_login = api_client.post(
            "/user/login/",
            json={
                "username": user["username"],
                "password": user["password"],
            },
        )
        assert resp_login.status_code == 200

        access_token = resp_login.json().get("access")
        assert access_token

        api_client.headers = {"Authorization": f"Bearer {access_token}"}

        resp_patch = api_client.patch(
            "/user/me/",
            json={"username": "updated_tester"},
        )

        assert resp_patch.status_code == 200
        assert set(resp_patch.json().keys()) == {
            "username",
            "email",
            "last_login",
        }

    def test_login_then_patch_empty_data(self, register_user, api_client):
        user = register_user

        resp_login = api_client.post(
            "/user/login/",
            json={
                "username": user["username"],
                "password": user["password"],
            },
        )
        assert resp_login.status_code == 200

        access_token = resp_login.json().get("access")
        assert access_token

        api_client.headers = {"Authorization": f"Bearer {access_token}"}

        resp_patch = api_client.patch(
            "/user/me/",
            json={},
        )

        assert resp_patch.status_code == 200
        assert resp_patch.json().get("username") == user["username"]
        assert resp_patch.json().get("email") == user["email"]

    def test_patch_without_authentication(self, register_user, api_client):
        resp_patch = api_client.patch(
            "/user/me/",
            json={"username": "updated_tester"},
        )

        assert resp_patch.status_code == 401

    def test_patch_with_invalid_token(self, register_user, api_client):
        api_client.headers = {"Authorization": "Bearer invalid-token"}

        resp_patch = api_client.patch(
            "/user/me/",
            json={"username": "updated_tester"},
        )

        assert resp_patch.status_code == 401

    def test_login_then_patch_invalid_email(self, register_user, api_client):
        user = register_user

        resp_login = api_client.post(
            "/user/login/",
            json={
                "username": user["username"],
                "password": user["password"],
            },
        )
        assert resp_login.status_code == 200

        access_token = resp_login.json().get("access")
        assert access_token

        api_client.headers = {"Authorization": f"Bearer {access_token}"}

        resp_patch = api_client.patch(
            "/user/me/",
            json={"email": "invalid-email"},
        )

        assert resp_patch.status_code == 400

    def test_login_then_patch_duplicate_username(self, register_user, api_client):
        user = register_user

        second_user = {
            "username": "second_user",
            "password": "testpass123",
            "email": "second@gmail.com",
        }

        resp_register = api_client.post(
            "/user/register/",
            json=second_user,
        )
        assert resp_register.status_code == 201

        resp_login = api_client.post(
            "/user/login/",
            json={
                "username": user["username"],
                "password": user["password"],
            },
        )
        assert resp_login.status_code == 200

        access_token = resp_login.json().get("access")
        assert access_token

        api_client.headers = {"Authorization": f"Bearer {access_token}"}

        resp_patch = api_client.patch(
            "/user/me/",
            json={"username": second_user["username"]},
        )

        assert resp_patch.status_code == 400

    def test_login_then_patch_duplicate_email(self, register_user, api_client):
        user = register_user

        second_user = {
            "username": "second_user",
            "password": "testpass123",
            "email": "second@gmail.com",
        }

        resp_register = api_client.post(
            "/user/register/",
            json=second_user,
        )
        assert resp_register.status_code == 201

        resp_login = api_client.post(
            "/user/login/",
            json={
                "username": user["username"],
                "password": user["password"],
            },
        )
        assert resp_login.status_code == 200

        access_token = resp_login.json().get("access")
        assert access_token

        api_client.headers = {"Authorization": f"Bearer {access_token}"}

        resp_patch = api_client.patch(
            "/user/me/",
            json={"email": second_user["email"]},
        )

        assert resp_patch.status_code == 400

    def test_login_then_patch_password_not_allowed(self, register_user, api_client):
        user = register_user

        resp_login = api_client.post(
            "/user/login/",
            json={
                "username": user["username"],
                "password": user["password"],
            },
        )
        assert resp_login.status_code == 200

        access_token = resp_login.json().get("access")
        assert access_token

        api_client.headers = {"Authorization": f"Bearer {access_token}"}

        resp_patch = api_client.patch(
            "/user/me/",
            json={"password": "newpassword123"},
        )

        assert resp_patch.status_code == 200

    def test_login_then_patch_non_allowed_field(self, register_user, api_client):
        user = register_user

        resp_login = api_client.post(
            "/user/login/",
            json={
                "username": user["username"],
                "password": user["password"],
            },
        )
        assert resp_login.status_code == 200

        access_token = resp_login.json().get("access")
        assert access_token

        api_client.headers = {"Authorization": f"Bearer {access_token}"}

        resp_patch = api_client.patch(
            "/user/me/",
            json={"id": 999},
        )

        assert resp_patch.status_code == 200
        assert resp_patch.json().get("username") == user["username"]

    def test_login_then_patch_null_username(self, register_user, api_client):
        user = register_user

        resp_login = api_client.post(
            "/user/login/",
            json={
                "username": user["username"],
                "password": user["password"],
            },
        )
        assert resp_login.status_code == 200

        access_token = resp_login.json().get("access")
        assert access_token

        api_client.headers = {"Authorization": f"Bearer {access_token}"}

        resp_patch = api_client.patch(
            "/user/me/",
            json={"username": None},
        )

        assert resp_patch.status_code == 400

    def test_login_then_patch_null_email(self, register_user, api_client):
        user = register_user

        resp_login = api_client.post(
            "/user/login/",
            json={
                "username": user["username"],
                "password": user["password"],
            },
        )
        assert resp_login.status_code == 200

        access_token = resp_login.json().get("access")
        assert access_token

        api_client.headers = {"Authorization": f"Bearer {access_token}"}

        resp_patch = api_client.patch(
            "/user/me/",
            json={"email": None},
        )

        assert resp_patch.status_code == 400
