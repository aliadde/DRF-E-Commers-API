from rest_framework import serializers

from .models import Category, Products


class CategoryPublicViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class ProductPublicViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Products
        fields = "__all__"


class ProductPrivateAdminViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Products
        fields = "__all__"
