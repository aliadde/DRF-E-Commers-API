from django.core.validators import MinValueValidator
from django.db import models

from django_ecommers.apps.products.models import Products
from django_ecommers.apps.users.models import Addresses, Users


class Orders(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        SHIPPED = "shipped", "Shipped"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(Users, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(default=None, null=True, blank=True)
    total = models.FloatField(
        blank=False, null=False, validators=[MinValueValidator(0)]
    )
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.PENDING,
    )
    address = models.ForeignKey(
        Addresses,
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
    )


class OrderItems(models.Model):
    order = models.ForeignKey(Orders, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    items_total = models.FloatField(validators=[MinValueValidator(0)])
    product = models.ForeignKey(
        Products, on_delete=models.SET_NULL, null=True, blank=False
    )
