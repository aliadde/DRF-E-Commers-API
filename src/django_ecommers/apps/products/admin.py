from django.contrib import admin

from django_ecommers.apps.products.models import Category, Products

admin.site.register(Products)
admin.site.register(Category)
