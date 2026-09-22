from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("user/", include("django_ecommers.apps.users.urls")),
    path("product/", include("django_ecommers.apps.products.urls")),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
