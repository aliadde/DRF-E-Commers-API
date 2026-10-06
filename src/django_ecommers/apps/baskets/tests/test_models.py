# django_ecommers/apps/baskets/tests/test_models.py
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from django_ecommers.apps.baskets.models import Baskets, BasketItems
from django_ecommers.apps.products.models import Products
from django_ecommers.apps.users.models import Users


def make_user(username="test", **kwargs):
    # Adjust to your Users model (e.g. email-based login)
    return Users.objects.create_user(
        username=username,
        email="test_@gmail.com",
        password="pass12345",
        **kwargs
    )


def make_product(name="Keyboard", **kwargs):
    return Products.objects.create(name=name, price=10, quantity=2, **kwargs)


class BasketsModelTests(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_basket_is_created_for_user(self):
        basket = Baskets.objects.get(user=self.user)
        self.assertEqual(basket.user, self.user)
        self.assertEqual(self.user.baskets, basket)  # reverse OneToOne accessor

    def test_created_at_is_set_automatically(self):
        basket = Baskets.objects.get(user=self.user)
        self.assertIsNotNone(basket.created_at)

    def test_deleting_user_deletes_basket(self):
        Baskets.objects.get(user=self.user)
        self.user.delete()
        self.assertEqual(Baskets.objects.count(), 0)


class BasketItemsModelTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.basket = Baskets.objects.get(user=self.user)
        self.product = make_product()

    def test_quantity_defaults_to_one(self):
        item = BasketItems.objects.create(basket=self.basket, product=self.product)
        self.assertEqual(item.quantity, 1)

    def test_valid_quantity_passes_validation(self):
        item = BasketItems(basket=self.basket, product=self.product, quantity=5)
        item.full_clean()  # should not raise

    def test_zero_quantity_is_invalid(self):
        item = BasketItems(basket=self.basket, product=self.product, quantity=0)
        with self.assertRaises(ValidationError) as ctx:
            item.full_clean()
        self.assertIn("quantity", ctx.exception.message_dict)

    def test_negative_quantity_is_invalid(self):
        item = BasketItems(basket=self.basket, product=self.product, quantity=-3)
        with self.assertRaises(ValidationError) as ctx:
            item.full_clean()
        self.assertIn("quantity", ctx.exception.message_dict)

    def test_basket_can_hold_multiple_different_products(self):
        other = make_product(name="Mouse")
        BasketItems.objects.create(basket=self.basket, product=self.product)
        BasketItems.objects.create(basket=self.basket, product=other)
        self.assertEqual(self.basket.basketitems_set.count(), 2)

    def test_deleting_basket_deletes_items(self):
        BasketItems.objects.create(basket=self.basket, product=self.product)
        self.basket.delete()
        self.assertEqual(BasketItems.objects.count(), 0)

    def test_deleting_product_deletes_basket_items(self):
        BasketItems.objects.create(basket=self.basket, product=self.product)
        self.product.delete()
        self.assertEqual(BasketItems.objects.count(), 0)
        self.assertTrue(Baskets.objects.filter(pk=self.basket.pk).exists())
