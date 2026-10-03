from rest_framework import serializers

from .models import BasketItems, Baskets


class BasketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Baskets
        fields = "__all__"
        read_only_fields = ["id", "created_at", "user"]


class BasketItemsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BasketItems
        fields = "__all__"
        read_only_fields = ["id", "basket"]
