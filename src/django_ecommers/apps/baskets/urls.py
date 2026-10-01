from django.urls import path

from .views import BasketItemView, BasketView

# basket/...
urlpatterns = [
    path("/", BasketView.as_view(), name="basket"),
    path("basket_item/<int:pk>", BasketItemView.as_view(), name="basket_item"),
]
