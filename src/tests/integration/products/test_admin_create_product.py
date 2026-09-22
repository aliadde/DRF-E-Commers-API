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
def url():
    return reverse("product")


@pytest.fixture
def valid_product_payload():
    return {
        "name": "Laptop",
        "description": "A powerful laptop",
        "price": 1200.50,
        "active": True,
    }


@pytest.fixture
def products():
    return {
        "pr01": {
            "name": "Laptop",
            "description": "A powerful laptop",
            "price": 1200.50,
            "active": True,
        },
        "pr02": {
            "name": "Mouse",
            "description": "Wireless mouse",
            "price": 35.99,
            "active": True,
        },
        "pr03": {
            "name": "Keyboard",
            "description": None,
            "price": 75.00,
            "active": False,
        },
    }


@pytest.fixture
def admin_user(db):
    return Users.objects.create_superuser(
        username="admin_test",
        email="admin@example.com",
        password="StrongPass123!",
    )


@pytest.fixture
def staff_user(db):
    """کاربر staff عادی، بدون superuser — باید بتونه مثل admin دسترسی داشته باشه اگه پرمیژن فقط is_staff رو چک می‌کنه."""
    return Users.objects.create_user(
        username="staff_test",
        email="staff@example.com",
        password="StrongPass123!",
        is_staff=True,
    )


@pytest.fixture
def regular_user(db):
    """کاربر احراز هویت‌شده ولی is_staff=False — باید 403 بگیره، نه 401."""
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
class TestProductCreatePermissions:
    def test_admin_can_create_product(self, admin_client, url, valid_product_payload):
        response = admin_client.post(url, data=valid_product_payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    def test_staff_can_create_product(self, staff_client, url, valid_product_payload):
        response = staff_client.post(url, data=valid_product_payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    def test_anonymous_user_cannot_create_product(
        self, anonymous_client, url, valid_product_payload
    ):
        response = anonymous_client.post(url, data=valid_product_payload, format="json")
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )
        assert Products.objects.count() == 0

    def test_authenticated_non_staff_user_cannot_create_product(
        self, regular_client, url, valid_product_payload
    ):
        response = regular_client.post(url, data=valid_product_payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Products.objects.count() == 0


# ---------------
# Success / data integrity tests
# ---------------
@pytest.mark.django_db
class TestProductCreateSuccess:
    def test_response_contains_correct_data(
        self, admin_client, url, valid_product_payload
    ):
        response = admin_client.post(url, data=valid_product_payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == valid_product_payload["name"]
        assert response.data["description"] == valid_product_payload["description"]
        assert response.data["price"] == valid_product_payload["price"]
        assert response.data["active"] == valid_product_payload["active"]
        assert "id" in response.data

    def test_product_persisted_in_database(
        self, admin_client, url, valid_product_payload
    ):
        admin_client.post(url, data=valid_product_payload, format="json")

        assert Products.objects.count() == 1
        product = Products.objects.first()
        assert product.name == valid_product_payload["name"]
        assert product.price == valid_product_payload["price"]

    def test_create_product_with_null_description(self, admin_client, url, products):
        response = admin_client.post(url, data=products["pr03"], format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["description"] is None

    def test_create_multiple_products(self, admin_client, url, products):
        for payload in products.values():
            response = admin_client.post(url, data=payload, format="json")
            assert response.status_code == status.HTTP_201_CREATED

        assert Products.objects.count() == len(products)

    def test_active_defaults_when_omitted(self, admin_client, url):
        payload = {
            "name": "No Active Field",
            "description": "desc",
            "price": 10.0,
        }
        response = admin_client.post(url, data=payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["active"] is True  # default=1 در مدل


# ---------------
# Validation tests
# ---------------
@pytest.mark.django_db
class TestProductCreateValidation:
    def test_missing_name_returns_400(self, admin_client, url, valid_product_payload):
        payload = valid_product_payload.copy()
        del payload["name"]

        response = admin_client.post(url, data=payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in response.data
        assert Products.objects.count() == 0

    def test_missing_price_returns_400(self, admin_client, url, valid_product_payload):
        payload = valid_product_payload.copy()
        del payload["price"]

        response = admin_client.post(url, data=payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "price" in response.data
        assert Products.objects.count() == 0

    def test_invalid_price_type_returns_400(
        self, admin_client, url, valid_product_payload
    ):
        payload = valid_product_payload.copy()
        payload["price"] = "not-a-number"

        response = admin_client.post(url, data=payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "price" in response.data
        assert Products.objects.count() == 0

    def test_empty_payload_returns_400(self, admin_client, url):
        response = admin_client.post(url, data={}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Products.objects.count() == 0

    def test_invalid_active_type_returns_400(
        self, admin_client, url, valid_product_payload
    ):
        payload = valid_product_payload.copy()
        payload["active"] = "maybe"

        response = admin_client.post(url, data=payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
