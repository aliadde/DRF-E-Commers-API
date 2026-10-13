from rest_framework import serializers

from django_ecommers.apps.orders.models import Orders
from django_ecommers.apps.users.models import Addresses


class CreateOrderSerializer(serializers.Serializer):
    address = serializers.PrimaryKeyRelatedField(queryset=Addresses.objects.all())


class GetOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Orders
        exclude = [
            "user",
        ]
