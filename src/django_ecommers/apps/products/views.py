from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import Products
from .permissions import IsStaffUser
from .serializer import ProductPrivateAdminViewSerializer, ProductPublicViewSerializer


class ProductsPublicView(APIView):
    def get(self, request):
        products = Products.objects.all()
        serializer = ProductPublicViewSerializer(products, many=True)

        return Response(serializer.data)


class ProductsPrivateAdminView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsStaffUser]

    def post(self, request):
        serializer = ProductPrivateAdminViewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def patch(self, request):
        pass

    def delete(self, request):
        pass
