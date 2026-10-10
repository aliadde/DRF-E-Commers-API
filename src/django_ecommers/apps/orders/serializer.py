from rest_framework import serializers

from django_ecommers.apps.users.models import Addresses


class CreateOrderSerializer(serializers.Serializer):
    address = serializers.PrimaryKeyRelatedField(queryset=Addresses.objects.all())
