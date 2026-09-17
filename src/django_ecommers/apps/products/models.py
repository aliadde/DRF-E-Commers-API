from django.db import models


class Products(models.Model):
    name = models.CharField()
    description = models.TextField(null=True, blank=True)
    price = models.FloatField()
    active = models.BooleanField(default=1)
    # category = models.ForeignKey()  connect to category model table
