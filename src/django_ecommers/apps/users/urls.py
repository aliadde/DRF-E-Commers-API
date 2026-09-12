"""all users related urls."""

from django.urls import path

from django_ecommers.apps.users.views import UserView

urlpatterns = [
    path("auth/", view=UserView.as_view(), name="users"),
]
