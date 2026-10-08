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

# ==============================
# Tests

@pytest.mark.django_db
def test_delete_item_from_basket_success(authenticated_client):
    product = create_product(name="pr 1", price=21 , quantity=3)

    # add to basket
    item = BasketItems.objects.create(
        basket=Baskets.objects.get(user__username="test"),
        product=product,
        quantity=1,
    )
    url = url_creator(item.id)

    response = authenticated_client.delete(url)

    assert response.status_code == 200


@pytest.fixture
def other_user_client():
    """کلاینت یک کاربر دوم (کاملاً جدا از کاربر test)."""
    client = APIClient()
    data = {"username": "other", "email": "other@gmail.com", "password": "other"}

    response = client.post(reverse("users_register"), data=data, format="json")
    assert response.status_code == 201

    response = client.post(
        reverse("login"),
        data={"username": "other", "password": "other"},
        format="json",
    )
    assert response.status_code == 200

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.json()['access']}")
    return client


def add_item(username: str, product, quantity: int = 1):
    """کمکی: یک آیتم به سبد کاربر مورد نظر اضافه می‌کند."""
    return BasketItems.objects.create(
        basket=Baskets.objects.get(user__username=username),
        product=product,
        quantity=quantity,
    )


@pytest.mark.django_db
def test_delete_item_removes_it_from_database(authenticated_client):
    product = create_product(name="pr 1", price=21, quantity=3)
    item = add_item("test", product)

    response = authenticated_client.delete(url_creator(item.id))

    assert response.status_code == 200
    assert not BasketItems.objects.filter(id=item.id).exists()


@pytest.mark.django_db
def test_delete_item_unauthenticated(api_client):
    response = api_client.delete(url_creator(1))

    assert response.status_code == 401


@pytest.mark.django_db
def test_delete_nonexistent_item_returns_404(authenticated_client):
    response = authenticated_client.delete(url_creator(99999))

    assert response.status_code == 404


@pytest.mark.django_db
def test_delete_other_users_item_is_forbidden(authenticated_client, other_user_client):
    product = create_product(name="pr 1", price=21, quantity=3)
    other_item = add_item("other", product)

    response = authenticated_client.delete(url_creator(other_item.id))

    assert response.status_code == 404
    assert BasketItems.objects.filter(id=other_item.id).exists()


@pytest.mark.django_db
def test_delete_item_does_not_affect_other_items(authenticated_client):
    product1 = create_product(name="pr 1", price=21, quantity=3)
    product2 = create_product(name="pr 2", price=30, quantity=5)
    item1 = add_item("test", product1)
    item2 = add_item("test", product2, quantity=2)

    response = authenticated_client.delete(url_creator(item1.id))

    assert response.status_code == 200
    assert not BasketItems.objects.filter(id=item1.id).exists()
    assert BasketItems.objects.filter(id=item2.id).exists()


@pytest.mark.django_db
def test_delete_same_item_twice(authenticated_client):
    product = create_product(name="pr 1", price=21, quantity=3)
    item = add_item("test", product)
    url = url_creator(item.id)

    assert authenticated_client.delete(url).status_code == 200
    assert authenticated_client.delete(url).status_code == 404


@pytest.mark.django_db
def test_delete_item_keeps_product_and_basket(authenticated_client):
    from django_ecommers.apps.products.models import Products

    product = create_product(name="pr 1", price=21, quantity=3)
    item = add_item("test", product)

    authenticated_client.delete(url_creator(item.id))

    assert Products.objects.filter(id=product.id).exists()
    assert Baskets.objects.filter(user__username="test").exists()


@pytest.mark.django_db
def test_delete_item_does_not_change_product_stock(authenticated_client):
    product = create_product(name="pr 1", price=21, quantity=3)
    item = add_item("test", product, quantity=2)

    authenticated_client.delete(url_creator(item.id))

    product.refresh_from_db()
    assert product.quantity == 3


@pytest.mark.django_db
def test_delete_item_with_invalid_token(api_client):
    api_client.credentials(HTTP_AUTHORIZATION="Bearer invalid.token.here")

    response = api_client.delete(url_creator(1))

    assert response.status_code == 401
