import pytest

from django_ecommers.apps.baskets.models import BasketItems
from django_ecommers.apps.products.models import Products
from django_ecommers.apps.users.models import Users


@pytest.mark.django_db
def test_authenticated_user_can_update_basket_item_quantity(api_client):
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

    test_basket_item = BasketItems.objects.create(
        basket=test_basket,
        product=test_product,
        quantity=2,
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
    response = api_client.patch(
        f"/basket/items/{test_basket_item.id}",
        json={
            "product":test_product.id,
            "quantity": 5,
        },
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    # Assert
    assert response.status_code == 200

    response_data = response.json()

    assert response_data["id"] == test_basket_item.id
    assert response_data["basket"] == test_basket.id
    assert response_data["product"] == test_product.id
    assert response_data["quantity"] == 5

    test_basket_item.refresh_from_db()

    assert test_basket_item.quantity == 5


@pytest.mark.django_db
def test_authenticated_user_cannot_update_basket_item_beyond_stock(api_client):
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
        quantity=2,
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
    response = api_client.patch(
        f"/basket/items/{test_basket_item.id}",
        json={
            "quantity": 6,
        },
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    # Assert
    assert response.status_code == 400

    test_basket_item.refresh_from_db()

    assert test_basket_item.quantity == 2


@pytest.mark.django_db
@pytest.mark.parametrize("invalid_quantity", [0, -1])
def test_authenticated_user_cannot_update_basket_item_with_invalid_quantity(
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
    response = api_client.patch(
        f"/basket/items/{test_basket_item.id}",
        json={
            "quantity": invalid_quantity,
        },
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    # Assert
    assert response.status_code == 400

    test_basket_item.refresh_from_db()

    assert test_basket_item.quantity == 3


@pytest.mark.django_db
def test_user_cannot_update_basket_item_belonging_to_another_user(api_client):
    # Arrange
    test_user_1 = Users.objects.create_user(
        username="test_user_1",
        email="test_user_1@example.com",
        password="test_password",
    )

    test_user_2 = Users.objects.create_user(
        username="test_user_2",
        email="test_user_2@example.com",
        password="test_password",
    )

    test_product = Products.objects.create(
        name="test_product",
        price=100.0,
        quantity=10,
    )

    test_basket_item = BasketItems.objects.create(
        basket=test_user_2.baskets,
        product=test_product,
        quantity=3,
    )

    login_response = api_client.post(
        "/user/login/",
        json={
            "username": "test_user_1",
            "password": "test_password",
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access"]

    # Act
    response = api_client.patch(
        f"/basket/items/{test_basket_item.id}",
        json={
            "quantity": 5,
        },
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    # Assert
    assert response.status_code == 404

    test_basket_item.refresh_from_db()

    assert test_basket_item.quantity == 3


@pytest.mark.django_db
def test_authenticated_user_gets_404_when_updating_nonexistent_basket_item(
    api_client,
):
    # Arrange
    test_user = Users.objects.create_user(
        username="test_user",
        email="test_user@example.com",
        password="test_password",
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
    response = api_client.patch(
        "/basket/items/999999",
        json={
            "quantity": 5,
        },
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    # Assert
    assert response.status_code == 404


@pytest.mark.django_db
def test_unauthenticated_user_cannot_update_basket_item(api_client):
    response = api_client.patch(
        "/basket/items/1",
        json={
            "quantity": 5,
        },
    )

    assert response.status_code == 401
