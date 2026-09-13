"""all users related urls."""

from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView

from django_ecommers.apps.users.views import UserView

urlpatterns = [
    path("auth/", view=UserView.as_view(), name="users"),
    path("login/", TokenObtainPairView.as_view(), name="login"),
]
