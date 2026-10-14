"""Unit tests for User views."""

from unittest.mock import MagicMock, patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate

from django_ecommers.apps.users.exceptions import DuplicateHTTPException
from django_ecommers.apps.users.models import Addresses, Users
from django_ecommers.apps.users.views import (
    UserAddressGetView,
    UserAddressPrivateView,
    UserPasswordResetView,
    UserPrivateView,
    UserPublicView,
)


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
    user = MagicMock()
    user.is_authenticated = True
    user.id = 1
    return user


@pytest.fixture
def user(db):
    user = Users.objects.create(
        username="testuser",
        email="test@example.com",
    )
    user.set_password("OldPassword123!")
    user.save()
    return user


@pytest.fixture
def another_user(db):
    return Users.objects.create(
        username="anotheruser",
        email="another@example.com",
    )


@pytest.fixture
def authenticated_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def address(user):
    return Addresses.objects.create(
        user=user,
        location="Berlin",
    )


@pytest.fixture
def address_payload():
    return {"location": "Hamburg"}


# ---------------------------------------------------------------------------
# UserPublicView.post
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestUserPublicViewPost:

    @patch("django_ecommers.apps.users.views.UserRegisterResponseSerializer")
    @patch("django_ecommers.apps.users.views.UserService")
    def test_post_creates_user_successfully(
        self,
        mock_service_cls,
        mock_response_serializer_cls,
        factory,
        valid_payload,
    ):
        fake_user = MagicMock()
        mock_service_cls.return_value.create_user.return_value = fake_user

        mock_response_serializer_cls.return_value.data = {
            "id": 1,
            "username": "john_doe",
            "email": "john@example.com",
        }

        request = factory.post("/user/register/", valid_payload, format="json")
        response = UserPublicView.as_view()(request)

        assert response.status_code == status.HTTP_201_CREATED
        mock_service_cls.return_value.create_user.assert_called_once()

        _, kwargs = mock_service_cls.return_value.create_user.call_args
        assert kwargs["user_data"]["username"] == valid_payload["username"]
        assert kwargs["user_data"]["email"] == valid_payload["email"]

        mock_response_serializer_cls.assert_called_once_with(fake_user)
        assert response.data == mock_response_serializer_cls.return_value.data

    def test_post_returns_400_for_missing_fields(self, factory):
        request = factory.post("/user/register/", {}, format="json")
        response = UserPublicView.as_view()(request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_returns_400_for_invalid_email(self, factory, valid_payload):
        payload = {**valid_payload, "email": "not-an-email"}
        request = factory.post("/user/register/", payload, format="json")
        response = UserPublicView.as_view()(request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_returns_400_for_missing_username(self, factory, valid_payload):
        payload = {**valid_payload}
        del payload["username"]

        request = factory.post("/user/register/", payload, format="json")
        response = UserPublicView.as_view()(request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_returns_400_for_missing_password(self, factory, valid_payload):
        payload = {**valid_payload}
        del payload["password"]

        request = factory.post("/user/register/", payload, format="json")
        response = UserPublicView.as_view()(request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch("django_ecommers.apps.users.views.UserRegisterResponseSerializer")
    @patch("django_ecommers.apps.users.views.UserService")
    def test_invalid_payload_does_not_call_service(
        self,
        mock_service_cls,
        mock_response_serializer_cls,
        factory,
    ):
        request = factory.post("/user/register/", {}, format="json")
        UserPublicView.as_view()(request)

        mock_service_cls.return_value.create_user.assert_not_called()
        mock_response_serializer_cls.assert_not_called()

    @patch("django_ecommers.apps.users.views.UserService")
    def test_post_returns_409_when_duplicate_user(
        self,
        mock_service_cls,
        factory,
        valid_payload,
    ):
        mock_service_cls.return_value.create_user.side_effect = (
            DuplicateHTTPException()
        )

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
        mock_service_cls.return_value.create_user.return_value = MagicMock()
        mock_response_serializer_cls.return_value.data = {
            "id": 1,
            "username": "john_doe",
            "email": "john@example.com",
        }

        request = factory.post("/user/register/", valid_payload, format="json")
        response = UserPublicView.as_view()(request)

        assert "password" not in response.data

    @patch("django_ecommers.apps.users.views.UserRegisterRequestSerializer")
    @patch("django_ecommers.apps.users.views.UserService")
    def test_post_passes_validated_data_to_service(
        self,
        mock_service_cls,
        mock_request_serializer_cls,
        factory,
        valid_payload,
    ):
        mock_request_serializer_cls.return_value.validated_data = {
            "username": "clean_data_only"
        }

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
# UserPrivateView.get
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestUserPrivateViewGet:

    @patch("django_ecommers.apps.users.views.UserMeResponseSerializer")
    def test_get_returns_serialized_user_data(
        self,
        mock_serializer_cls,
        factory,
        mock_user,
    ):
        mock_serializer_cls.return_value.data = {
            "id": 1,
            "username": "john_doe",
            "email": "john@example.com",
        }

        request = factory.get("/user/me/")
        force_authenticate(request, user=mock_user)
        response = UserPrivateView.as_view()(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == mock_serializer_cls.return_value.data

    @patch("django_ecommers.apps.users.views.UserMeResponseSerializer")
    def test_get_serializer_receives_request_user(
        self,
        mock_serializer_cls,
        factory,
        mock_user,
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
        self,
        mock_serializer_cls,
        factory,
        mock_user,
    ):
        mock_serializer_cls.return_value.data = {
            "id": 1,
            "username": "john_doe",
            "email": "john@example.com",
        }

        request = factory.get("/user/me/")
        force_authenticate(request, user=mock_user)
        response = UserPrivateView.as_view()(request)

        assert "password" not in response.data


# ---------------------------------------------------------------------------
# UserPrivateView.patch
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestUserPrivateViewPatch:

    @patch("django_ecommers.apps.users.views.UserUpdateResponseSerializer")
    def test_patch_updates_user_successfully(
        self,
        mock_serializer_cls,
        factory,
        mock_user,
    ):
        mock_serializer_cls.return_value.is_valid.return_value = True
        mock_serializer_cls.return_value.data = {
            "id": 1,
            "username": "new_name",
        }

        request = factory.patch(
            "/user/me/",
            {"username": "new_name"},
            format="json",
        )
        force_authenticate(request, user=mock_user)
        response = UserPrivateView.as_view()(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == mock_serializer_cls.return_value.data
        mock_serializer_cls.return_value.save.assert_called_once()

    @patch("django_ecommers.apps.users.views.UserUpdateResponseSerializer")
    def test_patch_serializer_receives_instance_data_and_partial(
        self,
        mock_serializer_cls,
        factory,
        mock_user,
    ):
        payload = {"username": "new_name"}
        request = factory.patch("/user/me/", payload, format="json")
        force_authenticate(request, user=mock_user)

        UserPrivateView.as_view()(request)

        mock_serializer_cls.assert_called_once_with(
            mock_user,
            data=payload,
            partial=True,
        )

    @patch("django_ecommers.apps.users.views.UserUpdateResponseSerializer")
    def test_patch_returns_400_when_serializer_invalid(
        self,
        mock_serializer_cls,
        factory,
        mock_user,
    ):
        mock_serializer_cls.return_value.is_valid.side_effect = ValidationError(
            {"email": ["Enter a valid email address."]}
        )

        request = factory.patch(
            "/user/me/",
            {"email": "not-an-email"},
            format="json",
        )
        force_authenticate(request, user=mock_user)
        response = UserPrivateView.as_view()(request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch("django_ecommers.apps.users.views.UserUpdateResponseSerializer")
    def test_patch_does_not_save_when_invalid(
        self,
        mock_serializer_cls,
        factory,
        mock_user,
    ):
        mock_serializer_cls.return_value.is_valid.side_effect = ValidationError(
            {"email": ["Enter a valid email address."]}
        )

        request = factory.patch(
            "/user/me/",
            {"email": "not-an-email"},
            format="json",
        )
        force_authenticate(request, user=mock_user)
        UserPrivateView.as_view()(request)

        mock_serializer_cls.return_value.save.assert_not_called()

    def test_patch_requires_authentication(self, factory):
        request = factory.patch(
            "/user/me/",
            {"username": "new_name"},
            format="json",
        )
        response = UserPrivateView.as_view()(request)

        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    @patch("django_ecommers.apps.users.views.UserUpdateResponseSerializer")
    def test_patch_allows_single_field_update(
        self,
        mock_serializer_cls,
        factory,
        mock_user,
    ):
        mock_serializer_cls.return_value.is_valid.return_value = True
        mock_serializer_cls.return_value.data = {
            "id": 1,
            "email": "new@example.com",
        }

        request = factory.patch(
            "/user/me/",
            {"email": "new@example.com"},
            format="json",
        )
        force_authenticate(request, user=mock_user)
        response = UserPrivateView.as_view()(request)

        assert response.status_code == status.HTTP_200_OK
        assert mock_serializer_cls.call_args.kwargs["partial"] is True

    @patch("django_ecommers.apps.users.views.UserUpdateResponseSerializer")
    def test_patch_response_does_not_leak_password(
        self,
        mock_serializer_cls,
        factory,
        mock_user,
    ):
        mock_serializer_cls.return_value.is_valid.return_value = True
        mock_serializer_cls.return_value.data = {
            "id": 1,
            "username": "new_name",
        }

        request = factory.patch(
            "/user/me/",
            {"username": "new_name"},
            format="json",
        )
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
# UserPasswordResetView.post
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestUserPasswordResetView:

    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def user(self, db):
        user = Users.objects.create(
            username="resetuser",
            email="reset@example.com",
        )
        user.set_password("OldPassword123!")
        user.save()
        return user

    @pytest.fixture
    def authenticated_client(self, api_client, user):
        api_client.force_authenticate(user=user)
        return api_client

    @pytest.fixture
    def url(self):
        return reverse("reset_password")

    def test_password_reset_success(self, authenticated_client, user, url):
        response = authenticated_client.post(
            url,
            {
                "current_password": "OldPassword123!",
                "new_password": "NewPassword123!",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            "message": "Your password reset successfully."
        }

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
        assert response.data == {
            "error": "Your current_password is incorrect."
        }

        user.refresh_from_db()
        assert user.check_password("OldPassword123!")
        assert not user.check_password("NewPassword123!")

    def test_password_reset_requires_authentication(self, api_client, url):
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
            {"new_password": "NewPassword123!"},
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
            {"current_password": "OldPassword123!"},
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


# ---------------------------------------------------------------------------
# UserAddressGetView.get
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestUserAddressGetView:

    def test_get_own_address_successfully(self, factory, user, address):
        request = factory.get(f"/user/address/{address.pk}/")
        force_authenticate(request, user=user)

        response = UserAddressGetView.as_view()(
            request,
            pk=address.pk,
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["location"] == address.location

    def test_get_nonexistent_address_returns_404(self, factory, user):
        request = factory.get("/user/address/999999/")
        force_authenticate(request, user=user)

        response = UserAddressGetView.as_view()(request, pk=999999)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_another_users_address_does_not_expose_it(
        self,
        factory,
        user,
        another_user,
    ):
        other_address = Addresses.objects.create(
            user=another_user,
            location="Munich",
        )

        request = factory.get(f"/user/address/{other_address.pk}/")
        force_authenticate(request, user=user)

        response = UserAddressGetView.as_view()(
            request,
            pk=other_address.pk,
        )

        # The current view returns 401 for an address owned by another user.
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_requires_authentication(self, factory, address):
        request = factory.get(f"/user/address/{address.pk}/")

        response = UserAddressGetView.as_view()(
            request,
            pk=address.pk,
        )

        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_get_not_allowed_methods_return_405(self, factory, user, address):
        for method in ("post", "put", "patch", "delete"):
            request = getattr(factory, method)(
                f"/user/address/{address.pk}/"
            )
            force_authenticate(request, user=user)

            response = UserAddressGetView.as_view()(
                request,
                pk=address.pk,
            )

            assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


# ---------------------------------------------------------------------------
# UserAddressPrivateView.post
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestUserAddressPrivateViewPost:

    def test_post_creates_address_successfully(
        self,
        factory,
        user,
        address_payload,
    ):
        request = factory.post(
            "/user/addresses/",
            address_payload,
            format="json",
        )
        force_authenticate(request, user=user)

        response = UserAddressPrivateView.as_view()(request)

        assert response.status_code == status.HTTP_201_CREATED
        assert Addresses.objects.filter(
            user=user,
            location=address_payload["location"],
        ).exists()

    def test_post_requires_authentication(
        self,
        factory,
        address_payload,
    ):
        request = factory.post(
            "/user/addresses/",
            address_payload,
            format="json",
        )

        response = UserAddressPrivateView.as_view()(request)

        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_post_invalid_payload_returns_400(self, factory, user):
        request = factory.post(
            "/user/addresses/",
            {},
            format="json",
        )
        force_authenticate(request, user=user)

        response = UserAddressPrivateView.as_view()(request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Addresses.objects.filter(user=user).count() == 0

    def test_post_not_allowed_methods_return_405(
        self,
        factory,
        user,
        address_payload,
    ):
        for method in ("get", "put", "patch"):
            request = getattr(factory, method)(
                "/user/addresses/",
                address_payload,
                format="json",
            )
            force_authenticate(request, user=user)

            response = UserAddressPrivateView.as_view()(request)

            assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


# ---------------------------------------------------------------------------
# UserAddressPrivateView.delete
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestUserAddressPrivateViewDelete:

    def test_delete_own_address_successfully(self, factory, user, address):
        request = factory.delete(
            "/user/addresses/",
            {"location": address.location},
            format="json",
        )
        force_authenticate(request, user=user)

        response = UserAddressPrivateView.as_view()(request)

        assert response.status_code == status.HTTP_200_OK
        assert not Addresses.objects.filter(pk=address.pk).exists()

    def test_delete_nonexistent_address_returns_404(
        self,
        factory,
        user,
    ):
        request = factory.delete(
            "/user/addresses/",
            {"location": "Nonexistent location"},
            format="json",
        )
        force_authenticate(request, user=user)

        response = UserAddressPrivateView.as_view()(request)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_another_users_address_does_not_delete_it(
        self,
        factory,
        user,
        another_user,
    ):
        other_address = Addresses.objects.create(
            user=another_user,
            location="Munich",
        )

        request = factory.delete(
            "/user/addresses/",
            {"location": other_address.location},
            format="json",
        )
        force_authenticate(request, user=user)

        response = UserAddressPrivateView.as_view()(request)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Addresses.objects.filter(pk=other_address.pk).exists()

    def test_delete_requires_authentication(
        self,
        factory,
        address,
    ):
        request = factory.delete(
            "/user/addresses/",
            {"location": address.location},
            format="json",
        )

        response = UserAddressPrivateView.as_view()(request)

        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_delete_invalid_payload_returns_400(self, factory, user):
        request = factory.delete(
            "/user/addresses/",
            {},
            format="json",
        )
        force_authenticate(request, user=user)

        response = UserAddressPrivateView.as_view()(request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
