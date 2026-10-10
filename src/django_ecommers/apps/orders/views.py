from rest_framework.views import APIView


class OrdersView(APIView):
    def get(self, request, pk):
        """get specific order data."""

    def delete(self, request, pk):
        """cancel a order"""


class OrderCreateView(APIView):
    def post(self, request):
        """create order from basket"""
