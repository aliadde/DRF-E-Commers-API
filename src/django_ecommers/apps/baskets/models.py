from django.core.validators import MinValueValidator
from django.db import models

from django_ecommers.apps.products.models import Products
from django_ecommers.apps.users.models import Users


class Baskets(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class BasketItems(models.Model):
    basket = models.ForeignKey(Baskets, on_delete=models.CASCADE)
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)])
