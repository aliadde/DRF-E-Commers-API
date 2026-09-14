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
    return reverse("reset_password")


@pytest.fixture
def valid_payload():
    return {
        "username": "Jane",
        "email": "newuser@example.com",
        "password": "StrongPassword123!",
    }


@pytest.fixture
def register_login(api_client, valid_payload) -> tuple[str, str]:
    # register
    api_client.post(
        reverse("users_register"),
        data=valid_payload,
    )

    # login
    login_response = api_client.post(
        reverse("login"),
        data={
            "username": valid_payload["username"],
            "password": valid_payload["password"],
        },
    )

    assert login_response.status_code == status.HTTP_200_OK

    access_token = login_response.json().get("access")
    refresh_token = login_response.json().get("refresh")

    return access_token, refresh_token


# ========================
# Success
# ========================


@pytest.mark.django_db
def test_reset_password(api_client, url, valid_payload, register_login):
    """Password is successfully reset."""
    token, refresh = register_login

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    data: dict[str, str] = {
        "current_password": valid_payload["password"],
        "new_password": "NewPassword123!",
    }

    response = api_client.post(
        url,
        data=data,
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert "password" not in response.json()
    assert "new_password" not in response.json()
    assert "message" in response.json()
    assert response.json()["message"] == ("Your password reset successfully.")


# ========================
# Wrong Current Password
# ========================


@pytest.mark.django_db
def test_reset_password_with_incorrect_current_password(
    api_client,
    url,
    valid_payload,
    register_login,
):
    """Password is not reset when current password is incorrect."""
    token, refresh = register_login

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    data: dict[str, str] = {
        "current_password": "WrongPassword123!",
        "new_password": "NewPassword123!",
    }

    response = api_client.post(
        url,
        data=data,
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "error" in response.json()
    assert response.json()["error"] == ("Your current_password is incorrect.")


# ========================
# Authentication
# ========================


@pytest.mark.django_db
def test_reset_password_without_authentication(
    api_client,
    url,
):
    """Unauthenticated user cannot reset password."""

    data: dict[str, str] = {
        "current_password": "StrongPassword123!",
        "new_password": "NewPassword123!",
    }

    response = api_client.post(
        url,
        data=data,
        format="json",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ========================
# Missing Fields
# ========================


@pytest.mark.django_db
def test_reset_password_without_current_password(
    api_client,
    url,
    valid_payload,
    register_login,
):
    """Current password is required."""
    token, refresh = register_login

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    data: dict[str, str] = {
        "new_password": "NewPassword123!",
    }

    response = api_client.post(
        url,
        data=data,
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "current_password" in response.json()


@pytest.mark.django_db
def test_reset_password_without_new_password(
    api_client,
    url,
    valid_payload,
    register_login,
):
    """New password is required."""
    token, refresh = register_login

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    data: dict[str, str] = {
        "current_password": valid_payload["password"],
    }

    response = api_client.post(
        url,
        data=data,
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "new_password" in response.json()


@pytest.mark.django_db
def test_reset_password_without_passwords(
    api_client,
    url,
    valid_payload,
    register_login,
):
    """Both passwords are required."""
    token, refresh = register_login

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    response = api_client.post(
        url,
        data={},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "current_password" in response.json()
    assert "new_password" in response.json()


# ========================
# Empty Values
# ========================


@pytest.mark.django_db
def test_reset_password_with_empty_current_password(
    api_client,
    url,
    valid_payload,
    register_login,
):
    """Empty current password is rejected."""
    token, refresh = register_login

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    data: dict[str, str] = {
        "current_password": "",
        "new_password": "NewPassword123!",
    }

    response = api_client.post(
        url,
        data=data,
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "current_password" in response.json()


@pytest.mark.django_db
def test_reset_password_with_empty_new_password(
    api_client,
    url,
    valid_payload,
    register_login,
):
    """Empty new password is rejected."""
    token, refresh = register_login

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    data: dict[str, str] = {
        "current_password": valid_payload["password"],
        "new_password": "",
    }

    response = api_client.post(
        url,
        data=data,
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "new_password" in response.json()


# ========================
# Verify Password Change
# ========================


@pytest.mark.django_db
def test_reset_password_really_changes_password(
    api_client,
    url,
    valid_payload,
    register_login,
):
    """New password works and old password no longer works."""
    token, refresh = register_login

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    new_password = "NewPassword123!"

    data: dict[str, str] = {
        "current_password": valid_payload["password"],
        "new_password": new_password,
    }

    response = api_client.post(
        url,
        data=data,
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK

    user = Users.objects.get(username=valid_payload["username"])

    assert user.check_password(new_password)
    assert not user.check_password(valid_payload["password"])
