from django.urls import path

from .views import ProductsPublicView

# /product/...
urlpatterns = [path("all/", ProductsPublicView.as_view(), name="get_all_products")]
