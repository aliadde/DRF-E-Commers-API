import pytest

from django_ecommers.apps.users.models import Users
from django_ecommers.apps.users.serializer import (
    UserRegisterRequestSerializer,
    UserRegisterResponseSerializer,
)


@pytest.mark.django_db
class TestUserRegisterRequestSerializer:
    """test for registeration serializer"""

    def valid_payload(self):
        return {
            "name": "Ali Rezaei",
            "email": "ali@example.com",
            "password": "StrongPass123",
        }

    def test_valid_data_is_accepted(self):
        serializer = UserRegisterRequestSerializer(data=self.valid_payload())
        assert serializer.is_valid(), serializer.errors

    def test_missing_email_is_invalid(self):
        payload = self.valid_payload()
        payload.pop("email")

        serializer = UserRegisterRequestSerializer(data=payload)
        assert serializer.is_valid() is False
        assert "email" in serializer.errors

    def test_invalid_email_format_is_rejected(self):
        payload = self.valid_payload()
        payload["email"] = "not-an-email"

        serializer = UserRegisterRequestSerializer(data=payload)
        assert serializer.is_valid() is False
        assert "email" in serializer.errors

    def test_blank_name_is_invalid(self):
        payload = self.valid_payload()
        payload["name"] = ""

        serializer = UserRegisterRequestSerializer(data=payload)
        assert serializer.is_valid() is False
        assert "name" in serializer.errors

    def test_missing_password_is_invalid(self):
        payload = self.valid_payload()
        payload.pop("password")

        serializer = UserRegisterRequestSerializer(data=payload)
        assert serializer.is_valid() is False
        assert "password" in serializer.errors

    def test_password_field_is_write_only(self):

        serializer = UserRegisterRequestSerializer(data=self.valid_payload())
        serializer.is_valid()

        assert "password" not in serializer.data

    def test_save_creates_user_in_db(self):
        serializer = UserRegisterRequestSerializer(data=self.valid_payload())
        assert serializer.is_valid()

        user = serializer.save()

        assert isinstance(user, Users)
        assert Users.objects.filter(pk=user.pk).exists()
        assert user.email == "ali@example.com"


@pytest.mark.django_db
class TestUserRegisterResponseSerializer:
    """test serializer response regisration"""

    def create_user(self):
        return Users.objects.create(name="Sara", email="sara@example.com")

    def test_response_contains_expected_fields(self):
        user = self.create_user()
        serializer = UserRegisterResponseSerializer(instance=user)

        assert set(serializer.data.keys()) == {"id", "name", "email"}

    def test_response_never_exposes_password(self):
        """
        امنیتی‌ترین تست این فایل: مطمئن می‌شیم پسورد
        (حتی هش‌شده‌ش) هیچ‌وقت توی response لو نره.
        """
        user = self.create_user()
        user.set_password("something-secret")
        user.save()

        serializer = UserRegisterResponseSerializer(instance=user)

        assert "password" not in serializer.data

    def test_response_values_match_instance(self):
        user = self.create_user()
        serializer = UserRegisterResponseSerializer(instance=user)

        assert serializer.data["id"] == user.id
        assert serializer.data["name"] == user.name
        assert serializer.data["email"] == user.email
