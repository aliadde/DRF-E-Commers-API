from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import BasketItems, Baskets
from .serializer import BasketItemsSerializer, BasketSerializer


class BasketView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_basket = Baskets.objects.filter(user_id=request.user.id).first()

        if not user_basket:
            return Response(status=status.HTTP_404_NOT_FOUND)

        basket_serializer = BasketSerializer(user_basket)

        basket_items = BasketItems.objects.filter(basket_id=user_basket.id)

        basket_items_serializer = BasketItemsSerializer(basket_items, many=True)

        return Response(
            {"basket": basket_serializer.data, "items": basket_items_serializer.data}
        )

    def post(self, request):
        user_basket = get_object_or_404(Baskets, user_id=request.user.id)

        serializer = BasketItemsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.validated_data["product"]
        quantity = serializer.validated_data["quantity"]

        with transaction.atomic():
            item, created = BasketItems.objects.get_or_create(
                basket=user_basket,
                product=product,
                defaults={"quantity": quantity},
            )
            if not created:
                item.quantity = F("quantity") + quantity
                item.save(update_fields=["quantity"])
                item.refresh_from_db()

        return Response(
            BasketItemsSerializer(item).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class BasketItemView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):

        user_basket = Baskets.objects.filter(user_id=request.user.id).first()
        if not user_basket:
            return Response(status=status.HTTP_404_NOT_FOUND)

        item = get_object_or_404(BasketItems, id=pk, basket=user_basket)

        item_serializer = BasketItemsSerializer(item)

        return Response(item_serializer.data)

    def patch(self, request, pk):
        pass

    def delete(self, request, pk):
        pass
