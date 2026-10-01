from django.core.validators import MinValueValidator
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=200)


class Products(models.Model):
    name = models.CharField(unique=True, null=False, blank=False)
    description = models.TextField(null=True, blank=True)
    price = models.FloatField(validators=[MinValueValidator(0.0)])
    active = models.BooleanField(default=1)
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(0)])
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
