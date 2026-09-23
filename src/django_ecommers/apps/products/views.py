from django.shortcuts import get_object_or_404
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


class ProductUpdateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsStaffUser]

    def patch(self, request, pk):
        product = get_object_or_404(Products, pk=pk)

        serializer = ProductPrivateAdminViewSerializer(
            product, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk):

        product = get_object_or_404(Products, pk=pk)
        product.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
