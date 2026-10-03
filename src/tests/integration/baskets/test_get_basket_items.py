import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from django_ecommers.apps.baskets.models import BasketItems, Baskets
from django_ecommers.apps.users.models import Users

from django.core.cache import cache


@pytest.fixture(autouse=True)
def clear_redis_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api_client():
    return APIClient()

def url_creator(*args):
    return reverse("basket_item", args=args)

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

def create_product(name: str, price: float, **kwargs):
    """ create product and dump in database. """
    from django_ecommers.apps.products.models import Products

    data = {
        "name": name,
        "price": price,
        **kwargs
    }

    new_product = Products.objects.create(**data)
    new_product.save()
    return new_product



@pytest.mark.django_db
def test_get_specific_item_from_basket( authenticated_client):
    product = create_product(name="pr 1", price=21.0)
    # add product to basket
    user = Users.objects.get(username='test')
    user_basket = Baskets.objects.get(user=user)
    item = BasketItems.objects.create(
        basket=user_basket,
        product=product,
        quantity=1
    )
    url = url_creator(item.id)

    response = authenticated_client.get(url)
    data = response.json()

    assert response.status_code == 200
    assert data["id"] == item.id
    assert data["basket"] == user_basket.id
    assert data["product"] == product.id
    assert data["quantity"] == 1


@pytest.mark.django_db
def test_get_item_unauthenticated(api_client):
    response = api_client.get(url_creator(1))
    assert response.status_code == 401


@pytest.mark.django_db
def test_get_item_not_found(authenticated_client):
    response = authenticated_client.get(url_creator(99999))
    assert response.status_code == 404


@pytest.mark.django_db
def test_get_item_of_other_user(authenticated_client):
    other = Users.objects.create_user(
        username="other", email="other@gmail.com", password="x"
    )
    other_basket = Baskets.objects.get(user=other)
    product = create_product(name="pr 2", price=10.0)
    other_item = BasketItems.objects.create(
        basket=other_basket, product=product, quantity=1
    )

    response = authenticated_client.get(url_creator(other_item.id))
    assert response.status_code == 404


@pytest.mark.django_db
def test_get_item_when_basket_missing(authenticated_client):
    Baskets.objects.filter(user__username="test").delete()
    response = authenticated_client.get(url_creator(1))
    assert response.status_code == 404
