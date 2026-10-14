
import pytest

from django_ecommers.apps.orders.models import Orders
from django_ecommers.apps.orders.serializer import (
    CreateOrderSerializer,
    GetOrderSerializer,
)
from django_ecommers.apps.users.models import Addresses, Users


@pytest.fixture
def user(db):
    return Users.objects.create(
        username="serializer_test_user",
        email="serializer_test@example.com",
    )


@pytest.fixture
def address(user):
    return Addresses.objects.create(
        user=user,
        location="Test address",
    )


@pytest.fixture
def another_user(db):
    return Users.objects.create(
        username="another_test_user",
        email="another_test@example.com",
    )


@pytest.fixture
def another_address(another_user):
    return Addresses.objects.create(
        user=another_user,
        location="Another test address",
    )


@pytest.fixture
def order(user, address):
    return Orders.objects.create(
        user=user,
        address=address,
        total=200.0,
    )


# -------------------------
# CreateOrderSerializer
# -------------------------


@pytest.mark.django_db
def test_create_order_serializer_accepts_valid_address(address):
    serializer = CreateOrderSerializer(
        data={"address": address.pk}
    )

    assert serializer.is_valid()
    assert serializer.validated_data["address"] == address


@pytest.mark.django_db
def test_create_order_serializer_rejects_missing_address():
    serializer = CreateOrderSerializer(data={})

    assert not serializer.is_valid()
    assert "address" in serializer.errors


@pytest.mark.django_db
@pytest.mark.parametrize(
    "invalid_address",
    [
        999999,
        0,
        -1,
        "invalid",
    ],
)
def test_create_order_serializer_rejects_invalid_address(
    invalid_address,
):
    serializer = CreateOrderSerializer(
        data={"address": invalid_address}
    )

    assert not serializer.is_valid()
    assert "address" in serializer.errors


@pytest.mark.django_db
def test_create_order_serializer_rejects_null_address():
    serializer = CreateOrderSerializer(
        data={"address": None}
    )

    assert not serializer.is_valid()
    assert "address" in serializer.errors


@pytest.mark.django_db
def test_create_order_serializer_rejects_nonexistent_address():
    serializer = CreateOrderSerializer(
        data={"address": 999999}
    )

    assert not serializer.is_valid()
    assert "address" in serializer.errors


@pytest.mark.django_db
def test_create_order_serializer_accepts_address_owned_by_another_user(
    another_address,
):
    serializer = CreateOrderSerializer(
        data={"address": another_address.pk}
    )

    assert serializer.is_valid()
    assert serializer.validated_data["address"] == another_address


# -------------------------
# GetOrderSerializer
# -------------------------


@pytest.mark.django_db
def test_get_order_serializer_returns_expected_fields(order):
    serializer = GetOrderSerializer(order)

    assert set(serializer.data.keys()) == {
        "id",
        "created_at",
        "updated_at",
        "total",
        "status",
        "address",
    }


@pytest.mark.django_db
def test_get_order_serializer_excludes_user(order):
    serializer = GetOrderSerializer(order)

    assert "user" not in serializer.data


@pytest.mark.django_db
def test_get_order_serializer_returns_order_values(order):
    serializer = GetOrderSerializer(order)
    data = serializer.data

    assert data["id"] == order.pk
    assert data["total"] == order.total
    assert data["status"] == Orders.Status.PENDING
    assert data["address"] == order.address_id


@pytest.mark.django_db
def test_get_order_serializer_returns_null_updated_at(order):
    serializer = GetOrderSerializer(order)

    assert serializer.data["updated_at"] is None


@pytest.mark.django_db
def test_get_order_serializer_serializes_updated_at(order):
    from django.utils import timezone

    order.updated_at = timezone.now()
    order.save(update_fields=["updated_at"])

    serializer = GetOrderSerializer(order)

    assert serializer.data["updated_at"] is not None
