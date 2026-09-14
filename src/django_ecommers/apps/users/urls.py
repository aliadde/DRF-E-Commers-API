"""all users related urls."""

from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView

from django_ecommers.apps.users.views import (
    UserPasswordResetView,
    UserPrivateView,
    UserPublicView,
)

# user/...
urlpatterns = [
    path("register/", view=UserPublicView.as_view(), name="users_register"),
    path("login/", TokenObtainPairView.as_view(), name="login"),
    path("me/", UserPrivateView.as_view(), name="users_private"),
    path("reset_password/", UserPasswordResetView.as_view(), name="reset_password"),
]
