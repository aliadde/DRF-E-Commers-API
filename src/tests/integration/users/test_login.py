import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from django_ecommers.apps.users.models import Users


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def url():
    # آدرس واقعی url name خودتون رو اینجا جایگزین کنید
    return reverse("login")


@pytest.fixture
def valid_payload():
    return {
        "email": "newuser@example.com",
        "password": "StrongPassword123!",
        "username": "Jane",
    }


@pytest.fixture
def registered_user(api_client, url, valid_payload):
    response = api_client.post(
        reverse("users_register"), data=valid_payload, format="json"
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert Users.objects.filter(email=valid_payload["email"]).exists()
    assert response.data["email"] == valid_payload["email"]
    assert "password" not in response.data
    return url, valid_payload


@pytest.mark.django_db
class TestLoginJWT:
    def test_success_login(self, api_client, registered_user):
        url, valid_payload = registered_user
        login_data = {
            "username": valid_payload["username"],
            "password": valid_payload["password"],
        }
        login_response = api_client.post(url, data=login_data, format="json")

        assert login_response.status_code == status.HTTP_200_OK
        assert "access" in login_response.data
        assert "refresh" in login_response.data

    def test_login_wrong_password(self, api_client, registered_user):
        url, valid_payload = registered_user
        login_data = {
            "username": valid_payload["username"],
            "password": "WrongPassword123!",
        }
        response = api_client.post(url, data=login_data, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "access" not in response.data
        assert "refresh" not in response.data

    def test_login_nonexistent_username(self, api_client, registered_user):
        url, _ = registered_user
        login_data = {
            "username": "doesnotexist",
            "password": "StrongPassword123!",
        }
        response = api_client.post(url, data=login_data, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_missing_password(self, api_client, registered_user):
        url, valid_payload = registered_user
        login_data = {"username": valid_payload["username"]}
        response = api_client.post(url, data=login_data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password" in response.data

    def test_login_missing_username(self, api_client, registered_user):
        url, valid_payload = registered_user
        login_data = {"password": valid_payload["password"]}
        response = api_client.post(url, data=login_data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "username" in response.data

    def test_login_empty_payload(self, api_client, registered_user):
        url, _ = registered_user
        response = api_client.post(url, data={}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "username" in response.data
        assert "password" in response.data

    def test_login_blank_username(self, api_client, registered_user):
        url, valid_payload = registered_user
        login_data = {"username": "", "password": valid_payload["password"]}
        response = api_client.post(url, data=login_data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_blank_password(self, api_client, registered_user):
        url, valid_payload = registered_user
        login_data = {"username": valid_payload["username"], "password": ""}
        response = api_client.post(url, data=login_data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_username_case_sensitivity(self, api_client, registered_user):
        """Adjust expected status based on whether your auth backend is case-insensitive."""
        url, valid_payload = registered_user
        login_data = {
            "username": valid_payload["username"].upper(),
            "password": valid_payload["password"],
        }
        response = api_client.post(url, data=login_data, format="json")

        # If usernames are case-insensitive in your backend, expect 200 instead.
        assert response.status_code in (
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_login_extra_unexpected_fields_ignored(self, api_client, registered_user):
        url, valid_payload = registered_user
        login_data = {
            "username": valid_payload["username"],
            "password": valid_payload["password"],
            "is_admin": True,  # should be silently ignored, not cause a crash
        }
        response = api_client.post(url, data=login_data, format="json")

        assert response.status_code == status.HTTP_200_OK

    def test_login_sql_injection_attempt_safe(self, api_client, registered_user):
        url, _ = registered_user
        login_data = {
            "username": "' OR '1'='1",
            "password": "' OR '1'='1",
        }
        response = api_client.post(url, data=login_data, format="json")

        # Must not authenticate and must not 500 — confirms ORM param binding is safe.
        assert response.status_code in (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
        )
