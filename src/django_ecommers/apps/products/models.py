from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=200)


class Products(models.Model):
    name = models.CharField()
    description = models.TextField(null=True, blank=True)
    price = models.FloatField()
    active = models.BooleanField(default=1)
    category_id = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
