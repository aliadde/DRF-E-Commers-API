
import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from django_ecommers.apps.orders.models import Orders, OrderItems
from django_ecommers.apps.products.models import Category, Products
from django_ecommers.apps.users.models import Addresses, Users


# --------------------
# Fixtures
# --------------------


@pytest.fixture
def user(db):
    # Use objects.create to avoid triggering create_user(),
    # which automatically creates a basket.
    return Users.objects.create(
        username="test_user",
        email="test@example.com",
    )


@pytest.fixture
def address(user):
    return Addresses.objects.create(
        user=user,
        location="Test address",
    )


@pytest.fixture
def product(db):
    return Products.objects.create(
        name="Test product",
        price=100.0,
        quantity=10,
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


# --------------------
# Orders tests
# --------------------


@pytest.mark.django_db
def test_order_default_values(order):
    assert order.status == Orders.Status.PENDING
    assert order.updated_at is None
    assert order.created_at is not None


@pytest.mark.django_db
def test_order_created_at_is_set(order):
    assert timezone.is_aware(order.created_at)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "total",
    [-1.0, -100.0],
)
def test_order_rejects_negative_total(order, total):
    order.total = total

    with pytest.raises(ValidationError) as exc_info:
        order.full_clean()

    assert "total" in exc_info.value.message_dict


@pytest.mark.django_db
def test_order_accepts_zero_total(order):
    order.total = 0.0
    order.full_clean()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "status",
    [
        Orders.Status.PENDING,
        Orders.Status.PAID,
        Orders.Status.SHIPPED,
        Orders.Status.CANCELLED,
    ],
)
def test_order_accepts_valid_status(order, status):
    order.status = status
    order.full_clean()


@pytest.mark.django_db
def test_order_rejects_invalid_status(order):
    order.status = "unknown"

    with pytest.raises(ValidationError) as exc_info:
        order.full_clean()

    assert "status" in exc_info.value.message_dict


@pytest.mark.django_db
def test_order_can_have_null_user(order):
    order.user = None
    order.full_clean()
    order.save()

    order.refresh_from_db()
    assert order.user is None


@pytest.mark.django_db
def test_deleting_order_user_sets_user_to_null(order):
    user = order.user

    user.delete()

    order.refresh_from_db()
    assert order.user is None


@pytest.mark.django_db
def test_deleting_order_address_sets_address_to_null(order):
    address = order.address

    address.delete()

    order.refresh_from_db()
    assert order.address is None


# --------------------
# OrderItems tests
# --------------------


@pytest.mark.django_db
def test_order_item_default_quantity(order, product):
    item = OrderItems.objects.create(
        order=order,
        product=product,
        items_total=100.0,
    )

    assert item.quantity == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    "quantity",
    [0, -1, -10],
)
def test_order_item_rejects_invalid_quantity(
    order_item,
    quantity,
):
    order_item.quantity = quantity

    with pytest.raises(ValidationError) as exc_info:
        order_item.full_clean()

    assert "quantity" in exc_info.value.message_dict


@pytest.mark.django_db
@pytest.mark.parametrize(
    "items_total",
    [-0.01, -10.0],
)
def test_order_item_rejects_negative_items_total(
    order_item,
    items_total,
):
    order_item.items_total = items_total

    with pytest.raises(ValidationError) as exc_info:
        order_item.full_clean()

    assert "items_total" in exc_info.value.message_dict


@pytest.mark.django_db
def test_order_item_accepts_zero_items_total(order_item):
    order_item.items_total = 0.0
    order_item.full_clean()


@pytest.mark.django_db
def test_deleting_product_sets_order_item_product_to_null(
    order_item,
):
    product = order_item.product

    product.delete()

    order_item.refresh_from_db()
    assert order_item.product is None


@pytest.mark.django_db
def test_deleting_order_cascades_to_order_items(order_item):
    order_id = order_item.order_id
    item_id = order_item.pk

    order_item.order.delete()

    assert not Orders.objects.filter(pk=order_id).exists()
    assert not OrderItems.objects.filter(pk=item_id).exists()
