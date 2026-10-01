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

        return Response(basket_serializer.data)


class BasketItemView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):

        user_basket = Baskets.objects.filter(user_id=request.user.id).first()
        if not user_basket or user_basket.id != pk:
            return Response(status=status.HTTP_404_NOT_FOUND)

        basket_items = BasketItems.objects.filter(basket_id=pk)

        basket_items_serializer = BasketItemsSerializer(basket_items, many=True)

        return Response(basket_items_serializer.data)

    def post(self, request, pk):
        pass

    def patch(self, request, pk):
        pass

    def delete(self, request, pk):
        pass
