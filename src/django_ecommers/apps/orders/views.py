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

from .serializer import CreateOrderSerializer, GetOrderSerializer


class OrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """get specific order data."""

        # get from database
        order = get_object_or_404(Orders, id=pk, user=request.user)

        # filter with serializer
        serializer = GetOrderSerializer(order)

        # return to user
        return Response(serializer.data)

    def delete(self, request, pk):
        """cancel an order"""
        with transaction.atomic():
            # get order that requested
            order = get_object_or_404(
                Orders.objects.select_for_update(),
                user=request.user,
                id=pk,
            )

            # only pending orders can be cancelled
            if order.status == Orders.Status.PENDING:
                order.status = Orders.Status.CANCELLED

                # back the product quantity
                orderitems = OrderItems.objects.filter(order=order).select_related(
                    "product"
                )

                product_ids = orderitems.values_list("product_id", flat=True)

                products = (
                    Products.objects.select_for_update()
                    .filter(id__in=product_ids)
                    .order_by("id")
                )

                locked_products = {product.id: product for product in products}

                for item in orderitems:
                    product = locked_products.get(item.product_id)

                    if product:
                        product.quantity += item.quantity
                        product.save()

                order.save()

        return Response(status=status.HTTP_200_OK)


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
