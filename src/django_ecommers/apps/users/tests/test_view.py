"""Unit tests for UserPublicView and UserPrivateView."""

from unittest.mock import MagicMock, patch
import pytest

from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory, force_authenticate

from django_ecommers.apps.users.exceptions import DuplicateHTTPException
from django_ecommers.apps.users.views import UserPrivateView, UserPublicView
from django_ecommers.apps.users.models import Users


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def factory():
    return APIRequestFactory()


@pytest.fixture
def valid_payload():
    return {
        "username": "john_doe",
        "email": "john@example.com",
        "password": "SuperSecret123",
    }


@pytest.fixture
def mock_user():
    """Stand-in for an authenticated Users instance (request.user)."""
    user = MagicMock()
    user.is_authenticated = True
    return user


# ---------------------------------------------------------------------------
# UserPublicView.post
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestUserPublicViewPost:
    """Tests for UserPublicView.post"""

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
            "username": "john_doe",
            "email": "john@example.com",
        }

        request = factory.post("/user/register/", valid_payload, format="json")

        # Act
        response = UserPublicView.as_view()(request)

        # Assert: status code
        assert response.status_code == status.HTTP_201_CREATED

        # Assert: service called with validated data
        mock_service.create_user.assert_called_once()
        _, kwargs = mock_service.create_user.call_args
        assert kwargs["user_data"]["username"] == valid_payload["username"]
        assert kwargs["user_data"]["email"] == valid_payload["email"]

        # Assert: response serializer built from the created user
        mock_response_serializer_cls.assert_called_once_with(fake_user)

        # Assert: response body matches serializer output
        assert response.data == mock_response_serializer.data

    def test_post_returns_400_for_missing_fields(self, factory):
        request = factory.post("/user/register/", {}, format="json")
        response = UserPublicView.as_view()(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_returns_400_for_invalid_email(self, factory, valid_payload):
        invalid_payload = {**valid_payload, "email": "not-an-email"}
        request = factory.post("/user/register/", invalid_payload, format="json")
        response = UserPublicView.as_view()(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_returns_400_for_missing_username(self, factory, valid_payload):
        invalid_payload = {**valid_payload}
        del invalid_payload["username"]
        request = factory.post("/user/register/", invalid_payload, format="json")
        response = UserPublicView.as_view()(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_returns_400_for_missing_password(self, factory, valid_payload):
        invalid_payload = {**valid_payload}
        del invalid_payload["password"]
        request = factory.post("/user/register/", invalid_payload, format="json")
        response = UserPublicView.as_view()(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch("django_ecommers.apps.users.views.UserRegisterResponseSerializer")
    @patch("django_ecommers.apps.users.views.UserService")
    def test_post_does_not_call_service_and_response_serializer_when_payload_invalid(
        self, mock_service_cls, mock_response_serializer_cls, factory
    ):
        request = factory.post("/user/register/", {}, format="json")
        UserPublicView.as_view()(request)
        mock_response_serializer_cls.return_value.assert_not_called()
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
        mock_service = mock_service_cls.return_value
        mock_service.create_user.side_effect = DuplicateHTTPException()

        request = factory.post("/user/register/", valid_payload, format="json")
        response = UserPublicView.as_view()(request)

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
            "username": "john_doe",
            "email": "john@example.com",
        }

        request = factory.post("/user/register/", valid_payload, format="json")
        response = UserPublicView.as_view()(request)

        assert "password" not in response.data

    @patch("django_ecommers.apps.users.views.UserRegisterRequestSerializer")
    @patch("django_ecommers.apps.users.views.UserService")
    def test_post_passes_validated_data_to_service_verbatim(
        self, mock_service_cls, mock_request_serializer_cls, factory, valid_payload
    ):
        """The view must forward serializer.validated_data unchanged, not raw request.data."""
        mock_request_serializer = mock_request_serializer_cls.return_value
        mock_request_serializer.validated_data = {"username": "clean_data_only"}

        request = factory.post("/user/register/", valid_payload, format="json")
        UserPublicView.as_view()(request)

        mock_service_cls.return_value.create_user.assert_called_once_with(
            user_data={"username": "clean_data_only"}
        )

    def test_post_not_allowed_methods_return_405(self, factory):
        for method in ("get", "put", "delete", "patch"):
            request = getattr(factory, method)("/user/register/")
            response = UserPublicView.as_view()(request)
            assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


# ---------------------------------------------------------------------------
# UserPrivateView.get Get User
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestUserPrivateViewGet:
    """Tests for UserPrivateView.get"""

    @patch("django_ecommers.apps.users.views.UserMeResponseSerializer")
    def test_get_returns_200_with_serialized_user_data(
        self, mock_serializer_cls, factory, mock_user
    ):
        mock_serializer = mock_serializer_cls.return_value
        mock_serializer.data = {
            "id": 1,
            "username": "john_doe",
            "email": "john@example.com",
        }

        request = factory.get("/user/me/")
        force_authenticate(request, user=mock_user)
        response = UserPrivateView.as_view()(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == mock_serializer.data

    @patch("django_ecommers.apps.users.views.UserMeResponseSerializer")
    def test_get_serializer_called_with_request_user(
        self, mock_serializer_cls, factory, mock_user
    ):
        request = factory.get("/user/me/")
        force_authenticate(request, user=mock_user)
        UserPrivateView.as_view()(request)

        mock_serializer_cls.assert_called_once_with(mock_user)

    def test_get_requires_authentication(self, factory):
        request = factory.get("/user/me/")
        response = UserPrivateView.as_view()(request)

        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    @patch("django_ecommers.apps.users.views.UserMeResponseSerializer")
    def test_get_response_does_not_leak_password(
        self, mock_serializer_cls, factory, mock_user
    ):
        mock_serializer = mock_serializer_cls.return_value
        mock_serializer.data = {
            "id": 1,
            "username": "john_doe",
            "email": "john@example.com",
        }

        request = factory.get("/user/me/")
        force_authenticate(request, user=mock_user)
        response = UserPrivateView.as_view()(request)

        assert "password" not in response.data


# ---------------------------------------------------------------------------
# UserPrivateView.patch Update
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestUserPrivateViewPatch:
    """Tests for UserPrivateView.patch"""

    @patch("django_ecommers.apps.users.views.UserUpdateResponseSerializer")
    def test_patch_updates_user_successfully(
        self, mock_serializer_cls, factory, mock_user
    ):
        mock_serializer = mock_serializer_cls.return_value
        mock_serializer.is_valid.return_value = True
        mock_serializer.data = {"id": 1, "username": "new_name"}

        request = factory.patch("/user/me/", {"username": "new_name"}, format="json")
        force_authenticate(request, user=mock_user)
        response = UserPrivateView.as_view()(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == mock_serializer.data
        mock_serializer.save.assert_called_once()

    @patch("django_ecommers.apps.users.views.UserUpdateResponseSerializer")
    def test_patch_calls_serializer_with_instance_data_and_partial_true(
        self, mock_serializer_cls, factory, mock_user
    ):
        payload = {"username": "new_name"}
        request = factory.patch("/user/me/", payload, format="json")
        force_authenticate(request, user=mock_user)
        UserPrivateView.as_view()(request)

        mock_serializer_cls.assert_called_once_with(
            mock_user, data=payload, partial=True
        )

    @patch("django_ecommers.apps.users.views.UserUpdateResponseSerializer")
    def test_patch_returns_400_when_serializer_invalid(
        self, mock_serializer_cls, factory, mock_user
    ):
        mock_serializer = mock_serializer_cls.return_value
        mock_serializer.is_valid.side_effect = ValidationError(
            {"email": ["Enter a valid email address."]}
        )

        request = factory.patch("/user/me/", {"email": "not-an-email"}, format="json")
        force_authenticate(request, user=mock_user)
        response = UserPrivateView.as_view()(request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch("django_ecommers.apps.users.views.UserUpdateResponseSerializer")
    def test_patch_does_not_save_when_invalid(
        self, mock_serializer_cls, factory, mock_user
    ):
        mock_serializer = mock_serializer_cls.return_value
        mock_serializer.is_valid.side_effect = ValidationError(
            {"email": ["Enter a valid email address."]}
        )

        request = factory.patch("/user/me/", {"email": "not-an-email"}, format="json")
        force_authenticate(request, user=mock_user)
        UserPrivateView.as_view()(request)

        mock_serializer.save.assert_not_called()

    def test_patch_requires_authentication(self, factory):
        request = factory.patch("/user/me/", {"username": "new_name"}, format="json")
        response = UserPrivateView.as_view()(request)

        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    @patch("django_ecommers.apps.users.views.UserUpdateResponseSerializer")
    def test_patch_allows_partial_update_with_single_field(
        self, mock_serializer_cls, factory, mock_user
    ):
        """partial=True means a single field should be enough, without others being required."""
        mock_serializer = mock_serializer_cls.return_value
        mock_serializer.is_valid.return_value = True
        mock_serializer.data = {"id": 1, "email": "new@example.com"}

        request = factory.patch(
            "/user/me/", {"email": "new@example.com"}, format="json"
        )
        force_authenticate(request, user=mock_user)
        response = UserPrivateView.as_view()(request)

        assert response.status_code == status.HTTP_200_OK
        _, kwargs = mock_serializer_cls.call_args
        assert kwargs["partial"] is True

    @patch("django_ecommers.apps.users.views.UserUpdateResponseSerializer")
    def test_patch_response_does_not_leak_password(
        self, mock_serializer_cls, factory, mock_user
    ):
        mock_serializer = mock_serializer_cls.return_value
        mock_serializer.is_valid.return_value = True
        mock_serializer.data = {"id": 1, "username": "new_name"}

        request = factory.patch("/user/me/", {"username": "new_name"}, format="json")
        force_authenticate(request, user=mock_user)
        response = UserPrivateView.as_view()(request)

        assert "password" not in response.data

    def test_patch_not_allowed_methods_return_405(self, factory, mock_user):
        for method in ("post", "put", "delete"):
            request = getattr(factory, method)("/user/me/")
            force_authenticate(request, user=mock_user)
            response = UserPrivateView.as_view()(request)
            assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


# ---------------------------------------------------------------------------
# UserPrivateView.post Reset Password
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestUserPasswordResetView:
    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def user(self):
        user = Users.objects.create(
            username="testuser",
            email="test@example.com",
        )
        user.set_password("OldPassword123!")
        user.save()
        user.refresh_from_db()
        return user

    @pytest.fixture
    def authenticated_client(self, api_client, user):
        api_client.force_authenticate(user=user)
        return api_client

    @pytest.fixture
    def url(self):
        return reverse("reset_password")

    def test_password_reset_success(
        self,
        authenticated_client,
        user,
        url,
    ):
        response = authenticated_client.post(
            url,
            {
                "current_password": "OldPassword123!",
                "new_password": "NewPassword123!",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"message": "Your password reset successfully."}

        user.refresh_from_db()
        assert user.check_password("NewPassword123!")
        assert not user.check_password("OldPassword123!")

    def test_password_reset_with_wrong_current_password(
        self,
        authenticated_client,
        user,
        url,
    ):
        response = authenticated_client.post(
            url,
            {
                "current_password": "WrongPassword123!",
                "new_password": "NewPassword123!",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {"error": "Your current_password is incorrect."}

        user.refresh_from_db()
        assert user.check_password("OldPassword123!")
        assert not user.check_password("NewPassword123!")

    def test_password_reset_requires_authentication(
        self,
        api_client,
        url,
    ):
        response = api_client.post(
            url,
            {
                "current_password": "OldPassword123!",
                "new_password": "NewPassword123!",
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_password_reset_missing_current_password(
        self,
        authenticated_client,
        user,
        url,
    ):
        response = authenticated_client.post(
            url,
            {
                "new_password": "NewPassword123!",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        user.refresh_from_db()
        assert user.check_password("OldPassword123!")

    def test_password_reset_missing_new_password(
        self,
        authenticated_client,
        user,
        url,
    ):
        response = authenticated_client.post(
            url,
            {
                "current_password": "OldPassword123!",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        user.refresh_from_db()
        assert user.check_password("OldPassword123!")

    def test_password_reset_with_empty_current_password(
        self,
        authenticated_client,
        user,
        url,
    ):
        response = authenticated_client.post(
            url,
            {
                "current_password": "",
                "new_password": "NewPassword123!",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        user.refresh_from_db()
        assert user.check_password("OldPassword123!")

    def test_password_reset_with_empty_new_password(
        self,
        authenticated_client,
        user,
        url,
    ):
        response = authenticated_client.post(
            url,
            {
                "current_password": "OldPassword123!",
                "new_password": "",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        user.refresh_from_db()
        assert user.check_password("OldPassword123!")

    def test_password_reset_with_same_password(
        self,
        authenticated_client,
        user,
        url,
    ):
        response = authenticated_client.post(
            url,
            {
                "current_password": "OldPassword123!",
                "new_password": "OldPassword123!",
            },
        )

        assert response.status_code == status.HTTP_200_OK

        user.refresh_from_db()
        assert user.check_password("OldPassword123!")
