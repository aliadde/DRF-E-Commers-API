import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from django_ecommers.apps.products.models import Products
from django_ecommers.apps.users.models import Users


# ---------------
# Fixtures
# ---------------
@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def product(db):
    return Products.objects.create(
        name="Laptop",
        description="A powerful laptop",
        price=1200.50,
        active=True,
    )


@pytest.fixture
def url(product):
    return reverse("update_product", kwargs={"pk": product.pk})


@pytest.fixture
def admin_user(db):
    return Users.objects.create_superuser(
        username="admin_test",
        email="admin@example.com",
        password="StrongPass123!",
    )


@pytest.fixture
def staff_user(db):
    return Users.objects.create_user(
        username="staff_test",
        email="staff@example.com",
        password="StrongPass123!",
        is_staff=True,
    )


@pytest.fixture
def regular_user(db):
    return Users.objects.create_user(
        username="regular_test",
        email="regular@example.com",
        password="StrongPass123!",
        is_staff=False,
    )


@pytest.fixture
def admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def staff_client(api_client, staff_user):
    api_client.force_authenticate(user=staff_user)
    return api_client


@pytest.fixture
def regular_client(api_client, regular_user):
    api_client.force_authenticate(user=regular_user)
    return api_client


@pytest.fixture
def anonymous_client(api_client):
    return api_client


# ---------------
# Permission tests
# ---------------
@pytest.mark.django_db
class TestProductDeletePermissions:
    def test_admin_can_delete_product(
        self,
        admin_client,
        url,
        product,
    ):
        response = admin_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_staff_can_delete_product(
        self,
        staff_client,
        url,
        product,
    ):
        response = staff_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_authenticated_non_staff_user_cannot_delete_product(
        self,
        regular_client,
        url,
        product,
    ):
        response = regular_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Product must not be deleted.
        assert Products.objects.filter(pk=product.pk).exists()

    def test_anonymous_user_cannot_delete_product(
        self,
        anonymous_client,
        url,
        product,
    ):
        response = anonymous_client.delete(url)

        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

        # Product must not be deleted.
        assert Products.objects.filter(pk=product.pk).exists()


# ---------------
# Success / data integrity tests
# ---------------
@pytest.mark.django_db
class TestProductDeleteSuccess:
    def test_product_is_deleted_from_database(
        self,
        admin_client,
        url,
        product,
    ):
        product_id = product.pk

        response = admin_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        assert not Products.objects.filter(pk=product_id).exists()

    def test_delete_returns_empty_response(
        self,
        admin_client,
        url,
        product,
    ):
        response = admin_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.data is None

    def test_delete_only_target_product(
        self,
        admin_client,
        url,
        product,
        db,
    ):
        another_product = Products.objects.create(
            name="Mouse",
            description="Wireless mouse",
            price=35.99,
            active=True,
        )

        response = admin_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Target product was deleted.
        assert not Products.objects.filter(pk=product.pk).exists()

        # Other products must remain.
        assert Products.objects.filter(pk=another_product.pk).exists()


# ---------------
# Error tests
# ---------------
@pytest.mark.django_db
class TestProductDeleteErrors:
    def test_delete_non_existing_product(
        self,
        admin_client,
    ):
        url = reverse(
            "update_product",
            kwargs={"pk": 99999},
        )

        response = admin_client.delete(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_does_not_require_request_body(
        self,
        admin_client,
        url,
        product,
    ):
        response = admin_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Products.objects.filter(pk=product.pk).exists()
