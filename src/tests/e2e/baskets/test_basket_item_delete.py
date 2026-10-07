import pytest

from django_ecommers.apps.baskets.models import BasketItems
from django_ecommers.apps.products.models import Products
from django_ecommers.apps.users.models import Users


@pytest.mark.django_db
def test_authenticated_user_can_delete_own_basket_item(api_client):
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
        json={"username": "test_user", "password": "test_password"},
    )
    assert login_response.status_code == 200
    access_token = login_response.json()["access"]

    response = api_client.delete(
        f"/basket/items/{test_basket_item.id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    assert not BasketItems.objects.filter(id=test_basket_item.id).exists()


@pytest.mark.django_db
def test_user_cannot_delete_basket_item_belonging_to_another_user(api_client):
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
        json={"username": "test_user_1", "password": "test_password"},
    )
    assert login_response.status_code == 200
    access_token = login_response.json()["access"]

    response = api_client.delete(
        f"/basket/items/{test_basket_item.id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 404
    assert BasketItems.objects.filter(id=test_basket_item.id).exists()


@pytest.mark.django_db
def test_authenticated_user_gets_404_when_deleting_nonexistent_basket_item(
    api_client,
):
    test_user = Users.objects.create_user(
        username="test_user",
        email="test_user@example.com",
        password="test_password",
    )

    login_response = api_client.post(
        "/user/login/",
        json={"username": "test_user", "password": "test_password"},
    )
    assert login_response.status_code == 200
    access_token = login_response.json()["access"]

    response = api_client.delete(
        "/basket/items/999999",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_unauthenticated_user_cannot_delete_basket_item(api_client):
    response = api_client.delete("/basket/items/1")

    assert response.status_code == 401
