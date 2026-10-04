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
# TEsts
# ==================
# basket
@pytest.mark.django_db
def test_add_item_success(authenticated_client, url):


    # create a product in database
    product = create_product(name="pr 1", price=12.0)

    item_data = {
        "product":product.id,
        "quantity":1,
    }
    response = authenticated_client.post(
        url,
        data=item_data,
        format="json"
    )

    assert response.status_code == 201
    basket = Baskets.objects.filter(
        user=Users.objects.get(username="test")
    ).first()
    basket_item = BasketItems.objects.filter(
        basket_id=basket.id,
        product_id=product.id
    ).first()

    assert basket_item.quantity == 1
    assert basket_item.product.id == product.id
    assert basket_item.basket.id == basket.id


@pytest.mark.django_db
def test_add_existing_product_increments_quantity(authenticated_client, url):
    product = create_product(name="pr 1", price=12.0, quantity=3)

    first = post_item(authenticated_client, url, product.id, 1)
    second = post_item(authenticated_client, url, product.id, 1)

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json()["quantity"] == 2

    items = BasketItems.objects.filter(
        basket__user__username="test", product_id=product.id
    )
    assert items.count() == 1
    assert items.first().quantity == 2


@pytest.mark.django_db
def test_add_different_products_creates_separate_items(authenticated_client, url):
    product_1 = create_product(name="pr 1", price=12.0)
    product_2 = create_product(name="pr 2", price=20.0)

    r1 = post_item(authenticated_client, url, product_1.id, 1)
    r2 = post_item(authenticated_client, url, product_2.id, 1)

    assert r1.status_code == 201
    assert r2.status_code == 201

    basket = Baskets.objects.get(user__username="test")
    items = BasketItems.objects.filter(basket=basket)
    assert items.count() == 2
    assert items.get(product=product_1).quantity == 1
    assert items.get(product=product_2).quantity == 1

@pytest.mark.django_db
def test_add_item_response_body(authenticated_client, url):
    product = create_product(name="pr 1", price=12.0)

    response = post_item(authenticated_client, url, product.id, 1)

    assert response.status_code == 201
    data = response.json()
    assert data["product"] == product.id
    assert data["quantity"] == 1


@pytest.mark.django_db
def test_add_item_unauthenticated(api_client, url):
    product = create_product(name="pr 1", price=12.0)

    response = post_item(api_client, url, product.id, 1)

    assert response.status_code == 401
    assert BasketItems.objects.count() == 0

@pytest.mark.django_db
def test_add_item_user_without_basket_returns_404(authenticated_client, url):
    product = create_product(name="pr 1", price=12.0)
    Baskets.objects.filter(user__username="test").delete()

    response = post_item(authenticated_client, url, product.id, 1)

    assert response.status_code == 404
    assert BasketItems.objects.count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize("bad_quantity", [0, -1, "abc", 1.5, None])
def test_add_item_invalid_quantity(authenticated_client, url, bad_quantity):
    product = create_product(name="pr 1", price=12.0)

    response = post_item(authenticated_client, url, product.id, bad_quantity)

    assert response.status_code == 400
    assert "quantity" in response.json()
    assert BasketItems.objects.count() == 0



@pytest.mark.django_db
def test_add_item_missing_product(authenticated_client, url):
    response = authenticated_client.post(url, data={"quantity": 2}, format="json")

    assert response.status_code == 400
    assert "product" in response.json()


@pytest.mark.django_db
def test_add_item_empty_body(authenticated_client, url):
    response = authenticated_client.post(url, data={}, format="json")

    assert response.status_code == 400
    assert BasketItems.objects.count() == 0

@pytest.mark.django_db
def test_add_item_does_not_affect_other_users_basket(authenticated_client, url):
    other_client = APIClient()
    resp = other_client.post(
        reverse("users_register"),
        data={"username": "other", "email": "other@gmail.com", "password": "other"},
        format="json",
    )
    assert resp.status_code == 201

    product = create_product(name="pr 1", price=12.0)
    post_item(authenticated_client, url, product.id, 2)

    other_basket = Baskets.objects.get(user__username="other")
    assert not BasketItems.objects.filter(basket=other_basket).exists()


@pytest.mark.django_db
def test_add_item_ignores_basket_in_payload(authenticated_client, url):
    other_client = APIClient()
    other_client.post(
        reverse("users_register"),
        data={"username": "other", "email": "other@gmail.com", "password": "other"},
        format="json",
    )
    other_basket = Baskets.objects.get(user__username="other")
    product = create_product(name="pr 1", price=12.0)

    response = authenticated_client.post(
        url,
        data={"product": product.id, "quantity": 1, "basket": other_basket.id},
        format="json",
    )

    assert response.status_code == 201
    assert not BasketItems.objects.filter(basket=other_basket).exists()
    my_basket = Baskets.objects.get(user__username="test")
    assert BasketItems.objects.filter(basket=my_basket, product=product).exists()


@pytest.mark.django_db
def test_quantity_more_than_real_product_quantity_fail(authenticated_client,url):
    product = create_product(name="pr 1", price=12, quantity=2)

    item_data = {
        "product": product.id,
        "quantity":3
    }
    response = authenticated_client.post(
        url,
        data=item_data,
        format="json"
    )
    assert response.status_code == 400
    assert response.json().get("detail") == "Requested quantity exceeds available stock."

@pytest.mark.django_db
def test_quantity_equal_to_real_product_quantity_success(authenticated_client,url):
    product = create_product(name="pr 1", price=12, quantity=2)

    item_data = {
        "product": product.id,
        "quantity":2
    }
    response = authenticated_client.post(
        url,
        data=item_data,
        format="json"
    )
    assert response.status_code == 201
