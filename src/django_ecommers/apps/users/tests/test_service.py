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
        "username": "john_doe",
        "email": "john@example.com",
        "password": "SuperSecret123",
    }


class TestCreateUser:
    """Tests for UserService.create_user"""

    @patch("django_ecommers.apps.users.services.Users")
    def test_create_user_success(self, mock_users_cls, user_service, valid_user_data):
        # Arrange: no existing user with same username/email
        mock_users_cls.objects.filter.return_value.exists.return_value = False

        mock_new_user = MagicMock()
        mock_users_cls.objects.create_user.return_value = mock_new_user

        # Act
        result = user_service.create_user(valid_user_data)

        # Assert: both uniqueness checks were performed
        mock_users_cls.objects.filter.assert_any_call(
            username=valid_user_data["username"]
        )
        mock_users_cls.objects.filter.assert_any_call(email=valid_user_data["email"])

        # Assert: create_user called with correct fields
        mock_users_cls.objects.create_user.assert_called_once_with(
            username=valid_user_data["username"],
            email=valid_user_data["email"],
            password=valid_user_data["password"],
        )

        # Assert: user saved
        mock_new_user.save.assert_called_once()

        # Assert: returned object is the created user
        assert result is mock_new_user

    @patch("django_ecommers.apps.users.services.Users")
    def test_create_user_raises_when_username_exists(
        self, mock_users_cls, user_service, valid_user_data
    ):
        # Arrange: username check returns True
        mock_users_cls.objects.filter.return_value.exists.return_value = True

        # Act / Assert
        with pytest.raises(DuplicateHTTPException):
            user_service.create_user(valid_user_data)

        # Only the username check should have run before raising
        mock_users_cls.objects.filter.assert_called_once_with(
            username=valid_user_data["username"]
        )
        # No user should have been created or saved
        mock_users_cls.objects.create_user.assert_not_called()
        mock_users_cls.objects.create_user.return_value.save.assert_not_called()

    @patch("django_ecommers.apps.users.services.Users")
    def test_create_user_raises_when_email_exists(
        self, mock_users_cls, user_service, valid_user_data
    ):
        # Arrange: username check passes (False), email check fails (True)
        mock_users_cls.objects.filter.return_value.exists.side_effect = [False, True]

        # Act / Assert
        with pytest.raises(DuplicateHTTPException):
            user_service.create_user(valid_user_data)

        assert mock_users_cls.objects.filter.call_count == 2
        mock_users_cls.objects.filter.assert_any_call(
            username=valid_user_data["username"]
        )
        mock_users_cls.objects.filter.assert_any_call(email=valid_user_data["email"])
        # No user should have been created or saved
        mock_users_cls.objects.create_user.assert_not_called()
        mock_users_cls.objects.create_user.return_value.save.assert_not_called()

    @patch("django_ecommers.apps.users.services.Users")
    def test_create_user_delegates_password_hashing_to_create_user(
        self, mock_users_cls, user_service, valid_user_data
    ):
        mock_users_cls.objects.filter.return_value.exists.return_value = False
        mock_new_user = MagicMock()
        mock_users_cls.objects.create_user.return_value = mock_new_user

        user_service.create_user(valid_user_data)

        # The raw password is handed to create_user, which is responsible for hashing
        _, kwargs = mock_users_cls.objects.create_user.call_args
        assert kwargs["password"] == valid_user_data["password"]

        # The service itself must not touch the password or construct Users directly
        mock_new_user.set_password.assert_not_called()
        mock_users_cls.assert_not_called()
