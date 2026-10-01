from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView


class BasketView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        pass


class BasketItemView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        pass

    def patch(self, request):
        pass

    def delete(self, request):
        pass
