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
def product():
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
class TestProductUpdatePermissions:
    def test_admin_can_update_product(self, admin_client, url):
        response = admin_client.patch(
            url,
            data={"price": 1500.00},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

    def test_staff_can_update_product(self, staff_client, url):
        response = staff_client.patch(
            url,
            data={"price": 1500.00},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

    def test_anonymous_user_cannot_update_product(
        self,
        anonymous_client,
        url,
    ):
        response = anonymous_client.patch(
            url,
            data={"price": 1500.00},
            format="json",
        )

        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_authenticated_non_staff_user_cannot_update_product(
        self,
        regular_client,
        url,
    ):
        response = regular_client.patch(
            url,
            data={"price": 1500.00},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


# ---------------
# Success / data integrity tests
# ---------------
@pytest.mark.django_db
class TestProductUpdateSuccess:
    def test_update_single_field(
        self,
        admin_client,
        url,
        product,
    ):
        response = admin_client.patch(
            url,
            data={"price": 1500.00},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["price"] == 1500.00

        product.refresh_from_db()

        assert product.price == 1500.00

    def test_update_multiple_fields(
        self,
        admin_client,
        url,
        product,
    ):
        payload = {
            "name": "Gaming Laptop",
            "description": "A powerful gaming laptop",
            "price": 1800.00,
            "active": False,
        }

        response = admin_client.patch(
            url,
            data=payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        product.refresh_from_db()

        assert product.name == payload["name"]
        assert product.description == payload["description"]
        assert product.price == payload["price"]
        assert product.active == payload["active"]

    def test_partial_update_preserves_unspecified_fields(
        self,
        admin_client,
        url,
        product,
    ):
        original_name = product.name
        original_description = product.description
        original_active = product.active

        response = admin_client.patch(
            url,
            data={"price": 999.99},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        product.refresh_from_db()

        assert product.price == 999.99
        assert product.name == original_name
        assert product.description == original_description
        assert product.active == original_active

    def test_response_contains_updated_data(
        self,
        admin_client,
        url,
    ):
        payload = {
            "name": "Updated Laptop",
            "price": 2000.00,
        }

        response = admin_client.patch(
            url,
            data=payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == payload["name"]
        assert response.data["price"] == payload["price"]

    def test_product_persisted_in_database(
        self,
        admin_client,
        url,
        product,
    ):
        admin_client.patch(
            url,
            data={"name": "Updated Laptop"},
            format="json",
        )

        product.refresh_from_db()

        assert product.name == "Updated Laptop"
        assert product.description == "A powerful laptop"
        assert product.price == 1200.50
        assert product.active is True


# ---------------
# Error tests
# ---------------
@pytest.mark.django_db
class TestProductUpdateErrors:
    def test_update_non_existing_product(
        self,
        admin_client,
    ):
        url = reverse("update_product", kwargs={"pk": 99999})

        response = admin_client.patch(
            url,
            data={"price": 1500.00},
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_with_invalid_price(
        self,
        admin_client,
        url,
        product,
    ):
        response = admin_client.patch(
            url,
            data={"price": "not-a-number"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        product.refresh_from_db()

        assert product.price == 1200.50
