from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from django_ecommers.apps.baskets.models import BasketItems, Baskets
from django_ecommers.apps.orders.models import OrderItems, Orders
from django_ecommers.apps.products.models import Products
from django_ecommers.apps.users.models import Addresses, Users

from .serializer import CreateOrderSerializer


class OrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """get specific order data."""

    def delete(self, request, pk):
        """cancel a order"""


class OrderCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            user_basket = get_object_or_404(
                Baskets,
                user=request.user,
            )

            basket_items = list(
                BasketItems.objects.filter(basket=user_basket).select_related("product")
            )

            if not basket_items:
                raise serializers.ValidationError({"basket": "Your basket is empty."})

            # Lock product rows to prevent concurrent stock updates.
            product_ids = {item.product_id for item in basket_items}

            products = Products.objects.select_for_update().filter(pk__in=product_ids)
            products_by_id = {product.pk: product for product in products}

            total: float = 0.0

            for item in basket_items:
                product = products_by_id[item.product_id]

                if item.quantity > product.quantity:
                    raise serializers.ValidationError(
                        {
                            "quantity": (
                                f"Insufficient stock for {product.name}. "
                                f"Available: {product.quantity}, "
                                f"requested: {item.quantity}."
                            )
                        }
                    )

                total += product.price * item.quantity

            order = Orders(
                user=request.user,
                total=total,
                address=serializer.validated_data["address"],
            )

            try:
                order.full_clean()
            except DjangoValidationError as exc:
                raise serializers.ValidationError(  # noqa:B904
                    exc.message_dict
                    if hasattr(exc, "message_dict")
                    else {"detail": exc.messages}
                )

            order.save()

            for item in basket_items:
                product = products_by_id[item.product_id]

                OrderItems.objects.create(
                    order=order,
                    quantity=item.quantity,
                    items_total=product.price * item.quantity,
                    product=product,
                )

                # Actually deduct the purchased quantity.
                product.quantity -= item.quantity
                product.save(update_fields=["quantity"])

            #  clear the basket after successful order creation.
            BasketItems.objects.filter(basket=user_basket).delete()

        return Response(
            {
                "detail": "Order created successfully.",
                "order_id": order.pk,
            },
            status=status.HTTP_201_CREATED,
        )
