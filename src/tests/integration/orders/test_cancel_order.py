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

# =================================================


pytestmark = pytest.mark.django_db


def test_cancel_pending_order_restores_product_quantity(
    authenticated_client,
):
    # Create an order. Each product is ordered with quantity=2.
    order = create_order(authenticated_client)

    order_items = list(
        OrderItems.objects.filter(order=order).select_related("product")
    )

    assert order.status == Orders.Status.PENDING
    assert len(order_items) == 3

    # Save stock levels after order creation, when stock has been deducted.
    stock_before_cancel = {
        item.product_id: item.product.quantity
        for item in order_items
    }

    response = authenticated_client.delete(
        url_creator("order", order.id)
    )

    assert response.status_code == status.HTTP_200_OK

    order.refresh_from_db()
    assert order.status == Orders.Status.CANCELLED

    # Verify that the ordered quantities have been restored.
    for item in order_items:
        product = Products.objects.get(id=item.product_id)

        assert product.quantity == (
            stock_before_cancel[item.product_id] + item.quantity
        )


def test_cancelled_order_does_not_restore_stock_twice(
    authenticated_client,
):
    order = create_order(authenticated_client)

    response = authenticated_client.delete(
        url_creator("order", order.id)
    )
    assert response.status_code == status.HTTP_200_OK

    order.refresh_from_db()
    assert order.status == Orders.Status.CANCELLED

    stock_after_first_cancel = dict(
        Products.objects.filter(
            orderitems__order=order
        ).values_list("id", "quantity").distinct()
    )

    # Cancel the same order again.
    response = authenticated_client.delete(
        url_creator("order", order.id)
    )

    assert response.status_code == status.HTTP_200_OK

    order.refresh_from_db()
    assert order.status == Orders.Status.CANCELLED

    stock_after_second_cancel = dict(
        Products.objects.filter(
            orderitems__order=order
        ).values_list("id", "quantity").distinct()
    )

    assert stock_after_second_cancel == stock_after_first_cancel


@pytest.mark.parametrize(
    "initial_status",
    [
        Orders.Status.PAID,
        Orders.Status.SHIPPED,
    ],
)
def test_non_pending_order_is_not_cancelled(
    authenticated_client,
    initial_status,
):
    order = create_order(authenticated_client)

    order.status = initial_status
    order.save(update_fields=["status"])

    stock_before_cancel = dict(
        Products.objects.filter(
            orderitems__order=order
        ).values_list("id", "quantity").distinct()
    )

    response = authenticated_client.delete(
        url_creator("order", order.id)
    )

    assert response.status_code == status.HTTP_200_OK

    order.refresh_from_db()
    assert order.status == initial_status

    stock_after_cancel = dict(
        Products.objects.filter(
            orderitems__order=order
        ).values_list("id", "quantity").distinct()
    )

    assert stock_after_cancel == stock_before_cancel


def test_cannot_cancel_another_users_order(
    authenticated_client,
):
    order = create_order(authenticated_client)

    other_client = create_other_authenticated_client()

    response = other_client.delete(
        url_creator("order", order.id)
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND

    order.refresh_from_db()
    assert order.status == Orders.Status.PENDING


def test_cancel_nonexistent_order_returns_404(
    authenticated_client,
):
    response = authenticated_client.delete(
        url_creator("order", 999999)
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_cancel_order_requires_authentication(api_client):
    response = api_client.delete(
        url_creator("order", 999999)
    )

    assert response.status_code in (
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    )
