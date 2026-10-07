import pytest

from django_ecommers.apps.baskets.models import BasketItems
from django_ecommers.apps.products.models import Category, Products
from django_ecommers.apps.users.models import Users
from django_ecommers.apps.baskets.models import Baskets


@pytest.mark.django_db
def test_authenticated_user_can_get_basket(api_client):
    # Arrange
    test_user = Users.objects.create_user(
        username="test_user",
        email="test_user@example.com",
        password="test_password",
    )

    test_basket = test_user.baskets

    test_category = Category.objects.create(
        name="test_category",
    )

    test_product_1 = Products.objects.create(
        name="test_product_1",
        description="test product 1",
        price=100.0,
        quantity=10,
        category=test_category,
    )

    test_product_2 = Products.objects.create(
        name="test_product_2",
        description="test product 2",
        price=200.0,
        quantity=20,
        category=test_category,
    )

    test_item_1 = BasketItems.objects.create(
        basket=test_basket,
        product=test_product_1,
        quantity=2,
    )

    test_item_2 = BasketItems.objects.create(
        basket=test_basket,
        product=test_product_2,
        quantity=3,
    )

    # Login through the real API
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
    response = api_client.get(
        "/basket/",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    # Assert
    assert response.status_code == 200

    response_data = response.json()

    assert "basket" in response_data
    assert "items" in response_data

    assert response_data["basket"]["id"] == test_basket.id
    assert response_data["basket"]["user"] == test_user.id

    assert len(response_data["items"]) == 2

    returned_items = {
        item["id"]: item
        for item in response_data["items"]
    }

    assert returned_items[test_item_1.id]["basket"] == test_basket.id
    assert returned_items[test_item_1.id]["product"] == test_product_1.id
    assert returned_items[test_item_1.id]["quantity"] == 2

    assert returned_items[test_item_2.id]["basket"] == test_basket.id
    assert returned_items[test_item_2.id]["product"] == test_product_2.id
    assert returned_items[test_item_2.id]["quantity"] == 3



# test authenticated user without basket
@pytest.mark.django_db
def test_authenticated_user_without_basket_gets_404(api_client):
    # Arrange
    test_user = Users.objects.create_user(
        username="test_user",
        email="test_user@example.com",
        password="test_password",
    )

    Baskets.objects.filter(user=test_user).delete()

    # Login through the real API
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
    response = api_client.get(
        "/basket/",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    # Assert
    assert response.status_code == 404


@pytest.mark.django_db
def test_unauthenticated_user_cannot_get_basket(api_client):
    response = api_client.get("/basket/")

    assert response.status_code == 401
