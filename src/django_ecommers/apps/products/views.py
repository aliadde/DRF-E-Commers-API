from django.core.cache import cache
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import Category, Products
from .permissions import IsStaffUser
from .serializer import (
    CategoryPublicViewSerializer,
    ProductPrivateAdminViewSerializer,
    ProductPublicViewSerializer,
)


class CategoryPublicView(ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategoryPublicViewSerializer


class ProductsPublicView(APIView):
    def get(self, request):
        cached_products = cache.get("all_products")

        if not cached_products:
            products = Products.objects.all()
            serializer = ProductPublicViewSerializer(products, many=True)

            cache.set("all_products", serializer.data, timeout=60 * 15)

            return Response(serializer.data)

        return Response(cached_products)


class ProductsPrivateAdminView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsStaffUser]

    def post(self, request):
        serializer = ProductPrivateAdminViewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        cache.delete("all_products")

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

        cache.delete("all_products")

        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk):

        product = get_object_or_404(Products, pk=pk)
        product.delete()

        cache.delete("all_products")

        return Response(status=status.HTTP_204_NO_CONTENT)
