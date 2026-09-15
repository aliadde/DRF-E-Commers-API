import pytest

from django_ecommers.apps.users.models import Users
from django_ecommers.apps.users.serializer import (
    MyTokenObtainPairSerializer,
    UserMeResponseSerializer,
    UserRegisterRequestSerializer,
    UserRegisterResponseSerializer,
    UserUpdateResponseSerializer,
    UserResetPasswordSerializer,
)


# ========================
# Register Request Serializer
# ========================
@pytest.mark.django_db
class TestUserRegisterRequestSerializer:
    """Tests for registration request serializer."""

    def valid_payload(self):
        return {
            "username": "Ali Rezaei",
            "email": "ali@example.com",
            "password": "StrongPass123",
        }

    def test_valid_data_is_accepted(self):
        serializer = UserRegisterRequestSerializer(data=self.valid_payload())

        assert serializer.is_valid(), serializer.errors

    def test_missing_username_is_invalid(self):
        payload = self.valid_payload()
        payload.pop("username")

        serializer = UserRegisterRequestSerializer(data=payload)

        assert serializer.is_valid() is False
        assert "username" in serializer.errors

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

    def test_blank_username_is_invalid(self):
        payload = self.valid_payload()
        payload["username"] = ""

        serializer = UserRegisterRequestSerializer(data=payload)

        assert serializer.is_valid() is False
        assert "username" in serializer.errors

    def test_missing_password_is_invalid(self):
        payload = self.valid_payload()
        payload.pop("password")

        serializer = UserRegisterRequestSerializer(data=payload)

        assert serializer.is_valid() is False
        assert "password" in serializer.errors

    def test_password_field_is_write_only(self):
        serializer = UserRegisterRequestSerializer(data=self.valid_payload())

        assert serializer.is_valid(), serializer.errors

        assert "password" not in serializer.data

    def test_validated_data_contains_password(self):
        serializer = UserRegisterRequestSerializer(data=self.valid_payload())

        assert serializer.is_valid(), serializer.errors

        assert "password" in serializer.validated_data
        assert serializer.validated_data["password"] == "StrongPass123"

    def test_save_creates_user_in_db(self):
        serializer = UserRegisterRequestSerializer(data=self.valid_payload())

        assert serializer.is_valid(), serializer.errors

        user = serializer.save()

        assert isinstance(user, Users)
        assert Users.objects.filter(pk=user.pk).exists()
        assert user.username == "Ali Rezaei"
        assert user.email == "ali@example.com"

    def test_password_is_not_stored_as_plain_text(self):
        serializer = UserRegisterRequestSerializer(data=self.valid_payload())

        assert serializer.is_valid(), serializer.errors

        user = serializer.save()

        assert user.password != "StrongPass123"
        assert user.check_password("StrongPass123")


# ========================
# Register Response Serializer
# ========================
@pytest.mark.django_db
class TestUserRegisterResponseSerializer:
    """Tests for registration response serializer."""

    def create_user(self):
        user = Users.objects.create(
            username="Sara",
            email="sara@example.com",
        )
        user.set_password("something-secret")
        user.save()

        return user

    def test_response_contains_expected_fields(self):
        user = self.create_user()

        serializer = UserRegisterResponseSerializer(instance=user)

        assert set(serializer.data.keys()) == {
            "id",
            "username",
            "email",
        }

    def test_response_never_exposes_password(self):
        user = self.create_user()

        serializer = UserRegisterResponseSerializer(instance=user)

        assert "password" not in serializer.data

    def test_response_values_match_instance(self):
        user = self.create_user()

        serializer = UserRegisterResponseSerializer(instance=user)

        assert serializer.data["id"] == user.id
        assert serializer.data["username"] == user.username
        assert serializer.data["email"] == user.email


# ========================
# GET Me Serializer
# ========================
@pytest.mark.django_db
class TestUserMeResponseSerializer:
    """Tests for user me response serializer."""

    def create_user(self):
        user = Users.objects.create(
            username="Ali",
            email="ali@example.com",
        )
        user.set_password("StrongPass123")
        user.save()

        return user

    def test_response_contains_expected_fields(self):
        user = self.create_user()

        serializer = UserMeResponseSerializer(instance=user)

        assert set(serializer.data.keys()) == {
            "id",
            "username",
            "email",
            "last_login",
        }

    def test_response_does_not_expose_password(self):
        user = self.create_user()

        serializer = UserMeResponseSerializer(instance=user)

        assert "password" not in serializer.data

    def test_response_values_match_instance(self):
        user = self.create_user()

        serializer = UserMeResponseSerializer(instance=user)

        assert serializer.data["id"] == user.id
        assert serializer.data["username"] == user.username
        assert serializer.data["email"] == user.email
        assert serializer.data["last_login"] == (
            user.last_login.isoformat().replace("+00:00", "Z")
            if user.last_login
            else None
        )


# ========================
# PATCH User Response Serializer
# ========================
@pytest.mark.django_db
class TestUserUpdateResponseSerializer:
    """Tests for user update response serializer."""

    def create_user(self):
        user = Users.objects.create(
            username="Ali",
            email="ali@example.com",
        )
        user.set_password("StrongPass123")
        user.save()

        return user

    def test_response_contains_expected_fields(self):
        user = self.create_user()

        serializer = UserUpdateResponseSerializer(instance=user)

        assert set(serializer.data.keys()) == {
            "username",
            "email",
            "last_login",
        }

    def test_response_does_not_expose_id(self):
        user = self.create_user()

        serializer = UserUpdateResponseSerializer(instance=user)

        assert "id" not in serializer.data

    def test_response_does_not_expose_password(self):
        user = self.create_user()

        serializer = UserUpdateResponseSerializer(instance=user)

        assert "password" not in serializer.data

    def test_response_values_match_instance(self):
        user = self.create_user()

        serializer = UserUpdateResponseSerializer(instance=user)

        assert serializer.data["username"] == user.username
        assert serializer.data["email"] == user.email


# ========================
# Reset Password Serializer
# ========================
@pytest.mark.django_db
class TestUserResetPasswordSerializer:
    """Tests for password reset serializer."""

    def valid_payload(self):
        return {
            "current_password": "OldPass123",
            "new_password": "NewPass123",
        }

    def test_valid_data_is_accepted(self):
        serializer = UserResetPasswordSerializer(data=self.valid_payload())

        assert serializer.is_valid(), serializer.errors

    def test_missing_current_password_is_invalid(self):
        payload = self.valid_payload()
        payload.pop("current_password")

        serializer = UserResetPasswordSerializer(data=payload)

        assert serializer.is_valid() is False
        assert "current_password" in serializer.errors

    def test_missing_new_password_is_invalid(self):
        payload = self.valid_payload()
        payload.pop("new_password")

        serializer = UserResetPasswordSerializer(data=payload)

        assert serializer.is_valid() is False
        assert "new_password" in serializer.errors

    def test_blank_current_password_is_invalid(self):
        payload = self.valid_payload()
        payload["current_password"] = ""

        serializer = UserResetPasswordSerializer(data=payload)

        assert serializer.is_valid() is False
        assert "current_password" in serializer.errors

    def test_blank_new_password_is_invalid(self):
        payload = self.valid_payload()
        payload["new_password"] = ""

        serializer = UserResetPasswordSerializer(data=payload)

        assert serializer.is_valid() is False
        assert "new_password" in serializer.errors

    def test_password_fields_are_write_only(self):
        serializer = UserResetPasswordSerializer(data=self.valid_payload())

        assert serializer.is_valid(), serializer.errors

        assert "current_password" not in serializer.data
        assert "new_password" not in serializer.data

    def test_validated_data_contains_passwords(self):
        serializer = UserResetPasswordSerializer(data=self.valid_payload())

        assert serializer.is_valid(), serializer.errors

        assert "current_password" in serializer.validated_data
        assert "new_password" in serializer.validated_data

        assert serializer.validated_data["current_password"] == "OldPass123"
        assert serializer.validated_data["new_password"] == "NewPass123"


# ========================
# Custom JWT Token Serializer
# ========================
@pytest.mark.django_db
class TestMyTokenObtainPairSerializer:
    """Tests for custom JWT token serializer."""

    def create_user(self):
        user = Users.objects.create(
            username="Ali",
            email="ali@example.com",
        )

        user.set_password("StrongPass123")
        user.save()

        return user

    def test_token_contains_username_claim(self):
        user = self.create_user()

        token = MyTokenObtainPairSerializer.get_token(user)

        assert token["username"] == user.username

    def test_token_contains_standard_claims(self):
        user = self.create_user()

        token = MyTokenObtainPairSerializer.get_token(user)

        assert "user_id" in token
        assert "token_type" in token
        assert token["token_type"] == "refresh"
