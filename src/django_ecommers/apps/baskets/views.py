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


class BasketItemView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):

        user_basket = Baskets.objects.filter(user_id=request.user.id).first()
        if not user_basket:
            return Response(status=status.HTTP_404_NOT_FOUND)

        item = BasketItems.objects.get(id=pk)
        if not item or item.basket_id != user_basket.id:
            return Response(status=status.HTTP_404_NOT_FOUND)

        item_serializer = BasketItemsSerializer(item)

        return Response(item_serializer.data)

    def post(self, request, pk):
        basket_items_serializer = BasketItemsSerializer(data=request.data)

        if basket_items_serializer.is_valid(raise_exception=True):
            basket_items_serializer.save()

    def patch(self, request, pk):
        pass

    def delete(self, request, pk):
        pass
