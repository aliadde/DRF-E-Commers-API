import pytest
from django.urls import reverse
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
# =============

@pytest.mark.django_db
def test_create_order_success(authenticated_client):
    add_product_basket(client=authenticated_client)

    response = authenticated_client.post(
        url_creator("create order"),
        data={"address":1},
        format="json"
    )
    assert response.json().get("detail") == "Order created successfully."


@pytest.mark.django_db
def test_create_order_success_creates_order_and_items(authenticated_client):
    products = add_product_basket(client=authenticated_client)
    address = Addresses.objects.create(
        location="home",
        user=Users.objects.get(username="test")
    )

    response = authenticated_client.post(
        url_creator("create order"),
        data={"address": address.id},
        format="json",
    )

    assert response.status_code == 201

    order = Orders.objects.get(pk=response.json()["order_id"])

    assert order.total == pytest.approx(72)
    assert order.status == Orders.Status.PENDING
    assert order.address_id == address.id

    order_items = OrderItems.objects.filter(order=order)

    assert order_items.count() == 3
    assert sum(item.items_total for item in order_items) == pytest.approx(72)

    for item in order_items:
        assert item.quantity == 2
        assert item.items_total == pytest.approx(item.product.price * item.quantity)


@pytest.mark.django_db
def test_create_order_reduces_product_stock(authenticated_client):
    add_product_basket(client=authenticated_client)
    address = Addresses.objects.create(
        location="home",
        user=Users.objects.get(username="test")
    )
    products_before = {
        product.id: product.quantity
        for product in Products.objects.all()
    }

    response = authenticated_client.post(
        url_creator("create order"),
        data={"address": address.id},
        format="json",
    )

    assert response.status_code == 201

    for product in Products.objects.all():
        assert product.quantity == products_before[product.id] - 2


@pytest.mark.django_db
def test_create_order_clears_basket(authenticated_client):
    add_product_basket(client=authenticated_client)
    address = Addresses.objects.create(
        location="home",
        user=Users.objects.get(username="test")
    )
    user = Users.objects.get(username="test")
    basket = Baskets.objects.get(user=user)

    assert BasketItems.objects.filter(basket=basket).count() == 3

    response = authenticated_client.post(
        url_creator("create order"),
        data={"address": address.id},
        format="json",
    )

    assert response.status_code == 201
    assert not BasketItems.objects.filter(basket=basket).exists()


@pytest.mark.django_db
def test_create_order_empty_basket_fails(authenticated_client):
    address = Addresses.objects.create(
        location="home",
        user=Users.objects.get(username="test")
    )
    response = authenticated_client.post(
        url_creator("create order"),
        data={"address": address.id},
        format="json",
    )

    assert response.status_code == 400
    assert response.json() == {
        "basket": "Your basket is empty."
    }
    assert not Orders.objects.exists()
    assert not OrderItems.objects.exists()


@pytest.mark.django_db
def test_create_order_insufficient_stock_fails(authenticated_client):
    products = add_product_basket(client=authenticated_client)
    address = Addresses.objects.create(
        location="home",
        user=Users.objects.get(username="test")
    )
    product = Products.objects.get(name="pr 1")
    product.quantity = 1
    product.save(update_fields=["quantity"])

    response = authenticated_client.post(
        url_creator("create order"),
        data={"address": address.id},
        format="json",
    )

    assert response.status_code == 400
    assert "quantity" in response.json()

    assert not Orders.objects.exists()
    assert not OrderItems.objects.exists()

    # The basket must remain unchanged.
    user = Users.objects.get(username="test")
    basket = Baskets.objects.get(user=user)

    assert BasketItems.objects.filter(basket=basket).count() == 3


@pytest.mark.django_db
def test_create_order_invalid_address_fails(authenticated_client):
    address = Addresses.objects.create(
        location="home",
        user=Users.objects.get(username="test")
    )
    response = authenticated_client.post(
        url_creator("create order"),
        data={"address": 999999},
        format="json",
    )

    assert response.status_code == 400
    assert not Orders.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "data",
    [
        {},
        {"address": None},
        {"address": "invalid"},
        {"address": ""},
    ],
)
def test_create_order_invalid_input_fails(authenticated_client, data):
    response = authenticated_client.post(
        url_creator("create order"),
        data=data,
        format="json",
    )

    assert response.status_code == 400
    assert not Orders.objects.exists()


@pytest.mark.django_db
def test_create_order_unauthenticated_fails(api_client):
    response = api_client.post(
        url_creator("create order"),
        data={"address": 1},
        format="json",
    )

    assert response.status_code in (401, 403)
    assert not Orders.objects.exists()


@pytest.mark.django_db
def test_create_order_does_not_affect_another_users_basket(
    authenticated_client,
    api_client,
):
    address = Addresses.objects.create(
        location="home",
        user=Users.objects.get(username="test")
    )
    add_product_basket(client=authenticated_client)

    # Create a second user and their basket.
    other_user = Users.objects.create_user(
        username="other",
        email="other@gmail.com",
        password="other-password",
    )

    other_product = Products.objects.create(
        name="other product",
        price=50,
        quantity=10,
    )

    other_basket = Baskets.objects.get(user=other_user)

    BasketItems.objects.create(
        basket=other_basket,
        product=other_product,
        quantity=3,
    )

    response = authenticated_client.post(
        url_creator("create order"),
        data={"address": address.id},
        format="json",
    )

    assert response.status_code == 201

    other_item = BasketItems.objects.get(
        basket=other_basket,
        product=other_product,
    )

    assert other_item.quantity == 3
    assert other_product.quantity == 10
