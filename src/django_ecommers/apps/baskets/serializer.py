from rest_framework import serializers

from .models import BasketItems, Baskets


class BasketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Baskets
        fields = "__all__"


class BasketItemsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BasketItems
        fields = "__all__"
