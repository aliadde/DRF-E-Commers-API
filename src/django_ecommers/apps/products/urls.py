from django.urls import path

from .views import ProductsPrivateAdminView, ProductsPublicView

# /product/...
urlpatterns = [
    path("all/", ProductsPublicView.as_view(), name="get_all_products"),
    path("", ProductsPrivateAdminView.as_view(), name="product"),
]
