import pytest

from django_ecommers.apps.baskets.models import BasketItems
from django_ecommers.apps.products.models import Products
from django_ecommers.apps.users.models import Users

@pytest.mark.django_db
def test_authenticated_user_can_add_new_product_to_basket(api_client):
    # Arrange
    test_user = Users.objects.create_user(
        username="test_user",
        email="test_user@example.com",
        password="test_password",
    )

    test_basket = test_user.baskets

    test_product = Products.objects.create(
        name="test_product",
        description="test product",
        price=100.0,
        quantity=10,
    )

    login_response = api_client.post(
        "/user/login/",
        json={
            "username": "test_user",
            "password": "test_password",
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access"]

    # Act
    response = api_client.post(
        "/basket/",
        json={
            "product": test_product.id,
            "quantity": 3,
        },
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    # Assert
    assert response.status_code == 201

    response_data = response.json()

    assert response_data["basket"] == test_basket.id
    assert response_data["product"] == test_product.id
    assert response_data["quantity"] == 3

    basket_item = BasketItems.objects.get(
        basket=test_basket,
        product=test_product,
    )

    assert basket_item.quantity == 3

@pytest.mark.django_db
def test_authenticated_user_cannot_add_product_exceeding_stock(api_client):
    # Arrange
    test_user = Users.objects.create_user(
        username="test_user",
        email="test_user@example.com",
        password="test_password",
    )

    test_basket = test_user.baskets

    test_product = Products.objects.create(
        name="test_product",
        price=100.0,
        quantity=5,
    )

    login_response = api_client.post(
        "/user/login/",
        json={
            "username": "test_user",
            "password": "test_password",
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access"]

    # Act
    response = api_client.post(
        "/basket/",
        json={
            "product": test_product.id,
            "quantity": 6,
        },
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    # Assert
    assert response.status_code == 400

    assert response.json() == {
        "detail": "Requested quantity exceeds available stock."
    }


@pytest.mark.django_db
def test_authenticated_user_cannot_increase_item_beyond_stock(api_client):
    # Arrange
    test_user = Users.objects.create_user(
        username="test_user",
        email="test_user@example.com",
        password="test_password",
    )

    test_basket = test_user.baskets

    test_product = Products.objects.create(
        name="test_product",
        price=100.0,
        quantity=5,
    )

    test_basket_item = BasketItems.objects.create(
        basket=test_basket,
        product=test_product,
        quantity=3,
    )

    login_response = api_client.post(
        "/user/login/",
        json={
            "username": "test_user",
            "password": "test_password",
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access"]

    # Act
    response = api_client.post(
        "/basket/",
        json={
            "product": test_product.id,
            "quantity": 3,
        },
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    # Assert
    assert response.status_code == 400

    assert response.json() == {
        "detail": "Requested quantity exceeds available stock."
    }

    test_basket_item.refresh_from_db()

    assert test_basket_item.quantity == 3

@pytest.mark.django_db
@pytest.mark.parametrize("invalid_quantity", [0, -1])
def test_authenticated_user_cannot_add_product_with_invalid_quantity(
    api_client,
    invalid_quantity,
):
    # Arrange
    test_user = Users.objects.create_user(
        username="test_user",
        email="test_user@example.com",
        password="test_password",
    )

    test_basket = test_user.baskets

    test_product = Products.objects.create(
        name="test_product",
        price=100.0,
        quantity=10,
    )

    login_response = api_client.post(
        "/user/login/",
        json={
            "username": "test_user",
            "password": "test_password",
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access"]

    # Act
    response = api_client.post(
        "/basket/",
        json={
            "product": test_product.id,
            "quantity": invalid_quantity,
        },
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    # Assert
    assert response.status_code == 400

    assert not BasketItems.objects.filter(
        basket=test_basket,
        product=test_product,
    ).exists()

@pytest.mark.django_db
def test_unauthenticated_user_cannot_add_product_to_basket(api_client):
    response = api_client.post(
        "/basket/",
        json={
            "product": 1,
            "quantity": 1,
        },
    )

    assert response.status_code == 401
