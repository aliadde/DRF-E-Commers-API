from django.urls import path

from .views import (
    ProductsPrivateAdminView,
    ProductsPublicView,
    ProductUpdateView,
)

# /product/...
urlpatterns = [
    path("all/", ProductsPublicView.as_view(), name="get_all_products"),
    path("<int:pk>/", ProductUpdateView.as_view(), name="update_product"),
    path("", ProductsPrivateAdminView.as_view(), name="product"),
]
