import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from django_ecommers.apps.products.models import Category

from django.core.cache import cache


@pytest.fixture(autouse=True)
def clear_redis_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def url():
    return reverse("basket")

@pytest.fixture
def user_data():
    return {
        "username":"test",
        "email":"test@gmail.com",
        "password":"test"
    }

@pytest.fixture
def register_user(api_client, user_data):
    response = api_client.post(
        reverse("users_register"),
        data=user_data,
        format="json"
    )
    assert response.status_code == 201

@pytest.fixture
def login_user(register_user, api_client, user_data):
    del user_data["email"]

    response = api_client.post(
        reverse("login"),
        data=user_data,
        format="json"
    )
    assert response.status_code  == 200

    return {"access_token": response.json().get("access")}

@pytest.fixture
def authenticated_client(login_user, api_client):
    api_client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {login_user["access_token"]}"
    )
    return api_client



@pytest.mark.django_db
def test_get_basket_success(authenticated_client, url):
    response = authenticated_client.get(url)

    assert response.status_code == 200
    assert "basket" in response.json()
    assert "items" in response.json()

@pytest.mark.django_db
def test_get_basket_unauthenticated(api_client, url):
    response = api_client.get(url)
    assert response.status_code == 401

@pytest.mark.django_db
def test_get_basket_empty_items(authenticated_client, url):
    response = authenticated_client.get(url)
    assert response.json()["items"] == []

@pytest.mark.django_db
def test_get_basket_with_items(authenticated_client, url):
    from django_ecommers.apps.baskets.models import Baskets, BasketItems
    from django_ecommers.apps.products.models import Products

    basket = Baskets.objects.get(user__username="test")

    product_data = {
        "name":"pr 1",
        "price": 12.0
    }

    product = Products.objects.create(**product_data)
    BasketItems.objects.create(basket=basket, product=product, quantity=2)

    response = authenticated_client.get(url)
    data = response.json()

    assert response.status_code == 200
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 2
    assert data["items"][0]["product"] == product.id
    assert data["items"][0]["basket"] == basket.id

@pytest.mark.django_db
def test_get_basket_does_not_show_other_users_items(authenticated_client, url):
    from django_ecommers.apps.baskets.models import Baskets, BasketItems
    from django_ecommers.apps.products.models import Products
    from django_ecommers.apps.users.models import Users

    product_data = {
        "name":"pr 1",
        "price": 12.0
    }
    other = Users.objects.create_user(username="other", email="o@gmail.com", password="x")
    other_basket = Baskets.objects.get(user=other)
    product = Products.objects.create(**product_data)
    BasketItems.objects.create(basket=other_basket, product=product, quantity=5)

    response = authenticated_client.get(url)
    assert response.json()["items"] == []
