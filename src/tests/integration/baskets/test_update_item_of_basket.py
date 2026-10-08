import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from django_ecommers.apps.baskets.models import Baskets, BasketItems
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

@pytest.fixture
def url():
    return reverse("basket")

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

def post_item(client, url, product_id, quantity):
    return client.post(
        url,
        data={"product": product_id, "quantity": quantity},
        format="json",
    )

# ==================
# PATCH /basket/items/<pk>/ tests
# ==================

@pytest.mark.django_db
def test_update_item_success(authenticated_client):
    product = create_product(name="pr 1", price=21, quantity=3)
    item = BasketItems.objects.create(
        basket=Baskets.objects.get(user__username="test"),
        product=product,
        quantity=2
    )

    update_data = {
        "product":product.id,
        "quantity": 1
    }

    response = authenticated_client.patch(
        url_creator(item.id),
        data=update_data,
        format="json"
    )
    data = response.json()
    assert response.status_code == 200
    assert data["quantity"] == 1
    assert data["product"] == product.id


def make_client(username: str) -> APIClient:
    """ Register + login a user and return an authenticated client. """
    client = APIClient()
    register = client.post(
        reverse("users_register"),
        data={
            "username": username,
            "email": f"{username}@gmail.com",
            "password": "test",
        },
        format="json",
    )
    assert register.status_code == 201

    login = client.post(
        reverse("login"),
        data={"username": username, "password": "test"},
        format="json",
    )
    assert login.status_code == 200

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.json()['access']}")
    return client


def create_basket_item(username: str, product, quantity: int) -> BasketItems:
    return BasketItems.objects.create(
        basket=Baskets.objects.get(user__username=username),
        product=product,
        quantity=quantity,
    )


@pytest.mark.django_db
def test_update_item_persists_in_database(authenticated_client):
    product = create_product(name="pr 1", price=21, quantity=5)
    item = create_basket_item("test", product, quantity=2)

    response = authenticated_client.patch(
        url_creator(item.id),
        data={"product": product.id, "quantity": 4},
        format="json",
    )

    assert response.status_code == 200
    item.refresh_from_db()
    # Make sure the change is really saved, not only returned in response.
    assert item.quantity == 4


@pytest.mark.django_db
def test_update_item_unauthenticated(api_client):
    # No credentials set on purpose.
    response = api_client.patch(
        url_creator(1),
        data={"product": 1, "quantity": 1},
        format="json",
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_update_item_not_found(authenticated_client):
    product = create_product(name="pr 1", price=21, quantity=5)

    response = authenticated_client.patch(
        url_creator(999999),
        data={"product": product.id, "quantity": 1},
        format="json",
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_update_item_of_another_user_is_forbidden(authenticated_client):
    """ A user must not be able to modify another user's basket item. """
    other_client = make_client("other")  # registered after "test"
    product = create_product(name="pr 1", price=21, quantity=5)
    other_item = create_basket_item("other", product, quantity=2)

    # "test" user tries to patch the item that belongs to "other".
    response = authenticated_client.patch(
        url_creator(other_item.id),
        data={"product": product.id, "quantity": 5},
        format="json",
    )

    assert response.status_code == 404
    other_item.refresh_from_db()
    assert other_item.quantity == 2  # must stay untouched


@pytest.mark.django_db
def test_update_item_exceeds_stock(authenticated_client):
    product = create_product(name="pr 1", price=21, quantity=3)
    item = create_basket_item("test", product, quantity=1)

    response = authenticated_client.patch(
        url_creator(item.id),
        data={"product": product.id, "quantity": 10},
        format="json",
    )

    assert response.status_code == 400
    item.refresh_from_db()
    assert item.quantity == 1


@pytest.mark.django_db
@pytest.mark.parametrize("bad_quantity", [0, -1, "abc", None, 1.5])
def test_update_item_invalid_quantity(authenticated_client, bad_quantity):
    product = create_product(name="pr 1", price=21, quantity=5)
    item = create_basket_item("test", product, quantity=2)

    response = authenticated_client.patch(
        url_creator(item.id),
        data={"product": product.id, "quantity": bad_quantity},
        format="json",
    )

    assert response.status_code == 400
    item.refresh_from_db()
    assert item.quantity == 2


@pytest.mark.django_db
def test_update_item_missing_quantity(authenticated_client):
    product = create_product(name="pr 1", price=21, quantity=5)
    item = create_basket_item("test", product, quantity=2)

    response = authenticated_client.patch(
        url_creator(item.id),
        data={"product": product.id},
        format="json",
    )

    assert response.status_code == 400
    assert "quantity" in response.json()


@pytest.mark.django_db
def test_update_item_nonexistent_product(authenticated_client):
    product = create_product(name="pr 1", price=21, quantity=5)
    item = create_basket_item("test", product, quantity=2)

    response = authenticated_client.patch(
        url_creator(item.id),
        data={"product": 999999, "quantity": 1},
        format="json",
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_update_item_does_not_touch_other_items(authenticated_client):
    product_1 = create_product(name="pr 1", price=21, quantity=5)
    product_2 = create_product(name="pr 2", price=30, quantity=5)
    item_1 = create_basket_item("test", product_1, quantity=2)
    item_2 = create_basket_item("test", product_2, quantity=3)

    response = authenticated_client.patch(
        url_creator(item_1.id),
        data={"product": product_1.id, "quantity": 1},
        format="json",
    )

    assert response.status_code == 200
    item_2.refresh_from_db()
    assert item_2.quantity == 3
