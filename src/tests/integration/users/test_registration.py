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
    return reverse("users")


@pytest.fixture
def valid_payload():
    return {
        "email": "newuser@example.com",
        "password": "StrongPassword123!",
        "name": "Jane",
    }


@pytest.mark.django_db
def test_register_user_success(api_client, url, valid_payload):
    """success registeration."""
    response = api_client.post(url, data=valid_payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED

    # بررسی این‌که کاربر واقعاً تو دیتابیس ساخته شده
    assert Users.objects.filter(email=valid_payload["email"]).exists()

    # بررسی محتوای response (کلیدها رو مطابق سریالایزر خودتون تنظیم کنید)
    assert response.data["email"] == valid_payload["email"]
    assert "password" not in response.data


@pytest.mark.django_db
def test_register_user_duplicate_email(api_client, url, valid_payload):
    """register with existing email."""

    Users.objects.create(
        email=valid_payload["email"],
        password="somepassword",
    )

    response = api_client.post(url, data=valid_payload, format="json")

    assert response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.django_db
def test_register_user_missing_required_field(api_client, url, valid_payload):
    """register fail because mising field."""
    valid_payload.pop("email")

    response = api_client.post(url, data=valid_payload, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "email" in response.data


@pytest.mark.django_db
def test_register_user_invalid_email_format(api_client, url, valid_payload):
    """invalid email format regisration."""
    valid_payload["email"] = "not-an-email"

    response = api_client.post(url, data=valid_payload, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "email" in response.data


@pytest.mark.django_db
def test_register_user_password_not_returned(api_client, url, valid_payload):
    """registre success and check password not return again to user (hash or plain)"""
    response = api_client.post(url, data=valid_payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert "password" not in response.data


@pytest.mark.django_db
def test_register_user_password_is_hashed(api_client, url, valid_payload):
    """password has been haashed"""
    api_client.post(url, data=valid_payload, format="json")

    user = Users.objects.get(email=valid_payload["email"])
    assert user.password != valid_payload["password"]
    assert user.check_password(valid_payload["password"])
