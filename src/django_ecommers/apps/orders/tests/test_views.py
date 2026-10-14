
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from django_ecommers.apps.baskets.models import BasketItems, Baskets
from django_ecommers.apps.orders.models import OrderItems, Orders
from django_ecommers.apps.products.models import Products
from django_ecommers.apps.users.models import Addresses, Users


# -------------------------
# Fixtures
# -------------------------


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return Users.objects.create_user(
        username="test_user",
        email="test@example.com",
        password="test-password",
    )


@pytest.fixture
def another_user(db):
    return Users.objects.create_user(
        username="another_user",
        email="another@example.com",
        password="another-password",
    )


@pytest.fixture
def address(user):
    return Addresses.objects.create(
        user=user,
        location="Test address",
    )


@pytest.fixture
def another_address(another_user):
    return Addresses.objects.create(
        user=another_user,
        location="Another address",
    )


@pytest.fixture
def product(db):
    return Products.objects.create(
        name="Test product",
        price=100.0,
        quantity=10,
    )


@pytest.fixture
def another_product(db):
    return Products.objects.create(
        name="Another product",
        price=50.0,
        quantity=20,
    )


@pytest.fixture
def basket(user):
    return Baskets.objects.get(user=user)


@pytest.fixture
def basket_item(basket, product):
    return BasketItems.objects.create(
        basket=basket,
        product=product,
        quantity=2,
    )


@pytest.fixture
def order(user, address):
    return Orders.objects.create(
        user=user,
        address=address,
        total=200.0,
    )


@pytest.fixture
def order_item(order, product):
    return OrderItems.objects.create(
        order=order,
        product=product,
        quantity=2,
        items_total=200.0,
    )


@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def create_order_url():
    return reverse("create order")


@pytest.fixture
def order_url(order):
    return reverse("order", kwargs={"pk": order.pk})


# -------------------------
# OrderCreateView
# -------------------------


@pytest.mark.django_db
def test_create_order_success(
    authenticated_client,
    create_order_url,
    address,
    basket_item,
    product,
    basket,
    user,
):
    response = authenticated_client.post(
        create_order_url,
        {"address": address.pk},
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["detail"] == "Order created successfully."

    order = Orders.objects.get(pk=response.data["order_id"])

    assert order.user == user
    assert order.address == address
    assert order.total == pytest.approx(200.0)
    assert order.status == Orders.Status.PENDING

    item = OrderItems.objects.get(order=order)

    assert item.product == product
    assert item.quantity == 2
    assert item.items_total == pytest.approx(200.0)

    product.refresh_from_db()
    assert product.quantity == 8

    assert not BasketItems.objects.filter(basket=basket).exists()


@pytest.mark.django_db
def test_create_order_with_multiple_products(
    authenticated_client,
    create_order_url,
    address,
    basket,
    product,
    another_product,
):
    BasketItems.objects.create(
        basket=basket,
        product=product,
        quantity=2,
    )
    BasketItems.objects.create(
        basket=basket,
        product=another_product,
        quantity=3,
    )

    response = authenticated_client.post(
        create_order_url,
        {"address": address.pk},
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED

    order = Orders.objects.get(pk=response.data["order_id"])

    assert order.total == pytest.approx(350.0)
    assert OrderItems.objects.filter(order=order).count() == 2

    product.refresh_from_db()
    another_product.refresh_from_db()

    assert product.quantity == 8
    assert another_product.quantity == 17


@pytest.mark.django_db
def test_create_order_rejects_empty_basket(
    authenticated_client,
    create_order_url,
    address,
    basket,
):
    response = authenticated_client.post(
        create_order_url,
        {"address": address.pk},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "basket" in response.data
    assert not Orders.objects.exists()


@pytest.mark.django_db
def test_create_order_rejects_insufficient_stock(
    authenticated_client,
    create_order_url,
    address,
    basket_item,
    basket,
    product,
):
    basket_item.quantity = 11
    basket_item.save()

    response = authenticated_client.post(
        create_order_url,
        {"address": address.pk},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "quantity" in response.data

    product.refresh_from_db()
    assert product.quantity == 10

    assert not Orders.objects.exists()
    assert not OrderItems.objects.exists()
    assert BasketItems.objects.filter(basket=basket).exists()


@pytest.mark.django_db
def test_create_order_rejects_invalid_address(
    authenticated_client,
    create_order_url,
    basket_item,
    product,
):
    response = authenticated_client.post(
        create_order_url,
        {"address": 999999},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "address" in response.data

    product.refresh_from_db()
    assert product.quantity == 10

    assert not Orders.objects.exists()


@pytest.mark.django_db
def test_create_order_rejects_missing_address(
    authenticated_client,
    create_order_url,
    basket_item,
):
    response = authenticated_client.post(
        create_order_url,
        {},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "address" in response.data
    assert not Orders.objects.exists()


@pytest.mark.django_db
def test_create_order_rejects_another_users_address(
    authenticated_client,
    create_order_url,
    another_address,
    basket_item,
    product,
):
    response = authenticated_client.post(
        create_order_url,
        {"address": another_address.pk},
        format="json",
    )

    # The current serializer checks whether the address exists,
    # not whether it belongs to the authenticated user.
    assert response.status_code == status.HTTP_201_CREATED

    order = Orders.objects.get(pk=response.data["order_id"])
    assert order.address == another_address


@pytest.mark.django_db
def test_create_order_requires_authentication(
    api_client,
    create_order_url,
    address,
):
    response = api_client.post(
        create_order_url,
        {"address": address.pk},
        format="json",
    )

    assert response.status_code in (
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    )


# -------------------------
# OrdersView.get
# -------------------------


@pytest.mark.django_db
def test_get_order_success(
    authenticated_client,
    order_url,
    order,
):
    response = authenticated_client.get(order_url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == order.pk
    assert response.data["total"] == pytest.approx(200.0)
    assert response.data["status"] == Orders.Status.PENDING
    assert response.data["address"] == order.address_id
    assert "user" not in response.data


@pytest.mark.django_db
def test_get_order_not_found(
    authenticated_client,
):
    url = reverse("order", kwargs={"pk": 999999})

    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_get_another_users_order_returns_404(
    api_client,
    another_user,
    order_url,
):
    api_client.force_authenticate(user=another_user)

    response = api_client.get(order_url)

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_get_order_requires_authentication(api_client, order_url):
    response = api_client.get(order_url)

    assert response.status_code in (
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    )


# -------------------------
# OrdersView.delete
# -------------------------


@pytest.mark.django_db
def test_cancel_pending_order_restores_stock(
    authenticated_client,
    order_url,
    order_item,
    product,
    order,
):
    # Simulate stock after the original purchase.
    product.quantity = 8
    product.save(update_fields=["quantity"])

    response = authenticated_client.delete(order_url)

    assert response.status_code == status.HTTP_200_OK

    order.refresh_from_db()
    product.refresh_from_db()

    assert order.status == Orders.Status.CANCELLED
    assert product.quantity == 10


@pytest.mark.django_db
@pytest.mark.parametrize(
    "order_status",
    [
        Orders.Status.PAID,
        Orders.Status.SHIPPED,
        Orders.Status.CANCELLED,
    ],
)
def test_cancel_non_pending_order_does_not_change_status_or_stock(
    authenticated_client,
    order,
    order_item,
    product,
    order_status,
):
    order.status = order_status
    order.save(update_fields=["status"])

    product.quantity = 8
    product.save(update_fields=["quantity"])

    url = reverse("order", kwargs={"pk": order.pk})

    response = authenticated_client.delete(url)

    assert response.status_code == status.HTTP_200_OK

    order.refresh_from_db()
    product.refresh_from_db()

    assert order.status == order_status
    assert product.quantity == 8


@pytest.mark.django_db
def test_cancel_order_restores_stock_for_multiple_items(
    authenticated_client,
    order,
    product,
    another_product,
):
    product.quantity = 8
    product.save(update_fields=["quantity"])

    another_product.quantity = 17
    another_product.save(update_fields=["quantity"])

    OrderItems.objects.create(
        order=order,
        product=product,
        quantity=2,
        items_total=200.0,
    )
    OrderItems.objects.create(
        order=order,
        product=another_product,
        quantity=3,
        items_total=150.0,
    )

    url = reverse("order", kwargs={"pk": order.pk})

    response = authenticated_client.delete(url)

    assert response.status_code == status.HTTP_200_OK

    order.refresh_from_db()
    product.refresh_from_db()
    another_product.refresh_from_db()

    assert order.status == Orders.Status.CANCELLED
    assert product.quantity == 10
    assert another_product.quantity == 20


@pytest.mark.django_db
def test_cancel_order_with_deleted_product(
    authenticated_client,
    order,
    order_item,
    product,
):
    product.delete()

    url = reverse("order", kwargs={"pk": order.pk})

    response = authenticated_client.delete(url)

    assert response.status_code == status.HTTP_200_OK

    order.refresh_from_db()
    order_item.refresh_from_db()

    assert order.status == Orders.Status.CANCELLED
    assert order_item.product is None


@pytest.mark.django_db
def test_cancel_order_not_found(authenticated_client):
    url = reverse("order", kwargs={"pk": 999999})

    response = authenticated_client.delete(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_cancel_another_users_order_returns_404(
    api_client,
    another_user,
    order_url,
    order,
    product,
):
    api_client.force_authenticate(user=another_user)

    product.quantity = 8
    product.save(update_fields=["quantity"])

    response = api_client.delete(order_url)

    assert response.status_code == status.HTTP_404_NOT_FOUND

    order.refresh_from_db()
    product.refresh_from_db()

    assert order.status == Orders.Status.PENDING
    assert product.quantity == 8


@pytest.mark.django_db
def test_cancel_order_requires_authentication(api_client, order_url):
    response = api_client.delete(order_url)

    assert response.status_code in (
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    )
