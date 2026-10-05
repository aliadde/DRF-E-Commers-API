from rest_framework import serializers

from .models import BasketItems, Baskets


class BasketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Baskets
        fields = "__all__"
        read_only_fields = ["id", "created_at", "user"]


class BasketItemsSerializer(serializers.ModelSerializer):
    quantity = serializers.IntegerField(min_value=1)

    class Meta:
        model = BasketItems
        fields = "__all__"
        read_only_fields = ["id", "basket"]

    def validate_quantity(self, value):
        if self.instance and value > self.instance.product.quantity:
            raise serializers.ValidationError(
                "Requested quantity exceeds available stock."
            )
        return value
