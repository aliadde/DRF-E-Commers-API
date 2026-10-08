from django.urls import path

from django_ecommers.apps.orders.views import OrdersView

# order/...
urlpatterns = [
    path("something", OrdersView.as_view(), name="something"),
]
