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
        "username": "Jane",
        "email": "newuser@example.com",
    }


@pytest.fixture
def register_login(api_client, valid_payload) -> tuple[str]:
    # register
    valid_payload["password"] = "StrongPassword123!"
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
def test_patch_user_success(api_client, url, valid_payload, register_login):
    """success registeration."""
    token, refresh = register_login
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    new_data = valid_payload.copy()
    new_data["username"] = "testuser"

    response = api_client.patch(url, data=new_data, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert "username" in response.json()
    assert response.json().get("username") == "testuser"
    assert "email" in response.json()
    assert "last_login" in response.json()
    assert "password" not in response.json()


@pytest.mark.django_db
def test_patch_user_unauthenticated_returns_401(api_client, url, valid_payload):
    """no credentials provided -> request must be rejected."""
    response = api_client.patch(url, data={"username": "hacker"}, format="json")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_patch_user_invalid_token_returns_401(api_client, url):
    """garbage/expired token -> request must be rejected."""
    api_client.credentials(HTTP_AUTHORIZATION="Bearer invalid.token.value")

    response = api_client.patch(url, data={"username": "hacker"}, format="json")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_patch_user_partial_update_only_username(api_client, url, register_login):
    """PATCH with a single field must not require the others and must not wipe them."""
    token, refresh = register_login
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    response = api_client.patch(url, data={"username": "onlyusername"}, format="json")

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body.get("username") == "onlyusername"
    assert (
        body.get("email") == "newuser@example.com"
    )  # untouched, still from valid_payload


@pytest.mark.django_db
def test_patch_user_partial_update_only_email(api_client, url, register_login):
    """PATCH with only email must leave username untouched."""
    token, refresh = register_login
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    response = api_client.patch(
        url, data={"email": "changed@example.com"}, format="json"
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body.get("email") == "changed@example.com"
    assert body.get("username") == "Jane"  # untouched, still from valid_payload


@pytest.mark.django_db
def test_patch_user_empty_payload_returns_200_and_no_changes(
    api_client, url, register_login
):
    """empty body is valid for PATCH -> should just return current representation unchanged."""
    token, refresh = register_login
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    response = api_client.patch(url, data={}, format="json")

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body.get("username") == "Jane"
    assert body.get("email") == "newuser@example.com"


@pytest.mark.django_db
def test_patch_user_invalid_email_format_returns_400(api_client, url, register_login):
    """malformed email must fail serializer validation."""
    token, refresh = register_login
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    response = api_client.patch(url, data={"email": "not-an-email"}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "email" in response.json()


@pytest.mark.django_db
def test_patch_user_duplicate_email_returns_400(api_client, url, register_login):
    """email already used by another user must be rejected."""
    # create a second, separate user owning "taken@example.com"
    other_payload = {
        "username": "other",
        "email": "taken@example.com",
        "password": "AnotherStrongPass123!",
    }
    api_client.post(reverse("users_register"), data=other_payload)

    token, refresh = register_login
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    response = api_client.patch(url, data={"email": "taken@example.com"}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "email" in response.json()


@pytest.mark.django_db
def test_patch_user_duplicate_username_returns_400(api_client, url, register_login):
    """username already used by another user must be rejected."""
    other_payload = {
        "username": "takenname",
        "email": "someoneelse@example.com",
        "password": "AnotherStrongPass123!",
    }
    api_client.post(reverse("users_register"), data=other_payload)

    token, refresh = register_login
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    response = api_client.patch(url, data={"username": "takenname"}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "username" in response.json()


@pytest.mark.django_db
def test_patch_user_can_change_own_username_to_same_value(
    api_client, url, register_login
):
    """updating a field to its own current value must not be rejected as 'duplicate'."""
    token, refresh = register_login
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    response = api_client.patch(url, data={"username": "Jane"}, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("username") == "Jane"


@pytest.mark.django_db
def test_patch_user_cannot_change_id(api_client, url, register_login):
    """id/pk must be read-only, not overridable via PATCH body."""
    token, refresh = register_login
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    user = Users.objects.get(username="Jane")
    original_id = user.id

    response = api_client.patch(url, data={"id": original_id + 999}, format="json")

    assert response.status_code == status.HTTP_200_OK
    user.refresh_from_db()
    assert user.id == original_id


@pytest.mark.django_db
def test_patch_user_unknown_field_is_ignored(api_client, url, register_login):
    """fields not defined on the serializer must be silently ignored, not error."""
    token, refresh = register_login
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    response = api_client.patch(
        url,
        data={"username": "stillvalid", "not_a_real_field": "whatever"},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("username") == "stillvalid"


@pytest.mark.django_db
def test_patch_user_only_updates_authenticated_users_own_record(
    api_client, url, register_login
):
    """PATCH on the private endpoint must only ever affect request.user, never another user's row."""
    other_payload = {
        "username": "bystander",
        "email": "bystander@example.com",
        "password": "AnotherStrongPass123!",
    }
    api_client.post(reverse("users_register"), data=other_payload)
    bystander = Users.objects.get(username="bystander")

    token, refresh = register_login
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    api_client.patch(url, data={"username": "janechanged"}, format="json")

    bystander.refresh_from_db()
    assert bystander.username == "bystander"  # untouched
