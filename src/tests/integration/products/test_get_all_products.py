import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from django_ecommers.apps.products.models import Products


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def url():
    return reverse("get_all_products")


@pytest.fixture
def products():
    return Products.objects.bulk_create(
        [
            Products(
                name="Laptop",
                description="A powerful laptop",
                price=1200.50,
                active=True,
            ),
            Products(
                name="Mouse",
                description="Wireless mouse",
                price=35.99,
                active=True,
            ),
            Products(
                name="Keyboard",
                description=None,
                price=75.00,
                active=False,
            ),
        ]
    )


@pytest.mark.django_db
def test_get_all_products(api_client, url, products):
    """Get all products."""
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == len(products)

    assert data == [
        {
            "id": products[0].id,
            "name": products[0].name,
            "description": products[0].description,
            "price": products[0].price,
            "active": products[0].active,
        },
        {
            "id": products[1].id,
            "name": products[1].name,
            "description": products[1].description,
            "price": products[1].price,
            "active": products[1].active,
        },
        {
            "id": products[2].id,
            "name": products[2].name,
            "description": products[2].description,
            "price": products[2].price,
            "active": products[2].active,
        },
    ]


@pytest.mark.django_db
def test_get_all_products_when_database_is_empty(api_client, url):
    """Return an empty list when there are no products."""
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


@pytest.mark.django_db
def test_get_all_products_returns_all_products(api_client, url):
    """Return every product in the database."""
    Products.objects.create(
        name="Laptop",
        description="A laptop",
        price=1200,
        active=True,
    )
    Products.objects.create(
        name="Mouse",
        description="A mouse",
        price=50,
        active=True,
    )
    Products.objects.create(
        name="Keyboard",
        description="A keyboard",
        price=100,
        active=False,
    )

    response = api_client.get(url)

    data = response.json()

    assert len(data) == Products.objects.count()


@pytest.mark.django_db
def test_get_all_products_includes_inactive_products(api_client, url):
    """Return inactive products as well as active products."""
    active_product = Products.objects.create(
        name="Laptop",
        price=1200,
        active=True,
    )

    inactive_product = Products.objects.create(
        name="Old Laptop",
        price=500,
        active=False,
    )

    response = api_client.get(url)

    data = response.json()

    returned_ids = {product["id"] for product in data}

    assert active_product.id in returned_ids
    assert inactive_product.id in returned_ids


@pytest.mark.django_db
def test_get_all_products_preserves_product_data(api_client, url):
    """Return the stored product data without changing it."""
    product = Products.objects.create(
        name="Gaming Laptop",
        description="High performance laptop",
        price=2499.99,
        active=True,
    )

    response = api_client.get(url)

    data = response.json()

    assert data == [
        {
            "id": product.id,
            "name": "Gaming Laptop",
            "description": "High performance laptop",
            "price": 2499.99,
            "active": True,
        }
    ]


@pytest.mark.django_db
def test_get_all_products_handles_null_description(api_client, url):
    """Return null when a product has no description."""
    product = Products.objects.create(
        name="Mouse",
        description=None,
        price=35.99,
        active=True,
    )

    response = api_client.get(url)

    data = response.json()

    assert data[0]["description"] is None
    assert data[0]["id"] == product.id


@pytest.mark.django_db
def test_get_all_products_preserves_boolean_active_value(api_client, url):
    """Return the correct active boolean value."""
    active_product = Products.objects.create(
        name="Active product",
        price=100,
        active=True,
    )

    inactive_product = Products.objects.create(
        name="Inactive product",
        price=200,
        active=False,
    )

    response = api_client.get(url)

    data = response.json()

    products_by_id = {product["id"]: product for product in data}

    assert products_by_id[active_product.id]["active"] is True
    assert products_by_id[inactive_product.id]["active"] is False


@pytest.mark.django_db
def test_get_all_products_preserves_price(api_client, url):
    """Return the correct price for every product."""
    product = Products.objects.create(
        name="Expensive Product",
        price=99999.99,
        active=True,
    )

    response = api_client.get(url)

    data = response.json()

    assert data[0]["price"] == 99999.99
    assert data[0]["price"] == product.price


@pytest.mark.django_db
def test_get_all_products_returns_expected_fields(api_client, url):
    """Return only the fields defined by the serializer."""
    Products.objects.create(
        name="Laptop",
        description="A laptop",
        price=1200,
        active=True,
    )

    response = api_client.get(url)

    data = response.json()

    assert set(data[0].keys()) == {
        "id",
        "name",
        "description",
        "price",
        "active",
    }


@pytest.mark.django_db
def test_get_all_products_returns_json(api_client, url):
    """Return a JSON response."""
    Products.objects.create(
        name="Laptop",
        price=1200,
    )

    response = api_client.get(url)

    assert response["Content-Type"].startswith("application/json")


@pytest.mark.django_db
def test_get_all_products_does_not_modify_database(api_client, url):
    """GET request must not modify the database."""
    Products.objects.create(
        name="Laptop",
        price=1200,
        active=True,
    )

    before_count = Products.objects.count()

    api_client.get(url)

    after_count = Products.objects.count()

    assert after_count == before_count
