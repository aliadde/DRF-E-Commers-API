from datetime import timedelta

import pytest
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(api_client) -> dict:

    class User:
        def __init__(self, id, username, email, password):
            self.id = id
            self.username = username
            self.email = email
            self.password = password

    user: dict = api_client.post(
        "/user/register/",
        {
            "username": "testuser",
            "email": "test_user@gmail.com",
            "password": "test-password-123",
        },
        format="json",
    ).json()
    user = User(
        id=user.get("id"),
        username=user.get("username"),
        email=user.get("email"),
        password="test-password-123",
    )
    return user


@pytest.fixture
def tokens(api_client, user):
    response = api_client.post(
        "/user/login/",
        {
            "username": user.username,
            "password": user.password,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK

    return response.json()


def authenticate(client, access_token):
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")


class TestJWTAuthentication:
    def test_valid_access_token_can_access_me(
        self,
        api_client,
        tokens,
        user,
    ):
        authenticate(api_client, tokens["access"])

        response = api_client.get("/user/me/")

        assert response.status_code == status.HTTP_200_OK

    def test_invalid_access_token_is_rejected(
        self,
        api_client,
    ):
        authenticate(api_client, "this-is-not-a-valid-jwt")

        response = api_client.get("/user/me/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_missing_access_token_is_rejected(
        self,
        api_client,
    ):
        response = api_client.get("/user/me/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_token_returns_new_tokens(
        self,
        api_client,
        tokens,
    ):
        old_refresh_token = tokens["refresh"]

        response = api_client.post(
            "/token/refresh/",
            {
                "refresh": old_refresh_token,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert "access" in data
        assert "refresh" in data

        assert data["refresh"] != old_refresh_token

    def test_old_refresh_token_is_invalid_after_rotation(
        self,
        api_client,
        tokens,
    ):
        old_refresh_token = tokens["refresh"]

        # First refresh rotates the refresh token.
        response = api_client.post(
            "/token/refresh/",
            {
                "refresh": old_refresh_token,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        new_refresh_token = response.json()["refresh"]

        assert new_refresh_token != old_refresh_token

        # Try using the old refresh token again.
        response = api_client.post(
            "/token/refresh/",
            {
                "refresh": old_refresh_token,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # The new refresh token must still work.
        response = api_client.post(
            "/token/refresh/",
            {
                "refresh": new_refresh_token,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

    def test_expired_access_token_is_rejected(
        self,
        api_client,
        user,
        monkeypatch,
    ):
        # Make newly-created access tokens live for only 1 second.
        monkeypatch.setattr(
            AccessToken,
            "lifetime",
            timedelta(seconds=1),
        )

        token = str(AccessToken.for_user(user))

        authenticate(api_client, token)

        # Token is still valid immediately after creation.
        response = api_client.get("/user/me/")

        assert response.status_code == status.HTTP_200_OK

        # Move time forward by changing the token's expiration.
        # We don't use sleep(1) because that makes the test unnecessarily slow/flaky.
        token_obj = AccessToken(token)

        token_obj.set_exp(
            from_time=token_obj.current_time,
            lifetime=timedelta(seconds=-1),
        )

        expired_token = str(token_obj)

        authenticate(api_client, expired_token)

        response = api_client.get("/user/me/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
