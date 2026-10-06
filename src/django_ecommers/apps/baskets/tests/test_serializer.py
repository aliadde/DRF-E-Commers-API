# django_ecommers/apps/baskets/tests/test_serializers.py
import unittest

from django.test import TestCase

from django_ecommers.apps.baskets.models import Baskets, BasketItems
from django_ecommers.apps.baskets.serializer import (
    BasketItemsSerializer,
    BasketSerializer,
)
from django_ecommers.apps.products.models import Products
from django_ecommers.apps.users.models import Users


def make_user(username="test", **kwargs):
    return Users.objects.create_user(
        username=username,
        email=f"{username}_@gmail.com",
        password="pass12345",
        **kwargs
    )


def make_product(name="Keyboard", quantity=10, **kwargs):
    return Products.objects.create(name=name, price=10, quantity=quantity, **kwargs)


class BasketSerializerTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.basket = Baskets.objects.get(user=self.user)

    def test_serialized_output_fields(self):
        data = BasketSerializer(self.basket).data
        self.assertEqual(set(data.keys()), {"id", "user", "created_at"})
        self.assertEqual(data["id"], self.basket.id)
        self.assertEqual(data["user"], self.user.pk)

    def test_read_only_fields_are_ignored_on_input(self):
        other_user = make_user(username="sara")
        serializer = BasketSerializer(
            data={"id": 999, "user": other_user.pk, "created_at": "2000-01-01T00:00:00Z"}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data, {})

class BasketItemsSerializerTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.basket = Baskets.objects.get(user=self.user)
        self.product = make_product(quantity=10)

    def make_item(self, quantity=2):
        return BasketItems.objects.create(
            basket=self.basket, product=self.product, quantity=quantity
        )

    # ---------- serialization ----------
    def test_serialized_output_fields(self):
        item = self.make_item(quantity=3)
        data = BasketItemsSerializer(item).data
        self.assertEqual(set(data.keys()), {"id", "basket", "product", "quantity"})
        self.assertEqual(data["basket"], self.basket.pk)
        self.assertEqual(data["product"], self.product.pk)
        self.assertEqual(data["quantity"], 3)

    # ---------- creation / field validation ----------
    def test_valid_data_creates_item(self):
        serializer = BasketItemsSerializer(
            data={"product": self.product.pk, "quantity": 2}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        item = serializer.save(basket=self.basket)
        self.assertEqual(item.basket, self.basket)
        self.assertEqual(item.product, self.product)
        self.assertEqual(item.quantity, 2)

    def test_quantity_is_required(self):
        # The explicit IntegerField overrides the model default of 1
        serializer = BasketItemsSerializer(data={"product": self.product.pk})
        self.assertFalse(serializer.is_valid())
        self.assertIn("quantity", serializer.errors)

    def test_quantity_zero_is_invalid(self):
        serializer = BasketItemsSerializer(
            data={"product": self.product.pk, "quantity": 0}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("quantity", serializer.errors)

    def test_negative_quantity_is_invalid(self):
        serializer = BasketItemsSerializer(
            data={"product": self.product.pk, "quantity": -5}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("quantity", serializer.errors)

    def test_non_integer_quantity_is_invalid(self):
        serializer = BasketItemsSerializer(
            data={"product": self.product.pk, "quantity": "abc"}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("quantity", serializer.errors)

    def test_product_is_required(self):
        serializer = BasketItemsSerializer(data={"quantity": 1})
        self.assertFalse(serializer.is_valid())
        self.assertIn("product", serializer.errors)

    def test_nonexistent_product_is_invalid(self):
        serializer = BasketItemsSerializer(data={"product": 99999, "quantity": 1})
        self.assertFalse(serializer.is_valid())
        self.assertIn("product", serializer.errors)

    def test_basket_in_input_is_ignored(self):
        other_basket = Baskets.objects.get(user=make_user(username="sara"))
        serializer = BasketItemsSerializer(
            data={"basket": other_basket.pk, "product": self.product.pk, "quantity": 1}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertNotIn("basket", serializer.validated_data)
        item = serializer.save(basket=self.basket)
        self.assertEqual(item.basket, self.basket)

    # ---------- stock validation on update ----------
    def test_update_within_stock_is_valid(self):
        item = self.make_item(quantity=2)
        serializer = BasketItemsSerializer(
            item, data={"product": self.product.pk, "quantity": 5}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.save().quantity, 5)

    def test_update_to_exact_stock_is_valid(self):
        item = self.make_item(quantity=2)
        serializer = BasketItemsSerializer(
            item, data={"product": self.product.pk, "quantity": 10}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_update_exceeding_stock_is_invalid(self):
        item = self.make_item(quantity=2)
        serializer = BasketItemsSerializer(
            item, data={"product": self.product.pk, "quantity": 11}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("quantity", serializer.errors)
        self.assertIn("exceeds available stock", str(serializer.errors["quantity"][0]))

    def test_partial_update_exceeding_stock_is_invalid(self):
        item = self.make_item(quantity=2)
        serializer = BasketItemsSerializer(item, data={"quantity": 50}, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn("quantity", serializer.errors)

    def test_partial_update_without_quantity_skips_stock_check(self):
        item = self.make_item(quantity=2)
        self.product.quantity = 0  # stock is now lower than the basket quantity
        self.product.save()
        serializer = BasketItemsSerializer(item, data={}, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    # ---------- known gap ----------
    @unittest.expectedFailure
    def test_create_exceeding_stock_should_be_invalid(self):
        # Currently PASSES validation because validate_quantity only checks
        # when self.instance exists (update). This test documents the gap.
        serializer = BasketItemsSerializer(
            data={"product": self.product.pk, "quantity": 999}
        )
        self.assertFalse(serializer.is_valid())
