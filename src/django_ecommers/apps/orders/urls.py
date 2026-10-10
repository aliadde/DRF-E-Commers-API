from django.urls import path

from django_ecommers.apps.orders.views import OrderCreateView, OrdersView

# order/...
urlpatterns = [
    path("", OrderCreateView.as_view(), name="create order"),
    path("/<int:pk>", OrdersView.as_view(), name="order"),
]
