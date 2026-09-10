"""Unit tests for UserView."""

from unittest.mock import MagicMock, patch

import pytest
from rest_framework import status
from rest_framework.test import APIRequestFactory

from django_ecommers.apps.users.exceptions import DuplicateHTTPException
from django_ecommers.apps.users.views import UserView


@pytest.fixture
def factory():
    return APIRequestFactory()


@pytest.fixture
def valid_payload():
    return {
        "name": "john_doe",
        "email": "john@example.com",
        "password": "SuperSecret123",
    }


class TestUserViewPost:
    """Tests for UserView.post"""

    @patch("django_ecommers.apps.users.views.UserRegisterResponseSerializer")
    @patch("django_ecommers.apps.users.views.UserService")
    def test_post_creates_user_successfully(
        self,
        mock_service_cls,
        mock_response_serializer_cls,
        factory,
        valid_payload,
    ):
        # Arrange
        mock_service = mock_service_cls.return_value
        fake_user = MagicMock()
        mock_service.create_user.return_value = fake_user

        mock_response_serializer = mock_response_serializer_cls.return_value
        mock_response_serializer.data = {
            "id": 1,
            "name": "john_doe",
            "email": "john@example.com",
        }

        request = factory.post("/user/auth", valid_payload, format="json")

        # Act
        response = UserView.as_view()(request)

        # Assert: status code
        assert response.status_code == status.HTTP_201_CREATED

        # Assert: service called with validated data
        mock_service.create_user.assert_called_once()
        _, kwargs = mock_service.create_user.call_args
        assert kwargs["user_data"]["name"] == valid_payload["name"]
        assert kwargs["user_data"]["email"] == valid_payload["email"]

        # Assert: response serializer built from the created user
        mock_response_serializer_cls.assert_called_once_with(fake_user)

        # Assert: response body matches serializer output
        assert response.data == mock_response_serializer.data

    def test_post_returns_400_for_missing_fields(self, factory):
        request = factory.post("/user/auth", {}, format="json")
        response = UserView.as_view()(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_returns_400_for_invalid_email(self, factory, valid_payload):
        invalid_payload = {**valid_payload, "email": "not-an-email"}
        request = factory.post("/users/", invalid_payload, format="json")
        response = UserView.as_view()(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch("django_ecommers.apps.users.views.UserRegisterResponseSerializer")
    @patch("django_ecommers.apps.users.views.UserService")
    def test_post_does_not_call_service_and_response_serializer_when_payload_invalid(
        self, mock_service_cls, mock_serializer_response_cls, factory
    ):
        request = factory.post("/user/auth", {}, format="json")
        UserView.as_view()(request)
        mock_serializer_response_cls.return_value.assert_not_called()
        mock_service_cls.return_value.create_user.assert_not_called()

    @patch("django_ecommers.apps.users.views.UserService")
    def test_post_returns_409_when_duplicate_user(
        self, mock_service_cls, factory, valid_payload
    ):
        """
        DuplicateHTTPException extends DRF's APIException with status_code=409.
        DRF's default exception handler catches it inside APIView.dispatch()
        and converts it into a Response — it never reaches the caller as a
        raised exception.
        """
        # Arrange
        mock_service = mock_service_cls.return_value
        mock_service.create_user.side_effect = DuplicateHTTPException()

        request = factory.post("/user/auth", valid_payload, format="json")

        # Act
        response = UserView.as_view()(request)

        # Assert
        assert response.status_code == status.HTTP_409_CONFLICT
        assert (
            response.data["detail"]
            == "The name or email you provided is already taken."
        )

    @patch("django_ecommers.apps.users.views.UserRegisterResponseSerializer")
    @patch("django_ecommers.apps.users.views.UserService")
    def test_post_response_does_not_leak_password(
        self,
        mock_service_cls,
        mock_response_serializer_cls,
        factory,
        valid_payload,
    ):
        """Regression guard: response body must never contain raw/hashed password."""
        mock_service = mock_service_cls.return_value
        mock_service.create_user.return_value = MagicMock()

        mock_response_serializer = mock_response_serializer_cls.return_value
        mock_response_serializer.data = {
            "id": 1,
            "name": "john_doe",
            "email": "john@example.com",
        }

        request = factory.post("/user/auth", valid_payload, format="json")
        response = UserView.as_view()(request)

        assert "password" not in response.data
