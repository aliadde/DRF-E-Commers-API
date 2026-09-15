import pytest


@pytest.fixture
def user() -> dict[str, str]:
    return {
        "username": "tester",
        "password": "testpass123",
        "email": "tester@gmail.com",
    }


@pytest.fixture
def register_user(user, api_client) -> dict[str, str]:
    resp_register = api_client.post(
        "/user/register/",
        json=user,
    )

    assert resp_register.status_code == 201
    assert resp_register.json().get("username") == user["username"]
    assert resp_register.json().get("email") == user["email"]

    return user


@pytest.fixture
def authenticated_client(register_user, api_client):
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

    api_client.headers = {
        "Authorization": f"Bearer {access_token}",
    }

    return api_client


@pytest.mark.django_db
class TestResetPasswordE2E:
    """User register, login, and reset password."""

    def test_reset_password_success(
        self,
        register_user,
        authenticated_client,
    ):
        user = register_user
        new_password = "newpass123"

        resp_reset_password = authenticated_client.post(
            "/user/reset_password/",
            json={
                "current_password": user["password"],
                "new_password": new_password,
            },
        )

        assert resp_reset_password.status_code == 200
        assert resp_reset_password.json() == {
            "message": "Your password reset successfully."
        }

        # New password must work.
        login_response = authenticated_client.post(
            "/user/login/",
            json={
                "username": user["username"],
                "password": new_password,
            },
        )

        assert login_response.status_code == 200
        assert login_response.json().get("access")

    def test_reset_password_with_wrong_current_password(
        self,
        register_user,
        authenticated_client,
    ):
        user = register_user

        resp_reset_password = authenticated_client.post(
            "/user/reset_password/",
            json={
                "current_password": "wrong-password",
                "new_password": "newpass123",
            },
        )

        assert resp_reset_password.status_code == 400
        assert resp_reset_password.json() == {
            "error": "Your current_password is incorrect."
        }

        # Password must remain unchanged.
        login_response = authenticated_client.post(
            "/user/login/",
            json={
                "username": user["username"],
                "password": user["password"],
            },
        )

        assert login_response.status_code == 200

    def test_reset_password_without_authentication(
        self,
        register_user,
        api_client,
    ):
        user = register_user

        response = api_client.post(
            "/user/reset_password/",
            json={
                "current_password": user["password"],
                "new_password": "newpass123",
            },
        )

        assert response.status_code == 401

    @pytest.mark.parametrize(
        "payload",
        [
            {
                "new_password": "newpass123",
            },
            {
                "current_password": "testpass123",
            },
            {},
        ],
    )
    def test_reset_password_missing_required_field(
        self,
        authenticated_client,
        payload,
    ):
        response = authenticated_client.post(
            "/user/reset_password/",
            json=payload,
        )

        assert response.status_code == 400
        assert response.json()

    @pytest.mark.parametrize(
        "current_password,new_password",
        [
            ("", "newpass123"),
            ("testpass123", ""),
            ("", ""),
        ],
    )
    def test_reset_password_with_blank_password(
        self,
        authenticated_client,
        current_password,
        new_password,
    ):
        response = authenticated_client.post(
            "/user/reset_password/",
            json={
                "current_password": current_password,
                "new_password": new_password,
            },
        )

        assert response.status_code == 400
        assert response.json()

    def test_reset_password_new_password_becomes_active(
        self,
        register_user,
        authenticated_client,
    ):
        user = register_user
        new_password = "completely-new-password123"

        response = authenticated_client.post(
            "/user/reset_password/",
            json={
                "current_password": user["password"],
                "new_password": new_password,
            },
        )

        assert response.status_code == 200

        # Old password must no longer work.
        old_login = authenticated_client.post(
            "/user/login/",
            json={
                "username": user["username"],
                "password": user["password"],
            },
        )

        assert old_login.status_code == 401

        # New password must work.
        new_login = authenticated_client.post(
            "/user/login/",
            json={
                "username": user["username"],
                "password": new_password,
            },
        )

        assert new_login.status_code == 200
        assert new_login.json().get("access")

    def test_reset_password_with_same_password(
        self,
        register_user,
        authenticated_client,
    ):
        user = register_user

        response = authenticated_client.post(
            "/user/reset_password/",
            json={
                "current_password": user["password"],
                "new_password": user["password"],
            },
        )

        # Current implementation allows using the same password.
        assert response.status_code == 200

        login_response = authenticated_client.post(
            "/user/login/",
            json={
                "username": user["username"],
                "password": user["password"],
            },
        )

        assert login_response.status_code == 200

    def test_reset_password_with_invalid_token(
        self,
        register_user,
        api_client,
    ):
        register_user

        api_client.headers = {
            "Authorization": "Bearer invalid-token",
        }

        response = api_client.post(
            "/user/reset_password/",
            json={
                "current_password": "testpass123",
                "new_password": "newpass123",
            },
        )

        assert response.status_code == 401

    def test_reset_password_with_malformed_authorization_header(
        self,
        register_user,
        api_client,
    ):
        register_user

        api_client.headers = {
            "Authorization": "NotBearer some-token",
        }

        response = api_client.post(
            "/user/reset_password/",
            json={
                "current_password": "testpass123",
                "new_password": "newpass123",
            },
        )

        assert response.status_code == 401

    def test_reset_password_does_not_accept_extra_fields(
        self,
        register_user,
        authenticated_client,
    ):
        user = register_user

        response = authenticated_client.post(
            "/user/reset_password/",
            json={
                "current_password": user["password"],
                "new_password": "newpass123",
                "username": "hacker",
                "email": "hacker@example.com",
            },
        )

        # DRF serializers.Serializer ignores unknown fields by default.
        assert response.status_code == 200

        login_response = authenticated_client.post(
            "/user/login/",
            json={
                "username": user["username"],
                "password": "newpass123",
            },
        )

        assert login_response.status_code == 200
