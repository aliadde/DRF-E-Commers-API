from django.contrib import admin

from .models import BasketItems, Baskets

admin.site.register(Baskets)
admin.site.register(BasketItems)
