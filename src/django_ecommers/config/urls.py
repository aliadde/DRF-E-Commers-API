from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("user/", include("django_ecommers.apps.users.urls")),
    path("product/", include("django_ecommers.apps.products.urls")),
    path("basket/", include("django_ecommers.apps.baskets.urls")),
    path("order/", include("django_ecommers.apps.orders.urls")),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]
