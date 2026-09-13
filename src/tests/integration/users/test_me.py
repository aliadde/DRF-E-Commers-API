import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from django_ecommers.apps.users.models import Users


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def url():
    return reverse("users_private")


@pytest.fixture
def valid_payload():
    return {
        "email": "newuser@example.com",
        "password": "StrongPassword123!",
        "username": "Jane",
    }


@pytest.fixture
def register_login(api_client, valid_payload) -> tuple[str]:
    # register
    api_client.post(reverse("users_register"), data=valid_payload)
    # login
    login_response = api_client.post(
        reverse("login"),
        data={
            "username": valid_payload["username"],
            "password": valid_payload["password"],
        },
    )
    # return access token and refresh token
    login_response.status_code == status.HTTP_200_OK

    access_token = login_response.json().get("access")
    refresh_token = login_response.json().get("refresh")

    return access_token, refresh_token


@pytest.mark.django_db
def test_get_me_user_success(api_client, url, register_login):
    """success registeration."""
    token, refresh = register_login

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert "id" in response.data
    assert "username" in response.data
    assert "email" in response.data
    assert "last_login" in response.data


@pytest.mark.django_db
def test_get_me_unauthenticated(api_client, url):
    """No token provided, should return 401."""
    response = api_client.get(url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_get_me_invalid_token(api_client, url):
    """Invalid/fake token, should return 401."""
    api_client.credentials(HTTP_AUTHORIZATION="Bearer this.is.not.a.valid.token")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_get_me_malformed_authorization_header(api_client, url, register_login):
    """Authorization header missing the 'Bearer' prefix or wrong format."""
    token, _ = register_login

    api_client.credentials(HTTP_AUTHORIZATION=token)  # missing "Bearer "
    response = api_client.get(url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_get_me_with_refresh_token_instead_of_access(api_client, url, register_login):
    """Using a refresh token instead of an access token for auth should be rejected."""
    _, refresh = register_login

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh}")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_get_me_does_not_expose_password(api_client, url, register_login):
    """Password or other sensitive fields must not be exposed in the response."""
    token, _ = register_login

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert "password" not in response.data


@pytest.mark.django_db
def test_get_me_returns_correct_user_data(
    api_client, url, register_login, valid_payload
):
    """Returned data must belong to the currently logged-in user."""
    token, _ = register_login

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["email"] == valid_payload["email"]
    assert response.data["username"] == valid_payload["username"]


@pytest.mark.django_db
def test_get_me_method_not_allowed_post(api_client, url, register_login):
    """If the endpoint only supports GET/PATCH, POST should return 405."""
    token, _ = register_login

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    response = api_client.post(url, data={})

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
def test_get_me_after_user_deleted(api_client, url, register_login):
    """If the user is deleted after login, access should no longer be valid."""
    token, _ = register_login
    Users.objects.all().delete()

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    response = api_client.get(url)

    assert response.status_code in (
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_404_NOT_FOUND,
    )
