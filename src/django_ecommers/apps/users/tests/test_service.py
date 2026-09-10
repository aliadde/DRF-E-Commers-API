"""Unit tests for UserService"""

from unittest.mock import MagicMock, patch

import pytest

from django_ecommers.apps.users.exceptions import DuplicateHTTPException
from django_ecommers.apps.users.services import UserService


@pytest.fixture
def user_service():
    return UserService()


@pytest.fixture
def valid_user_data():
    return {
        "name": "john_doe",
        "email": "john@example.com",
        "password": "SuperSecret123",
    }


class TestCreateUser:
    """Tests for UserService.create_user"""

    @patch("django_ecommers.apps.users.services.Users")
    def test_create_user_success(self, mock_users_cls, user_service, valid_user_data):
        # Arrange: no existing user with same name/email
        mock_users_cls.objects.filter.return_value.exists.return_value = False

        mock_new_user = MagicMock()
        mock_users_cls.return_value = mock_new_user

        # Act
        result = user_service.create_user(valid_user_data)

        # Assert: filter called for both name and email uniqueness checks
        mock_users_cls.objects.filter.assert_any_call(name=valid_user_data["name"])
        mock_users_cls.objects.filter.assert_any_call(email=valid_user_data["email"])

        # Assert: user instance created with correct fields
        mock_users_cls.assert_called_once_with(
            name=valid_user_data["name"],
            email=valid_user_data["email"],
        )

        # Assert: password hashed and user saved
        mock_new_user.set_password.assert_called_once_with(valid_user_data["password"])
        mock_new_user.save.assert_called_once()

        # Assert: returned object is the created user
        assert result is mock_new_user

    @patch("django_ecommers.apps.users.services.Users")
    def test_create_user_raises_when_name_exists(
        self, mock_users_cls, user_service, valid_user_data
    ):
        # Arrange: first filter().exists() call (name check) returns True
        mock_users_cls.objects.filter.return_value.exists.return_value = True

        # Act / Assert
        with pytest.raises(DuplicateHTTPException):
            user_service.create_user(valid_user_data)

        # Only the name check should have run before raising
        mock_users_cls.objects.filter.assert_called_once_with(
            name=valid_user_data["name"]
        )
        mock_users_cls.assert_not_called()
        # save() should never be reached
        mock_users_cls.return_value.save.assert_not_called()

    @patch("django_ecommers.apps.users.services.Users")
    def test_create_user_raises_when_email_exists(
        self, mock_users_cls, user_service, valid_user_data
    ):
        # Arrange: name check passes (False), email check fails (True)
        mock_users_cls.objects.filter.return_value.exists.side_effect = [False, True]

        # Act / Assert
        with pytest.raises(DuplicateHTTPException):
            user_service.create_user(valid_user_data)

        assert mock_users_cls.objects.filter.call_count == 2
        mock_users_cls.objects.filter.assert_any_call(name=valid_user_data["name"])
        mock_users_cls.objects.filter.assert_any_call(email=valid_user_data["email"])
        mock_users_cls.assert_not_called()
        # save() should never be reached
        mock_users_cls.return_value.save.assert_not_called()

    @patch("django_ecommers.apps.users.services.Users")
    def test_create_user_password_is_hashed_not_stored_plain(
        self, mock_users_cls, user_service, valid_user_data
    ):
        mock_users_cls.objects.filter.return_value.exists.return_value = False
        mock_new_user = MagicMock()
        mock_users_cls.return_value = mock_new_user

        user_service.create_user(valid_user_data)

        # set_password should be called with the raw password
        mock_new_user.set_password.assert_called_once_with(valid_user_data["password"])
        # Users() constructor should NOT have been called with a "password" kwarg
        _, kwargs = mock_users_cls.call_args
        assert "password" not in kwargs
