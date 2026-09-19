from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Products
from .serializer import ProductPublicViewSerializer


class ProductsPublicView(APIView):
    def get(self, request):
        products = Products.objects.all()
        serializer = ProductPublicViewSerializer(products, many=True)

        return Response(serializer.data)
