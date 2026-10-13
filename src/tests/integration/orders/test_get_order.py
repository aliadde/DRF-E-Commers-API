import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django_ecommers.apps.users.models import Users, Addresses
from django_ecommers.apps.products.models import Products
from django_ecommers.apps.orders.models import Orders, OrderItems
from django_ecommers.apps.baskets.models import Baskets, BasketItems


@pytest.fixture
def api_client():
    return APIClient()

def url_creator(url_name, *args):
    return reverse(url_name, args=args)

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

    user: Users = Users.objects.get(username=user_data['username'])
    address = Addresses.objects.create(
        location= "home",
        user=user
    )

    assert address

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

# create some product in basket
def add_product_basket(client:APIClient)-> list[dict[str,str|int]]:
    # create products
    products = [
        {
            "name":"pr 1",
            "price": 11,
            "quantity":10
        },
        {
            "name":"pr 2",
            "price": 12,
            "quantity":10
        },
        {
            "name":"pr 3",
            "price": 13,
            "quantity":10
        }
    ]

    for pr in products:
        product = create_product(
            name=pr["name"],
            price=pr["price"],
            quantity=pr["quantity"]
        )
        assert product.name  == pr["name"]
        assert product.quantity  == pr["quantity"]
        assert product.price  == pr["price"]

        # client  add product for user (user_client)
        resp  =client.post(
            url_creator("basket"),
            data={
                "product":product.id,
                "quantity":"2"
            },
            format="json"
        )
        assert resp.status_code == 201
    return products

def create_order(client: APIClient):
    products = add_product_basket(client)

    user = Users.objects.get(username="test")
    address = Addresses.objects.create(
        location="home",
        user=user
    )
    response = client.post(
        url_creator("create order"),
        data={"address":address.id},
        format="json"
    )
    assert response.json().get("detail") == "Order created successfully."

    return Orders.objects.get(id=response.json().get("order_id"))

def create_other_authenticated_client():
    user = Users.objects.create_user(
        username="other",
        email="other@gmail.com",
        password="other-password",
    )

    client = APIClient()
    response = client.post(
        reverse("login"),
        data={
            "username": user.username,
            "password": "other-password",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK

    client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {response.json()['access']}"
    )
    return client


# =============

@pytest.mark.django_db
def test_get_order_success(authenticated_client):
    order = create_order(authenticated_client)

    response = authenticated_client.get(
        reverse("order", args=[order.id])
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["id"] == order.id
    assert data["total"] == pytest.approx(72.0)
    assert data["status"] == Orders.Status.PENDING
    assert data["address"] == order.address_id

    assert "user" not in data


@pytest.mark.django_db
def test_get_order_contains_all_order_items(authenticated_client):
    order = create_order(authenticated_client)

    response = authenticated_client.get(
        reverse("order", args=[order.id])
    )

    assert response.status_code == status.HTTP_200_OK

    # GetOrderSerializer is a ModelSerializer for Orders.
    # OrderItems are not declared as a nested field in that serializer.
    assert "orderitems_set" not in response.json()
    assert OrderItems.objects.filter(order=order).count() == 3


@pytest.mark.django_db
def test_get_order_not_found(authenticated_client):
    response = authenticated_client.get(
        reverse("order", args=[999999])
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_get_order_requires_authentication(api_client):
    response = api_client.get(
        reverse("order", args=[1])
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_user_cannot_get_another_users_order(authenticated_client):
    order = create_order(authenticated_client)
    other_client = create_other_authenticated_client()

    response = other_client.get(
        reverse("order", args=[order.id])
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_get_order_does_not_change_order(authenticated_client):
    order = create_order(authenticated_client)

    original_total = order.total
    original_status = order.status
    original_address_id = order.address_id
    original_items_count = OrderItems.objects.filter(order=order).count()

    response = authenticated_client.get(
        reverse("order", args=[order.id])
    )

    assert response.status_code == status.HTTP_200_OK

    order.refresh_from_db()

    assert order.total == original_total
    assert order.status == original_status
    assert order.address_id == original_address_id
    assert OrderItems.objects.filter(order=order).count() == original_items_count
