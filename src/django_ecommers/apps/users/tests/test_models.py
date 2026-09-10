import pytest
from django.core.exceptions import ValidationError
from django.db import DataError, IntegrityError

from django_ecommers.apps.users.models import Users


@pytest.mark.django_db
class TestUsersModelCreation:
    """Test for creation of user record"""

    def test_create_user_with_valid_data(self):
        user = Users.objects.create(
            name="test",
            email="test@example.com",
        )
        user.set_password("StrongPass123")
        user.save()

        assert user.pk is not None
        assert user.name == "test"
        assert user.email == "test@example.com"

    def test_email_is_stored_correctly(self):
        user = Users.objects.create(name="Sara", email="sara@example.com")
        db_user = Users.objects.get(pk=user.pk)
        assert db_user.email == "sara@example.com"

    def test_last_login_defaults_to_none(self):
        user = Users.objects.create(name="Reza", email="reza@example.com")
        assert user.last_login is None


@pytest.mark.django_db
class TestUsersModelFieldConstraints:
    """tests for limitation of fields"""

    def test_name_field_is_required(self):
        user = Users(name="", email="noname@example.com")
        with pytest.raises(ValidationError):
            user.full_clean()

    def test_name_field_cannot_be_null(self):
        with pytest.raises(IntegrityError):
            Users.objects.create(name=None, email="null@example.com")

    def test_email_max_length_validation(self):
        long_email_local_part = "a" * 150
        user = Users(name="Test User", email=f"{long_email_local_part}@example.com")
        with pytest.raises(ValidationError):
            user.full_clean()


@pytest.mark.django_db
class TestUsersModelAuthBehavior:
    """test for behavior of authenction of AbstractBaseUser class"""

    def test_username_field_is_email(self):
        assert Users.USERNAME_FIELD == "email"

    def test_get_username_returns_email(self):
        user = Users.objects.create(name="Nima", email="nima@example.com")
        assert user.get_username() == "nima@example.com"

    def test_set_password_and_check_password(self):
        user = Users.objects.create(name="Parisa", email="parisa@example.com")
        user.set_password("MySecret123")
        user.save()

        assert user.password != "MySecret123"  # باید هش شده باشد
        assert user.check_password("MySecret123") is True
        assert user.check_password("WrongPassword") is False

    def test_is_authenticated_is_always_true(self):
        user = Users(name="Kian", email="kian@example.com")
        assert user.is_authenticated is True

    def test_is_anonymous_is_always_false(self):
        user = Users(name="Kian", email="kian@example.com")
        assert user.is_anonymous is False
